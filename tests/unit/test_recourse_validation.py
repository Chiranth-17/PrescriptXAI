"""Unit tests for scaled-space recourse and independent validation tiers."""

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.constraints.bounds import allowed_interval
from prescriptxai.constraints.coupling import evaluate_rule, validate_couplings
from prescriptxai.constraints.taxonomy import ActuatorConstraint, CouplingRule
from prescriptxai.data.preprocess import fit_feature_scaler
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.baselines import no_action_baseline, single_actuator_baseline
from prescriptxai.recourse.objective import prediction_flip_loss, scaled_l1_distance
from prescriptxai.recourse.optimizer import optimize_recourse
from prescriptxai.recourse.sparsify import sparsify_candidate
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


def test_tier3_rejects_out_of_bounds_but_allows_dependent_sensor_changes() -> None:
    """Engineering validation checks actuator bounds while allowing dependent updates."""
    _, taxonomy, _ = make_recourse_fixture()

    invalid = validate_engineering(
        {"actuator": -2.0, "sensor": 2.0},
        {"actuator": 2.5, "sensor": 2.1},
        taxonomy,
    )
    dependent_only = validate_engineering(
        {"actuator": -2.0, "sensor": 2.0},
        {"actuator": -2.0, "sensor": 2.5},
        taxonomy,
    )

    assert not invalid.valid
    assert any("physical maximum" in entry or "rate" in entry for entry in invalid.diagnostics)
    assert dependent_only.valid


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
    assert result.final_risk <= config.model.safe_threshold
    assert len(result.deltas) == 1
    assert result.deltas[0].feature == "actuator"
    assert result.state["actuator"] <= taxonomy.actuator_constraints["actuator"].maximum
    assert (
        result.state["actuator"] - initial["actuator"]
        <= taxonomy.actuator_constraints["actuator"].max_change_per_step
    )
    assert result.deltas[0].raw_delta != result.deltas[0].scaled_delta
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
    assert not low_risk_result.model_valid
    assert "below the configured danger" in low_risk_result.message


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
    """Disabled simulator calls are omitted; enabled calls require an implementation."""

    class FixtureSimulator:
        def validate_candidate(self, state: Mapping[str, float]) -> SimulatorResult:
            return SimulatorResult(valid=state["actuator"] <= 1.0, diagnostics=())

    state = {"actuator": 0.5}
    assert run_simulator_validation(state, enabled=False, simulator=None) is None
    with pytest.raises(RuntimeError, match="no simulator adapter"):
        run_simulator_validation(state, enabled=True, simulator=None)
    result = run_simulator_validation(state, enabled=True, simulator=FixtureSimulator())
    assert result is not None and result.valid
