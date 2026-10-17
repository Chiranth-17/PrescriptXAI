"""Integration checks for bounded true-model search after surrogate mismatch."""

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.optimizer import RecourseOptimizer
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


class ThresholdEstimator:
    """Small non-differentiable risk model used only to test true-model rescoring."""

    classes_ = np.array([0, 1])
    supports_gradients = False

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return a calibrated step probability over the first scaled feature."""
        risk = np.where(features[:, 0] < 0.3, 0.9, 0.1)
        return np.column_stack((1.0 - risk, risk))


class UnsafeThresholdEstimator(ThresholdEstimator):
    """Step predictor whose reachable lower-risk region remains above tau_safe."""

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return a lower but still unsafe probability beyond the threshold."""
        risk = np.where(features[:, 0] < 0.3, 0.9, 0.7)
        return np.column_stack((1.0 - risk, risk))


class OpposingSurrogate:
    """Differentiable path with a deliberately opposing local direction."""

    supports_gradients = True
    device = "cpu"

    def torch_forward(self, features: torch.Tensor) -> torch.Tensor:
        """Return a smooth risk direction that intentionally opposes the teacher."""
        return torch.sigmoid(8.0 * features[:, 0])


def test_bounded_true_model_search_recovers_safe_sparse_physical_candidate() -> None:
    """A true-model step missed by a mismatched surrogate is recovered within all tiers."""
    original, taxonomy, training = make_recourse_fixture()
    bundle = ModelBundle(
        estimator=ThresholdEstimator(),
        scaler=original.scaler,
        feature_names=original.feature_names,
        training_engine_ids=original.training_engine_ids,
        model_type="test-only-step-model",
        seed=original.seed,
        surrogate=OpposingSurrogate(),
    )
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_changed_features = 1
    config.recourse.restarts = 1
    config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = 1
    config.recourse.max_iterations = 8
    config.recourse.true_model_grid_points = 5
    training_rows = training.rename(columns={"actuator": "actuator", "sensor": "sensor"})
    validator = fit_mahalanobis_validator(
        training_rows, bundle, bundle.training_engine_ids, config
    )

    result = RecourseOptimizer(bundle, taxonomy, mahalanobis=validator).solve(
        {"actuator": -2.5, "sensor": 2.0}, config
    )

    assert result.model_valid
    assert len(result.deltas) == 1
    assert result.final_risk <= config.model.safe_threshold
    assert result.state["actuator"] < 2.0
    assert taxonomy.actuator_constraints["actuator"].minimum <= result.state["actuator"]
    assert result.state["actuator"] <= taxonomy.actuator_constraints["actuator"].maximum
    assert abs(result.state["actuator"] + 2.5) <= taxonomy.actuator_constraints[
        "actuator"
    ].max_change_per_step
    assert result.true_model_evaluations > 0
    assert result.stage_timings_ms["true_model_grid_search"] >= 0.0
    assert "Tier 2–4 checks pass" in result.message
    assert validator.validate(bundle.scaler.transform(pd.DataFrame([result.state]))[0]).valid


def test_grid_failure_returns_its_closest_true_model_candidate() -> None:
    """When safety is unreachable, grid search can improve the structured failure diagnostic."""
    original, taxonomy, training = make_recourse_fixture()
    bundle = ModelBundle(
        estimator=UnsafeThresholdEstimator(),
        scaler=original.scaler,
        feature_names=original.feature_names,
        training_engine_ids=original.training_engine_ids,
        model_type="test-only-unreachable-step-model",
        seed=original.seed,
        surrogate=OpposingSurrogate(),
    )
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_changed_features = 1
    config.recourse.restarts = 1
    config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = 1
    config.recourse.max_iterations = 8
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)

    result = RecourseOptimizer(bundle, taxonomy, mahalanobis=validator).solve(
        {"actuator": -2.0, "sensor": 2.0}, config
    )

    assert not result.model_valid
    assert result.failure_reason == "safe_risk_not_reached"
    assert result.final_risk == 0.7
    assert result.final_risk > config.model.safe_threshold
    assert len(result.deltas) == 1
    assert result.true_model_evaluations > 0
