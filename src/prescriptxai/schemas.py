"""Validated public schemas for machine states and recourse results."""

from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MachineState(BaseModel):
    """Named raw-unit feature values for one machine state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    engine_id: int = Field(ge=1)
    cycle: int = Field(ge=1)
    features: dict[str, float]

    @model_validator(mode="after")
    def feature_values_are_finite(self) -> "MachineState":
        """Reject empty names, empty vectors, NaN, and infinities."""
        if not self.features:
            raise ValueError("features must not be empty")
        if any(not name.strip() for name in self.features):
            raise ValueError("feature names must not be empty")
        if any(not isfinite(value) for value in self.features.values()):
            raise ValueError("feature values must be finite")
        return self


class DeltaMapping(BaseModel):
    """A named feature's raw physical and scaled optimization deltas."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature: str = Field(min_length=1)
    raw_delta: float
    scaled_delta: float

    @model_validator(mode="after")
    def deltas_are_finite(self) -> "DeltaMapping":
        """Ensure reporting and optimization deltas can be serialized safely."""
        if not isfinite(self.raw_delta) or not isfinite(self.scaled_delta):
            raise ValueError("deltas must be finite")
        return self


class RecourseOutcome(BaseModel):
    """Machine-readable result with separate model and physical validity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_risk: float = Field(ge=0, le=1)
    final_risk: float = Field(ge=0, le=1)
    model_valid: bool
    tier2_plausible: bool
    tier3_engineering_valid: bool
    tier4_coupling_valid: bool
    deltas: tuple[DeltaMapping, ...]
    success: bool

    @model_validator(mode="after")
    def success_matches_checks(self) -> "RecourseOutcome":
        """Prevent a successful outcome from hiding a failed required check."""
        checks_pass = (
            self.model_valid
            and self.tier2_plausible
            and self.tier3_engineering_valid
            and self.tier4_coupling_valid
        )
        if self.success != checks_pass:
            raise ValueError("success must equal the conjunction of model and physical checks")
        return self
