"""Versioned machine identity, telemetry mapping and decision policy."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from prescriptxai.config import LatencyBudgetConfig
from prescriptxai.constraints.taxonomy import (
    BoundEstimationConfig,
    BoundsSpec,
    CouplingConfig,
    CouplingRule,
    FeatureGroupName,
    RateLimitSpec,
)

MACHINE_ID_PATTERN = r"^[a-z][a-z0-9_]*$"
FeatureRole = Literal["sensor", "controllable", "frozen"]
LabelSource = Literal["remaining_life", "terminal_event", "run_to_failure"]
LimitsStatus = Literal["confirmed", "demonstration"]
DEMONSTRATION_LIMITS_LABEL = "Demonstration limits: not confirmed by an engineer"
ALERTS_ONLY_LABEL = "Alerts only: limits not yet confirmed by an engineer"


class SpecSection(BaseModel):
    """Reject unrecognized fields and nonfinite policy values."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False, str_strip_whitespace=True
    )


class MachineFeature(SpecSection):
    """One feature with raw-unit constraints and a source column."""

    id: str = Field(pattern=MACHINE_ID_PATTERN)
    label: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    column: str = Field(min_length=1)
    role: FeatureRole
    bounds: BoundsSpec
    step_limit: RateLimitSpec | None = None
    direction: Literal["any", "increase_only", "decrease_only"] = "any"
    why: str = Field(min_length=1)
    coupling_group: str | None = None
    legacy_group: FeatureGroupName | None = None
    proxy: bool = False

    @model_validator(mode="after")
    def check_control(self) -> MachineFeature:
        """Require an explicit rate policy for each controllable feature."""
        if self.role == "controllable" and self.step_limit is None:
            raise ValueError(f"controllable feature {self.id} requires a step limit")
        if self.role != "controllable" and (self.step_limit is not None or self.proxy):
            raise ValueError(f"noncontrollable feature {self.id} has a control policy")
        if self.legacy_group is not None and (
            (self.role == "controllable") != (self.legacy_group == "controllable")
            or (self.role == "sensor") != (self.legacy_group == "dependent")
        ):
            raise ValueError(f"feature role and legacy group disagree for {self.id}")
        if any(
            value is not None and not float("-inf") < value < float("inf")
            for value in (self.bounds.minimum, self.bounds.maximum)
        ):
            raise ValueError(f"feature {self.id} bounds must be finite")
        return self


class FailurePolicy(SpecSection):
    """Failure horizon in the source time-index units and calibrated risk gates."""

    horizon: int = Field(gt=0)
    label_source: LabelSource
    tau_safe: float = Field(ge=0, le=1)
    tau_danger: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def thresholds_ordered(self) -> FailurePolicy:
        """Require the safe threshold to be strictly below the alert threshold."""
        if self.tau_safe >= self.tau_danger:
            raise ValueError("tau_safe must be less than tau_danger")
        return self


class DatasetMapping(SpecSection):
    """Source location and source-to-canonical identity/label columns."""

    adapter: Literal["cmapss", "tabular"]
    path: Path
    unit_column: str = Field(min_length=1)
    time_column: str = Field(min_length=1)
    remaining_life_column: str | None = None
    event_column: str | None = None
    subset: Literal["FD001", "FD002", "FD003", "FD004"] | None = None
    split_fractions: tuple[float, float, float] = (0.7, 0.15, 0.15)
    lifetime_buckets: int = Field(default=6, ge=1)

    @model_validator(mode="after")
    def check_mapping(self) -> DatasetMapping:
        """Require one source column per field and a compatible adapter."""
        columns = [
            column
            for column in (
                self.unit_column,
                self.time_column,
                self.remaining_life_column,
                self.event_column,
            )
            if column is not None
        ]
        if any(not column.strip() for column in columns) or len(set(columns)) != len(columns):
            raise ValueError("mapped identity and label columns must be nonempty and distinct")
        if (self.adapter == "cmapss") != (self.subset is not None):
            raise ValueError("a subset is required only for the archive adapter")
        if min(self.split_fractions) <= 0 or abs(sum(self.split_fractions) - 1) > 1e-9:
            raise ValueError("positive split fractions must sum to one")
        return self


