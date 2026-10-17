"""Deterministic evaluation over high-risk rows from held-out engines."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from time import perf_counter_ns

import numpy as np
import pandas as pd

from prescriptxai.constraints.bounds import (
    allowed_interval,
    check_bound_violations,
    check_rate_violations,
)
from prescriptxai.evaluation.metrics import EvaluationRecord, EvaluationSummary, calculate_metrics
from prescriptxai.pipeline import PrescriptXAIEngine

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationRun:
    """Actual evaluation records and their aggregate metrics."""

    records: tuple[EvaluationRecord, ...]
    summary: EvaluationSummary
    direction_consistency: DirectionConsistency = field(
        default_factory=lambda: DirectionConsistency(1.0, 0, None, {})
    )
    infeasible_high_risk_states: int = 0


@dataclass(frozen=True)
class DirectionConsistency:
    """Sign agreement among recommendations for nearby scaled operating states."""

    similarity_radius: float
    similar_pair_count: int
    pairwise_sign_agreement: float | None
    per_feature_sign_agreement: dict[str, float | None]


def evaluate_states(
    engine: PrescriptXAIEngine,
    held_out_rows: pd.DataFrame,
    ingestion_ms: float | None = None,
) -> EvaluationRun:
    """Sample high-risk held-out states reproducibly and run full recommendation validation."""
    if held_out_rows.empty:
        summary = calculate_metrics((), 0, None, ingestion_ms, engine.config.evaluation)
        return EvaluationRun(
            (),
            summary,
            DirectionConsistency(
                engine.config.evaluation.direction_similarity_radius, 0, None, {}
            ),
            0,
        )
    missing = set(engine.model.feature_names) - set(held_out_rows.columns)
    if missing:
        raise ValueError(f"held-out data is missing model features: {sorted(missing)}")
    risk_scores = engine.model.predict_risk(held_out_rows[list(engine.model.feature_names)])
    high_risk_indices = np.flatnonzero(risk_scores >= engine.config.model.danger_threshold)
    eligible_count = int(len(high_risk_indices))
    actionable_indices = np.asarray(
        [
            index
            for index in high_risk_indices
            if _has_feasible_actuator_intervals(engine, held_out_rows.iloc[int(index)])
        ],
        dtype=np.int64,
    )
    infeasible_count = eligible_count - len(actionable_indices)
    selected = actionable_indices
    if len(actionable_indices) > engine.config.evaluation.max_queries:
        rng = np.random.default_rng(engine.config.evaluation.random_seed)
        selected = np.sort(
            rng.choice(
                actionable_indices,
                size=engine.config.evaluation.max_queries,
                replace=False,
            )
        )
    feature_groups = engine.taxonomy.feature_groups.model_dump()
    state_features = tuple(
        dict.fromkeys(name for group in feature_groups.values() for name in group["features"])
    )
    missing_state_fields = set(state_features) - set(held_out_rows.columns)
    if missing_state_fields:
        raise ValueError(
            f"held-out data is missing configured state fields: {sorted(missing_state_fields)}"
        )
    records: list[EvaluationRecord] = []
    sampled_states: list[dict[str, float]] = []
    inference_samples_ms: list[float] = []
    for index in selected:
        row = held_out_rows.iloc[int(index)]
        state = {name: float(row[name]) for name in state_features}
        sampled_states.append(state)
        inference_started = perf_counter_ns()
        engine.model.predict_risk(pd.DataFrame([state], columns=engine.model.feature_names))
        inference_samples_ms.append((perf_counter_ns() - inference_started) / 1_000_000)
        result = engine.recommend(state)
        if not result.optimization.actuator_constraints_feasible:
            raise RuntimeError(
                "evaluation pre-screen selected a state without feasible actuator intervals"
            )
        frozen_names = engine.taxonomy.immutable_feature_names()
        frozen_violations = sum(
            state.get(name) != result.optimization.state.get(name)
            for name in frozen_names
            if name in state
        )
        actuator_names = tuple(engine.taxonomy.actuator_constraints)
        bound_violations = check_bound_violations(
            result.optimization.state, engine.taxonomy, features=actuator_names
        )
        rate_violations = check_rate_violations(
            state, result.optimization.state, engine.taxonomy
        )
        records.append(
            EvaluationRecord(
                engine_id=int(row["engine_id"]),
                cycle=int(row["cycle"]),
                initial_risk=result.optimization.initial_risk,
                final_risk=result.optimization.final_risk,
                model_valid=result.outcome.model_valid,
                tier2_plausible=result.outcome.tier2_plausible,
                tier3_engineering_valid=result.outcome.tier3_engineering_valid,
                tier4_coupling_valid=result.outcome.tier4_coupling_valid,
                changed_features=len(result.outcome.deltas),
                optimization_ms=result.optimization_ms,
                validation_ms=result.validation_ms,
                solver_success=result.optimization.solver_success,
                message=result.optimization.message,
                counterfactual_signs=result.optimization.counterfactual_signs,
                frozen_feature_violations=frozen_violations,
                actuator_bound_violations=len(bound_violations),
                rate_limit_violations=len(rate_violations),
            )
        )
    inference_per_row = float(np.mean(inference_samples_ms)) if inference_samples_ms else None
    record_tuple = tuple(records)
    summary = calculate_metrics(
        record_tuple,
        eligible_count,
        inference_per_row,
        ingestion_ms,
        engine.config.evaluation,
    )
    LOGGER.info(
        "Evaluated %d feasible recourse states from %d high-risk held-out states; "
        "infeasible=%d frozen=%d actuator_bounds=%d rate=%d",
        len(record_tuple),
        eligible_count,
        infeasible_count,
        sum(record.frozen_feature_violations for record in record_tuple),
        sum(record.actuator_bound_violations for record in record_tuple),
        sum(record.rate_limit_violations for record in record_tuple),
    )
    direction = _direction_consistency(
        engine,
        sampled_states,
        record_tuple,
        engine.config.evaluation.direction_similarity_radius,
    )
    LOGGER.info(
        "Counterfactual direction agreement for nearby states: pairs=%d agreement=%s",
        direction.similar_pair_count,
        direction.pairwise_sign_agreement,
    )
    return EvaluationRun(record_tuple, summary, direction, infeasible_count)


def _has_feasible_actuator_intervals(
    engine: PrescriptXAIEngine, row: pd.Series
) -> bool:
    """Check box/rate/trust-interval feasibility before selecting a recourse benchmark case."""
    active_controls = engine.taxonomy.active_controllable_feature_names(
        engine.model.feature_names
    )
    feature_positions = {
        name: index for index, name in enumerate(engine.model.feature_names)
    }
    for name in active_controls:
        try:
            raw_lower, raw_upper = allowed_interval(
                float(row[name]), engine.taxonomy.actuator_constraints[name]
            )
        except (KeyError, ValueError):
            return False
        scale = float(engine.model.scaler.scaler.scale_[feature_positions[name]])
        lower = max(
            (raw_lower - float(row[name])) / scale,
            -engine.config.recourse.max_scaled_distance,
        )
        upper = min(
            (raw_upper - float(row[name])) / scale,
            engine.config.recourse.max_scaled_distance,
        )
        if lower > upper:
            return False
    return bool(active_controls)


def _direction_consistency(
    engine: PrescriptXAIEngine,
    states: list[dict[str, float]],
    records: tuple[EvaluationRecord, ...],
    radius: float,
) -> DirectionConsistency:
    """Measure equal signed actions only for pairs within the scaled state-space radius."""
    if len(states) < 2:
        return DirectionConsistency(radius, 0, None, {})
    matrix = engine.model.scaler.transform(
        pd.DataFrame(states, columns=engine.model.feature_names)
    )
    names = engine.taxonomy.feature_groups.controllable_actuators.features
    comparisons = {name: [0, 0] for name in names}
    pair_agreements: list[float] = []
    for left in range(len(states) - 1):
        distances = np.linalg.norm(matrix[left + 1 :] - matrix[left], axis=1)
        for offset in np.flatnonzero(distances <= radius):
            right = left + 1 + int(offset)
            feature_matches: list[bool] = []
            for name in names:
                left_sign = records[left].counterfactual_signs.get(name, 0)
                right_sign = records[right].counterfactual_signs.get(name, 0)
                matched = left_sign == right_sign
                comparisons[name][0] += int(matched)
                comparisons[name][1] += 1
                feature_matches.append(matched)
            if feature_matches:
                pair_agreements.append(float(np.mean(feature_matches)))
    return DirectionConsistency(
        similarity_radius=radius,
        similar_pair_count=len(pair_agreements),
        pairwise_sign_agreement=(
            float(np.mean(pair_agreements)) if pair_agreements else None
        ),
        per_feature_sign_agreement={
            name: (matched / count if count else None)
            for name, (matched, count) in comparisons.items()
        },
    )
