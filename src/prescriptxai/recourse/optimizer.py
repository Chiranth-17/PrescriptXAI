"""Deterministic L-BFGS-B recourse with hard physical bounds and true-model checks."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
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
from prescriptxai.recourse.sparsify import (
    bounded_sparse_delta_grid,
    candidate_supports,
)
from prescriptxai.schemas import DeltaMapping
from prescriptxai.validation.feasibility import build_feasibility_penalty, frozen_settings
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator
from prescriptxai.validation.tier3_engineering import validate_engineering
from prescriptxai.validation.tier4_coupling import coupling_pass_mask, validate_sensor_coupling

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
    true_model_evaluations: int = 0
    actuator_constraints_feasible: bool = False
    effective_solver_settings: dict[str, int | float | bool | str | None] = field(
        default_factory=dict
    )
    engineering_only_fallback: bool = False
    search_candidate_states: tuple[dict[str, float], ...] = ()


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
        mahalanobis: MahalanobisValidator | None = None,
        *,
        validate_plausibility: bool = True,
        check_distribution: bool = True,
        check_coupling: bool = True,
        propagate_dependents: bool = True,
        grid_support_cap: int | None = None,
    ) -> None:
        """Bind the calibrated predictor, physical limits, and fitted validation artifacts."""
        self.bundle = bundle
        self.taxonomy = taxonomy
        self.coupling = coupling
        self.mahalanobis = mahalanobis
        self.validate_plausibility = validate_plausibility
        self.check_distribution = check_distribution
        self.check_coupling = check_coupling
        self.propagate_dependents = propagate_dependents
        self.grid_support_cap = grid_support_cap

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
        if hasattr(self.bundle.estimator, "window"):
            raise ValueError(
                "LSTM recourse requires a telemetry history window; "
                "the snapshot recourse interface cannot score this request"
            )
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
                    float(current),
                    self.taxonomy.actuator_constraints[name],
                    horizon_steps=config.recourse.rate_horizon_steps,
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

        required_controls = tuple(
            name
            for index, name in enumerate(controls)
            if lower_array[index] > 0.0 or upper_array[index] < 0.0
        )

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
            if self.coupling is not None and self.propagate_dependents
            else None
        )
        rng = np.random.default_rng(config.seed)
        solver_calls = 0
        true_model_evaluations = 0
        grid_candidates_generated = 0
        grid_max_changed_features = 0
        grid_max_scaled_distance = 0.0
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
            ObjectiveTerms(
                0.0,
                config.recourse.prediction_weight * initial_penalty,
                0.0,
                0.0,
                config.recourse.prediction_weight * initial_penalty,
                initial_risk,
            ),
            config.recourse.prediction_weight,
            config.recourse.l1_weight,
        )
        valid_candidates: list[_Candidate] = []
        candidate_trace: list[dict[str, float]] = []
        optimization_started = perf_counter_ns()
        sparsification_ns = 0
        rescore_ns = 0
        feedback_weight = config.validation.feedback_penalty_weight
        feedback_attempts = 0
        manifold_penalty = (
            build_feasibility_penalty(
                self.bundle,
                self.taxonomy,
                self.mahalanobis,
                self.coupling,
                state,
                check_distribution=self.check_distribution,
                check_coupling=self.check_coupling,
            )
            if self.mahalanobis is not None and self.validate_plausibility
            else None
        )

        def build_feature_function(
            support_positions: NDArray[np.int64],
        ) -> Callable[[torch.Tensor], torch.Tensor]:
            """Lift local control changes to the full differentiable model feature vector."""
            model_index = torch.as_tensor(
                control_positions[support_positions], dtype=torch.long, device=device
            )
            control_start = original_scaled.index_select(0, model_index)

            def feature_function(local_delta: torch.Tensor) -> torch.Tensor:
                full = original_scaled.index_copy(0, model_index, control_start + local_delta)
                row = full.unsqueeze(0)
                if coupling_module is not None:
                    row = coupling_module(row, original_scaled.unsqueeze(0).to(row.dtype))
                return row

            return feature_function

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
            if self.coupling is not None and self.propagate_dependents:
                candidate = apply_coupling_for_bundle(
                    candidate, self.coupling, self.bundle.scaler, reference_state=state
                )
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
            # Search schedules use different alpha/L1 values and surrogate risks. Compare all
            # returned candidates using one common objective and the measured true-model risk.
            score = _grid_objective_score(delta, risk, config)
            delta_map = {
                name: float(delta[index])
                for index, name in enumerate(controls)
                if abs(float(delta[index])) > config.recourse.change_tolerance
            }
            if config.recourse.record_candidate_trace:
                candidate_trace.append(dict(candidate_state))
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
        if len(required_controls) > config.recourse.max_changed_features:
            timing["total"] = _elapsed_ms(started_ns)
            return OptimizationResult(
                state=nearest_state,
                deltas=_delta_mappings(
                    closest.delta_scaled,
                    controls,
                    state,
                    specs,
                    control_scales,
                    config.recourse.change_tolerance,
                ),
                initial_risk=initial_risk,
                final_risk=nearest_risk,
                solver_success=False,
                model_valid=nearest_risk <= config.model.safe_threshold,
                message=(
                    f"physical bounds require changing {len(required_controls)} controls, "
                    f"exceeding k_max={config.recourse.max_changed_features}; "
                    "projected state is a diagnostic only"
                ),
                objective_value=closest.score,
                failure_reason="mandatory_changes_exceed_sparsity",
                risk_reached=nearest_risk,
                stage_timings_ms=timing,
                actuator_constraints_feasible=True,
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
            if not set(required_controls).issubset(support):
                raise ValueError("optimization support must include mandatory bound corrections")
            support_positions = np.asarray([controls.index(name) for name in support], dtype=int)
            support_lower = lower_array[support_positions]
            support_upper = upper_array[support_positions]
            feature_function = build_feature_function(support_positions)

            def risk_function(local_delta: torch.Tensor) -> torch.Tensor:
                return self.bundle.torch_forward(feature_function(local_delta).float()).reshape(-1)[
                    0
                ]

            def feasibility_function(local_delta: torch.Tensor) -> torch.Tensor:
                assert manifold_penalty is not None
                return manifold_penalty(feature_function(local_delta))

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
                feasibility_function=feasibility_function if manifold_penalty is not None else None,
                feasibility_weight=feedback_weight,
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
                required_features=required_controls,
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

        def true_model_grid_search() -> list[_Candidate]:
            """Search bounded sparse supports against the true predictor in one batch."""
            nonlocal closest, rescore_ns, true_model_evaluations
            nonlocal grid_candidates_generated, grid_max_changed_features
            nonlocal grid_max_scaled_distance
            delta_grid = bounded_sparse_delta_grid(
                lower_array,
                upper_array,
                max_changed_features=(
                    self.grid_support_cap or config.recourse.max_changed_features
                ),
                grid_points=config.recourse.true_model_grid_points,
                change_tolerance=config.recourse.change_tolerance,
            )
            if not len(delta_grid):
                return []
            grid_candidates_generated += len(delta_grid)
            grid_max_changed_features = max(
                grid_max_changed_features,
                int(
                    np.max(
                        np.count_nonzero(
                            np.abs(delta_grid) > config.recourse.change_tolerance, axis=1
                        )
                    )
                ),
            )
            grid_max_scaled_distance = max(
                grid_max_scaled_distance,
                float(np.max(np.abs(delta_grid))) if delta_grid.size else 0.0,
            )
            if config.recourse.search_mode == "fast":
                return true_model_grid_search_fast(delta_grid)
            true_model_evaluations += len(delta_grid)

            raw_initial = np.asarray(
                [state[name] for name in self.bundle.feature_names], dtype=np.float64
            )
            raw_rows = np.repeat(raw_initial[None, :], len(delta_grid), axis=0)
            raw_rows[:, control_positions] = current_raw + delta_grid * control_scales
            if self.coupling is not None and self.propagate_dependents:
                raw_rows = self.coupling.propagate_batch(
                    raw_rows, self.bundle.feature_names, reference_state=raw_initial
                )
            scaled_rows = self.bundle.scaler.transform(
                pd.DataFrame(raw_rows, columns=self.bundle.feature_names)
            )

            score_started = perf_counter_ns()
            probabilities = self.bundle.predict_risk(
                pd.DataFrame(raw_rows, columns=self.bundle.feature_names)
            )

            def candidate_at(index: int) -> _Candidate:
                """Materialize one batched grid row as an auditable optimizer candidate."""
                delta = delta_grid[index]
                risk = float(probabilities[index])
                l1_value = _grid_l1_value(delta, config)
                hinge = max(
                    0.0,
                    risk - config.model.safe_threshold + config.recourse.safety_margin,
                )
                prediction_term = config.recourse.prediction_weight * (
                    hinge**2 if config.recourse.prediction_loss == "squared_hinge" else hinge
                )
                terms = ObjectiveTerms(
                    l1=l1_value,
                    prediction=prediction_term,
                    immutable=0.0,
                    bounds=0.0,
                    total=l1_value + prediction_term,
                    risk=risk,
                )
                candidate_state = {
                    **state,
                    **{
                        name: float(raw_rows[index, position])
                        for position, name in enumerate(self.bundle.feature_names)
                    },
                }
                return score_candidate(
                    candidate_state,
                    delta,
                    risk,
                    solver_success=True,
                    message="bounded sparse grid candidate rescored by the true model",
                    terms=terms,
                    alpha=config.recourse.prediction_weight,
                    l1_weight=config.recourse.l1_weight,
                )

            rescore_ns += perf_counter_ns() - score_started
            safe_indices = np.flatnonzero(probabilities <= config.model.safe_threshold)
            if not len(safe_indices):
                best_grid_candidate = candidate_at(int(np.argmin(probabilities)))
                if (
                    best_grid_candidate.risk < closest.risk
                    and validate_engineering(
                        state,
                        best_grid_candidate.state,
                        self.taxonomy,
                        horizon_steps=config.recourse.rate_horizon_steps,
                    ).valid
                ):
                    closest = best_grid_candidate
                return []

            if (
                self.mahalanobis is not None
                and self.validate_plausibility
                and self.check_distribution
            ):
                distances = self.mahalanobis.distance_batch(
                    scaled_rows[safe_indices],
                    frozen_operating_settings=frozen_settings(self.mahalanobis, state),
                )
                plausible_indices = safe_indices[
                    distances
                    <= self.mahalanobis.threshold_for(frozen_settings(self.mahalanobis, state))
                ]
            else:
                plausible_indices = safe_indices

            # Build candidates in objective order. If Tier 2–4 artifacts are available, prefer a
            # fully plausible candidate; retain every model-safe grid point as a fallback only
            # when no grid point passes all physical checks.
            ordered = sorted(
                (int(index) for index in safe_indices),
                key=lambda index: _grid_objective_score(
                    delta_grid[index], float(probabilities[index]), config
                ),
            )
            best_safe = candidate_at(ordered[0])
            physically_valid: list[_Candidate] = []
            plausible_set = set(int(index) for index in plausible_indices)
            coupling_mask = (
                coupling_pass_mask(
                    raw_rows, self.bundle.feature_names, state, self.taxonomy, self.coupling
                )
                if self.mahalanobis is not None
                and self.validate_plausibility
                and self.check_coupling
                else np.ones(len(raw_rows), dtype=bool)
            )
            plausible_ordered = [
                index for index in ordered if index in plausible_set and coupling_mask[index]
            ]
            for index in plausible_ordered:
                candidate = candidate_at(index)
                if self._is_physically_valid(
                    state, candidate.state, config.recourse.rate_horizon_steps
                ):
                    physically_valid.append(candidate)
                    break
            return physically_valid or [best_safe]

        def true_model_grid_search_fast(
            delta_grid: NDArray[np.float64],
        ) -> list[_Candidate]:
            """Batch-score supports and stop when a discrete-grid bound certifies optimality.

            For each unvisited support, its minimum configured grid L1 cost is a lower bound
            because the prediction loss is non-negative. Once a physical candidate with the
            requested risk margin is found and all remaining support lower bounds exceed its
            objective, it is safe to stop without changing the THOROUGH grid optimum.
            """
            nonlocal closest, rescore_ns, true_model_evaluations
            raw_initial = np.asarray(
                [state[name] for name in self.bundle.feature_names], dtype=np.float64
            )
            support_groups: dict[tuple[int, ...], list[int]] = {}
            for row_index, delta in enumerate(delta_grid):
                support = tuple(
                    int(index)
                    for index in np.flatnonzero(np.abs(delta) > config.recourse.change_tolerance)
                )
                if support:
                    support_groups.setdefault(support, []).append(row_index)

            def support_l1_lower_bound(indices: list[int]) -> float:
                return min(_grid_l1_value(delta_grid[index], config) for index in indices)

            ordered_groups = sorted(
                support_groups.items(),
                key=lambda item: (support_l1_lower_bound(item[1]), item[0]),
            )
            best_safe: _Candidate | None = None
            best_physical: _Candidate | None = None
            found_margin = False
            for group_position, (_, indices) in enumerate(ordered_groups):
                raw_rows = np.repeat(raw_initial[None, :], len(indices), axis=0)
                deltas = delta_grid[np.asarray(indices, dtype=np.int64)]
                raw_rows[:, control_positions] = current_raw + deltas * control_scales
                if self.coupling is not None and self.propagate_dependents:
                    raw_rows = self.coupling.propagate_batch(
                        raw_rows, self.bundle.feature_names, reference_state=raw_initial
                    )
                true_model_evaluations += len(indices)
                score_started = perf_counter_ns()
                probabilities = self.bundle.predict_risk(
                    pd.DataFrame(raw_rows, columns=self.bundle.feature_names)
                )
                scaled_rows = self.bundle.scaler.transform(
                    pd.DataFrame(raw_rows, columns=self.bundle.feature_names)
                )
                rescore_ns += perf_counter_ns() - score_started
                safe_indices = np.flatnonzero(probabilities <= config.model.safe_threshold)
                if (
                    self.mahalanobis is not None
                    and self.validate_plausibility
                    and self.check_distribution
                    and len(safe_indices)
                ):
                    distances = self.mahalanobis.distance_batch(
                        scaled_rows[safe_indices],
                        frozen_operating_settings=frozen_settings(self.mahalanobis, state),
                    )
                    plausible_indices = safe_indices[
                        distances
                        <= self.mahalanobis.threshold_for(frozen_settings(self.mahalanobis, state))
                    ]
                else:
                    plausible_indices = safe_indices
                safe_order = sorted(
                    (int(index) for index in safe_indices),
                    key=lambda index: _grid_objective_score(
                        deltas[index], float(probabilities[index]), config
                    ),
                )
                if safe_order:
                    group_best_safe = materialize_fast_candidate(
                        raw_rows, deltas, probabilities, safe_order[0]
                    )
                    if best_safe is None or group_best_safe.score < best_safe.score:
                        best_safe = group_best_safe
                lowest_risk_index = int(np.argmin(probabilities))
                group_closest = materialize_fast_candidate(
                    raw_rows, deltas, probabilities, lowest_risk_index
                )
                if (
                    group_closest.risk < closest.risk
                    and validate_engineering(
                        state,
                        group_closest.state,
                        self.taxonomy,
                        horizon_steps=config.recourse.rate_horizon_steps,
                    ).valid
                ):
                    closest = group_closest
                plausible_set = set(int(index) for index in plausible_indices)
                coupling_mask = (
                    coupling_pass_mask(
                        raw_rows, self.bundle.feature_names, state, self.taxonomy, self.coupling
                    )
                    if self.mahalanobis is not None
                    and self.validate_plausibility
                    and self.check_coupling
                    else np.ones(len(raw_rows), dtype=bool)
                )
                for candidate_index in safe_order:
                    if candidate_index not in plausible_set or not coupling_mask[candidate_index]:
                        continue
                    candidate = materialize_fast_candidate(
                        raw_rows, deltas, probabilities, candidate_index
                    )
                    if not self._is_physically_valid(
                        state, candidate.state, config.recourse.rate_horizon_steps
                    ):
                        continue
                    if best_physical is None or candidate.score < best_physical.score:
                        best_physical = candidate
                    margin_threshold = config.model.safe_threshold - config.recourse.safety_margin
                    found_margin = found_margin or candidate.risk <= margin_threshold
                    if found_margin:
                        break
                if found_margin and best_physical is not None:
                    if group_position + 1 == len(ordered_groups):
                        break
                    next_lower_bound = support_l1_lower_bound(ordered_groups[group_position + 1][1])
                    if next_lower_bound > best_physical.score:
                        break
            if best_physical is not None:
                return [best_physical]
            return [best_safe] if best_safe is not None else []

        def materialize_fast_candidate(
            raw_rows: NDArray[np.float64],
            deltas: NDArray[np.float64],
            probabilities: NDArray[np.float64],
            index: int,
        ) -> _Candidate:
            """Materialize a candidate from one vector-scored support batch."""
            delta = deltas[index]
            risk = float(probabilities[index])
            hinge = max(
                0.0,
                risk - config.model.safe_threshold + config.recourse.safety_margin,
            )
            l1_value = _grid_l1_value(delta, config)
            prediction_term = config.recourse.prediction_weight * (
                hinge**2 if config.recourse.prediction_loss == "squared_hinge" else hinge
            )
            candidate_state = {
                **state,
                **{
                    name: float(raw_rows[index, position])
                    for position, name in enumerate(self.bundle.feature_names)
                },
            }
            terms = ObjectiveTerms(
                l1=l1_value,
                prediction=prediction_term,
                immutable=0.0,
                bounds=0.0,
                total=l1_value + prediction_term,
                risk=risk,
            )
            return score_candidate(
                candidate_state,
                delta,
                risk,
                solver_success=True,
                message="bounded sparse grid candidate rescored by the true model (FAST)",
                terms=terms,
                alpha=config.recourse.prediction_weight,
                l1_weight=config.recourse.l1_weight,
            )

        # Find one dense true-model-safe point by increasing alpha. Only then escalate L1 and
        # solve sparse supports; a larger L1 weight cannot help an already-unsafe dense point.
        dense_candidates: list[_Candidate] = []
        dense_safe: _Candidate | None = None
        alpha_used = config.recourse.prediction_weight
        for alpha_step in range(config.recourse.alpha_steps):
            alpha = config.recourse.prediction_weight * config.recourse.alpha_growth**alpha_step
            attempts = optimize_support(tuple(controls), alpha, config.recourse.l1_weight)
            dense_candidates.extend(attempts)
            valid_candidates.extend(
                attempt
                for attempt in attempts
                if attempt.risk <= config.model.safe_threshold
                and len(attempt.delta_scaled) <= config.recourse.max_changed_features
            )
            safe_attempts = [
                attempt for attempt in attempts if attempt.risk <= config.model.safe_threshold
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
                    attempts = optimize_support(tuple(controls), alpha_used, l1_weight)
                    dense_candidates.extend(attempts)
                    safe_attempts = [
                        attempt
                        for attempt in attempts
                        if attempt.risk <= config.model.safe_threshold
                    ]
                    if not safe_attempts:
                        continue
                    current_dense = min(safe_attempts, key=lambda candidate: candidate.score)
                sparse_attempts = search_sparse_supports(current_dense, alpha_used, l1_weight)
                for attempt in sparse_attempts:
                    if (
                        attempt.risk < closest.risk
                        and len(attempt.delta_scaled) <= config.recourse.max_changed_features
                        and validate_engineering(
                            state,
                            attempt.state,
                            self.taxonomy,
                            horizon_steps=config.recourse.rate_horizon_steps,
                        ).valid
                    ):
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
                if (
                    attempt.risk < closest.risk
                    and len(attempt.delta_scaled) <= config.recourse.max_changed_features
                    and validate_engineering(
                        state,
                        attempt.state,
                        self.taxonomy,
                        horizon_steps=config.recourse.rate_horizon_steps,
                    ).valid
                ):
                    closest = attempt
            valid_candidates.extend(
                attempt
                for attempt in fallback_supports
                if attempt.risk <= config.model.safe_threshold
                and len(attempt.delta_scaled) <= config.recourse.max_changed_features
            )

        engineering_valid_candidates = [
            candidate
            for candidate in valid_candidates
            if validate_engineering(
                state,
                candidate.state,
                self.taxonomy,
                horizon_steps=config.recourse.rate_horizon_steps,
            ).valid
        ]
        physically_valid_candidates = (
            [
                candidate
                for candidate in engineering_valid_candidates
                if self._is_physically_valid(
                    state, candidate.state, config.recourse.rate_horizon_steps
                )
            ]
            if self.mahalanobis is not None
            else list(engineering_valid_candidates)
        )
        grid_search_started = perf_counter_ns()
        if config.recourse.true_model_grid_enabled and not physically_valid_candidates:
            grid_candidates = true_model_grid_search()
            valid_candidates.extend(grid_candidates)
            engineering_valid_candidates = [
                candidate
                for candidate in valid_candidates
                if validate_engineering(
                    state,
                    candidate.state,
                    self.taxonomy,
                    horizon_steps=config.recourse.rate_horizon_steps,
                ).valid
            ]
            if self.mahalanobis is not None:
                physically_valid_candidates = [
                    candidate
                    for candidate in engineering_valid_candidates
                    if self._is_physically_valid(
                        state, candidate.state, config.recourse.rate_horizon_steps
                    )
                ]
            else:
                physically_valid_candidates = list(engineering_valid_candidates)
        if true_model_evaluations:
            timing["true_model_grid_search"] = _elapsed_ms(grid_search_started)

        feedback_started = perf_counter_ns()
        if manifold_penalty is not None and not physically_valid_candidates:
            for _ in range(config.validation.feedback_max_refinements):
                feedback_attempts += 1
                feedback_weight *= config.validation.feedback_penalty_growth
                seed_candidate = (
                    min(engineering_valid_candidates, key=lambda item: item.risk)
                    if (engineering_valid_candidates)
                    else closest
                )
                support = tuple(seed_candidate.delta_scaled)
                if not support:
                    support = controls[: config.recourse.max_changed_features]
                start_delta = np.asarray(
                    [seed_candidate.delta_scaled.get(name, 0.0) for name in controls], dtype=float
                )
                attempts = optimize_support(
                    support,
                    seed_candidate.alpha,
                    seed_candidate.l1_weight,
                    initial_delta=start_delta,
                )
                for attempt in attempts:
                    bounded = validate_engineering(
                        state,
                        attempt.state,
                        self.taxonomy,
                        horizon_steps=config.recourse.rate_horizon_steps,
                    ).valid
                    sparse = len(attempt.delta_scaled) <= config.recourse.max_changed_features
                    if bounded and sparse and attempt.risk < closest.risk:
                        closest = attempt
                    if bounded and sparse and attempt.risk <= config.model.safe_threshold:
                        engineering_valid_candidates.append(attempt)
                physically_valid_candidates = [
                    candidate
                    for candidate in engineering_valid_candidates
                    if self._is_physically_valid(
                        state,
                        candidate.state,
                        config.recourse.rate_horizon_steps,
                    )
                ]
                if physically_valid_candidates:
                    break
        timing["validation_feedback"] = _elapsed_ms(feedback_started)

        # Failure returns the closest sparse, bounded point, never an unpruned dense solution.
        if physically_valid_candidates:
            selected = min(physically_valid_candidates, key=lambda candidate: candidate.score)
            failure_reason = None
            message = (
                "true calibrated risk and Tier 2–4 checks pass with a sparse bounded candidate"
                if self.mahalanobis is not None and self.validate_plausibility
                else "true calibrated risk meets tau_safe with a sparse bounded candidate"
            )
            valid = True
        elif engineering_valid_candidates:
            selected = min(engineering_valid_candidates, key=lambda candidate: candidate.score)
            failure_reason = "validation_feedback_exhausted"
            message = (
                "true calibrated risk meets tau_safe with a sparse bounded candidate; "
                "no searched candidate passed all configured physical checks"
            )
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
        delta_values = {name: selected.delta_scaled.get(name, 0.0) for name in controls}
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
            solver_success=selected.solver_success and failure_reason is None,
            model_valid=valid,
            message=message if valid else f"{message}; solver: {selected.message}",
            objective_value=selected.score,
            failure_reason=failure_reason,
            risk_reached=selected.risk,
            stage_timings_ms=timing,
            objective_terms={
                "l1": _grid_l1_value(
                    np.asarray(list(delta_values.values()), dtype=np.float64), config
                ),
                "prediction": config.recourse.prediction_weight
                * prediction_flip_loss(
                    selected.risk,
                    config.model.safe_threshold,
                    safety_margin=config.recourse.safety_margin,
                    squared=config.recourse.prediction_loss == "squared_hinge",
                ),
                "immutable": 0.0,
                "bounds": 0.0,
                "total": selected.score,
                "risk": selected.risk,
                "true_risk": selected.risk,
                "search_l1": selected.terms.l1,
                "search_prediction": selected.terms.prediction,
                "search_total": selected.terms.total,
                "search_risk": selected.terms.risk,
                "search_feasibility": selected.terms.feasibility,
            },
            counterfactual_signs={delta.feature: int(np.sign(delta.raw_delta)) for delta in deltas},
            alpha_used=selected.alpha,
            l1_weight_used=selected.l1_weight,
            solver_calls=solver_calls,
            true_model_evaluations=true_model_evaluations,
            actuator_constraints_feasible=True,
            engineering_only_fallback=bool(
                engineering_valid_candidates and not physically_valid_candidates
            ),
            search_candidate_states=tuple(candidate_trace),
            effective_solver_settings={
                "selected_alpha": selected.alpha,
                "selected_l1_weight": selected.l1_weight,
                "solver_calls": solver_calls,
                "true_model_evaluations": true_model_evaluations,
                "validate_plausibility": self.validate_plausibility,
                "effective_distribution_filter": (
                    self.validate_plausibility and self.check_distribution
                ),
                "effective_coupling_filter": self.validate_plausibility and self.check_coupling,
                "check_distribution": self.check_distribution,
                "check_coupling": self.check_coupling,
                "propagate_dependents": self.propagate_dependents,
                "max_iter": config.recourse.max_iterations,
                "restarts": config.recourse.restarts,
                "alpha_steps": config.recourse.alpha_steps,
                "support_search_limit": config.recourse.support_search_limit,
                "feedback_max_refinements": config.validation.feedback_max_refinements,
                "feedback_refinements_executed": feedback_attempts,
                "feedback_final_weight": feedback_weight,
                "search_mode": config.recourse.search_mode,
                "k_max": config.recourse.max_changed_features,
                "max_scaled_distance": config.recourse.max_scaled_distance,
                "true_model_grid_points": config.recourse.true_model_grid_points,
                "grid_support_cap": self.grid_support_cap,
                "grid_ran": grid_candidates_generated > 0,
                "grid_candidates_generated": grid_candidates_generated,
                "grid_candidates_scored": true_model_evaluations,
                "grid_max_changed_features": (
                    grid_max_changed_features if grid_candidates_generated else None
                ),
                "grid_max_scaled_distance": (
                    grid_max_scaled_distance if grid_candidates_generated else None
                ),
                "grid_k_limit_honored": (
                    grid_max_changed_features <= config.recourse.max_changed_features
                    if grid_candidates_generated
                    else None
                ),
                "grid_scaled_distance_honored": (
                    grid_max_scaled_distance
                    <= config.recourse.max_scaled_distance + config.recourse.change_tolerance
                    if grid_candidates_generated
                    else None
                ),
            },
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
                "true_model_evaluations": result.true_model_evaluations,
            },
        )
        return result

    def _is_physically_valid(
        self,
        initial_state: dict[str, float],
        candidate_state: dict[str, float],
        horizon_steps: int,
    ) -> bool:
        """Apply independent empirical and engineering tiers when their fit is available."""
        if self.mahalanobis is None or not self.validate_plausibility:
            return True
        scaled = self.bundle.scaler.transform(
            pd.DataFrame([candidate_state], columns=self.bundle.feature_names)
        )[0]
        if (
            self.check_distribution
            and not self.mahalanobis.validate(
                np.asarray(scaled, dtype=np.float64),
                frozen_operating_settings=frozen_settings(self.mahalanobis, initial_state),
            ).valid
        ):
            return False
        if not validate_engineering(
            initial_state,
            candidate_state,
            self.taxonomy,
            horizon_steps=horizon_steps,
        ).valid:
            return False
        return (
            not self.check_coupling
            or validate_sensor_coupling(candidate_state, self.taxonomy, self.coupling).valid
        )

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
    mahalanobis: MahalanobisValidator | None = None,
    *,
    validate_plausibility: bool = True,
) -> OptimizationResult:
    """Compatibility function delegating to :class:`RecourseOptimizer`."""
    return RecourseOptimizer(
        bundle, taxonomy, coupling, mahalanobis, validate_plausibility=validate_plausibility
    ).solve(initial_state, config)


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


def _grid_l1_value(delta: NDArray[np.float64], config: AppConfig) -> float:
    """Return the configured scaled L1 penalty for one true-model grid point."""
    if config.recourse.l1_mode == "split":
        distance = float(np.abs(delta).sum())
    else:
        epsilon = config.recourse.l1_smoothing_epsilon
        distance = float((np.sqrt(delta**2 + epsilon**2) - epsilon).sum())
    return config.recourse.l1_weight * distance


def _grid_objective_score(delta: NDArray[np.float64], risk: float, config: AppConfig) -> float:
    """Evaluate the objective used to order true-model grid candidates."""
    hinge = max(0.0, risk - config.model.safe_threshold + config.recourse.safety_margin)
    prediction = hinge**2 if config.recourse.prediction_loss == "squared_hinge" else hinge
    return _grid_l1_value(delta, config) + config.recourse.prediction_weight * prediction


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
