"""Validated feature groups and actuator constraints."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FeatureGroup(BaseModel):
    """Names in one feature category."""

    model_config = ConfigDict(extra="forbid")

    features: list[str]


class FeatureGroups(BaseModel):
    """Disjoint feature categories used by recourse and validation."""

    model_config = ConfigDict(extra="forbid")

    controllable_actuators: FeatureGroup
    immutable_operational: FeatureGroup
    immutable_environmental: FeatureGroup
    dependent_sensors: FeatureGroup
    context: FeatureGroup

    @model_validator(mode="after")
    def groups_are_disjoint(self) -> "FeatureGroups":
        """Reject duplicate feature names within or across groups."""
        names: list[str] = []
        for group in self.model_dump().values():
            names.extend(group["features"])
        if any(not name.strip() for name in names):
            raise ValueError("feature names must not be empty")
        if len(names) != len(set(names)):
            raise ValueError("features must appear once across taxonomy groups")
        return self


class ActuatorConstraint(BaseModel):
    """Physical limits and per-step rate limit for one actuator."""

    model_config = ConfigDict(extra="forbid")

    minimum: float
    maximum: float
    max_change_per_step: float = Field(gt=0)

    @model_validator(mode="after")
    def minimum_below_maximum(self) -> "ActuatorConstraint":
        """Require a nonempty actuator operating interval."""
        if self.minimum >= self.maximum:
            raise ValueError("actuator minimum must be below maximum")
        return self


class CouplingRule(BaseModel):
    """A configurable two-feature engineering relationship."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    feature_a: str = Field(min_length=1)
    feature_b: str = Field(min_length=1)
    relation: str = Field(pattern=r"^(less_than|greater_than|linear_band)$")
    tolerance: float = Field(ge=0)
    slope: float | None = None
    intercept: float | None = None

    @model_validator(mode="after")
    def linear_rule_has_coefficients(self) -> "CouplingRule":
        """Require affine coefficients only for a linear-band rule."""
        if self.relation == "linear_band" and (self.slope is None or self.intercept is None):
            raise ValueError("linear_band rules require slope and intercept")
        return self


class FeatureTaxonomy(BaseModel):
    """Complete feature and constraint configuration."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(ge=1)
    dataset: str = Field(min_length=1)
    feature_groups: FeatureGroups
    actuator_constraints: dict[str, ActuatorConstraint]
    coupling_rules: list[CouplingRule]

    @model_validator(mode="after")
    def constraints_reference_declared_features(self) -> "FeatureTaxonomy":
        """Ensure constraints reference declared actuators and sensors."""
        actuator_names = set(self.feature_groups.controllable_actuators.features)
        constraint_names = set(self.actuator_constraints)
        if actuator_names != constraint_names:
            raise ValueError("actuator constraints must match controllable actuator features")
        known_features: set[str] = set()
        for group in self.feature_groups.model_dump().values():
            known_features.update(group["features"])
        for rule in self.coupling_rules:
            if rule.feature_a not in known_features or rule.feature_b not in known_features:
                raise ValueError(f"coupling rule {rule.name!r} references an unknown feature")
        return self


def load_taxonomy(path: Path) -> FeatureTaxonomy:
    """Load and validate feature taxonomy YAML."""
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("feature taxonomy root must be a mapping")
    return FeatureTaxonomy.model_validate(raw)
