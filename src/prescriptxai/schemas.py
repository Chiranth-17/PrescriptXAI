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


class RecourseRequest(BaseModel):
    """Raw-unit state submitted through the API or operator dashboard."""

    model_config = ConfigDict(extra="forbid")

    state: dict[str, float]

    @model_validator(mode="after")
    def state_values_are_finite(self) -> "RecourseRequest":
        """Reject empty states and non-finite telemetry before model inference."""
        if not self.state:
            raise ValueError("state must not be empty")
        if any(not name.strip() for name in self.state):
            raise ValueError("state feature names must not be empty")
        if any(not isfinite(value) for value in self.state.values()):
            raise ValueError("state values must be finite")
        return self


class FeatureDelta(BaseModel):
    """One feature's recommended adjustment in raw units and percent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_delta: float
    percent_change: float | None

    @model_validator(mode="after")
    def values_are_finite(self) -> "FeatureDelta":
        """Reject non-finite amounts while permitting undefined percent at a zero origin."""
        if not isfinite(self.raw_delta) or (
            self.percent_change is not None and not isfinite(self.percent_change)
        ):
            raise ValueError("delta values must be finite when defined")
        return self


class TierValidation(BaseModel):
    """Machine-readable result and optional measurement for one validation tier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    passed: bool
    diagnostics: tuple[str, ...] = ()
    measurement: float | None = None
    limit: float | None = None


class ValidationReport(BaseModel):
    """Independent validation results for model safety and physical plausibility tiers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tier1_model_safety: TierValidation
    tier2_distributional: TierValidation
    tier3_engineering: TierValidation
    tier4_sensor_coupling: TierValidation
    simulator: TierValidation | None = None


class StageTimings(BaseModel):
    """Measured wall-clock time for named pipeline stages, in milliseconds."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ingestion_ms: float | None = Field(default=None, ge=0)
    inference_ms: float | None = Field(default=None, ge=0)
    optimization_ms: float | None = Field(default=None, ge=0)
    validation_ms: float | None = Field(default=None, ge=0)
    pipeline_ms: float | None = Field(default=None, ge=0)
    dashboard_ms: float | None = Field(default=None, ge=0)


class RecourseResult(BaseModel):
    """Serialized recourse decision with raw-unit changes and per-tier evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    original_state: dict[str, float]
    new_state: dict[str, float]
    delta_per_feature: dict[str, FeatureDelta]
    risk_before: float = Field(ge=0, le=1)
    risk_after: float = Field(ge=0, le=1)
    validation_report: ValidationReport
    timings: StageTimings
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def states_and_deltas_are_consistent(self) -> "RecourseResult":
        """Require each reported delta to connect the same named raw-unit states."""
        if set(self.original_state) != set(self.new_state):
            raise ValueError("original_state and new_state must have identical feature names")
        if not set(self.delta_per_feature).issubset(self.original_state):
            raise ValueError("delta feature names must exist in both states")
        for name, value in (*self.original_state.items(), *self.new_state.items()):
            if not isfinite(value):
                raise ValueError(f"state value for {name} must be finite")
        for name, delta in self.delta_per_feature.items():
            if abs((self.new_state[name] - self.original_state[name]) - delta.raw_delta) > 1e-9:
                raise ValueError(f"raw delta for {name} does not match the states")
            original = self.original_state[name]
            if original == 0 and delta.percent_change is not None:
                raise ValueError(f"percent change for zero-valued feature {name} must be null")
            if original != 0:
                expected_percent = delta.raw_delta / abs(original) * 100
                if (
                    delta.percent_change is None
                    or abs(delta.percent_change - expected_percent) > 1e-6
                ):
                    raise ValueError(f"percent change for {name} does not match raw units")
        return self


class TierPayload(BaseModel):
    """Serialized status for one validation tier."""

    valid: bool
    diagnostics: tuple[str, ...]
    measurement: float | None = None
    limit: float | None = None


class RecommendationResponse(BaseModel):
    """API response preserving optimizer and independent validation outcomes."""

    outcome: RecourseOutcome
    solver_success: bool
    optimizer_message: str
    objective_value: float | None
    tiers: dict[str, TierPayload]
