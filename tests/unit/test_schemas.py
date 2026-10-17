"""Public state and recourse schema tests."""

import pytest
from pydantic import ValidationError

from prescriptxai.schemas import (
    DeltaMapping,
    FeatureDelta,
    MachineState,
    RecourseOutcome,
    RecourseResult,
    StageTimings,
    TierValidation,
    ValidationReport,
)


def test_machine_state_rejects_non_finite_values() -> None:
    """Machine state values cannot contain NaN or infinity."""
    with pytest.raises(ValidationError, match="feature values must be finite"):
        MachineState(engine_id=1, cycle=1, features={"sensor": float("nan")})


def test_machine_state_rejects_empty_feature_vector() -> None:
    """Empty telemetry is rejected rather than interpreted as a valid state."""
    with pytest.raises(ValidationError, match="features must not be empty"):
        MachineState(engine_id=1, cycle=1, features={})


def test_delta_keeps_raw_and_scaled_values_separate() -> None:
    """A delta explicitly records both physical and optimization-space changes."""
    delta = DeltaMapping(feature="fuel", raw_delta=-0.2, scaled_delta=-1.5)

    assert (delta.raw_delta, delta.scaled_delta) == (-0.2, -1.5)


def test_success_cannot_hide_failed_physical_validation() -> None:
    """Model validity alone cannot make physical validation pass."""
    with pytest.raises(ValidationError, match="success must equal"):
        RecourseOutcome(
            initial_risk=0.9,
            final_risk=0.1,
            model_valid=True,
            recourse_feasible=True,
            tier2_plausible=False,
            tier3_engineering_valid=True,
            tier4_coupling_valid=True,
            deltas=(),
            success=True,
        )


def test_safe_risk_does_not_make_a_failed_sparse_search_successful() -> None:
    """True model safety stays separate from optimizer feasibility and success."""
    outcome = RecourseOutcome(
        initial_risk=0.9,
        final_risk=0.15,
        model_valid=True,
        recourse_feasible=False,
        tier2_plausible=True,
        tier3_engineering_valid=True,
        tier4_coupling_valid=True,
        deltas=(),
        success=False,
    )

    assert outcome.model_valid
    assert not outcome.recourse_feasible
    assert not outcome.success


def test_recourse_result_round_trips_raw_deltas_and_per_tier_report() -> None:
    """Serialized operator results preserve physical changes and every tier status."""
    tier = TierValidation(passed=True, diagnostics=("within configured limit",))
    result = RecourseResult(
        original_state={"flow": 10.0},
        new_state={"flow": 9.0},
        delta_per_feature={"flow": FeatureDelta(raw_delta=-1.0, percent_change=-10.0)},
        risk_before=0.84,
        risk_after=0.18,
        validation_report=ValidationReport(
            tier1_model_safety=tier,
            tier2_distributional=tier,
            tier3_engineering=tier,
            tier4_sensor_coupling=tier,
        ),
        timings=StageTimings(optimization_ms=10.5, validation_ms=2.5),
        warnings=(),
    )

    reloaded = RecourseResult.model_validate_json(result.model_dump_json())

    assert reloaded == result
    assert reloaded.delta_per_feature["flow"].raw_delta == -1.0
    assert reloaded.delta_per_feature["flow"].percent_change == -10.0
