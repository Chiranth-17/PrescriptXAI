"""Deterministic L-BFGS-B recourse with hard physical bounds and true-model checks."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from time import perf_counter_ns

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray
from scipy.optimize import OptimizeResult, minimize

from prescriptxai.config import AppConfig
from prescriptxai.constraints.bounds import allowed_interval, check_bound_violations
from prescriptxai.constraints.coupling import SensorCouplingModel, apply_coupling_for_bundle
from prescriptxai.constraints.taxonomy import FeatureSpec, FeatureTaxonomy
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.objective import (
    ObjectiveTerms,
    RecourseObjective,
    prediction_flip_loss,
)
from prescriptxai.recourse.sparsify import candidate_supports
from prescriptxai.schemas import DeltaMapping

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class OptimizationResult:
    """Raw-unit candidate, true-model status, objective terms, and solver diagnostics."""

    state: dict[str, float]
    deltas: tuple[DeltaMapping, ...]
    initial_risk: float
    final_risk: float
    solver_success: bool
    model_valid: bool
    message: str
    objective_value: float | None
    failure_reason: str | None = None
    risk_reached: float | None = None
    stage_timings_ms: dict[str, float] = field(default_factory=dict)
    objective_terms: dict[str, float] = field(default_factory=dict)
    counterfactual_signs: dict[str, int] = field(default_factory=dict)
    alpha_used: float | None = None
    l1_weight_used: float | None = None
    solver_calls: int = 0
    actuator_constraints_feasible: bool = False


@dataclass(frozen=True)
class _Candidate:
    """One fully propagated candidate, scored with the true calibrated predictor."""

    state: dict[str, float]
    delta_scaled: dict[str, float]
    risk: float
    score: float
    solver_success: bool
    message: str
    terms: ObjectiveTerms
    alpha: float
    l1_weight: float


class RecourseOptimizer:
    """Find sparse model-valid candidates from one model bundle and feature taxonomy."""

    def __init__(
        self,
        bundle: ModelBundle,
        taxonomy: FeatureTaxonomy,
        coupling: SensorCouplingModel | None = None,
    ) -> None:
        """Bind the calibrated predictor, feature limits, and optional coupling fit."""
        self.bundle = bundle
        self.taxonomy = taxonomy
        self.coupling = coupling

    def solve(self, x: dict[str, float], config: AppConfig) -> OptimizationResult:
        """Solve recourse and return the closest sparse candidate even when unsafe.

        Optimization uses the differentiable calibrated model path. For XGBoost bundles that path
        is the trained distillation surrogate. Every returned candidate is then rescored with the
        actual calibrated estimator; only that score can set ``model_valid``.
        """
        started_ns = perf_counter_ns()
        timing: dict[str, float] = {}
        state = {name: float(value) for name, value in x.items()}
        _validate_state(state, self.bundle.feature_names)
        initial_frame = pd.DataFrame([state])
        initial_risk = float(self.bundle.predict_risk(initial_frame)[0])
        if initial_risk <= config.model.safe_threshold:
            timing["total"] = _elapsed_ms(started_ns)
            controls_at_start = self.taxonomy.active_controllable_feature_names(
                self.bundle.feature_names
            )
            return OptimizationResult(
                state,
                (),
                initial_risk,
                initial_risk,
                True,
                True,
                "no action needed: state is already within the safe-risk threshold",
                0.0,
                risk_reached=initial_risk,
                stage_timings_ms=timing,
                actuator_constraints_feasible=not check_bound_violations(
                    state, self.taxonomy, features=controls_at_start
                ),
            )
        if initial_risk < config.model.danger_threshold:
            return self._failure(
                state,
                initial_risk,
                "input_not_high_risk",
                "no recourse attempted: input is below the configured danger threshold",
                started_ns,
            )
        if hasattr(self.bundle.estimator, "window"):
            return self._failure(
                state,
                initial_risk,
                "sequence_history_unavailable",
                "LSTM recourse requires a history window; this request contains a snapshot",
                started_ns,
            )
        if not self.bundle.supports_gradients:
            return self._failure(
                state,
                initial_risk,
                "differentiable_predictor_unavailable",
                "no differentiable predictor or XGBoost surrogate is available",
                started_ns,
            )
        if self.taxonomy.coupling is not None and self.coupling is None:
            return self._failure(
                state,
                initial_risk,
                "coupling_model_unavailable",
                "configured dependent sensors require a fitted coupling artifact",
                started_ns,
            )

        controls = self.taxonomy.active_controllable_feature_names(self.bundle.feature_names)
        if not controls:
            return self._failure(
                state,
                initial_risk,
                "no_controllable_features",
                "no controllable actuators/proxies are present in the model features",
                started_ns,
            )
        missing = set(self.bundle.feature_names) - set(state)
        if missing:
            raise ValueError(f"input state is missing model features: {sorted(missing)}")

        bounds_started = perf_counter_ns()
        specs = self.taxonomy.feature_by_name()
        scales = dict(zip(self.bundle.feature_names, self.bundle.scaler.scaler.scale_, strict=True))
        current_raw = np.asarray([state[name] for name in controls], dtype=np.float64)
        control_scales = np.asarray([scales[name] for name in controls], dtype=np.float64)
        lower: list[float] = []
        upper: list[float] = []
        try:
            for name, current, scale in zip(controls, current_raw, control_scales, strict=True):
                raw_lower, raw_upper = allowed_interval(
                    float(current), self.taxonomy.actuator_constraints[name]
                )
                scaled_lower = (raw_lower - current) / scale
                scaled_upper = (raw_upper - current) / scale
                # Preserve the configured legacy per-feature trust radius in scaled coordinates.
                lower.append(max(scaled_lower, -config.recourse.max_scaled_distance))
                upper.append(min(scaled_upper, config.recourse.max_scaled_distance))
        except (KeyError, ValueError) as error:
            timing["bounds"] = _elapsed_ms(bounds_started)
            return self._failure(
                state,
                initial_risk,
                "infeasible_actuator_interval",
                str(error),
                started_ns,
                timing=timing,
            )
        lower_array = np.asarray(lower, dtype=np.float64)
        upper_array = np.asarray(upper, dtype=np.float64)
        if np.any(lower_array > upper_array):
            timing["bounds"] = _elapsed_ms(bounds_started)
            return self._failure(
                state,
                initial_risk,
                "infeasible_actuator_interval",
                "physical bounds, rate limits, and scaled movement limits do not intersect",
                started_ns,
                timing=timing,
            )
        timing["bounds"] = _elapsed_ms(bounds_started)

        model_input = self.bundle.scaler.transform(
            initial_frame.loc[:, list(self.bundle.feature_names)]
        )[0]
        device = _model_device(self.bundle, config)
        original_scaled = torch.as_tensor(model_input, dtype=torch.float64, device=device)
        control_positions = np.asarray(
            [self.bundle.feature_names.index(name) for name in controls], dtype=np.int64
        )
        coupling_module = (
            self.coupling.propagate_scaled_torch_module(self.bundle.scaler).to(device)
            if self.coupling is not None
            else None
        )
        rng = np.random.default_rng(config.seed)
        solver_calls = 0
        initial_penalty = prediction_flip_loss(
            initial_risk,
            config.model.safe_threshold,
            safety_margin=config.recourse.safety_margin,
            squared=config.recourse.prediction_loss == "squared_hinge",
        )
        closest = _Candidate(
            state,
            {},
            initial_risk,
            config.recourse.prediction_weight * initial_penalty,
            False,
            "original state",
            ObjectiveTerms(0.0, config.recourse.prediction_weight * initial_penalty, 0.0, 0.0,
                           config.recourse.prediction_weight * initial_penalty, initial_risk),
            config.recourse.prediction_weight,
            config.recourse.l1_weight,
        )
        valid_candidates: list[_Candidate] = []
        optimization_started = perf_counter_ns()
        sparsification_ns = 0
        rescore_ns = 0

        def build_risk_function(
            support_positions: NDArray[np.int64],
        ) -> Callable[[torch.Tensor], torch.Tensor]:
            """Lift local control changes to the full differentiable model feature vector."""
            model_index = torch.as_tensor(
                control_positions[support_positions], dtype=torch.long, device=device
            )
            control_start = original_scaled.index_select(0, model_index)

            def risk_function(local_delta: torch.Tensor) -> torch.Tensor:
                full = original_scaled.index_copy(0, model_index, control_start + local_delta)
                row = full.unsqueeze(0).to(dtype=torch.float32)
                if coupling_module is not None:
                    row = coupling_module(row)
                return self.bundle.torch_forward(row).reshape(-1)[0]

            return risk_function

        def build_candidate(
            delta: NDArray[np.float64],
        ) -> tuple[dict[str, float], float, NDArray[np.float64]]:
            """Apply scaled control changes, propagate dependent sensors, and use true risk."""
            changed = np.clip(np.asarray(delta, dtype=np.float64), lower_array, upper_array)
            for index, value in enumerate(changed):
                if abs(value) <= config.recourse.change_tolerance and (
                    lower_array[index] <= 0 <= upper_array[index]
                ):
                    changed[index] = 0.0
            candidate = dict(state)
            for index, name in enumerate(controls):
                raw_value = current_raw[index] + changed[index] * control_scales[index]
                raw_lower = current_raw[index] + lower_array[index] * control_scales[index]
                raw_upper = current_raw[index] + upper_array[index] * control_scales[index]
                candidate[name] = float(np.clip(raw_value, raw_lower, raw_upper))
                changed[index] = (candidate[name] - current_raw[index]) / control_scales[index]
            if self.coupling is not None:
                candidate = apply_coupling_for_bundle(candidate, self.coupling, self.bundle.scaler)
            check_started = perf_counter_ns()
            # This is the true estimator and its fitted calibrator, not the gradient surrogate.
            risk = float(self.bundle.predict_risk(pd.DataFrame([candidate]))[0])
            nonlocal rescore_ns
            rescore_ns += perf_counter_ns() - check_started
            return candidate, risk, changed

        def score_candidate(
            candidate_state: dict[str, float],
            delta: NDArray[np.float64],
            risk: float,
            *,
            solver_success: bool,
            message: str,
            terms: ObjectiveTerms,
            alpha: float,
            l1_weight: float,
        ) -> _Candidate:
            """Record a candidate and its common base-objective score for selection."""
            score = terms.total
            delta_map = {
                name: float(delta[index])
                for index, name in enumerate(controls)
                if abs(float(delta[index])) > config.recourse.change_tolerance
            }
            return _Candidate(
                candidate_state,
                delta_map,
                risk,
                score,
                solver_success,
                message,
                terms,
                alpha,
                l1_weight,
            )

        # A failed search still returns the nearest point in the physical/rate intersection,
        # rather than echoing an out-of-range input as if it were an actuator candidate.
        nearest_delta = np.clip(np.zeros(len(controls), dtype=np.float64), lower_array, upper_array)
        nearest_state, nearest_risk, nearest_delta = build_candidate(nearest_delta)
        nearest_l1 = config.recourse.l1_weight * float(np.abs(nearest_delta).sum())
        nearest_prediction = config.recourse.prediction_weight * prediction_flip_loss(
            nearest_risk,
            config.model.safe_threshold,
            safety_margin=config.recourse.safety_margin,
            squared=config.recourse.prediction_loss == "squared_hinge",
        )
        nearest_terms = ObjectiveTerms(
            l1=nearest_l1,
            prediction=nearest_prediction,
            immutable=0.0,
            bounds=0.0,
            total=nearest_l1 + nearest_prediction,
            risk=nearest_risk,
        )
        closest = score_candidate(
            nearest_state,
            nearest_delta,
            nearest_risk,
            solver_success=True,
            message="nearest actuator-bound and rate-limited state",
            terms=nearest_terms,
            alpha=config.recourse.prediction_weight,
            l1_weight=config.recourse.l1_weight,
        )

        def optimize_support(
            support: tuple[str, ...],
            alpha: float,
            l1_weight: float,
            *,
            initial_delta: NDArray[np.float64] | None = None,
            restart_count: int | None = None,
        ) -> list[_Candidate]:
            """Optimize a selected support with L-BFGS-B and seeded starts."""
            nonlocal solver_calls
            support_positions = np.asarray([controls.index(name) for name in support], dtype=int)
            support_lower = lower_array[support_positions]
            support_upper = upper_array[support_positions]
            risk_function = build_risk_function(support_positions)
            objective = RecourseObjective(
                risk_function,
                support_lower,
                support_upper,
                safe_threshold=config.model.safe_threshold,
                safety_margin=config.recourse.safety_margin,
                alpha=alpha,
                beta=config.recourse.beta,
                gamma=config.recourse.gamma,
                l1_weight=l1_weight,
                l1_mode=config.recourse.l1_mode,
                smoothing_epsilon=config.recourse.l1_smoothing_epsilon,
                prediction_loss=config.recourse.prediction_loss,
                device=device,
            )
            if initial_delta is None:
                first = np.clip(np.zeros(len(support)), support_lower, support_upper)
            else:
                first = np.clip(initial_delta[support_positions], support_lower, support_upper)
            count = restart_count or config.recourse.restarts
            starts = [first]
            for _ in range(1, count):
                starts.append(rng.uniform(support_lower, support_upper))
            attempt_results: list[_Candidate] = []
            for start_delta in starts:
                decision = objective.encode(start_delta)
                result: OptimizeResult = minimize(
                    objective.value_and_grad,
                    decision,
                    method="L-BFGS-B",
                    jac=True,
                    bounds=objective.decision_bounds,
                    options={
                        "maxiter": config.recourse.max_iterations,
                        "ftol": config.recourse.solver_ftol,
                        "maxls": config.recourse.max_line_search_steps,
                    },
                )
                solver_calls += 1
                solved_decision = np.asarray(result.x, dtype=np.float64)
                local_delta_result = objective.decode(solved_decision)
                assert isinstance(local_delta_result, np.ndarray)
                local_delta = np.clip(local_delta_result, support_lower, support_upper)
                full_delta: NDArray[np.float64] = np.zeros(len(controls), dtype=np.float64)
                full_delta[support_positions] = local_delta
                candidate_state, risk, full_delta = build_candidate(full_delta)
                terms = objective.components(objective.encode(local_delta))
                attempt_results.append(
                    score_candidate(
                        candidate_state,
                        full_delta,
                        risk,
                        solver_success=bool(result.success),
                        message=str(result.message),
                        terms=terms,
                        alpha=alpha,
                        l1_weight=l1_weight,
                    )
                )
            return attempt_results

        def search_sparse_supports(
            dense: _Candidate, alpha: float, l1_weight: float
        ) -> list[_Candidate]:
            """Prune by |scaled delta|, re-optimize, and search nearby top-m supports."""
            nonlocal sparsification_ns
            started = perf_counter_ns()
            supports = candidate_supports(
                dense.delta_scaled,
                controls,
                max_changed_features=config.recourse.max_changed_features,
                top_m=config.recourse.support_search_top_m,
                max_supports=config.recourse.support_search_limit,
            )
            candidates: list[_Candidate] = []
            full_dense_delta = np.asarray(
                [dense.delta_scaled.get(name, 0.0) for name in controls], dtype=np.float64
            )
            for support in supports:
                if not support:
                    continue
                candidates.extend(
                    optimize_support(
                        support,
                        alpha,
                        l1_weight,
                        initial_delta=full_dense_delta,
                        restart_count=config.recourse.restarts,
                    )
                )
            sparsification_ns += perf_counter_ns() - started
            return candidates

        # Find one dense true-model-safe point by increasing alpha. Only then escalate L1 and
        # solve sparse supports; a larger L1 weight cannot help an already-unsafe dense point.
        dense_candidates: list[_Candidate] = []
        dense_safe: _Candidate | None = None
        alpha_used = config.recourse.prediction_weight
        for alpha_step in range(config.recourse.alpha_steps):
            alpha = config.recourse.prediction_weight * config.recourse.alpha_growth**alpha_step
            attempts = optimize_support(tuple(controls), alpha, config.recourse.l1_weight)
            dense_candidates.extend(attempts)
            safe_attempts = [
                attempt
                for attempt in attempts
                if attempt.risk <= config.model.safe_threshold
            ]
            if safe_attempts:
                dense_safe = min(safe_attempts, key=lambda candidate: candidate.score)
                alpha_used = alpha
                break

        if dense_safe is not None:
            for l1_step in range(config.recourse.l1_escalation_steps):
                l1_weight = config.recourse.l1_weight * config.recourse.l1_growth**l1_step
                if l1_step == 0:
                    current_dense = dense_safe
                else:
                    attempts = optimize_support(
                        tuple(controls), alpha_used, l1_weight
                    )
                    dense_candidates.extend(attempts)
                    safe_attempts = [
                        attempt
                        for attempt in attempts
                        if attempt.risk <= config.model.safe_threshold
                    ]
                    if not safe_attempts:
                        continue
                    current_dense = min(safe_attempts, key=lambda candidate: candidate.score)
                sparse_attempts = search_sparse_supports(
                    current_dense, alpha_used, l1_weight
                )
                for attempt in sparse_attempts:
                    if attempt.risk < closest.risk:
                        closest = attempt
                valid_candidates.extend(
                    attempt
                    for attempt in sparse_attempts
                    if attempt.risk <= config.model.safe_threshold
                    and len(attempt.delta_scaled) <= config.recourse.max_changed_features
                )
                if valid_candidates:
                    break
        elif dense_candidates:
            # Even if the dense run did not pass, a different local support can reveal a
            # feasible true-model point. Search around the best true-risk dense point once.
            best_dense = min(dense_candidates, key=lambda candidate: candidate.risk)
            fallback_supports = search_sparse_supports(
                best_dense, best_dense.alpha, best_dense.l1_weight
            )
            for attempt in fallback_supports:
                if attempt.risk < closest.risk:
                    closest = attempt
            valid_candidates.extend(
                attempt
                for attempt in fallback_supports
                if attempt.risk <= config.model.safe_threshold
                and len(attempt.delta_scaled) <= config.recourse.max_changed_features
            )

        # Failure returns the closest sparse, bounded point, never an unpruned dense solution.
        if valid_candidates:
            selected = min(valid_candidates, key=lambda candidate: candidate.score)
            failure_reason = None
            message = "true calibrated risk meets tau_safe with a sparse bounded candidate"
            valid = True
        else:
            selected = closest
            failure_reason = "safe_risk_not_reached"
            message = (
                "no sparse candidate met tau_safe under the true calibrated predictor; "
                f"closest risk reached was {selected.risk:.6g}"
            )
            valid = False
        timing["optimization"] = _elapsed_ms(optimization_started)
        timing["sparsification"] = sparsification_ns / 1_000_000
        timing["true_rescoring"] = rescore_ns / 1_000_000
        timing["total"] = _elapsed_ms(started_ns)
        delta_values = {
            name: selected.delta_scaled.get(name, 0.0) for name in controls
        }
        deltas = _delta_mappings(
            delta_values,
            controls,
            state,
            specs,
            control_scales,
            config.recourse.change_tolerance,
        )
        result = OptimizationResult(
            state=selected.state,
            deltas=deltas,
            initial_risk=initial_risk,
            final_risk=selected.risk,
            solver_success=selected.solver_success,
            model_valid=valid,
            message=message if valid else f"{message}; solver: {selected.message}",
            objective_value=selected.score,
            failure_reason=failure_reason,
            risk_reached=selected.risk,
            stage_timings_ms=timing,
            objective_terms={
                **asdict(selected.terms),
                "true_risk": selected.risk,
            },
            counterfactual_signs={
                delta.feature: int(np.sign(delta.raw_delta)) for delta in deltas
            },
            alpha_used=selected.alpha,
            l1_weight_used=selected.l1_weight,
            solver_calls=solver_calls,
            actuator_constraints_feasible=True,
        )
        LOGGER.info(
            "Recourse optimization completed",
            extra={
                "risk_before": initial_risk,
                "risk_reached": result.risk_reached,
                "model_valid": result.model_valid,
                "changed_features": len(result.deltas),
                "failure_reason": result.failure_reason,
                "timings_ms": result.stage_timings_ms,
                "counterfactual_signs": result.counterfactual_signs,
            },
        )
        return result

    @staticmethod
    def _failure(
        state: dict[str, float],
        risk: float,
        reason: str,
        message: str,
        started_ns: int,
        *,
        timing: dict[str, float] | None = None,
    ) -> OptimizationResult:
        """Create an explicit failed result with the original state as closest candidate."""
        measured = dict(timing or {})
        measured["total"] = _elapsed_ms(started_ns)
        return OptimizationResult(
            state,
            (),
            risk,
            risk,
            False,
            False,
            message,
            None,
            failure_reason=reason,
            risk_reached=risk,
            stage_timings_ms=measured,
        )


def optimize_recourse(
    initial_state: dict[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    config: AppConfig,
    coupling: SensorCouplingModel | None = None,
) -> OptimizationResult:
    """Compatibility function delegating to :class:`RecourseOptimizer`."""
    return RecourseOptimizer(bundle, taxonomy, coupling).solve(initial_state, config)


def _validate_state(state: dict[str, float], model_features: tuple[str, ...]) -> None:
    """Reject malformed raw state values before calibrated prediction."""
    if not state:
        raise ValueError("state must not be empty")
    if not all(np.isfinite(value) for value in state.values()):
        raise ValueError("state values must be finite")
    missing = set(model_features) - set(state)
    if missing:
        raise ValueError(f"input state is missing model features: {sorted(missing)}")


def _model_device(bundle: ModelBundle, config: AppConfig) -> torch.device:
    """Use the actual differentiable estimator device and keep coupling tensors aligned."""
    estimator = (
        bundle.estimator
        if getattr(bundle.estimator, "supports_gradients", False)
        else bundle.surrogate
    )
    configured = getattr(estimator, "device", config.model.torch_device)
    if configured == "cuda" and not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(configured)


def _elapsed_ms(start_ns: int) -> float:
    """Return elapsed wall-clock milliseconds from a monotonic timestamp."""
    return (perf_counter_ns() - start_ns) / 1_000_000


def _delta_mappings(
    delta_by_feature: dict[str, float],
    feature_names: tuple[str, ...],
    original: dict[str, float],
    specs: dict[str, FeatureSpec],
    control_scales: NDArray[np.float64],
    tolerance: float,
) -> tuple[DeltaMapping, ...]:
    """Build raw, scaled, current-percent, and physical-range-percent reports."""
    mappings: list[DeltaMapping] = []
    for index, name in enumerate(feature_names):
        scaled_delta = float(delta_by_feature.get(name, 0.0))
        if abs(scaled_delta) <= tolerance:
            continue
        raw_delta = scaled_delta * float(control_scales[index])
        current = float(original[name])
        spec = specs[name]
        bounds = spec.bounds
        if bounds.minimum is None or bounds.maximum is None:
            raise ValueError(f"physical bounds for {name!r} are unresolved")
        percent_current = raw_delta / abs(current) * 100 if current != 0 else None
        span = bounds.maximum - bounds.minimum
        percent_range = raw_delta / span * 100 if span > 0 else None
        mappings.append(
            DeltaMapping(
                feature=name,
                raw_delta=raw_delta,
                scaled_delta=scaled_delta,
                percent_of_current=percent_current,
                percent_of_range=percent_range,
            )
        )
    return tuple(mappings)
