"""Unit tests for scaled-space recourse and independent validation tiers."""

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.constraints.bounds import allowed_interval, check_bound_violations
from prescriptxai.constraints.coupling import evaluate_rule, validate_couplings
from prescriptxai.constraints.taxonomy import ActuatorConstraint, BoundsSpec, CouplingRule
from prescriptxai.data.preprocess import fit_feature_scaler
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.baselines import no_action_baseline, single_actuator_baseline
from prescriptxai.recourse.objective import (
    RecourseObjective,
    prediction_flip_loss,
    scaled_l1_distance,
)
from prescriptxai.recourse.optimizer import RecourseOptimizer, optimize_recourse
from prescriptxai.recourse.sparsify import bounded_sparse_delta_grid, sparsify_candidate
from prescriptxai.schemas import DeltaMapping
from prescriptxai.validation.pipeline import (
    ValidationReport,
    fit_mahalanobis_validator,
    validate_candidate,
)
from prescriptxai.validation.simulator import SimulatorResult, run_simulator_validation
from prescriptxai.validation.tier1_model import validate_model_risk
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator
from prescriptxai.validation.tier3_engineering import validate_engineering
from prescriptxai.validation.tier4_coupling import validate_sensor_coupling


def test_prediction_flip_and_scaled_l1_objective_components() -> None:
    """The prediction hinge and L1 distance use their stated mathematical definitions."""
    assert prediction_flip_loss(0.3, 0.2) == pytest.approx(0.01)
    assert prediction_flip_loss(0.1, 0.2) == 0.0
    assert scaled_l1_distance(np.array([1.0, -1.0]), np.array([0.0, 1.0])) == 3.0
    with pytest.raises(ValueError, match="same-shaped"):
        scaled_l1_distance(np.array([1.0]), np.array([1.0, 2.0]))


def test_absolute_bounds_and_rate_limit_intersection() -> None:
    """Actuator feasibility intersects physical bounds with per-step rate limits."""
    constraint = ActuatorConstraint(minimum=0, maximum=10, max_change_per_step=2)
    assert allowed_interval(5, constraint) == (3, 7)
    with pytest.raises(ValueError, match="no feasible interval"):
        allowed_interval(13, constraint)


def test_cumulative_rate_horizon_scales_allowance_and_keeps_hard_bounds() -> None:
    """The K-step sensitivity expands rate allowance but never physical actuator bounds."""
    constraint = ActuatorConstraint(minimum=0, maximum=10, max_change_per_step=2)
    assert allowed_interval(5, constraint, horizon_steps=2) == (1.0, 9.0)
    assert allowed_interval(5, constraint, horizon_steps=3) == (0.0, 10.0)
    with pytest.raises(ValueError, match="positive integer"):
        allowed_interval(5, constraint, horizon_steps=0)


def test_tier1_checks_safe_threshold_without_claiming_physical_validity() -> None:
    """Tier 1 reports only the model target result."""
    assert validate_model_risk(0.2, 0.2).valid
    assert not validate_model_risk(0.21, 0.2).valid


def test_coupling_rules_and_empty_rule_configuration() -> None:
    """Configured rules are evaluated; no rules are explicitly unvalidated."""
    rule = CouplingRule(
        name="linear_sensor",
        feature_a="a",
        feature_b="b",
        relation="linear_band",
        tolerance=0.1,
        slope=2.0,
        intercept=1.0,
    )
    assert evaluate_rule({"a": 1.0, "b": 3.05}, rule).passed
    greater_rule = CouplingRule(
        name="greater",
        feature_a="a",
        feature_b="b",
        relation="greater_than",
        tolerance=0.0,
    )
    assert evaluate_rule({"a": 3.0, "b": 1.0}, greater_rule).passed
    _, taxonomy, _ = make_recourse_fixture()
    taxonomy.coupling_rules = []
    valid, diagnostics = validate_couplings({"actuator": 0.0, "sensor": 2.0}, taxonomy)
    assert not valid
    assert "no sensor coupling rules" in diagnostics[0]
    assert not validate_sensor_coupling({"actuator": 0.0, "sensor": 2.0}, taxonomy).valid


