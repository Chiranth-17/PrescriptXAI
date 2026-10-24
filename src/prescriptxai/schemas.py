"""Validated public schemas for machine states and recourse results."""

from math import isfinite
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from prescriptxai.validation.base import CheckResult, EvidenceLevel, TierStatus


def _reject_nonreal_measurement(value: object, subject: str) -> None:
    """Reject lossy boolean/complex coercion at raw Pydantic input boundaries."""
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{subject} cannot contain boolean measurements")
    if isinstance(value, (complex, np.complexfloating)):
        raise ValueError(f"{subject} cannot contain complex measurements")


class MachineState(BaseModel):
    """Named raw-unit feature values for one machine state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    engine_id: int = Field(ge=1)
    cycle: int = Field(ge=1)
    features: dict[str, float]

    @field_validator("features", mode="before")
    @classmethod
    def preserve_measurement_types(cls, value: object) -> object:
        """Check original scalar types before conversion to raw real-valued telemetry."""
        if isinstance(value, dict):
            for item in value.values():
                _reject_nonreal_measurement(item, "telemetry")
        return value

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
    context: "InputContext | None" = None
    mode: Literal["fast", "thorough"] = "fast"

    @field_validator("state", mode="before")
    @classmethod
    def reject_boolean_measurements(cls, value: object) -> object:
        """Reject booleans before Pydantic can coerce them into physical measurements."""
        if isinstance(value, dict):
            for item in value.values():
                _reject_nonreal_measurement(item, "telemetry")
        return value

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

    scaled_delta: float | None = None
    role: Literal["action", "dependent", "other"] = "action"

    @model_validator(mode="after")
    def values_are_finite(self) -> "FeatureDelta":
        """Reject non-finite amounts while permitting undefined percent at a zero origin."""
        if (
            not isfinite(self.raw_delta)
            or (self.percent_change is not None and not isfinite(self.percent_change))
            or (self.percent_of_range is not None and not isfinite(self.percent_of_range))
            or (self.scaled_delta is not None and not isfinite(self.scaled_delta))
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
        if any(
            v is not None and not isfinite(v) for v in (self.measurement, self.limit, self.margin)
        ) or any(c.margin is not None and not isfinite(c.margin) for c in self.checks):
            raise ValueError("tier measurements and margins must be finite when defined")
        if self.status is None:
            object.__setattr__(self, "status", "pass" if self.passed else "fail")
        if self.passed != (self.status == "pass"):
            raise ValueError("passed must match tier status")
        return self


class ValidationReport(BaseModel):
    """Independent validation results for model safety and physical plausibility tiers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["2.0.0"] = "2.0.0"
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

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    ingestion_ms: float | None = Field(default=None, ge=0)
    inference_ms: float | None = Field(default=None, ge=0)
    optimization_ms: float | None = Field(default=None, ge=0)
    validation_ms: float | None = Field(default=None, ge=0)
    pipeline_ms: float | None = Field(default=None, ge=0)
    dashboard_ms: float | None = Field(default=None, ge=0)


Mode = Literal["FAST", "THOROUGH"]
Triage = Literal["RECOVERABLE", "PARTIAL", "ESCALATE"]


class InputContext(BaseModel):
    """Observed context, canonical vector order, units, and fixed LSTM prefix."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    telemetry: dict[str, float] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    feature_names: tuple[str, ...] | None = None
    history: tuple[tuple[float, ...], ...] | None = None
    engine_id: int | None = Field(default=None, ge=1)
    cycle: int | None = Field(default=None, ge=1)

    @model_validator(mode="before")
    @classmethod
    def reject_boolean_context(cls, value: object) -> object:
        """Preserve numeric physical context before scalar coercion."""
        if isinstance(value, dict):
            telemetry = value.get("telemetry", {})
            if isinstance(telemetry, dict):
                for item in telemetry.values():
                    _reject_nonreal_measurement(item, "telemetry")
            for name in ("engine_id", "cycle"):
                _reject_nonreal_measurement(value.get(name), name)
            history = value.get("history")
            if isinstance(history, np.ndarray) and history.ndim != 2:
                raise ValueError("history must be a two-dimensional observed array")
            if isinstance(history, (list, tuple, np.ndarray)):
                for row in history:
                    if isinstance(row, np.ndarray) and row.ndim != 1:
                        raise ValueError("history rows must be one-dimensional")
                    if isinstance(row, (list, tuple, np.ndarray)):
                        for item in row:
                            _reject_nonreal_measurement(item, "history")
        return value

    @model_validator(mode="after")
    def rectangular_history(self) -> "InputContext":
        """Require rectangular observed raw feature rows."""
        if self.history and len({len(row) for row in self.history}) != 1:
            raise ValueError("history rows must have equal lengths")
        return self


class Assessment(BaseModel):
    """True calibrated risk and alert decision without optimization."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    mode: Literal["FAST", "THOROUGH"] = "FAST"
    risk: float = Field(ge=0, le=1)
    alert: bool
    tau_danger: float
    tau_safe: float
    model_version: str
    config_hash: str
    seed: int
    warnings: tuple[str, ...] = ()


