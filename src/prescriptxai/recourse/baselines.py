"""Transparent unconstrained, bounded, no-action, and optional DiCE baselines."""

from __future__ import annotations

import logging
from importlib import import_module
from time import perf_counter_ns

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray
from scipy.optimize import minimize

from prescriptxai.config import AppConfig
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.objective import prediction_flip_loss
from prescriptxai.recourse.optimizer import OptimizationResult, optimize_recourse
from prescriptxai.schemas import DeltaMapping

LOGGER = logging.getLogger(__name__)


def no_action_baseline(
    initial_state: dict[str, float], bundle: ModelBundle, safe_threshold: float
) -> OptimizationResult:
    """Return an unchanged candidate and its model-only target-risk status."""
    started = perf_counter_ns()
    if not 0 < safe_threshold < 1:
        raise ValueError("safe_threshold must be within (0, 1)")
    risk = float(bundle.predict_risk(pd.DataFrame([initial_state]))[0])
    model_valid = risk <= safe_threshold
    return OptimizationResult(
        initial_state,
        (),
        risk,
        risk,
        solver_success=True,
        model_valid=model_valid,
        message=(
            "no-action state meets the model-risk target"
            if model_valid
            else "no-action baseline does not meet the safe-risk target"
        ),
        objective_value=0.0,
        risk_reached=risk,
        stage_timings_ms={"total": _elapsed_ms(started)},
    )