def test_tier3_checks_only_actuator_bounds_and_allows_dependent_sensor_changes() -> None:
    """Empirical sensor ranges are not actuator limits; Tier 3 checks controls and freezes."""
    _, taxonomy, _ = make_recourse_fixture()

    invalid = validate_engineering(
        {"actuator": -2.0, "sensor": 2.0},
        {"actuator": 2.5, "sensor": 2.1},
        taxonomy,
    )
    dependent_only = validate_engineering(
        {"actuator": -2.0, "sensor": 2.0},
        {"actuator": -2.0, "sensor": 12.0},
        taxonomy,
    )

    assert not invalid.valid
    assert any("physical maximum" in entry or "rate" in entry for entry in invalid.diagnostics)
    assert dependent_only.valid


def test_tier3_does_not_treat_unresolved_dropped_sensor_bounds_as_actuator_failures() -> None:
    """A dropped/unresolved sensor is outside Tier 3's actuator-bound scope."""
    _, taxonomy, _ = make_recourse_fixture()
    sensor_spec = taxonomy.feature_by_name()["sensor"].model_copy(
        update={"bounds": BoundsSpec(minimum=None, maximum=None)}
    )
    taxonomy.features = tuple(
        sensor_spec if spec.name == "sensor" else spec for spec in taxonomy.features
    )

    result = validate_engineering(
        {"actuator": -1.0, "sensor": 2.0},
        {"actuator": -1.0, "sensor": 2.5},
        taxonomy,
    )

    assert result.valid


def test_tier3_rejects_rate_violation_and_missing_features() -> None:
    """Engineering tier does not confuse absolute bounds with rate compliance."""
    _, taxonomy, _ = make_recourse_fixture()
    taxonomy.actuator_constraints["actuator"].max_change_per_step = 0.5
    rate_result = validate_engineering(
        {"actuator": -2.0, "sensor": 2.0},
        {"actuator": -1.0, "sensor": 2.0},
        taxonomy,
    )
    missing_result = validate_engineering({"actuator": 0.0}, {"actuator": 0.0}, taxonomy)

    assert not rate_result.valid
    assert any(
        "exceeds limit" in message or "rate limit" in message for message in rate_result.diagnostics
    )
    assert not missing_result.valid
    assert "missing configured features" in missing_result.diagnostics[0]


def test_mahalanobis_fits_only_declared_training_engines_and_handles_constant_feature() -> None:
    """Regularization yields finite distances and rejects held-out engine rows at fit time."""
    training = np.column_stack((np.linspace(-1, 1, 8), np.zeros(8)))
    row_engines = np.repeat(np.arange(1, 5, dtype=np.int64), 2)
    fitted = MahalanobisValidator.fit(
        training,
        ("variable", "constant"),
        row_engines,
        (1, 2, 3, 4),
        max_distance=5,
        regularization=1e-6,
    )

    assert fitted.training_engine_ids == (1, 2, 3, 4)
    assert np.isfinite(fitted.distance(np.array([0.0, 0.0])))
    assert not fitted.validate(np.array([10.0, 0.0])).valid
    with pytest.raises(ValueError, match="exactly the declared training engines"):
        MahalanobisValidator.fit(
            training,
            ("variable", "constant"),
            row_engines,
            (1, 2, 3, 5),
            max_distance=5,
            regularization=1e-6,
        )


def test_mahalanobis_rejects_nan_and_wrong_shape() -> None:
    """Mahalanobis candidate vectors must match fitted schema and be finite."""
    bundle, _, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)

    with pytest.raises(ValueError, match="shape does not match"):
        validator.distance(np.array([1.0]))
    with pytest.raises(ValueError, match="must be finite"):
        validator.distance(np.array([np.nan, 0.0]))
    with pytest.raises(ValueError, match="at least two rows"):
        MahalanobisValidator.fit(np.array([[0.0, 0.0]]), ("a", "b"), np.array([1]), (1,), 5, 1e-6)


