"""Finite reference search and controllable leverage with original constraints retained."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import pandas as pd

from prescriptxai.constraints.bounds import allowed_interval
from prescriptxai.evaluation.experiments import ExperimentObservation, QueryCase, StudyConfig
from prescriptxai.evaluation.metrics import action_sparsity
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.recourse.optimizer import RecourseOptimizer
from prescriptxai.recourse.sparsify import bounded_sparse_delta_grid
from prescriptxai.validation.pipeline import validate_candidate


def reference_search(
    case: QueryCase, production: ExperimentObservation, study: StudyConfig
) -> dict[str, Any]:
    """Search a verified union on a FAILED production state; finite misses stay unresolved.

    Exact replay, the entire production grid, traced optimizer outputs and the saved return are
    included. This certifies a superset of the finite production search, not a continuous oracle.
    """
    if production.joint:
        raise ValueError("reference classification is defined only for failed production states")
    if production.case_id != case.case_id:
        raise ValueError("production record does not match this query")
    pipeline = PrescriptXAI.from_config(case.config)
    state, observed = pipeline._normalize(case.state, case.context, complete=True)
    bundle = pipeline._bundle(observed)
    engine = pipeline.engine
    config = case.config.model_copy(deep=True)
    config.recourse.record_candidate_trace = True
    replay = RecourseOptimizer(bundle, engine.taxonomy, engine.coupling, engine.mahalanobis).solve(
        state, config
    )
    replay_risk = float(bundle.predict_risk(pd.DataFrame([replay.state]))[0])
    reproduced = replay.state == production.candidate and replay_risk == production.risk_after
    names = bundle.feature_names
    controls = engine.taxonomy.active_controllable_feature_names(names)
    scales = dict(zip(names, bundle.scaler.scaler.scale_, strict=True))
    lower, upper = [], []
    empty = []
    for name in controls:
        try:
            lo, hi = allowed_interval(
                state[name],
                engine.taxonomy.actuator_constraints[name],
                horizon_steps=config.recourse.rate_horizon_steps,
            )
        except ValueError:
            empty.append(name)
            continue
        lo = max((lo - state[name]) / scales[name], -config.recourse.max_scaled_distance)
        hi = min((hi - state[name]) / scales[name], config.recourse.max_scaled_distance)
        if lo > hi:
            empty.append(name)
        lower.append(lo)
        upper.append(hi)
    best_risk = production.risk_after
    found = False
    scored = 0

    def candidates() -> Iterator[dict[str, float]]:
        """Include exact returned states before any floating-point grid reconstruction."""
        yield dict(production.candidate)
        yield from replay.search_candidate_states
        if empty:
            return
        for points in (config.recourse.true_model_grid_points, study.oracle_grid_points):
            grid = bounded_sparse_delta_grid(
                np.asarray(lower),
                np.asarray(upper),
                max_changed_features=config.recourse.k_max,
                grid_points=points,
                change_tolerance=config.recourse.change_tolerance,
            )
            for delta in grid:
                candidate = dict(state)
                candidate.update(
                    {
                        n: state[n] + float(d) * scales[n]
                        for n, d in zip(controls, delta, strict=True)
                    }
                )
                if engine.coupling is not None:
                    raw = np.asarray([[candidate[n] for n in names]])
                    propagated = engine.coupling.propagate_batch(
                        raw, names, reference_state=np.asarray([state[n] for n in names])
                    )[0]
                    candidate.update(dict(zip(names, map(float, propagated), strict=True)))
                yield candidate

    # The finite sparse grid is small at the frozen k; score in configured batches.
    pending: list[dict[str, float]] = []

    def score(batch: list[dict[str, float]]) -> None:
        """Retain every failure and validate only true-model-safe points in full."""
        nonlocal best_risk, found, scored
        risk = bundle.predict_risk(pd.DataFrame(batch))
        scored += len(batch)
        best_risk = min(best_risk, float(np.min(risk)))
        for candidate, probability in zip(batch, risk, strict=True):
            if probability > config.tau_safe:
                continue
            count = action_sparsity(
                state, candidate, controls, scales, config.recourse.change_tolerance
            )
            trust = all(
                abs(candidate[n] - state[n]) / scales[n]
                <= config.recourse.max_scaled_distance + config.recourse.change_tolerance
                for n in controls
            )
            verdict = validate_candidate(
                state,
                candidate,
                bundle,
                engine.taxonomy,
                engine.mahalanobis,
                config,
                engine.coupling,
            )
            found |= verdict.joint and count <= config.recourse.k_max and trust

    for candidate in candidates():
        pending.append(candidate)
        if len(pending) >= study.oracle_chunk_rows:
            score(pending)
            pending.clear()
    if pending:
        score(pending)
    classification = (
        "superset_verification_failed"
        if not reproduced
        else "search_failure_candidate_found"
        if found
        else "truly_infeasible_empty_actuator_interval"
        if empty
        else "unresolved_finite_search"
    )
    return {
        "case_id": case.case_id,
        "engine_id": production.engine_id,
        "group": production.group,
        "classification": classification,
        "verified_search_superset": reproduced,
        "production_reproduced": reproduced,
        "candidate_count": scored,
        "best_true_risk": best_risk,
        "joint_candidate_found": found,
        "empty_interval_features": empty,
        "global_infeasibility_certified": reproduced and bool(empty),
        "scope": "finite production-search union; continuous feasibility unresolved otherwise",
    }


def controllable_leverage(case: QueryCase) -> dict[str, Any]:
    """Score both allowed endpoints independently, retaining distance and coupling margins."""
    pipeline = PrescriptXAI.from_config(case.config)
    state, observed = pipeline._normalize(case.state, case.context, complete=True)
    bundle = pipeline._bundle(observed)
    engine = pipeline.engine
    points = []
    scales = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
    for name in engine.taxonomy.active_controllable_feature_names(bundle.feature_names):
        try:
            lo, hi = allowed_interval(
                state[name],
                engine.taxonomy.actuator_constraints[name],
                horizon_steps=case.config.recourse.rate_horizon_steps,
            )
        except ValueError as exc:
            points.append({"feature": name, "empty_interval": True, "reason": str(exc)})
            continue
        radius = case.config.recourse.max_scaled_distance * float(scales[name])
        lo, hi = max(lo, state[name] - radius), min(hi, state[name] + radius)
        if lo > hi:
            points.append(
                {
                    "feature": name,
                    "empty_interval": True,
                    "reason": "physical/rate interval does not intersect search trust region",
                }
            )
            continue
        for side, value in (("lower", lo), ("upper", hi)):
            candidate = dict(state)
            candidate[name] = value
            if engine.coupling is not None:
                raw = np.asarray([[candidate[n] for n in bundle.feature_names]])
                propagated = engine.coupling.propagate_batch(
                    raw,
                    bundle.feature_names,
                    reference_state=np.asarray([state[n] for n in bundle.feature_names]),
                )[0]
                candidate.update(
                    dict(zip(bundle.feature_names, map(float, propagated), strict=True))
                )
            verdict = validate_candidate(
                state,
                candidate,
                bundle,
                engine.taxonomy,
                engine.mahalanobis,
                case.config,
                engine.coupling,
            )
            points.append(
                {
                    "feature": name,
                    "side": side,
                    "interval_width_raw": hi - lo,
                    "true_risk": verdict.tier1_model.measurement,
                    "D_M": verdict.tier2_plausibility.measurement,
                    "coupling_margin": verdict.tier4_coupling.margin,
                    "tier3": verdict.tier3_engineering.valid,
                    "tier4": verdict.tier4_coupling.valid,
                }
            )
    return {"case_id": case.case_id, "points": points}