class ValidationPolicy(SpecSection):
    """Statistical and proxy constraint settings for each protocol."""

    plausibility: dict[str, float] = Field(min_length=1)
    coupling_rules: tuple[CouplingRule, ...] = ()
    fitted_coupling: CouplingConfig | None = None
    bound_estimation: BoundEstimationConfig | None = None
    rate_assumption: str = Field(min_length=1)
    intervention_steps: int = Field(ge=1)

    @model_validator(mode="after")
    def check_protocols(self) -> ValidationPolicy:
        """Reject empty protocol names and nonpositive or nonfinite distances."""
        if any(
            not version.strip() or not 0 < limit < float("inf")
            for version, limit in self.plausibility.items()
        ):
            raise ValueError("protocols require a named positive finite plausibility limit")
        return self


class QualityPolicy(SpecSection):
    """Window policies in source time units and raw feature units."""

    max_time_gap: float = Field(gt=0)
    stuck_window: int = Field(ge=2)
    stuck_tolerance: float = Field(ge=0)
    stuck_features: tuple[str, ...] = ()


class LimitConfirmation(SpecSection):
    """Recorded engineering confirmation for limits explicitly marked confirmed."""

    confirmed_by: str | None = None
    role: str | None = None
    confirmed_on: date | None = None

    @model_validator(mode="after")
    def all_or_none(self) -> LimitConfirmation:
        """Reject partially filled confirmation blocks."""
        entries = (bool(self.confirmed_by), bool(self.role), self.confirmed_on is not None)
        if any(entries) and not all(entries):
            raise ValueError("limits confirmation requires name, role and date")
        return self

    @property
    def confirmed(self) -> bool:
        """Whether the complete confirmation record is present."""
        return bool(self.confirmed_by and self.role and self.confirmed_on)


class SentenceTemplates(SpecSection):
    """Human-readable action and escalation text."""

    increase: str = Field(min_length=1)
    decrease: str = Field(min_length=1)
    escalation: str = Field(min_length=1)


