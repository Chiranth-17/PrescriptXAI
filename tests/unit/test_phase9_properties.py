"""Property checks for scientific contracts, using explicit test-only fixture models."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.pipeline import PrescriptXAI, PrescriptXAIEngine
from prescriptxai.validation.base import TierResult
from prescriptxai.validation.pipeline import ValidationReport, fit_mahalanobis_validator

FINITE = st.floats(min_value=-2.5, max_value=2.5, allow_nan=False, allow_infinity=False)
PROPERTY = settings(max_examples=20, deadline=None, derandomize=True)


def property_service() -> PrescriptXAI:
    """Build a known monotone logic fixture, never an empirical efficacy estimate."""
    bundle, taxonomy, training = make_recourse_fixture()
    taxonomy.feature_groups.dependent_sensors.features = []
    taxonomy.feature_groups.immutable_environmental.features = ["sensor"]
    config = load_config(Path("configs/default.yaml"))
    config.recourse.alpha_steps = config.recourse.restarts = 1
    config.recourse.l1_escalation_steps = config.recourse.support_search_limit = 1
    config.recourse.max_iterations = 25
    config.recourse.max_changed_features = 1
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    return PrescriptXAI(PrescriptXAIEngine(config, taxonomy, bundle, validator))


@PROPERTY
@given(actuator=FINITE, frozen=st.floats(min_value=1, max_value=4, allow_nan=False))
def test_recourse_frozen_bounds_sparsity_finiteness_and_triage(
    actuator: float, frozen: float
) -> None:
    """Every solved state obeys its declared immutable and outcome-dependent guarantees."""
    service = property_service()
    result = service.recommend({"actuator": actuator, "sensor": frozen})
    assert result.new_state["sensor"] == frozen
    numeric = [result.risk_before, result.risk_after, *result.new_state.values()]
    numeric += [d.raw_delta for d in result.delta_per_feature.values()]
    numeric += [
        d.scaled_delta for d in result.delta_per_feature.values() if d.scaled_delta is not None
    ]
    assert np.isfinite(numeric).all()
    if result.status == "RECOVERABLE":
        assert result.risk_after <= service.config.tau_safe
        assert result.validation_report.joint and result.action_feasible
        assert len(result.action_features) <= service.config.recourse.k_max
        constraint = service.engine.taxonomy.actuator_constraints["actuator"]
        assert constraint.minimum <= result.new_state["actuator"] <= constraint.maximum
        assert abs(result.new_state["actuator"] - actuator) <= constraint.max_change_per_step
    if result.status == "PARTIAL":
        assert result.risk_after > service.config.tau_safe
        assert result.risk_before - result.risk_after >= service.config.pipeline.delta_min
        assert result.validation_report.plausible and result.validation_report.constraints_ok
    if result.risk_after <= service.config.tau_safe:
        assert result.status != "PARTIAL"
    if not result.alert:
        assert result.status == "NO_INTERVENTION"
        assert result.original_state == result.new_state
        assert result.risk_before == result.risk_after
    if result.status == "ESCALATE":
        assert result.failure is not None and result.failure.suggested_escalation


@PROPERTY
@given(actuator=FINITE, sensor=FINITE, delta=FINITE)
def test_raw_scaled_round_trip_and_delta_direction(
    actuator: float, sensor: float, delta: float
) -> None:
    """Scaling and inverse scaling preserve values and the sign/units of interventions."""
    bundle, _, _ = make_recourse_fixture()
    raw = np.asarray([[actuator, sensor]], dtype=np.float64)
    transformed = bundle.scaler.transform(pd.DataFrame(raw, columns=bundle.feature_names))
    np.testing.assert_allclose(bundle.scaler.scaler.inverse_transform(transformed), raw, atol=1e-14)
    changed = raw.copy()
    changed[0, 0] += delta
    transformed_changed = bundle.scaler.transform(
        pd.DataFrame(changed, columns=bundle.feature_names)
    )
    expected = delta / bundle.scaler.scaler.scale_[0]
    assert transformed_changed[0, 0] - transformed[0, 0] == pytest.approx(expected, abs=1e-14)


@PROPERTY
@given(first=FINITE, second=FINITE)
def test_mahalanobis_is_nonnegative_and_zero_at_the_mean(first: float, second: float) -> None:
    """Distance is a norm in the fitted regime, including identical vectors at its mean."""
    service = property_service()
    validator = service.engine.mahalanobis
    assert validator.distance(np.asarray([first, second])) >= 0
    assert validator.distance(validator.mean.copy()) == 0


@PROPERTY
@given(bits=st.tuples(st.booleans(), st.booleans(), st.booleans(), st.booleans()))
def test_validation_verdicts_follow_the_four_independent_tiers(
    bits: tuple[bool, bool, bool, bool],
) -> None:
    """Tier2 plausibility, proxy constraints and joint success retain distinct definitions."""
    report = ValidationReport(*(TierResult(bit, ()) for bit in bits))
    public = report.to_schema()
    assert report.model_valid == public.model_valid == bits[0]
    assert report.plausible == public.plausible == bits[1]
    assert report.constraints_ok == public.constraints_ok == all(bits[2:])
    assert report.physical_valid == all(bits[1:])
    assert report.joint == public.joint == all(bits)


@PROPERTY
@given(control=st.floats(min_value=-2, max_value=2, allow_nan=False))
def test_manual_preview_never_reports_partial_for_a_safe_predictor(control: float) -> None:
    """A candidate at/below .20 is recoverable or rejected, never a PARTIAL inspection case."""
    service = property_service()
    result = service.validate_controls({"actuator": -2.0, "sensor": 2.0}, {"actuator": control})
    assert result.risk_after > service.config.tau_safe or result.status != "PARTIAL"