def single_actuator_baseline(
    initial_state: dict[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    config: AppConfig,
    coupling: SensorCouplingModel | None = None,
) -> OptimizationResult:
    """Search single-control supports while retaining every actuator's physical limits."""
    one_feature_config = config.model_copy(deep=True)
    one_feature_config.recourse.max_changed_features = 1
    return optimize_recourse(
        initial_state, bundle, taxonomy, one_feature_config, coupling,
        validate_plausibility=False,
    )


def unconstrained_gradient_baseline(
    initial_state: dict[str, float], bundle: ModelBundle, config: AppConfig
) -> OptimizationResult:
    """Optimize every model input without masks, bounds, or physical validation."""
    started = perf_counter_ns()
    initial_risk = float(bundle.predict_risk(pd.DataFrame([initial_state]))[0])
    if initial_risk <= config.model.safe_threshold:
        return no_action_baseline(initial_state, bundle, config.model.safe_threshold)
    if not bundle.supports_gradients:
        return OptimizationResult(
            initial_state, (), initial_risk, initial_risk, False, False,
            "unconstrained gradient baseline has no differentiable predictor", None,
            failure_reason="differentiable_predictor_unavailable",
            risk_reached=initial_risk,
            stage_timings_ms={"total": _elapsed_ms(started)},
        )
    raw = pd.DataFrame([initial_state], columns=bundle.feature_names)
    scaled = bundle.scaler.transform(raw)[0]
    device_name = config.model.torch_device
    if device_name == "cuda" and not torch.cuda.is_available():
        device_name = "cpu"
    base = torch.as_tensor(scaled, dtype=torch.float32, device=device_name)
    scales = bundle.scaler.scaler.scale_

    def value_and_grad(delta: np.ndarray) -> tuple[float, np.ndarray]:
        """Return smooth unconstrained objective and autograd gradient."""
        change = torch.tensor(
            delta, dtype=torch.float64, device=base.device, requires_grad=True
        )
        risk = bundle.torch_forward((base + change.to(torch.float32)).unsqueeze(0)).reshape(())
        hinge = torch.relu(risk - config.model.safe_threshold + config.recourse.safety_margin)
        prediction_loss = (
            hinge.square()
            if config.recourse.prediction_loss == "squared_hinge"
            else hinge
        )
        epsilon = config.recourse.l1_smoothing_epsilon
        l1 = (torch.sqrt(change.square() + epsilon**2) - epsilon).sum()
        objective = l1 + config.recourse.prediction_weight * prediction_loss
        gradient = torch.autograd.grad(objective, change)[0]
        return float(objective.detach()), np.asarray(gradient.detach().cpu(), dtype=np.float64)

    solved = minimize(
        value_and_grad,
        np.zeros(len(bundle.feature_names), dtype=np.float64),
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": config.recourse.max_iterations, "ftol": config.recourse.solver_ftol},
    )
    candidate = dict(initial_state)
    deltas: list[DeltaMapping] = []
    for index, name in enumerate(bundle.feature_names):
        scaled_delta = float(solved.x[index])
        if abs(scaled_delta) <= config.recourse.change_tolerance:
            continue
        raw_delta = scaled_delta * float(scales[index])
        current = float(initial_state[name])
        candidate[name] = current + raw_delta
        deltas.append(
            DeltaMapping(
                feature=name,
                raw_delta=raw_delta,
                scaled_delta=scaled_delta,
                percent_of_current=raw_delta / abs(current) * 100 if current else None,
            )
        )
    final_risk = float(bundle.predict_risk(pd.DataFrame([candidate]))[0])
    valid = final_risk <= config.model.safe_threshold
    return OptimizationResult(
        state=candidate,
        deltas=tuple(deltas),
        initial_risk=initial_risk,
        final_risk=final_risk,
        solver_success=bool(solved.success),
        model_valid=valid,
        message="unconstrained gradient baseline; physical validation was not evaluated",
        objective_value=float(solved.fun),
        failure_reason=None if valid else "safe_risk_not_reached",
        risk_reached=final_risk,
        stage_timings_ms={"optimization": _elapsed_ms(started)},
        objective_terms={
            "l1": float(np.abs(solved.x).sum()),
            "prediction": config.recourse.prediction_weight
            * prediction_flip_loss(final_risk, config.model.safe_threshold),
            "immutable": 0.0,
            "bounds": 0.0,
        },
    )


def bounded_l1_baseline(
    initial_state: dict[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    config: AppConfig,
    coupling: SensorCouplingModel | None = None,
) -> OptimizationResult:
    """Run masked bounded L1 recourse without Tier 2 or Tier 4 candidate filtering."""
    result = optimize_recourse(
        initial_state, bundle, taxonomy, config, coupling, validate_plausibility=False
    )
    return OptimizationResult(
        **{
            **result.__dict__,
            "message": (
                "bounded L1 baseline; physical plausibility not evaluated; " + result.message
            ),
        }
    )


def dice_baseline(
    initial_state: dict[str, float],
    bundle: ModelBundle,
    training_frame: pd.DataFrame,
    config: AppConfig,
    *,
    outcome_name: str = "failure",
) -> OptimizationResult | None:
    """Run the optional DiCE classifier baseline, or log a clear skip if unavailable."""
    try:
        dice_ml = import_module("dice_ml")
    except ImportError:
        LOGGER.info("Skipping optional DiCE baseline: install dice-ml to enable it")
        return None
    if outcome_name not in training_frame:
        raise ValueError(f"DiCE training frame is missing outcome column {outcome_name!r}")

    class BundleAdapter:
        """Minimal sklearn-compatible probability adapter used by DiCE."""

        classes_ = np.asarray([0, 1])

        def predict_proba(
            self, values: pd.DataFrame | np.ndarray
        ) -> NDArray[np.float64]:
            frame = pd.DataFrame(values, columns=bundle.feature_names)
            risk = bundle.predict_risk(frame)
            probabilities: NDArray[np.float64] = np.empty(
                (len(risk), 2), dtype=np.float64
            )
            probabilities[:, 0] = 1.0 - risk
            probabilities[:, 1] = risk
            return probabilities

    data = dice_ml.Data(
        dataframe=training_frame.loc[:, [*bundle.feature_names, outcome_name]],
        continuous_features=list(bundle.feature_names),
        outcome_name=outcome_name,
    )
    model = dice_ml.Model(model=BundleAdapter(), backend="sklearn", model_type="classifier")
    explainer = dice_ml.Dice(data, model, method="random")
    generated = explainer.generate_counterfactuals(
        pd.DataFrame([initial_state], columns=bundle.feature_names),
        total_CFs=1,
        desired_class=0,
    )
    initial_risk = float(bundle.predict_risk(pd.DataFrame([initial_state]))[0])
    examples = generated.cf_examples_list
    if not examples or examples[0].final_cfs_df is None:
        return OptimizationResult(
            initial_state, (), initial_risk, initial_risk, False, False,
            "DiCE did not produce a counterfactual", None,
            failure_reason="dice_no_candidate", risk_reached=initial_risk,
        )
    candidate = {
        name: float(examples[0].final_cfs_df.iloc[0][name]) for name in bundle.feature_names
    }
    risk = float(bundle.predict_risk(pd.DataFrame([candidate]))[0])
    deltas = tuple(
        DeltaMapping(
            feature=name,
            raw_delta=candidate[name] - initial_state[name],
            scaled_delta=(candidate[name] - initial_state[name])
            / float(bundle.scaler.scaler.scale_[index]),
            percent_of_current=(
                (candidate[name] - initial_state[name]) / abs(initial_state[name]) * 100
                if initial_state[name]
                else None
            ),
        )
        for index, name in enumerate(bundle.feature_names)
        if candidate[name] != initial_state[name]
    )
    valid = risk <= config.model.safe_threshold
    return OptimizationResult(
        candidate, deltas, initial_risk, risk, True, valid,
        "optional DiCE candidate; physical validity requires separate checks", None,
        failure_reason=None if valid else "safe_risk_not_reached", risk_reached=risk,
    )


def _elapsed_ms(started_ns: int) -> float:
    """Return elapsed monotonic wall time in milliseconds."""
    return (perf_counter_ns() - started_ns) / 1_000_000
