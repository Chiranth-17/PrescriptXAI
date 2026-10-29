"""Deterministic evaluation over high-risk rows from held-out engines."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
import torch

from prescriptxai.artifacts import validate_engine_ids
from prescriptxai.config import AppConfig
from prescriptxai.constraints.bounds import (
    allowed_interval,
    check_bound_violations,
    check_rate_violations,
)
from prescriptxai.evaluation.ablations import SearchPolicy, run_ablation_search
from prescriptxai.evaluation.experiments import (
    ExperimentObservation,
    ExperimentStore,
    QueryCase,
    content_hash,
)
from prescriptxai.evaluation.metrics import (
    EvaluationRecord,
    EvaluationSummary,
    action_sparsity,
    calculate_metrics,
    state_proximity,
)
from prescriptxai.pipeline import PrescriptXAI, PrescriptXAIEngine
from prescriptxai.recourse.baselines import (
    dice_baseline,
    no_action_baseline,
    unconstrained_gradient_baseline,
)
from prescriptxai.schemas import InputContext
from prescriptxai.validation.feasibility import frozen_settings
from prescriptxai.validation.pipeline import validate_candidate

LOGGER = logging.getLogger(__name__)


def observed_alert_cohort(
    pipeline: PrescriptXAI,
    rows: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[tuple[int, int], InputContext], dict[str, int]]:
    """Score every supported state and retain actual LSTM prefixes without fabricated history."""
    ordered = rows.sort_values(["engine_id", "cycle"]).copy()
    window = int(getattr(pipeline.engine.model.estimator, "window", 1))
    contexts: dict[tuple[int, int], InputContext] = {}
    risks: dict[int, float] = {}
    unavailable = 0
    if window == 1:
        risks = {
            int(index): float(pipeline.engine.model.predict_risk(ordered.loc[[index]])[0])
            for index in ordered.index
        }
    else:
        for _, engine in ordered.groupby("engine_id", sort=False):
            unit = int(engine.iloc[0].engine_id)
            raw = engine.loc[:, pipeline.engine.model.feature_names].to_numpy(dtype=float)
            unavailable += min(window - 1, len(raw))
            if len(raw) < window:
                continue
            sequences = np.stack([raw[i - window + 1 : i + 1] for i in range(window - 1, len(raw))])
            probabilities = [
                float(pipeline.engine.model.predict_risk_sequence(sequence[None, :])[0])
                for sequence in sequences
            ]
            for offset, probability in enumerate(probabilities, start=window - 1):
                row = engine.iloc[offset]
                risks[int(engine.index[offset])] = float(probability)
                if probability >= pipeline.config.tau_danger:
                    contexts[(int(unit), int(row.cycle))] = InputContext(
                        feature_names=pipeline.engine.model.feature_names,
                        history=tuple(
                            tuple(map(float, history))
                            for history in raw[offset - window + 1 : offset]
                        ),
                    )
    ordered["risk_before"] = pd.Series(risks)
    alerts = ordered.loc[ordered.risk_before >= pipeline.config.tau_danger].copy()
    first = alerts.groupby("engine_id").cycle.min().to_dict()
    alerts["first_alert"] = pd.Series(
        [cycle == first[unit] for unit, cycle in zip(alerts.engine_id, alerts.cycle, strict=True)],
        index=alerts.index,
        dtype=bool,
    )
    return (
        alerts,
        contexts,
        {
            "total_rows": len(ordered),
            "scorable_rows": len(risks),
            "insufficient_history_rows": unavailable,
            "alert_rows": len(alerts),
            "engines": int(ordered.engine_id.nunique()),
            "engines_without_scorable_alert": int(
                ordered.engine_id.nunique() - alerts.engine_id.nunique()
            ),
        },
    )


def raw_telemetry(row: pd.Series) -> dict[str, float]:
    """Exclude retrospective labels and experiment columns from actual predictor inputs."""
    return {
        str(name): float(value)
        for name, value in row.items()
        if name in {"engine_id", "cycle"} or str(name).startswith(("sensor_", "op_setting_"))
    }


def make_cases(
    config: AppConfig,
    config_path: Path,
    rows: pd.DataFrame,
    contexts: dict[tuple[int, int], InputContext],
    *,
    dataset: str,
    model: str,
    population: str,
    protocol: str,
    variant: str,
    mode: Literal["fast", "thorough"],
    seeds: list[int],
    free_rate_fraction: float,
    policy: SearchPolicy | None = None,
) -> Iterator[QueryCase]:
    """Yield stable per-query IDs including the effective settings and observed input/context."""
    for seed in seeds:
        local = config.model_copy(deep=True)
        local.seed = local.evaluation.random_seed = seed
        local.recourse.search_mode = mode
        group = "/".join((dataset, model, protocol, population, mode, variant))
        for _, row in rows.iterrows():
            state = raw_telemetry(row)
            context = contexts.get((int(row.engine_id), int(row.cycle)))
            payload = dict(
                group=group,
                dataset=dataset,
                model=model,
                population=population,
                protocol=protocol,
                variant=variant,
                mode=mode,
                config_path=config_path,
                config=local,
                state=state,
                context=context,
                rul=float(row.rul),
                first_alert=bool(row.first_alert),
                policy=policy.__dict__ if policy is not None else None,
                free_rate_fraction=free_rate_fraction,
            )
            case = QueryCase.model_validate({"case_id": "pending", **payload})
            case.case_id = content_hash(case.model_dump(mode="json", exclude={"case_id"}))
            yield case


def run_experiment_case(case: QueryCase) -> ExperimentObservation:
    """Run a genuine query or component-removal search, then validate original constraints."""
    started = perf_counter_ns()
    pipeline = PrescriptXAI.from_config(case.config)
    engine = pipeline.engine
    # Fitted artifacts may be shared; each case owns its runtime configuration.
    pipeline.config = case.config.model_copy(deep=True)
    config = pipeline.config
    normalization_started = perf_counter_ns()
    state, observed = pipeline._normalize(case.state, case.context, complete=True)
    ingestion_ms = (perf_counter_ns() - normalization_started) / 1e6
    bundle = pipeline._bundle(observed)
    action_names = engine.taxonomy.active_controllable_feature_names(bundle.feature_names)
    direct_names = action_names
    effective_k = config.recourse.k_max
    settings: dict[str, Any]
    if case.variant == "full" and case.policy is None:
        result = pipeline.recommend(state, case.context, case.mode)
        candidate = result.new_state
        before, after = result.risk_before, result.risk_after
        report = result.validation_report.model_dump(mode="json")
        tier2, tier3, tier4 = (
            result.plausible,
            result.validation_report.tier3_engineering.passed,
            result.validation_report.tier4_sensor_coupling.passed,
        )
        status, joint, reason = (
            result.status,
            result.joint,
            result.failure.reason if result.failure else None,
        )
        feasible = result.action_feasible
        surrogate = result.surrogate_risk_after
        settings = result.solver_settings
        evidence = result.evidence_level
        margin = result.validation_report.tier4_sensor_coupling.margin
        timings = {
            key: float(value)
            for key, value in result.timings.model_dump().items()
            if value is not None
        }
    else:
        inference_started = perf_counter_ns()
        before = float(bundle.predict_risk(pd.DataFrame([state]))[0])
        inference_ms = (perf_counter_ns() - inference_started) / 1e6
        solve_started = perf_counter_ns()
        if before < config.tau_danger:
            optimized = no_action_baseline(state, bundle, config.tau_safe)
            feasible = not check_bound_violations(state, engine.taxonomy, features=action_names)
        elif case.variant in {"unconstrained", "dice"}:
            if case.variant == "dice":
                from prescriptxai.evaluation.assets import dataset_frames

                training, _ = dataset_frames(config)
                training = training.loc[training.engine_id.isin(bundle.training_engine_ids)].copy()
                training["failure"] = (training.rul <= config.horizon_H).astype(int)
                dice = dice_baseline(state, bundle, training, config)
                if dice is None:
                    raise RuntimeError("DiCE scheduled but optional dependency is unavailable")
                optimized = dice
            else:
                optimized = unconstrained_gradient_baseline(state, bundle, config)
            direct_names = bundle.feature_names
            feasible = True
        else:
            policy = SearchPolicy(**(case.policy or {}))
            optimized = run_ablation_search(
                state,
                bundle,
                engine.taxonomy,
                config,
                engine.coupling,
                engine.mahalanobis,
                policy,
                free_rate_fraction=case.free_rate_fraction,
            )
            feasible = optimized.actuator_constraints_feasible
            if not policy.freeze_immutable:
                direct_names += tuple(
                    n
                    for n in bundle.feature_names
                    if n in engine.taxonomy.immutable_feature_names()
                )
            if policy.free_dependents:
                direct_names += tuple(
                    n
                    for n in bundle.feature_names
                    if n in engine.taxonomy.feature_groups.dependent_sensors.features
                )
        optimization_ms = (perf_counter_ns() - solve_started) / 1e6
        candidate = optimized.state
        validation_started = perf_counter_ns()
        validation = validate_candidate(
            state, candidate, bundle, engine.taxonomy, engine.mahalanobis, config, engine.coupling
        )
        validation_ms = (perf_counter_ns() - validation_started) / 1e6
        report = validation.to_schema().model_dump(mode="json")
        after = cast(float, validation.tier1_model.measurement)
        tier2, tier3, tier4 = (
            validation.tier2_plausibility.valid,
            validation.tier3_engineering.valid,
            validation.tier4_coupling.valid,
        )
        scales_local = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
        direct_count = action_sparsity(
            state, candidate, direct_names, scales_local, config.recourse.change_tolerance
        )
        limit = (
            len(direct_names)
            if case.variant in {"unconstrained", "dice"}
            or (case.policy and not case.policy.get("enforce_sparsity", True))
            else config.recourse.k_max
        )
        effective_k = limit
        feasible = feasible and direct_count <= limit
        physical = tier2 and tier3 and tier4
        joint = validation.model_valid and physical and feasible
        status = (
            "NO_INTERVENTION"
            if before < config.tau_danger
            else "RECOVERABLE"
            if joint
            else "PARTIAL"
            if physical
            and feasible
            and before - after >= config.pipeline.delta_min
            and after > config.tau_safe
            else "ESCALATE"
        )
        reason = optimized.failure_reason or (
            None if joint else "original_constraint_validation_failed"
        )
        settings = optimized.effective_solver_settings
        if before < config.tau_danger:
            settings = {**settings, "risk_gate_skipped": True}
            reason = "below_alert_gate_no_intervention"
        evidence = validation.to_schema().evidence_level
        margin = validation.tier4_coupling.margin
        scaled = bundle.scaler.transform(pd.DataFrame([candidate])[list(bundle.feature_names)])
        with torch.no_grad():
            estimator = (
                bundle.estimator
                if getattr(bundle.estimator, "supports_gradients", False)
                else bundle.surrogate
            )
            surrogate = float(
                bundle.torch_forward(
                    torch.as_tensor(
                        scaled, dtype=torch.float32, device=getattr(estimator, "device", "cpu")
                    )
                ).reshape(-1)[0]
            )
        timings = {
            "ingestion_ms": ingestion_ms,
            "inference_ms": inference_ms,
            "optimization_ms": optimization_ms,
            "validation_ms": validation_ms,
        }
    scales = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
    raw_l1, scaled_l1 = state_proximity(state, candidate, scales)
    proxy_sparsity = action_sparsity(
        state, candidate, action_names, scales, config.recourse.change_tolerance
    )
    sparsity = action_sparsity(
        state, candidate, direct_names, scales, config.recourse.change_tolerance
    )
    if case.policy is not None:
        effective_policy = case.policy
    elif case.variant in {"unconstrained", "dice"}:
        effective_policy = SearchPolicy(
            False, False, False, False, True, False, False, False, False
        ).__dict__
    else:
        effective_policy = SearchPolicy().__dict__
    settings = {
        **settings,
        "search_policy": effective_policy,
        "direct_inputs": list(direct_names),
        "effective_k_max": effective_k,
    }
    changes = [
        name
        for name in bundle.feature_names
        if abs((candidate[name] - state[name]) / scales[name]) > config.recourse.change_tolerance
    ]
    frozen = frozen_settings(engine.mahalanobis, state)
    distance_before, distance_after = (
        float(
            engine.mahalanobis.distance(
                bundle.scaler.transform(pd.DataFrame([point])[list(bundle.feature_names)])[0],
                frozen_operating_settings=frozen,
            )
        )
        for point in (state, candidate)
    )
    bound = check_bound_violations(candidate, engine.taxonomy, features=action_names)
    rate = check_rate_violations(
        state, candidate, engine.taxonomy, horizon_steps=config.recourse.rate_horizon_steps
    )
    immutable = sum(
        candidate[name] != state[name]
        for name in engine.taxonomy.immutable_feature_names()
        if name in state
    )
    timings["pipeline_ms"] = (perf_counter_ns() - started) / 1e6
    return ExperimentObservation(
        case_id=case.case_id,
        group=case.group,
        dataset=case.dataset,
        model=case.model,
        population=case.population,
        protocol=case.protocol,
        variant=case.variant,
        mode="FAST" if case.mode == "fast" else "THOROUGH",
        seed=config.seed,
        engine_id=int(state["engine_id"]),
        cycle=int(state["cycle"]),
        risk_before=before,
        risk_after=after,
        surrogate_after=surrogate,
        original=state,
        candidate=candidate,
        changed_features=changes,
        sparsity=sparsity,
        proxy_sparsity=proxy_sparsity,
        raw_l1=raw_l1,
        scaled_l1=scaled_l1,
        returned=bool(changes) and feasible,
        action_feasible=feasible,
        tier2=tier2,
        tier3=tier3,
        tier4=tier4,
        joint=joint,
        status=status,
        reason=reason,
        evidence_level=evidence,
        mahalanobis_before=distance_before,
        mahalanobis_after=distance_after,
        tier4_margin=margin,
        immutable_violations=immutable,
        bound_violations=len(bound),
        rate_violations=len(rate),
        rul=case.rul,
        life_fraction=state["cycle"] / (state["cycle"] + case.rul),
        first_alert=case.first_alert,
        timings=timings,
        config_hash=content_hash(config.model_dump(mode="json")),
        config_path=str(case.config_path),
        k_max=effective_k,
        K=config.recourse.rate_horizon_steps,
        D_max=engine.mahalanobis.threshold_for(frozen),
        solver_tau_safe=config.tau_safe,
        solver_tau_danger=config.tau_danger,
        solver_settings=settings,
        validation=report,
    )


def _worker_threads(count: int) -> None:
    """Bound torch and numerical-library threads for declared CPU worker isolation."""
    torch.set_num_threads(count)
    import_module("threadpoolctl").threadpool_limits(limits=count)


def execute_experiment_cases(
    cases: Iterable[QueryCase],
    store: ExperimentStore,
    *,
    workers: int,
    cpu_threads: int,
) -> int:
    """Bound in-flight work and atomically save completions; do not rerun completed query IDs."""
    completed = store.completed()
    pending = (case for case in cases if case.case_id not in completed)
    count = 0
    if workers == 1:
        _worker_threads(cpu_threads)
        for case in pending:
            store.register_case(case)
            store.save(run_experiment_case(case))
            count += 1
        return count
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_worker_threads, initargs=(cpu_threads,)
    ) as pool:
        futures: dict[Future[ExperimentObservation], str] = {}
        exhausted = False
        while futures or not exhausted:
            while not exhausted and len(futures) < workers:
                next_case = next(pending, None)
                if next_case is None:
                    exhausted = True
                else:
                    store.register_case(next_case)
                    futures[pool.submit(run_experiment_case, next_case)] = next_case.case_id
            if not futures:
                break
            finished, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in finished:
                record = future.result()
                store.save(record)
                count += 1
                LOGGER.info("Checkpointed case %s (new=%s)", record.case_id, count)
                del futures[future]
    return count


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
    *,
    on_selection: Callable[[pd.DataFrame, dict[str, int]], None] | None = None,
    on_record: Callable[[EvaluationRecord], None] | None = None,
) -> EvaluationRun:
    """Sample high-risk held-out states reproducibly and run full recommendation validation."""
    if held_out_rows.empty:
        summary = calculate_metrics((), 0, None, ingestion_ms, engine.config.evaluation)
        return EvaluationRun(
            (),
            summary,
            DirectionConsistency(engine.config.evaluation.direction_similarity_radius, 0, None, {}),
            0,
        )
    validate_evaluation_provenance(engine, held_out_rows)
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
    if on_selection is not None:
        on_selection(
            held_out_rows.iloc[selected].copy(),
            {"eligible_alerts": eligible_count, "interval_prescreen_exclusions": infeasible_count},
        )
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
        pipeline_started = perf_counter_ns()
        result = engine.recommend(state)
        backend_pipeline_ms = (perf_counter_ns() - pipeline_started) / 1_000_000
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
            state,
            result.optimization.state,
            engine.taxonomy,
            horizon_steps=engine.config.recourse.rate_horizon_steps,
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
                recourse_feasible=result.outcome.recourse_feasible,
                true_model_grid_ms=result.optimization.stage_timings_ms.get(
                    "true_model_grid_search", 0.0
                ),
                true_model_evaluations=result.optimization.true_model_evaluations,
                inference_ms=inference_samples_ms[-1],
                backend_pipeline_ms=backend_pipeline_ms,
                effective_solver_settings=(
                    result.optimization.effective_solver_settings
                    or {
                        "search_mode": engine.config.recourse.search_mode,
                        "k_max": engine.config.recourse.max_changed_features,
                        "max_scaled_distance": engine.config.recourse.max_scaled_distance,
                        "true_model_grid_points": engine.config.recourse.true_model_grid_points,
                        "grid_ran": False,
                        "grid_candidates_generated": 0,
                        "grid_candidates_scored": 0,
                        "grid_max_changed_features": None,
                        "grid_max_scaled_distance": None,
                        "grid_k_limit_honored": None,
                        "grid_scaled_distance_honored": None,
                    }
                ),
                candidate_state=dict(result.optimization.state),
                final_mahalanobis_distance=result.validation.tier2_plausibility.measurement,
                engineering_only_fallback=(result.optimization.engineering_only_fallback),
                dependent_sensor_count=(
                    len(engine.coupling.dependent_features) if engine.coupling is not None else None
                ),
                dependent_residual_violation_count=(
                    sum(
                        not item.passed
                        for item in engine.coupling.evaluate_learned_constraints(
                            result.optimization.state
                        )
                    )
                    if engine.coupling is not None
                    else None
                ),
                searched_candidate_states=(result.optimization.search_candidate_states),
                evidence_level=result.validation.evidence_level,
            )
        )
        if on_record is not None:
            on_record(records[-1])
    inference_per_row = float(np.mean(inference_samples_ms)) if inference_samples_ms else None
    record_tuple = tuple(records)
    summary = calculate_metrics(
        record_tuple,
        eligible_count,
        inference_per_row,
        ingestion_ms,
        engine.config.evaluation,
        inference_samples_ms=inference_samples_ms,
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


def fitted_engine_provenance(
    engine: PrescriptXAIEngine,
) -> dict[str, tuple[int, ...] | None]:
    """Return fitted engine IDs, preserving unavailable legacy provenance as unknown."""
    provenance: dict[str, tuple[int, ...] | None] = {
        "model_training": _engine_ids(engine.model.training_engine_ids),
        "scaler_training": _engine_ids(engine.model.scaler.training_engine_ids),
        "mahalanobis_training": _engine_ids(engine.mahalanobis.training_engine_ids),
    }
    metrics = engine.model.metrics or {}
    partitions = metrics.get("split_engines")
    if isinstance(partitions, dict):
        provenance["model_validation"] = _engine_ids(partitions.get("validation"))
    if engine.model.calibrator is not None:
        calibration = metrics.get("calibration")
        provenance["calibration_fit"] = (
            _engine_ids(calibration.get("fit_engine_ids"))
            if isinstance(calibration, dict)
            else None
        )
    if engine.coupling is not None:
        provenance["coupling_training"] = _engine_ids(
            getattr(engine.coupling, "training_engine_ids", None)
        )
        provenance["coupling_fit"] = _engine_ids(engine.coupling.fit_engine_ids)
        provenance["coupling_calibration"] = _engine_ids(engine.coupling.calibration_engine_ids)
    tuning = metrics.get("solver_tuning")
    if tuning is not None:
        if not isinstance(tuning, dict):
            raise ValueError("solver_tuning provenance must declare fit_engine_ids")
        provenance["solver_tuning"] = _engine_ids(tuning.get("fit_engine_ids"))
    return provenance


def _engine_ids(value: object) -> tuple[int, ...] | None:
    """Decode persisted IDs without treating missing or empty provenance as verified."""
    if not isinstance(value, (list, tuple)) or not value:
        return None
    return validate_engine_ids(value)


def validate_evaluation_provenance(engine: PrescriptXAIEngine, held_out_rows: pd.DataFrame) -> None:
    """Reject fitting/evaluation leakage even when runtime split settings have changed."""
    required = {"engine_id", "cycle"}
    if not required.issubset(held_out_rows.columns):
        raise ValueError("held-out rows must contain engine_id and cycle provenance")
    for name in sorted(required):
        values = held_out_rows[name].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 1).any() or (values % 1 != 0).any():
            raise ValueError(f"held-out {name} values must be finite positive integers")
    ids = set(int(value) for value in held_out_rows["engine_id"].unique())
    for component, fitted_ids in fitted_engine_provenance(engine).items():
        if fitted_ids is None:
            LOGGER.warning(
                "Evaluation cannot verify %s: fitted engine IDs are unavailable", component
            )
            continue
        overlap = ids.intersection(fitted_ids)
        if overlap:
            raise ValueError(
                f"held-out engine IDs overlap {component} engines: {sorted(overlap)}; "
                "use the persisted engine split rather than changing the evaluation seed"
            )
    metrics = engine.model.metrics or {}
    fitted_dataset = metrics.get("dataset")
    if fitted_dataset is not None and fitted_dataset != engine.config.data.dataset:
        raise ValueError("evaluation dataset does not match the fitted model dataset")
    fitted_horizon = metrics.get("horizon_H")
    if fitted_horizon is not None and fitted_horizon != engine.config.data.failure_horizon:
        raise ValueError("evaluation failure horizon does not match the fitted model horizon")


def _has_feasible_actuator_intervals(engine: PrescriptXAIEngine, row: pd.Series) -> bool:
    """Check box/rate/trust-interval feasibility before selecting a recourse benchmark case."""
    active_controls = engine.taxonomy.active_controllable_feature_names(engine.model.feature_names)
    feature_positions = {name: index for index, name in enumerate(engine.model.feature_names)}
    for name in active_controls:
        try:
            raw_lower, raw_upper = allowed_interval(
                float(row[name]),
                engine.taxonomy.actuator_constraints[name],
                horizon_steps=engine.config.recourse.rate_horizon_steps,
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
    matrix = engine.model.scaler.transform(pd.DataFrame(states, columns=engine.model.feature_names))
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
        pairwise_sign_agreement=(float(np.mean(pair_agreements)) if pair_agreements else None),
        per_feature_sign_agreement={
            name: (matched / count if count else None)
            for name, (matched, count) in comparisons.items()
        },
    )