def test_optimizer_finds_sparse_safe_bounded_candidate_and_reports_both_delta_units() -> None:
    """The optimizer obeys actuator bounds/rate limits and keeps both delta mappings."""
    bundle, taxonomy, _ = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_scaled_distance = 3.0
    config.recourse.max_changed_features = 1
    config.recourse.max_iterations = 200
    initial = {"actuator": -2.0, "sensor": 2.0}

    result = optimize_recourse(initial, bundle, taxonomy, config)

    assert result.initial_risk >= config.model.danger_threshold
    assert result.model_valid
    assert result.actuator_constraints_feasible
    assert result.final_risk <= config.model.safe_threshold
    assert len(result.deltas) == 1
    assert result.deltas[0].feature == "actuator"
    assert result.state["actuator"] <= taxonomy.actuator_constraints["actuator"].maximum
    assert (
        result.state["actuator"] - initial["actuator"]
        <= taxonomy.actuator_constraints["actuator"].max_change_per_step
    )
    assert not check_bound_violations(
        result.state, taxonomy, features=("actuator",)
    )
    assert result.deltas[0].raw_delta != result.deltas[0].scaled_delta
    assert result.deltas[0].percent_of_current is not None
    assert result.deltas[0].percent_of_range == pytest.approx(
        result.deltas[0].raw_delta / 4.0 * 100
    )
    assert abs(result.deltas[0].scaled_delta) <= config.recourse.max_scaled_distance


def test_optimizer_refuses_no_actuator_and_low_risk_inputs() -> None:
    """No-actuator and below-danger states return explicit non-success outcomes."""
    bundle, taxonomy, _ = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    initial = {"actuator": -2.0, "sensor": 2.0}
    no_controls = taxonomy.model_copy(deep=True)
    no_controls.feature_groups.controllable_actuators.features = []
    no_controls.actuator_constraints = {}
    no_actuator_result = optimize_recourse(initial, bundle, no_controls, config)
    low_risk_result = optimize_recourse({"actuator": 2.0, "sensor": 2.0}, bundle, taxonomy, config)

    assert not no_actuator_result.model_valid
    assert "no controllable actuators" in no_actuator_result.message
    assert low_risk_result.model_valid
    assert "no action needed" in low_risk_result.message


