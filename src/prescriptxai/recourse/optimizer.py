"""Bounded scaled-space recourse optimization with raw-unit actuator reporting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.optimize import minimize

from prescriptxai.config import AppConfig
from prescriptxai.constraints.bounds import allowed_interval
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.objective import recourse_objective
from prescriptxai.recourse.sparsify import sparsify_candidate
from prescriptxai.schemas import DeltaMapping


@dataclass(frozen=True)
class OptimizationResult:
    """Model-level candidate and its raw/scaled deltas; physical checks are separate."""

    state: dict[str, float]
    deltas: tuple[DeltaMapping, ...]
    initial_risk: float
    final_risk: float
    solver_success: bool
    model_valid: bool
    message: str
    objective_value: float | None


def _raw_state_frame(state: dict[str, float]) -> pd.DataFrame:
    """Create a single-row numeric DataFrame from a named state."""
    if not state:
        raise ValueError("state must not be empty")
    values = np.asarray(list(state.values()), dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("state values must be finite")
    return pd.DataFrame([state])


def optimize_recourse(
    initial_state: dict[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    config: AppConfig,
) -> OptimizationResult:
    """Optimize actuator changes under physical/rate bounds, then enforce sparsity.

    SLSQP performs finite-difference optimization with hard risk and scaled-distance constraints
    against the calibrated model. The optimizer changes only configured actuators. Its
    ``model_valid`` field records only the predictor check; Tiers 2–4 are evaluated separately.
    """
    state_frame = _raw_state_frame(initial_state)
    initial_risk = float(bundle.predict_risk(state_frame)[0])
    if initial_risk < config.model.danger_threshold:
        return OptimizationResult(
            initial_state, (), initial_risk, initial_risk, False, False,
            "initial state is below the configured danger threshold", None,
        )
    actuator_names = tuple(taxonomy.feature_groups.controllable_actuators.features)
    if not actuator_names:
        return OptimizationResult(
            initial_state, (), initial_risk, initial_risk, False, False,
            "no controllable actuators are configured", None,
        )
    if any(name not in bundle.feature_names for name in actuator_names):
        raise ValueError("every configured actuator must be a model feature")
    if any(name not in initial_state for name in bundle.feature_names):
        raise ValueError("initial state is missing one or more model features")

    feature_indices = np.asarray([bundle.feature_names.index(name) for name in actuator_names])
    scaler_mean = bundle.scaler.scaler.mean_[feature_indices]
    scaler_scale = bundle.scaler.scaler.scale_[feature_indices]
    raw_start = np.asarray([initial_state[name] for name in actuator_names], dtype=float)
    scaled_start = (raw_start - scaler_mean) / scaler_scale
    recourse_limits = config.recourse
    lower_scaled: list[float] = []
    upper_scaled: list[float] = []
    for name, current, mean, scale in zip(
        actuator_names, raw_start, scaler_mean, scaler_scale, strict=True
    ):
        lower_raw, upper_raw = allowed_interval(
            float(current), taxonomy.actuator_constraints[name]
        )
        lower_scaled.append((lower_raw - mean) / scale)
        upper_scaled.append((upper_raw - mean) / scale)
    bounds = list(zip(lower_scaled, upper_scaled, strict=True))
    if any(lower > upper for lower, upper in bounds):
        raise ValueError("physical and scaled-distance constraints have no feasible interval")

    def candidate_state(scaled_controls: NDArray[np.float64]) -> dict[str, float]:
        candidate = dict(initial_state)
        raw_controls = scaler_mean + scaled_controls * scaler_scale
        for name, value in zip(actuator_names, raw_controls, strict=True):
            candidate[name] = float(value)
        return candidate

    def objective(scaled_controls: NDArray[np.float64]) -> float:
        candidate = candidate_state(scaled_controls)
        risk = float(bundle.predict_risk(pd.DataFrame([candidate]))[0])
        return recourse_objective(
            scaled_controls,
            scaled_start,
            risk,
            config.model.safe_threshold,
            recourse_limits.prediction_weight,
        )

    def risk_constraint(scaled_controls: NDArray[np.float64]) -> float:
        """Nonnegative when model safety target plus configured numerical margin is met."""
        risk = float(bundle.predict_risk(pd.DataFrame([candidate_state(scaled_controls)]))[0])
        return config.model.safe_threshold - recourse_limits.safety_margin - risk

    def distance_constraint(scaled_controls: NDArray[np.float64]) -> float:
        """Nonnegative when total scaled actuator movement is within configured maximum."""
        return recourse_limits.max_scaled_distance - float(
            np.linalg.norm(scaled_controls - scaled_start)
        )

    feasible_start = np.asarray(
        [
            np.clip(value, lower, upper)
            for value, (lower, upper) in zip(scaled_start, bounds, strict=True)
        ],
        dtype=float,
    )
    solution = minimize(
        objective,
        feasible_start,
        method="SLSQP",
        bounds=bounds,
        constraints=(
            {"type": "ineq", "fun": risk_constraint},
            {"type": "ineq", "fun": distance_constraint},
        ),
        options={"maxiter": recourse_limits.max_iterations, "ftol": recourse_limits.solver_ftol},
    )
    candidate = candidate_state(np.asarray(solution.x, dtype=float))
    sparse = sparsify_candidate(
        bundle,
        initial_state,
        candidate,
        actuator_names,
        recourse_limits.max_changed_features,
        config.model.safe_threshold,
    )
    mappings = tuple(
        DeltaMapping(
            feature=name,
            raw_delta=float(sparse.state[name] - initial_state[name]),
            scaled_delta=float(
                (sparse.state[name] - initial_state[name])
                / bundle.scaler.scaler.scale_[bundle.feature_names.index(name)]
            ),
        )
        for name in sparse.changed_features
    )
    return OptimizationResult(
        state=sparse.state,
        deltas=mappings,
        initial_risk=initial_risk,
        final_risk=sparse.risk,
        solver_success=bool(solution.success),
        model_valid=sparse.success,
        message=sparse.message if sparse.success else f"{solution.message}; {sparse.message}",
        objective_value=float(solution.fun),
    )
