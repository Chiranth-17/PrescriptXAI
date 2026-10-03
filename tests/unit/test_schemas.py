"""Public state and recourse schema tests."""

import pytest
from pydantic import ValidationError

from prescriptxai.schemas import DeltaMapping, MachineState, RecourseOutcome


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
            tier2_plausible=False,
            tier3_engineering_valid=True,
            tier4_coupling_valid=True,
            deltas=(),
            success=True,
        )