def test_differentiable_objective_gradient_matches_finite_differences() -> None:
    """Torch autograd agrees with centered differences away from the hinge kink."""

    def risk(delta: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(2.0 * delta[0] - delta[1] + 0.7)

    objective = RecourseObjective(
        risk,
        np.array([-1.0, -1.0]),
        np.array([1.0, 1.0]),
        safe_threshold=0.2,
        safety_margin=0.01,
        alpha=8.0,
        beta=1.0,
        gamma=1.0,
        l1_weight=0.7,
        l1_mode="smooth",
        smoothing_epsilon=1e-5,
        prediction_loss="squared_hinge",
    )
    point = np.array([0.2, -0.15])
    _, gradient = objective.value_and_grad(point)
    finite_difference = np.zeros_like(point)
    step = 1e-6
    for index in range(len(point)):
        plus, minus = point.copy(), point.copy()
        plus[index] += step
        minus[index] -= step
        finite_difference[index] = (
            objective.value_and_grad(plus)[0] - objective.value_and_grad(minus)[0]
        ) / (2 * step)
    np.testing.assert_allclose(gradient, finite_difference, rtol=2e-5, atol=2e-5)


def test_objective_terms_are_separately_reported_and_weighted() -> None:
    """L1, prediction, immutable, and bound terms remain individually inspectable."""

    def risk(delta: torch.Tensor) -> torch.Tensor:
        return delta[0] * 0.0 + 0.8

    objective = RecourseObjective(
        risk,
        np.array([-0.2]),
        np.array([0.2]),
        safe_threshold=0.2,
        safety_margin=0.01,
        alpha=2.0,
        beta=50.0,
        gamma=1.0,
        l1_weight=1.0,
        l1_mode="smooth",
        smoothing_epsilon=1e-6,
        prediction_loss="squared_hinge",
    )
    terms = objective.components(np.array([0.5]))

    assert terms.l1 == pytest.approx(0.5, abs=1e-6)
    assert terms.prediction == pytest.approx(2.0 * (0.8 - 0.2 + 0.01) ** 2)
    assert terms.immutable == 0.0
    assert terms.bounds == pytest.approx((0.5 - 0.2) ** 2)
    assert terms.total == pytest.approx(
        terms.l1 + terms.prediction + terms.immutable + terms.bounds
    )


def test_smooth_and_positive_negative_l1_modes_agree() -> None:
    """The split formulation approaches the smooth formulation as epsilon shrinks."""

    def risk(delta: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(delta.sum() + 0.5)

    common = {
        "risk_function": risk,
        "lower_change": np.array([-1.0, -1.0]),
        "upper_change": np.array([1.0, 1.0]),
        "safe_threshold": 0.2,
        "safety_margin": 0.0,
        "alpha": 3.0,
        "beta": 1.0,
        "gamma": 1.0,
        "l1_weight": 1.0,
        "smoothing_epsilon": 1e-8,
        "prediction_loss": "squared_hinge",
    }
    smooth = RecourseObjective(**common, l1_mode="smooth")
    split = RecourseObjective(**common, l1_mode="split")
    change = np.array([0.25, -0.4])
    assert smooth.components(smooth.encode(change)).total == pytest.approx(
        split.components(split.encode(change)).total, abs=1e-7
    )


@settings(max_examples=5, deadline=None)
@given(sensor_value=st.floats(min_value=-10, max_value=10, allow_nan=False))
def test_frozen_feature_is_unchanged_for_random_states(sensor_value: float) -> None:
    """Only the configured controllable proxy enters the solver decision vector."""
    bundle, taxonomy, _ = make_recourse_fixture()
    taxonomy.feature_groups.dependent_sensors.features = []
    taxonomy.feature_groups.immutable_environmental.features = ["sensor"]
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_changed_features = 1
    config.recourse.alpha_steps = 4
    config.recourse.l1_escalation_steps = 1
    config.recourse.restarts = 1
    config.recourse.max_iterations = 60
    result = RecourseOptimizer(bundle, taxonomy).solve(
        {"actuator": -2.0, "sensor": sensor_value}, config
    )
    assert result.state["sensor"] == sensor_value


def test_optimizer_no_action_timing_extreme_bound_and_seeded_multistart() -> None:
    """Safe states are no-ops; bounded edge states remain feasible and seeded results repeat."""
    bundle, taxonomy, _ = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_changed_features = 1
    config.recourse.restarts = 2
    config.recourse.max_iterations = 100
    optimizer = RecourseOptimizer(bundle, taxonomy)

    safe = optimizer.solve({"actuator": 2.0, "sensor": 2.0}, config)
    assert safe.model_valid and not safe.deltas
    assert safe.message.startswith("no action needed")
    assert safe.stage_timings_ms["total"] >= 0

    edge = optimizer.solve({"actuator": -2.0, "sensor": 10.0}, config)
    assert taxonomy.actuator_constraints["actuator"].minimum <= edge.state["actuator"]
    assert edge.state["actuator"] <= taxonomy.actuator_constraints["actuator"].maximum
    assert abs(edge.state["actuator"] + 2.0) <= 4.0

    config.recourse.restarts = 1
    single_start = optimizer.solve({"actuator": -2.0, "sensor": 2.0}, config)
    config.recourse.restarts = 2
    repeated = optimizer.solve({"actuator": -2.0, "sensor": 2.0}, config)
    again = optimizer.solve({"actuator": -2.0, "sensor": 2.0}, config)
    assert repeated.state == again.state
    assert repeated.final_risk == again.final_risk
    assert repeated.stage_timings_ms["optimization"] >= 0
    if single_start.objective_value is not None and repeated.objective_value is not None:
        assert repeated.objective_value <= single_start.objective_value + 1e-9


def test_bounded_sparse_grid_respects_change_bounds_and_support_limit() -> None:
    """True-model fallback points obey the same box and configured k-sparsity limits."""
    candidates = bounded_sparse_delta_grid(
        np.array([-1.0, 0.0, -2.0]),
        np.array([1.0, 0.0, 2.0]),
        max_changed_features=2,
        grid_points=5,
        change_tolerance=1e-8,
    )
    assert candidates.ndim == 2 and candidates.shape[1] == 3
    assert len(candidates) == 24
    assert np.all(candidates >= np.array([-1.0, 0.0, -2.0]))
    assert np.all(candidates <= np.array([1.0, 0.0, 2.0]))
    assert np.all(np.count_nonzero(candidates, axis=1) <= 2)
    assert np.all(np.count_nonzero(candidates, axis=1) >= 1)
    mandatory = bounded_sparse_delta_grid(
        np.array([0.5, -1.0]),
        np.array([1.0, 1.0]),
        max_changed_features=1,
        grid_points=3,
        change_tolerance=1e-8,
    )
    assert mandatory.shape == (3, 2)
    assert np.all(mandatory[:, 0] > 0.0)
    assert np.all(mandatory[:, 1] == 0.0)
    with pytest.raises(ValueError, match="grid_points"):
        bounded_sparse_delta_grid(
            np.array([-1.0]),
            np.array([1.0]),
            max_changed_features=1,
            grid_points=1,
            change_tolerance=0.0,
        )


def test_optimizer_reports_structured_failure_for_missing_gradients() -> None:
    """A nondifferentiable primary without an XGBoost surrogate fails explicitly."""
    bundle, taxonomy, _ = make_recourse_fixture()
    bundle.estimator.supports_gradients = False
    config = load_config(Path("configs/default.yaml"))
    result = RecourseOptimizer(bundle, taxonomy).solve(
        {"actuator": -2.0, "sensor": 2.0}, config
    )
    assert not result.model_valid
    assert result.failure_reason == "differentiable_predictor_unavailable"
    assert result.risk_reached == result.initial_risk


def test_unsafe_direction_limited_recourse_returns_closest_candidate_and_reason() -> None:
    """A rate/direction-fixed actuator returns a structured failure, not false success."""
    bundle, taxonomy, _ = make_recourse_fixture()
    taxonomy.actuator_constraints["actuator"].direction = "decrease_only"
    config = load_config(Path("configs/default.yaml"))
    config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = 1
    config.recourse.restarts = 1
    config.recourse.max_iterations = 20
    initial = {"actuator": -2.0, "sensor": 2.0}

    result = RecourseOptimizer(bundle, taxonomy).solve(initial, config)

    assert not result.model_valid
    assert result.failure_reason == "safe_risk_not_reached"
    assert result.state["actuator"] == initial["actuator"]
    assert result.risk_reached == result.initial_risk
    assert result.solver_calls >= 1
    assert result.actuator_constraints_feasible


def test_unreachable_out_of_bounds_state_returns_no_feasible_candidate() -> None:
    """An out-of-range state beyond its one-step rate limit is explicitly infeasible."""
    bundle, taxonomy, _ = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    result = RecourseOptimizer(bundle, taxonomy).solve(
        {"actuator": -20.0, "sensor": 2.0}, config
    )

    assert not result.model_valid
    assert result.failure_reason == "infeasible_actuator_interval"
    assert not result.actuator_constraints_feasible
    assert result.risk_reached == result.initial_risk


def test_failure_candidate_projects_reachable_out_of_bounds_input() -> None:
    """When the rate box can reach physical bounds, even failure output is bound-feasible."""
    bundle, taxonomy, _ = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = 1
    config.recourse.restarts = 1
    config.recourse.max_iterations = 1

    result = RecourseOptimizer(bundle, taxonomy).solve(
        {"actuator": -2.5, "sensor": 2.0}, config
    )

    assert result.actuator_constraints_feasible
    assert result.state["actuator"] >= taxonomy.actuator_constraints["actuator"].minimum
    assert result.state["actuator"] <= taxonomy.actuator_constraints["actuator"].maximum
    assert abs(result.state["actuator"] + 2.5) <= 4.0


def test_validation_pipeline_reports_model_and_physical_checks_separately() -> None:
    """A full fixture validates all tiers, and no-rule configurations cannot pass Tier 4."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    initial = {"actuator": -2.0, "sensor": 2.0}
    candidate = {"actuator": 0.9, "sensor": 2.0}

    report: ValidationReport = validate_candidate(
        initial, candidate, bundle, taxonomy, validator, config
    )
    outcome = report.as_outcome(
        float(bundle.predict_risk(pd.DataFrame([initial]))[0]),
        float(bundle.predict_risk(pd.DataFrame([candidate]))[0]),
        (
            DeltaMapping(
                feature="actuator",
                raw_delta=2.9,
                scaled_delta=2.9 / bundle.scaler.scaler.scale_[0],
            ),
        ),
        recourse_feasible=True,
    )
    assert report.model_valid
    assert report.physical_valid
    assert outcome.success

    taxonomy.coupling_rules = []
    failed_report = validate_candidate(initial, candidate, bundle, taxonomy, validator, config)
    assert failed_report.model_valid
    assert not failed_report.physical_valid
    assert not failed_report.success
    assert not failed_report.tier4_coupling.valid


def test_sparsifier_and_baselines_report_failures_without_claims() -> None:
    """Unsafe subsets remain failures; baseline output states exactly what it checked."""
    bundle, taxonomy, _ = make_recourse_fixture()
    initial = {"actuator": -2.0, "sensor": 2.0}
    sparse = sparsify_candidate(
        bundle, initial, {"actuator": -1.5, "sensor": 2.0}, ("actuator",), 1, 0.2
    )
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_scaled_distance = 3.0
    config.recourse.max_iterations = 200
    no_action = no_action_baseline(initial, bundle, config.model.safe_threshold)
    single = single_actuator_baseline(initial, bundle, taxonomy, config)

    assert not sparse.success
    assert "no safe candidate" in sparse.message
    assert not no_action.model_valid
    assert not single.model_valid or len(single.deltas) == 1


def test_sparsifier_never_returns_more_than_configured_changes_when_unsafe() -> None:
    """An infeasible safe target still returns a sparse best-effort candidate."""
    from fixtures.recourse_models import SigmoidEstimator

    training = pd.DataFrame(
        {
            "engine_id": [1, 1, 2, 2, 3, 3],
            "actuator": [-2.0, -1.0, 0.0, 1.0, 2.0, 1.0],
            "second_actuator": [-2.0, 0.0, 2.0, -1.0, 1.0, 0.5],
            "sensor": [2.0] * 6,
        }
    )
    feature_names = ("actuator", "second_actuator", "sensor")
    scaler = fit_feature_scaler(training, feature_names)
    bundle = ModelBundle(
        estimator=SigmoidEstimator(),
        scaler=scaler,
        feature_names=feature_names,
        training_engine_ids=scaler.training_engine_ids,
        model_type="test-only-sigmoid",
        seed=17,
    )
    initial = {"actuator": -2.0, "second_actuator": -2.0, "sensor": 2.0}
    candidate = {"actuator": -1.5, "second_actuator": 2.0, "sensor": 2.0}

    result = sparsify_candidate(
        bundle,
        initial,
        candidate,
        ("actuator", "second_actuator"),
        max_changed_features=1,
        safe_threshold=0.2,
    )

    assert not result.success
    assert len(result.changed_features) <= 1
    assert result.changed_features == ("actuator",)
    assert result.risk < bundle.predict_risk(pd.DataFrame([initial]))[0]


def test_simulator_interface_is_opt_in_and_requires_an_adapter() -> None:
    """Unavailable dynamic evidence is explicitly skipped; adapters declare their level."""

    class FixtureSimulator:
        def validate_candidate(self, state: Mapping[str, float]) -> SimulatorResult:
            return SimulatorResult(
                valid=state["actuator"] <= 1.0, diagnostics=(), evidence_level="E4"
            )

    state = {"actuator": 0.5}
    assert run_simulator_validation(state, enabled=False, simulator=None).status == "skipped"
    assert run_simulator_validation(state, enabled=True, simulator=None).status == "skipped"
    result = run_simulator_validation(state, enabled=True, simulator=FixtureSimulator())
    assert result is not None and result.valid
