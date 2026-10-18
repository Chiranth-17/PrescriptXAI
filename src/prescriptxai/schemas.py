"""Validated public schemas for machine states and recourse results."""

from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from prescriptxai.validation.base import CheckResult, EvidenceLevel, TierStatus


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
    """A named feature's raw and scaled changes plus interpretable percentages."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature: str = Field(min_length=1)
    raw_delta: float
    scaled_delta: float
    percent_of_current: float | None = None
    percent_of_range: float | None = None

    @model_validator(mode="after")
    def deltas_are_finite(self) -> "DeltaMapping":
        """Ensure reporting and optimization deltas can be serialized safely."""
        percentages = (self.percent_of_current, self.percent_of_range)
        if (
            not isfinite(self.raw_delta)
            or not isfinite(self.scaled_delta)
            or any(value is not None and not isfinite(value) for value in percentages)
        ):
            raise ValueError("deltas must be finite")
        return self


class RecourseOutcome(BaseModel):
    """Result with separate risk, physical, and feasible-action statuses."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_risk: float = Field(ge=0, le=1)
    final_risk: float = Field(ge=0, le=1)
    model_valid: bool
    recourse_feasible: bool
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
            and self.recourse_feasible
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
    percent_of_range: float | None = None

    @model_validator(mode="after")
    def values_are_finite(self) -> "FeatureDelta":
        """Reject non-finite amounts while permitting undefined percent at a zero origin."""
        if (
            not isfinite(self.raw_delta)
            or (self.percent_change is not None and not isfinite(self.percent_change))
            or (self.percent_of_range is not None and not isfinite(self.percent_of_range))
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
    margin: float | None = None
    status: TierStatus | None = None
    evidence_level: EvidenceLevel = "none"
    checks: tuple[CheckResult, ...] = ()
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def status_matches_passed(self) -> "TierValidation":
        """Prevent a skipped tier from counting as a successful check."""
        if self.status is None:
            object.__setattr__(self, "status", "pass" if self.passed else "fail")
        if self.passed != (self.status == "pass"):
            raise ValueError("passed must match tier status")
        return self


class ValidationReport(BaseModel):
    """Independent validation results for model safety and physical plausibility tiers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.1.0"] = "1.1.0"
    tier1_model_safety: TierValidation
    tier2_distributional: TierValidation
    tier3_engineering: TierValidation
    tier4_sensor_coupling: TierValidation
    simulator: TierValidation | None = None
    assumptions: tuple[str, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def verify_serialized_verdicts(cls, value: object) -> object:
        """Accept round-trip computed outputs only when they agree with the tier inputs."""
        outputs = (
            "model_valid",
            "plausible",
            "constraints_ok",
            "joint",
            "failing_tiers",
            "evidence_level",
        )
        if isinstance(value, dict) and any(name in value for name in outputs):
            inputs = {name: item for name, item in value.items() if name not in outputs}
            verified = cls.model_validate(inputs)
            for name in outputs:
                if name in value:
                    supplied = tuple(value[name]) if name == "failing_tiers" else value[name]
                    if supplied != getattr(verified, name):
                        raise ValueError(f"serialized {name} disagrees with tier results")
            return inputs
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def model_valid(self) -> bool:
        """Expose true model validity independently of plausibility."""
        return self.tier1_model_safety.passed

    @computed_field  # type: ignore[prop-decorator]
    @property
    def plausible(self) -> bool:
        """Expose Tier 2 distributional plausibility only."""
        return self.tier2_distributional.passed

    @computed_field  # type: ignore[prop-decorator]
    @property
    def constraints_ok(self) -> bool:
        """Require both static proxy constraint tiers."""
        return self.tier3_engineering.passed and self.tier4_sensor_coupling.passed

    @computed_field  # type: ignore[prop-decorator]
    @property
    def joint(self) -> bool:
        """Require all four static checks, without applying a plausibility target to joint."""
        return self.model_valid and self.plausible and self.constraints_ok

    @computed_field  # type: ignore[prop-decorator]
    @property
    def failing_tiers(self) -> tuple[str, ...]:
        """Return failed tiers while keeping skipped results distinct."""
        return tuple(
            name
            for name in (
                "tier1_model_safety",
                "tier2_distributional",
                "tier3_engineering",
                "tier4_sensor_coupling",
                "simulator",
            )
            if (tier := getattr(self, name)) is not None and tier.status == "fail"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def evidence_level(self) -> EvidenceLevel:
        """State the highest contiguous evidence level reached by this result."""
        if not self.model_valid:
            return "none"
        if not self.plausible:
            return "E1"
        if not self.constraints_ok:
            return "E2"
        if (
            self.simulator is not None
            and self.simulator.passed
            and (self.simulator.evidence_level in {"E4", "E5"})
        ):
            return self.simulator.evidence_level
        return "E3"


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

    schema_version: Literal["1.1.0"] = "1.1.0"
    original_state: dict[str, float]
    new_state: dict[str, float]
    delta_per_feature: dict[str, FeatureDelta]
    risk_before: float = Field(ge=0, le=1)
    risk_after: float = Field(ge=0, le=1)
    validation_report: ValidationReport
    timings: StageTimings
    warnings: tuple[str, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def verify_serialized_evidence(cls, value: object) -> object:
        """Reject altered evidence labels while accepting the public JSON round trip."""
        if isinstance(value, dict) and "evidence_level" in value:
            inputs = {name: item for name, item in value.items() if name != "evidence_level"}
            verified = cls.model_validate(inputs)
            if value["evidence_level"] != verified.evidence_level:
                raise ValueError("serialized evidence_level disagrees with validation report")
            return inputs
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def evidence_level(self) -> EvidenceLevel:
        """Attach achieved evidence to every public recommendation."""
        return self.validation_report.evidence_level

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
    margin: float | None = None
    status: TierStatus | None = None
    evidence_level: EvidenceLevel = "none"
    checks: tuple[CheckResult, ...] = ()
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def status_matches_valid(self) -> "TierPayload":
        """Prevent an API payload from converting skipped into valid."""
        if self.status is None:
            self.status = "pass" if self.valid else "fail"
        if self.valid != (self.status == "pass"):
            raise ValueError("valid must match tier status")
        return self


class RecommendationResponse(BaseModel):
    """API response preserving optimizer and independent validation outcomes."""

    schema_version: Literal["1.1.0"] = "1.1.0"
    evidence_level: EvidenceLevel = "none"
    plausible: bool = False
    constraints_ok: bool = False
    joint: bool = False
    failing_tiers: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    original_state: dict[str, float]
    new_state: dict[str, float]
    outcome: RecourseOutcome
    solver_success: bool
    optimizer_message: str
    objective_value: float | None
    failure_reason: str | None = None
    risk_reached: float | None = Field(default=None, ge=0, le=1)
    stage_timings_ms: dict[str, float] = Field(default_factory=dict)
    objective_terms: dict[str, float] = Field(default_factory=dict)
    counterfactual_signs: dict[str, int] = Field(default_factory=dict)
    solver_calls: int = Field(default=0, ge=0)
    actuator_constraints_feasible: bool = False
    tiers: dict[str, TierPayload]