class MachineSpec(SpecSection):
    """Complete configuration boundary for one registered machine."""

    schema_version: Literal[1, 2]
    machine_id: str = Field(pattern=MACHINE_ID_PATTERN)
    display_name: str = Field(min_length=1)
    unit_word: str = Field(min_length=1)
    unit_plural: str = Field(min_length=1)
    data_source: str = Field(min_length=1)
    license_note: str = Field(min_length=1)
    synthetic: bool
    dataset: DatasetMapping
    features: tuple[MachineFeature, ...] = Field(min_length=1)
    failure: FailurePolicy
    validation: ValidationPolicy
    quality: QualityPolicy
    delta_min: float = Field(ge=0, le=1)
    k_max: int = Field(ge=1)
    latency_budgets: dict[Literal["FAST", "THOROUGH"], LatencyBudgetConfig]
    confirmation: LimitConfirmation = Field(default_factory=LimitConfirmation)
    limits_status: LimitsStatus | None = None
    sentences: SentenceTemplates

    @model_validator(mode="before")
    @classmethod
    def portable_dataset_path(cls, value: object) -> object:
        """Version 2 uses a workspace-relative dataset path on both operating systems."""
        if not isinstance(value, dict) or value.get("schema_version") != 2:
            return value
        dataset = value.get("dataset")
        if not isinstance(dataset, dict) or "path" not in dataset:
            return value
        if not isinstance(dataset["path"], (str, Path)):
            return value
        path = str(dataset["path"]).replace("\\", "/")
        relative = PurePosixPath(path)
        if relative.is_absolute() or PureWindowsPath(path).drive or ".." in relative.parts:
            raise ValueError("version 2 dataset path must be workspace-relative")
        return {**value, "dataset": {**dataset, "path": relative.as_posix()}}

    @model_validator(mode="after")
    def check_references(self) -> MachineSpec:
        """Validate mapped columns, constraint references and required runtime policies."""
        if self.limits_status == "confirmed" and not self.confirmation.confirmed:
            raise ValueError("confirmed limits require an engineer name, role and date")
        if self.limits_status == "demonstration" and self.confirmation.confirmed:
            raise ValueError("demonstration limits cannot carry engineer confirmation")
        names = {feature.id for feature in self.features}
        columns = {feature.column for feature in self.features}
        if len(names) != len(self.features) or len(columns) != len(self.features):
            raise ValueError("feature IDs and source columns must each be unique")
        measurements = tuple(
            feature for feature in self.features if feature.legacy_group != "context"
        )
        reserved = {
            "unit_id",
            "time_index",
            "remaining_life",
            "event",
            "failure_label",
            "engine_id",
            "cycle",
            "rul",
        }
        if any(feature.id in reserved for feature in measurements):
            raise ValueError("measurement feature ID collides with a canonical metadata field")
        mapped_metadata = {
            self.dataset.unit_column,
            self.dataset.time_column,
            self.dataset.event_column,
            self.dataset.remaining_life_column,
        }
        if any(feature.column in mapped_metadata for feature in measurements):
            raise ValueError("measurement source column collides with a metadata mapping")
        if not set(self.quality.stuck_features) <= {feature.id for feature in measurements}:
            raise ValueError("stuck checks must reference measurement features")
        if any(
            not {rule.feature_a, rule.feature_b} <= names for rule in self.validation.coupling_rules
        ):
            raise ValueError("coupling rules must reference declared features")
        if self.k_max > sum(feature.role == "controllable" for feature in self.features):
            raise ValueError("k_max exceeds the declared controllable feature count")
        if set(self.latency_budgets) != {"FAST", "THOROUGH"}:
            raise ValueError("both FAST and THOROUGH budgets are required")
        if self.dataset.adapter == "tabular":
            source_columns = {
                "remaining_life": self.dataset.remaining_life_column,
                "terminal_event": self.dataset.event_column,
            }
            if (
                self.failure.label_source in source_columns
                and not source_columns[self.failure.label_source]
            ):
                raise ValueError("failure label source requires its mapped column")
        return self

    @property
    def alerts_only(self) -> bool:
        """Withhold recommendations for specs without an active limits declaration."""
        return self.limits_status != "demonstration" and not (
            self.limits_status == "confirmed" and self.confirmation.confirmed
        )

    @property
    def limits_label(self) -> str:
        """Name the current publication mode without implying physical safety."""
        if self.alerts_only:
            return ALERTS_ONLY_LABEL
        if self.limits_status == "demonstration":
            return DEMONSTRATION_LIMITS_LABEL
        return "Advisory mode · Engineer-confirmed limits"

    @property
    def spec_hash(self) -> str:
        """Fingerprint the validated configuration, independent of YAML formatting."""
        import json

        spec = self.model_dump(mode="json")
        if self.schema_version == 2:
            spec["dataset"]["path"] = self.dataset.path.as_posix()
        if self.limits_status is None:
            spec.pop("limits_status")  # Preserve identity for historical specs without this field.
        payload = json.dumps(spec, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()

    @property
    def measurement_features(self) -> tuple[MachineFeature, ...]:
        """Features consumed by a predictor, with identity metadata kept separate."""
        return tuple(feature for feature in self.features if feature.legacy_group != "context")


def load_machine_spec(path: Path) -> MachineSpec:
    """Read a versioned machine specification from a local YAML file."""
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"invalid machine YAML in {path}") from error
    return MachineSpec.model_validate(document)


def migrate_machine_spec_v1(document: dict[str, object]) -> dict[str, object]:
    """Return a separate v2 spec without changing legacy specs, fits or recorded results."""
    original = MachineSpec.model_validate(document)
    if original.schema_version != 1:
        raise ValueError("machine spec migration requires schema version 1")
    migrated = MachineSpec.model_validate({**document, "schema_version": 2})
    result = migrated.model_dump(mode="json")
    result["dataset"]["path"] = migrated.dataset.path.as_posix()
    return result
