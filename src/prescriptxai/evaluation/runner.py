"""Deterministic evaluation over high-risk rows from held-out engines."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from time import perf_counter_ns

import numpy as np
import pandas as pd

from prescriptxai.evaluation.metrics import EvaluationRecord, EvaluationSummary, calculate_metrics
from prescriptxai.pipeline import PrescriptXAIEngine

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvaluationRun:
    """Actual evaluation records and their aggregate metrics."""

    records: tuple[EvaluationRecord, ...]
    summary: EvaluationSummary


def evaluate_states(
    engine: PrescriptXAIEngine,
    held_out_rows: pd.DataFrame,
    ingestion_ms: float | None = None,
) -> EvaluationRun:
    """Sample high-risk held-out states reproducibly and run full recommendation validation."""
    if held_out_rows.empty:
        summary = calculate_metrics((), 0, None, ingestion_ms, engine.config.evaluation)
        return EvaluationRun((), summary)
    missing = set(engine.model.feature_names) - set(held_out_rows.columns)
    if missing:
        raise ValueError(f"held-out data is missing model features: {sorted(missing)}")
    risk_scores = engine.model.predict_risk(held_out_rows[list(engine.model.feature_names)])
    high_risk_indices = np.flatnonzero(risk_scores >= engine.config.model.danger_threshold)
    eligible_count = int(len(high_risk_indices))
    selected = high_risk_indices
    if eligible_count > engine.config.evaluation.max_queries:
        rng = np.random.default_rng(engine.config.evaluation.random_seed)
        selected = np.sort(
            rng.choice(selected, size=engine.config.evaluation.max_queries, replace=False)
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
    inference_samples_ms: list[float] = []
    for index in selected:
        row = held_out_rows.iloc[int(index)]
        state = {name: float(row[name]) for name in state_features}
        inference_started = perf_counter_ns()
        engine.model.predict_risk(pd.DataFrame([state], columns=engine.model.feature_names))
        inference_samples_ms.append((perf_counter_ns() - inference_started) / 1_000_000)
        result = engine.recommend(state)
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
        "Evaluated %d of %d high-risk held-out states",
        len(record_tuple),
        eligible_count,
    )
    return EvaluationRun(record_tuple, summary)
