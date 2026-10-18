"""Regression coverage for preserving safe candidates and mandatory sparse actions."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
from numpy.typing import NDArray

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.taxonomy import ActuatorConstraint, CouplingRule, RateLimitSpec
from prescriptxai.models.torch_models import LSTMFailureModel
from prescriptxai.recourse.optimizer import RecourseOptimizer
from prescriptxai.recourse.sparsify import candidate_supports
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


class NarrowSafeBowl:
    """Test-only differentiable classifier with a safe interval between grid endpoints."""

    supports_gradients = True
    classes_ = np.array([0, 1])

    def predict_proba(self, values: NDArray[np.float64]) -> NDArray[np.float64]:
        """Produce matching NumPy probabilities for true-model rescoring."""
        risk = 1.0 / (1.0 + np.exp(-8.0 * ((values[:, 0] - 0.3) ** 2 - 0.3)))
        return np.column_stack((1.0 - risk, risk))

    def torch_forward(self, values: torch.Tensor) -> torch.Tensor:
        """Provide the exact gradient of the synthetic classifier."""
        return torch.sigmoid(8.0 * ((values[:, 0] - 0.3) ** 2 - 0.3))


def _config() -> AppConfig:
    """Keep real solver regression tests small and deterministic."""
    config = load_config(Path("configs/default.yaml"))
    config.recourse.restarts = 1
    config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = 1
    config.recourse.max_iterations = 100
    config.recourse.max_changed_features = 1
    return config


def test_grid_miss_preserves_safe_gradient_candidate() -> None:
    """Skip needless grids at feasible means; preserve safe diagnostics on impossible coupling."""
    bundle, taxonomy, training = make_recourse_fixture()
    bundle.estimator = NarrowSafeBowl()
    config = _config()
    config.recourse.prediction_weight = 1000.0
    config.recourse.true_model_grid_points = 2
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    validator = replace(validator, max_distance=1e-12)
    initial = {"actuator": -0.5, "sensor": 2.0}
    optimizer = RecourseOptimizer(bundle, taxonomy, mahalanobis=validator)

    config.recourse.true_model_grid_enabled = False
    gradient_result = optimizer.solve(initial, config)
    config.recourse.true_model_grid_enabled = True
    grid_result = optimizer.solve(initial, config)

    assert gradient_result.model_valid
    assert grid_result.true_model_evaluations == 0
    assert grid_result.model_valid
    assert grid_result.failure_reason is None
    assert grid_result.final_risk <= config.model.safe_threshold
    assert grid_result.state == gradient_result.state
    scaled_candidate = bundle.scaler.transform(pd.DataFrame([grid_result.state]))[0]
    assert validator.validate(scaled_candidate).valid

    # No actuator change can satisfy sensor=5 while this dependent fixture sensor remains 2.
    # A coarse grid must not erase the existing safe gradient point or disguise this failure.
    taxonomy.coupling_rules = [
        CouplingRule(
            name="impossible_constant_relation",
            feature_a="actuator",
            feature_b="sensor",
            relation="linear_band",
            slope=0.0,
            intercept=5.0,
            tolerance=0.0,
        )
    ]
    config.recourse.true_model_grid_enabled = False
    failed_gradient = optimizer.solve(initial, config)
    config.recourse.true_model_grid_enabled = True
    failed_grid = optimizer.solve(initial, config)
    assert failed_gradient.model_valid and failed_grid.model_valid
    assert failed_grid.true_model_evaluations > 0
    assert failed_grid.state == failed_gradient.state
    assert failed_grid.failure_reason == "validation_feedback_exhausted"
    assert not failed_grid.solver_success

    baseline = RecourseOptimizer(
        bundle, taxonomy, mahalanobis=validator, validate_plausibility=False
    ).solve(initial, config)
    assert baseline.model_valid
    assert baseline.true_model_evaluations == 0
    assert "Tier 2" not in baseline.message


def test_mandatory_bound_corrections_consume_sparse_support_budget() -> None:
    """A required correction cannot be silently appended after optimizing a different support."""
    bundle, taxonomy, _ = make_recourse_fixture()
    taxonomy.feature_groups.controllable_actuators.features.append("sensor")
    taxonomy.feature_groups.dependent_sensors.features = []
    taxonomy.actuator_constraints["sensor"] = ActuatorConstraint(
        minimum=0.0, maximum=10.0, max_change_per_step=4.0
    )
    taxonomy.features = tuple(
        feature.model_copy(
            update={
                "group": "controllable",
                "max_rate_of_change": RateLimitSpec(absolute=4.0),
            }
        )
        if feature.name == "sensor"
        else feature
        for feature in taxonomy.features
    )
    config = _config()
    config.recourse.true_model_grid_enabled = False
    initial = {"actuator": -2.0, "sensor": 11.0}

    result = RecourseOptimizer(bundle, taxonomy).solve(initial, config)

    assert not result.model_valid
    assert len(result.deltas) == 1
    assert result.deltas[0].feature == "sensor"
    assert result.state["actuator"] == initial["actuator"]
    assert result.state["sensor"] == 10.0
    assert result.final_risk == result.initial_risk

    impossible = RecourseOptimizer(bundle, taxonomy).solve(
        {"actuator": -2.5, "sensor": 11.0}, config
    )
    assert impossible.failure_reason == "mandatory_changes_exceed_sparsity"
    assert not impossible.model_valid
    assert "diagnostic only" in impossible.message

    taxonomy.actuator_constraints["actuator"].minimum = 0.8
    safe_projection = RecourseOptimizer(bundle, taxonomy).solve(initial, config)
    assert safe_projection.failure_reason == "mandatory_changes_exceed_sparsity"
    assert safe_projection.model_valid
    assert safe_projection.final_risk <= config.model.safe_threshold
    assert len(safe_projection.deltas) > config.recourse.max_changed_features
    assert not safe_projection.solver_success


def test_candidate_supports_include_required_features_before_optional_ranking() -> None:
    """Mandatory small corrections count toward k even when optional changes rank higher."""
    supports = candidate_supports(
        {"a": 2.0, "b": 1.0, "c": 0.01},
        ("a", "b", "c"),
        max_changed_features=2,
        top_m=3,
        max_supports=8,
        required_features=("c",),
    )
    assert supports == (("c", "a"), ("c", "b"), ("c",))
    assert (
        candidate_supports(
            {"a": 2.0, "b": 1.0},
            ("a", "b"),
            max_changed_features=1,
            top_m=2,
            max_supports=8,
            required_features=("a", "b"),
        )
        == ()
    )
    with pytest.raises(ValueError, match="required_features"):
        candidate_supports(
            {"a": 2.0},
            ("a",),
            max_changed_features=1,
            top_m=1,
            max_supports=1,
            required_features=("unknown",),
        )


def test_candidate_objective_uses_common_weights_and_true_predictor_risk() -> None:
    """Alpha escalation guides search while candidates share a comparable selection cost."""
    bundle, taxonomy, _ = make_recourse_fixture()
    config = _config()
    config.recourse.alpha_steps = 4
    config.recourse.alpha_growth = 10.0
    config.recourse.true_model_grid_enabled = False
    config.recourse.l1_mode = "split"

    result = RecourseOptimizer(bundle, taxonomy).solve({"actuator": -2.0, "sensor": 2.0}, config)

    assert result.model_valid
    assert result.alpha_used is not None and result.alpha_used > config.recourse.prediction_weight
    action_cost = sum(abs(delta.scaled_delta) for delta in result.deltas)
    hinge = max(
        0.0, result.final_risk - config.model.safe_threshold + config.recourse.safety_margin
    )
    expected = (
        config.recourse.l1_weight * action_cost + config.recourse.prediction_weight * hinge**2
    )
    assert result.objective_value == pytest.approx(expected)
    assert result.objective_terms["total"] == result.objective_value
    assert result.objective_terms["risk"] == result.final_risk
    assert result.objective_terms["search_total"] != result.objective_terms["total"]


def test_snapshot_recourse_rejects_lstm_before_attempting_to_score() -> None:
    """A fitted sequence predictor requires observed history instead of fabricated risk."""
    bundle, taxonomy, training = make_recourse_fixture()
    scaled = bundle.scaler.transform(training.loc[:, list(bundle.feature_names)])
    sequences = np.repeat(scaled[:, None, :], 2, axis=1)
    labels = (training["actuator"].to_numpy() < 0.0).astype(np.float64)
    bundle.estimator = LSTMFailureModel(window=2, hidden_dims=(4,), epochs=1).fit(sequences, labels)

    with pytest.raises(ValueError, match="LSTM recourse requires a telemetry history window"):
        RecourseOptimizer(bundle, taxonomy).solve({"actuator": -2.0, "sensor": 2.0}, _config())