class FailureInformation(BaseModel):
    """Diagnostic state and operator escalation; not a globally infeasible certificate."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    reason: str
    message: str
    closest_candidate: dict[str, float]
    risk_reached: float
    failing_tiers: tuple[str, ...]
    suggested_escalation: str


class Explanation(BaseModel):
    """Plain-text actions and independently measured decision evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    summary: str
    actions: tuple[str, ...]
    risk_before: float
    risk_after: float
    verdict: dict[str, bool]
    evidence_level: EvidenceLevel
    warnings: tuple[str, ...]


class RecourseResult(BaseModel):
    """Serialized recourse decision with raw-unit changes and per-tier evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["2.0.0"] = "2.0.0"
    original_state: dict[str, float]
    new_state: dict[str, float]
    delta_per_feature: dict[str, FeatureDelta]
    risk_before: float = Field(ge=0, le=1)
    risk_after: float = Field(ge=0, le=1)
    validation_report: ValidationReport
    timings: StageTimings
    warnings: tuple[str, ...] = ()
    alert: bool = True
    status: Literal["NO_INTERVENTION", "RECOVERABLE", "PARTIAL", "ESCALATE"] = "ESCALATE"
    triage: Triage | None = "ESCALATE"
    mode: Mode = "FAST"
    surrogate_risk_before: float | None = Field(default=None, ge=0, le=1)
    surrogate_risk_after: float | None = Field(default=None, ge=0, le=1)
    failure: FailureInformation | None = None
    proxy_assumptions: bool = True
    assumptions: tuple[str, ...] = ()
    action_features: tuple[str, ...] = ()
    action_feasible: bool = False
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_version: str = Field(min_length=1)
    seed: int = Field(ge=0)
    run_id: str = Field(min_length=1)
    tau_danger: float = Field(default=0.8, ge=0, le=1)
    tau_safe: float = Field(default=0.2, ge=0, le=1)
    delta_min: float = Field(default=0.3, ge=0, le=1)
    solver_settings: dict[str, int | float | str | bool | None] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def verify_serialized_evidence(cls, value: object) -> object:
        """Reject altered evidence labels while accepting the public JSON round trip."""
        outputs = (
            "evidence_level",
            "plausible",
            "constraints_ok",
            "joint",
            "tiers",
            "outcome",
            "actuator_constraints_feasible",
        )
        if isinstance(value, dict) and any(name in value for name in outputs):
            inputs = {name: item for name, item in value.items() if name not in outputs}
            verified = cls.model_validate(inputs).model_dump(mode="json")
            for name in outputs:
                if name in value and value[name] != verified[name]:
                    raise ValueError(f"serialized {name} disagrees with validation report")
            return inputs
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def evidence_level(self) -> EvidenceLevel:
        """Attach achieved evidence to every public recommendation."""
        return self.validation_report.evidence_level

    @computed_field  # type: ignore[prop-decorator]
    @property
    def plausible(self) -> bool:
        """Retain the read-only Tier 2 alias for existing service clients."""
        return self.validation_report.plausible

    @computed_field  # type: ignore[prop-decorator]
    @property
    def constraints_ok(self) -> bool:
        """Retain the read-only Tiers 3–4 alias."""
        return self.validation_report.constraints_ok

    @computed_field  # type: ignore[prop-decorator]
    @property
    def joint(self) -> bool:
        """Retain the read-only all-static-tiers alias."""
        return self.validation_report.joint

    @computed_field  # type: ignore[prop-decorator]
    @property
    def actuator_constraints_feasible(self) -> bool:
        """Expose the same sparse-action feasibility under the legacy name."""
        return self.action_feasible

    @computed_field  # type: ignore[prop-decorator]
    @property
    def outcome(self) -> RecourseOutcome:
        """Adapt existing service clients without a second decision computation."""
        return RecourseOutcome(
            initial_risk=self.risk_before,
            final_risk=self.risk_after,
            model_valid=self.validation_report.model_valid,
            recourse_feasible=self.action_feasible,
            tier2_plausible=self.plausible,
            tier3_engineering_valid=self.validation_report.tier3_engineering.passed,
            tier4_coupling_valid=self.validation_report.tier4_sensor_coupling.passed,
            deltas=tuple(
                DeltaMapping(
                    feature=n,
                    raw_delta=self.delta_per_feature[n].raw_delta,
                    scaled_delta=self.delta_per_feature[n].scaled_delta or 0.0,
                    percent_of_current=self.delta_per_feature[n].percent_change,
                    percent_of_range=self.delta_per_feature[n].percent_of_range,
                )
                for n in self.action_features
            ),
            success=self.validation_report.joint and self.action_feasible,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tiers(self) -> dict[str, dict[str, object]]:
        """Preserve legacy tier names with the same status, margins and evidence."""
        names = (
            ("tier1_model", "tier1_model_safety"),
            ("tier2_plausibility", "tier2_distributional"),
            ("tier3_engineering", "tier3_engineering"),
            ("tier4_coupling", "tier4_sensor_coupling"),
            ("simulator", "simulator"),
        )
        result = {}
        for old, new in names:
            tier = getattr(self.validation_report, new)
            if tier is not None:
                record = tier.model_dump(mode="json")
                record["valid"] = record.pop("passed")
                result[old] = record
        return result

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
        if not self.original_state or self.tau_safe >= self.tau_danger:
            raise ValueError("nonempty states and tau_safe < tau_danger are required")
        if len(set(self.action_features)) != len(self.action_features) or set(
            self.action_features
        ) != {n for n, d in self.delta_per_feature.items() if d.role == "action"}:
            raise ValueError("action_features must match unique action deltas")
        if any(self.delta_per_feature[n].scaled_delta is None for n in self.action_features):
            raise ValueError("action deltas require scaled_delta")
        physical = self.validation_report.plausible and self.validation_report.constraints_ok
        if self.alert != (self.risk_before >= self.tau_danger):
            raise ValueError("alert disagrees with the true risk gate")
        if not self.alert:
            expected = "NO_INTERVENTION"
            if (
                self.risk_before != self.risk_after
                or self.original_state != self.new_state
                or any(d.raw_delta for d in self.delta_per_feature.values())
            ):
                raise ValueError("below-alert result must have zero change")
        elif (
            self.risk_after <= self.tau_safe
            and self.validation_report.joint
            and self.action_feasible
        ):
            expected = "RECOVERABLE"
        elif (
            self.risk_after > self.tau_safe
            and physical
            and self.action_feasible
            and self.risk_before - self.risk_after >= self.delta_min
        ):
            expected = "PARTIAL"
        else:
            expected = "ESCALATE"
        if self.status != expected or self.triage != (
            None if expected == "NO_INTERVENTION" else expected
        ):
            raise ValueError("triage disagrees with risk, feasibility or validation")
        if (
            self.validation_report.tier1_model_safety.measurement != self.risk_after
            or self.validation_report.model_valid != (self.risk_after <= self.tau_safe)
        ):
            raise ValueError("true risk_after disagrees with Tier 1 measurement/verdict")
        if self.status in {"PARTIAL", "ESCALATE"} and (
            self.failure is None
            or self.failure.closest_candidate != self.new_state
            or self.failure.risk_reached != self.risk_after
        ):
            raise ValueError(
                "failed/partial decisions require consistent structured failure information"
            )
        changed = {
            name
            for name in self.original_state
            if self.original_state[name] != self.new_state[name]
        }
        if not changed.issubset(self.delta_per_feature):
            raise ValueError("every changed feature must have a raw delta")
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

    schema_version: Literal["2.0.0"] = "2.0.0"
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


class BatchRequest(BaseModel):
    """Bounded service batch; per-row input checks are performed by the shared pipeline."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    states: list[dict[str, float]] = Field(min_length=1)
    mode: Literal["fast", "thorough"] = "fast"
    contexts: list[InputContext | None] | None = None

    @field_validator("states", mode="before")
    @classmethod
    def reject_boolean_measurements(cls, value: object) -> object:
        """Apply the same raw numeric contract to every batch item."""
        if isinstance(value, list):
            for row in value:
                RecourseRequest.reject_boolean_measurements(row)
        return value


RecourseRequest.model_rebuild()
