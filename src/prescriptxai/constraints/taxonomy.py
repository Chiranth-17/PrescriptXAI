"""Validated feature taxonomy, bounds, and classification masks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
import yaml
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

from prescriptxai.data.preprocess import FittedFeatureScaler

FeatureGroupName = Literal[
    "controllable",
    "immutable_operational",
    "immutable_environmental",
    "dependent",
    "context",
]

_GROUP_TO_FIELD: dict[FeatureGroupName, str] = {
    "controllable": "controllable_actuators",
    "immutable_operational": "immutable_operational",
    "immutable_environmental": "immutable_environmental",
    "dependent": "dependent_sensors",
    "context": "context",
}


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
    def groups_are_disjoint(self) -> FeatureGroups:
        """Reject duplicate feature names within or across groups."""
        names: list[str] = []
        for group in self.model_dump().values():
            names.extend(group["features"])
        if any(not name.strip() for name in names):
            raise ValueError("feature names must not be empty")
        if len(names) != len(set(names)):
            raise ValueError("features must appear once across taxonomy groups")
        return self


class BoundsSpec(BaseModel):
    """Physical bounds, either explicit or awaiting train-only estimation."""

    model_config = ConfigDict(extra="forbid")

    minimum: float | None
    maximum: float | None
    source: Literal["training_percentiles", "manual"] = "training_percentiles"

    @model_validator(mode="after")
    def minimum_below_maximum(self) -> BoundsSpec:
        """Require a nonempty operating interval."""
        if (self.minimum is None) != (self.maximum is None):
            raise ValueError("feature bounds must provide both minimum and maximum, or neither")
        if self.minimum is not None and self.maximum is not None and self.minimum >= self.maximum:
            raise ValueError("feature bounds minimum must be below maximum")
        if self.source == "manual" and self.minimum is None:
            raise ValueError("manual feature bounds require minimum and maximum")
        return self


class RateLimitSpec(BaseModel):
    """Per-step change limit as absolute, range-relative, or train-derived telemetry delta."""

    model_config = ConfigDict(extra="forbid")

    absolute: float | None = Field(default=None, ge=0)
    fraction_of_span: float | None = Field(default=None, gt=0)
    training_delta_quantile: float | None = Field(default=None, gt=0, lt=1)

    @model_validator(mode="after")
    def exactly_one_mode(self) -> RateLimitSpec:
        """Require exactly one configured or train-derived rate-limit mode."""
        modes = (self.absolute, self.fraction_of_span, self.training_delta_quantile)
        if sum(value is not None for value in modes) != 1:
            raise ValueError(
                "rate limit requires exactly one of absolute, fraction_of_span, "
                "or training_delta_quantile"
            )
        return self


class FeatureSpec(BaseModel):
    """One C-MAPSS channel with taxonomy, bounds, and optional proxy metadata."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    label: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    cmapss_column: str = Field(min_length=1)
    group: FeatureGroupName
    bounds: BoundsSpec
    max_rate_of_change: RateLimitSpec | None = None
    direction: Literal["any", "increase_only", "decrease_only"] = "any"
    controllable_proxy: bool = False
    proxy_note: str | None = None

    @model_validator(mode="after")
    def controllable_features_have_rate_limits(self) -> FeatureSpec:
        """Require controllable proxies to declare how fast they may move per cycle."""
        if self.group == "controllable" and self.max_rate_of_change is None:
            raise ValueError(f"controllable feature {self.name!r} requires max_rate_of_change")
        if self.group != "controllable" and self.controllable_proxy:
            raise ValueError(
                f"only controllable features may set controllable_proxy on {self.name!r}"
            )
        return self


class BoundEstimationConfig(BaseModel):
    """Defaults used when deriving bounds from training telemetry."""

    model_config = ConfigDict(extra="forbid")

    lower_percentile: float = Field(ge=0, le=100)
    upper_percentile: float = Field(ge=0, le=100)
    margin_fraction: float = Field(ge=0)
    degenerate_half_width: float = Field(gt=0)

    @model_validator(mode="after")
    def percentiles_ordered(self) -> BoundEstimationConfig:
        """Require a positive percentile window."""
        if self.lower_percentile >= self.upper_percentile:
            raise ValueError("lower_percentile must be below upper_percentile")
        return self


class CouplingConfig(BaseModel):
    """Training and Tier 4 settings for the sensor coupling model."""

    model_config = ConfigDict(extra="forbid")

    backend: Literal["ridge", "gradient_boosting", "mlp"] = "ridge"
    ridge_alpha: float = Field(ge=0)
    gradient_boosting_estimators: int = Field(ge=1)
    gradient_boosting_max_depth: int = Field(ge=1)
    gradient_boosting_learning_rate: float = Field(gt=0)
    mlp_hidden_dims: tuple[int, ...] = Field(min_length=1)
    mlp_max_iter: int = Field(ge=1)
    mlp_learning_rate: float = Field(gt=0)
    residual_sigma_k: float = Field(gt=0)
    min_r2: float = Field(ge=0, le=1)
    min_rul_cycles: int = Field(ge=0)
    artifact_name: str = Field(min_length=1)
    cross_validation_folds: int = Field(ge=2)
    torch_hidden_dims: tuple[int, ...] = Field(min_length=1)
    torch_epochs: int = Field(ge=1)
    torch_learning_rate: float = Field(gt=0)


class ActuatorConstraint(BaseModel):
    """Physical limits and per-step rate limit for one actuator."""

    model_config = ConfigDict(extra="forbid")

    minimum: float
    maximum: float
    max_change_per_step: float = Field(ge=0)
    direction: Literal["any", "increase_only", "decrease_only"] = "any"

    @model_validator(mode="after")
    def minimum_below_maximum(self) -> ActuatorConstraint:
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
    def linear_rule_has_coefficients(self) -> CouplingRule:
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
    features: tuple[FeatureSpec, ...] = ()
    bound_estimation: BoundEstimationConfig | None = None
    coupling: CouplingConfig | None = None

    @model_validator(mode="after")
    def constraints_reference_declared_features(self) -> FeatureTaxonomy:
        """Ensure constraints reference declared actuators and sensors."""
        if self.features:
            actuator_names = {
                spec.name
                for spec in self.features
                if spec.group == "controllable" and spec.bounds.minimum is not None
            }
        else:
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
        if self.features:
            declared = {spec.name for spec in self.features}
            if declared != known_features:
                raise ValueError("feature specs must cover exactly the declared taxonomy groups")
            mapped_columns = [spec.cmapss_column for spec in self.features]
            if len(mapped_columns) != len(set(mapped_columns)):
                raise ValueError("each taxonomy feature must map to a unique C-MAPSS column")
        return self

    def feature_by_name(self) -> dict[str, FeatureSpec]:
        """Return feature specs keyed by name when schema v2 metadata is present."""
        return {spec.name: spec for spec in self.features}

    def immutable_feature_names(self) -> frozenset[str]:
        """Operational, environmental, and context fields that recourse must not mutate."""
        groups = self.feature_groups
        return frozenset(
            groups.immutable_operational.features
            + groups.immutable_environmental.features
            + groups.context.features
        )

    def dependent_feature_names(self) -> frozenset[str]:
        """Telemetry channels updated by coupling propagation rather than direct control."""
        return frozenset(self.feature_groups.dependent_sensors.features)

    def controllable_feature_names(self) -> frozenset[str]:
        """Return configured controllable proxy channels."""
        return frozenset(self.feature_groups.controllable_actuators.features)

    def active_controllable_feature_names(
        self, model_features: tuple[str, ...]
    ) -> tuple[str, ...]:
        """Return controllable proxies present in the selected model feature order."""
        active = set(model_features)
        return tuple(
            name for name in self.feature_groups.controllable_actuators.features if name in active
        )

    def validate_model_feature_coverage(self, model_features: tuple[str, ...]) -> None:
        """Ensure every model input is classified and every controllable proxy is modeled."""
        classified = {
            name
            for group in self.feature_groups.model_dump().values()
            for name in group["features"]
            if name not in {"engine_id", "cycle"}
        }
        missing = set(model_features) - classified
        if missing:
            raise ValueError(f"model features missing from taxonomy: {sorted(missing)}")
        if len(model_features) != len(set(model_features)):
            raise ValueError("model feature names must be unique")
        if not self.controllable_feature_names() & set(model_features):
            raise ValueError("at least one controllable proxy must be a model feature")

    def fit_training_bounds(
        self,
        training_frame: pd.DataFrame,
        *,
        columns: tuple[str, ...],
    ) -> FeatureTaxonomy:
        """Fit unresolved percentile bounds using only the supplied training-engine rows.

        For feature ``j``, let ``q_l`` and ``q_u`` be configured training percentiles and
        ``r = q_u - q_l``. The physical interval is ``[q_l - m r, q_u + m r]`` where
        ``m`` is the configured margin fraction. Constant telemetry uses the configured
        positive half-width so all intervals remain nonempty.
        """
        if training_frame.empty:
            raise ValueError("cannot estimate feature bounds from an empty training frame")
        if self.bound_estimation is None:
            raise ValueError("feature taxonomy is missing bound_estimation settings")
        requested = set(columns)
        missing = requested - set(training_frame.columns)
        if missing:
            raise ValueError(f"training frame is missing bound features: {sorted(missing)}")
        estimation = self.bound_estimation
        updated_specs: list[FeatureSpec] = []
        engine_column: str | None = None
        if "engine_id" in training_frame.columns:
            engine_column = "engine_id"
        elif "unit_id" in training_frame.columns:
            engine_column = "unit_id"
        rate_training = training_frame
        if engine_column is not None and "cycle" in training_frame.columns:
            rate_training = training_frame.sort_values([engine_column, "cycle"])
        for spec in self.features:
            current = spec.bounds
            updated = spec
            if spec.name in requested and current.minimum is None:
                values = training_frame[spec.name].to_numpy(dtype=float)
                if values.size == 0 or not np.isfinite(values).all():
                    raise ValueError(f"training data for {spec.name!r} must be nonempty and finite")
                lower, upper = np.percentile(
                    values,
                    [estimation.lower_percentile, estimation.upper_percentile],
                )
                span = float(upper - lower)
                if span <= 0:
                    lower = float(lower) - estimation.degenerate_half_width
                    upper = float(upper) + estimation.degenerate_half_width
                else:
                    margin = span * estimation.margin_fraction
                    lower = float(lower) - margin
                    upper = float(upper) + margin
                updated = updated.model_copy(
                    update={
                        "bounds": BoundsSpec.model_validate(
                            {
                                "minimum": lower,
                                "maximum": upper,
                                "source": "training_percentiles",
                            }
                        )
                    }
                )
            rate_spec = updated.max_rate_of_change
            if (
                spec.name in requested
                and rate_spec is not None
                and rate_spec.training_delta_quantile is not None
            ):
                if engine_column is None or "cycle" not in rate_training.columns:
                    raise ValueError(
                        "training-delta rate fitting requires engine_id/unit_id and cycle columns"
                    )
                cycles = pd.to_numeric(rate_training["cycle"], errors="coerce")
                cycle_steps = cycles.groupby(rate_training[engine_column], sort=False).diff()
                observed_steps = cycle_steps.dropna().to_numpy(dtype=float)
                if observed_steps.size == 0 or not np.allclose(observed_steps, 1.0):
                    raise ValueError(
                        "training-delta rate fitting requires contiguous cycles within each engine"
                    )
                feature_values = rate_training[spec.name].to_numpy(dtype=float)
                if feature_values.size == 0 or not np.isfinite(feature_values).all():
                    raise ValueError(
                        f"training cycle values for {spec.name!r} must be nonempty and finite"
                    )
                differences = rate_training.groupby(engine_column, sort=False)[spec.name].diff()
                absolute_changes = differences.abs().dropna()
                if absolute_changes.empty or not np.isfinite(absolute_changes).all():
                    raise ValueError(
                        f"training cycle changes for {spec.name!r} must be nonempty and finite"
                    )
                fitted_limit = float(absolute_changes.quantile(rate_spec.training_delta_quantile))
                updated = updated.model_copy(
                    update={"max_rate_of_change": RateLimitSpec(absolute=fitted_limit)}
                )
            updated_specs.append(updated)
        return _taxonomy_with_features(self, tuple(updated_specs))

    def with_resolved_bounds(
        self,
        bounds: Mapping[str, tuple[float, float]],
        rate_limits: Mapping[str, float] | None = None,
    ) -> FeatureTaxonomy:
        """Apply persisted train-derived bounds and optional rates to this YAML taxonomy."""
        resolved_rates = rate_limits or {}
        updated_specs: list[FeatureSpec] = []
        for spec in self.features:
            updated = spec
            if spec.name in bounds:
                minimum, maximum = bounds[spec.name]
                updated = updated.model_copy(
                    update={
                        "bounds": BoundsSpec.model_validate(
                            {
                                "minimum": minimum,
                                "maximum": maximum,
                                "source": spec.bounds.source,
                            }
                        )
                    }
                )
            rate_spec = updated.max_rate_of_change
            if rate_spec is not None and rate_spec.training_delta_quantile is not None:
                if spec.name in resolved_rates:
                    updated = updated.model_copy(
                        update={
                            "max_rate_of_change": RateLimitSpec(
                                absolute=float(resolved_rates[spec.name])
                            )
                        }
                    )
                elif updated.bounds.minimum is not None:
                    raise ValueError(
                        f"training-derived rate for {spec.name!r} is missing from the model "
                        "artifact; retrain the model with the configured taxonomy"
                    )
            updated_specs.append(updated)
        return _taxonomy_with_features(self, tuple(updated_specs))

    def validate_bounds_against_observed(
        self,
        frame: pd.DataFrame,
        *,
        columns: tuple[str, ...] | None = None,
    ) -> None:
        """Require configured bounds to contain observed training telemetry."""
        if not self.features:
            return
        specs = self.feature_by_name()
        target_columns = columns or tuple(
            spec.name for spec in self.features if spec.name in frame.columns
        )
        for name in target_columns:
            spec = specs.get(name)
            if spec is None or name not in frame.columns:
                continue
            values = frame[name].to_numpy(dtype=float)
            if not np.isfinite(values).all():
                raise ValueError(f"training data for {name!r} contains non-finite values")
            if spec.bounds.minimum is None or spec.bounds.maximum is None:
                raise ValueError(
                    f"bounds for {name!r} are unresolved; fit them on training engines first"
                )
            observed_min = float(values.min())
            observed_max = float(values.max())
            estimation = self.bound_estimation
            if estimation is None:
                margin = 0.0
            else:
                observed_span = observed_max - observed_min
                margin = max(
                    observed_span * estimation.margin_fraction,
                    estimation.degenerate_half_width,
                )
            if (
                spec.bounds.minimum < observed_min - margin - 1e-12
                or spec.bounds.maximum > observed_max + margin + 1e-12
            ):
                raise ValueError(
                    f"configured bounds for {name!r} exceed observed training range plus margin "
                    f"[{observed_min - margin:g}, {observed_max + margin:g}]"
                )


@dataclass(frozen=True)
class FeatureMasks:
    """Boolean masks aligned to a model feature order."""

    feature_names: tuple[str, ...]
    controllable: NDArray[np.bool_]
    frozen: NDArray[np.bool_]
    dependent: NDArray[np.bool_]


@dataclass(frozen=True)
class BoundVectors:
    """Per-feature physical and scaled bounds aligned to model feature order."""

    feature_names: tuple[str, ...]
    raw_minimum: NDArray[np.float64]
    raw_maximum: NDArray[np.float64]
    scaled_minimum: NDArray[np.float64]
    scaled_maximum: NDArray[np.float64]


def _rate_limit(spec: FeatureSpec) -> float:
    """Resolve the configured per-step rate limit to an absolute raw-unit value."""
    if spec.max_rate_of_change is None:
        raise ValueError(f"feature {spec.name!r} has no rate limit")
    if spec.bounds.minimum is None or spec.bounds.maximum is None:
        raise ValueError(f"feature bounds for {spec.name!r} must be resolved first")
    span = spec.bounds.maximum - spec.bounds.minimum
    if spec.max_rate_of_change.absolute is not None:
        return float(spec.max_rate_of_change.absolute)
    if spec.max_rate_of_change.training_delta_quantile is not None:
        raise ValueError(
            f"training-derived rate for {spec.name!r} must be fitted on engine cycles first"
        )
    fraction = spec.max_rate_of_change.fraction_of_span
    assert fraction is not None
    return float(fraction * span)


def _build_groups(feature_specs: list[FeatureSpec]) -> FeatureGroups:
    """Construct legacy feature group lists from v2 feature metadata."""
    buckets: dict[str, list[str]] = {field: [] for field in _GROUP_TO_FIELD.values()}
    for spec in feature_specs:
        buckets[_GROUP_TO_FIELD[spec.group]].append(spec.name)
    return FeatureGroups(
        controllable_actuators=FeatureGroup(features=buckets["controllable_actuators"]),
        immutable_operational=FeatureGroup(features=buckets["immutable_operational"]),
        immutable_environmental=FeatureGroup(features=buckets["immutable_environmental"]),
        dependent_sensors=FeatureGroup(features=buckets["dependent_sensors"]),
        context=FeatureGroup(features=buckets["context"]),
    )


def _build_actuator_constraints(feature_specs: list[FeatureSpec]) -> dict[str, ActuatorConstraint]:
    """Derive actuator intervals and rate limits from controllable proxy specs."""
    constraints: dict[str, ActuatorConstraint] = {}
    for spec in feature_specs:
        if spec.group != "controllable":
            continue
        if spec.bounds.minimum is None or spec.bounds.maximum is None:
            continue
        constraints[spec.name] = ActuatorConstraint(
            minimum=spec.bounds.minimum,
            maximum=spec.bounds.maximum,
            max_change_per_step=_rate_limit(spec),
            direction=spec.direction,
        )
    return constraints


def _taxonomy_with_features(
    taxonomy: FeatureTaxonomy, features: tuple[FeatureSpec, ...]
) -> FeatureTaxonomy:
    """Rebuild derived taxonomy fields after resolving feature bounds."""
    if not features:
        return taxonomy
    payload = taxonomy.model_dump(mode="python")
    payload["features"] = features
    payload["actuator_constraints"] = {
        name: constraint.model_dump()
        for name, constraint in _build_actuator_constraints(list(features)).items()
    }
    return FeatureTaxonomy.model_validate(payload)


def classification_masks(taxonomy: FeatureTaxonomy, feature_names: tuple[str, ...]) -> FeatureMasks:
    """Build controllable, frozen, and dependent masks for the supplied model feature order."""
    controllable = taxonomy.controllable_feature_names()
    dependent = taxonomy.dependent_feature_names()
    frozen = taxonomy.immutable_feature_names() - {"engine_id", "cycle"}
    return FeatureMasks(
        feature_names=feature_names,
        controllable=np.asarray([name in controllable for name in feature_names], dtype=bool),
        frozen=np.asarray([name in frozen for name in feature_names], dtype=bool),
        dependent=np.asarray([name in dependent for name in feature_names], dtype=bool),
    )


def bound_vectors(taxonomy: FeatureTaxonomy, scaler: FittedFeatureScaler) -> BoundVectors:
    """Map configured raw bounds to scaled space using the fitted training scaler."""
    names = scaler.feature_names
    specs = taxonomy.feature_by_name()
    raw_minimum: list[float] = []
    raw_maximum: list[float] = []
    for name in names:
        spec = specs.get(name)
        if spec is None:
            raise ValueError(f"taxonomy is missing bounds metadata for model feature {name!r}")
        if spec.bounds.minimum is None or spec.bounds.maximum is None:
            raise ValueError(
                f"bounds for model feature {name!r} are unresolved; fit training bounds first"
            )
        raw_minimum.append(spec.bounds.minimum)
        raw_maximum.append(spec.bounds.maximum)
    mean = scaler.scaler.mean_
    scale = scaler.scaler.scale_
    scaled_minimum = (np.asarray(raw_minimum, dtype=float) - mean) / scale
    scaled_maximum = (np.asarray(raw_maximum, dtype=float) - mean) / scale
    ordered_minimum = np.minimum(scaled_minimum, scaled_maximum)
    ordered_maximum = np.maximum(scaled_minimum, scaled_maximum)
    return BoundVectors(
        feature_names=names,
        raw_minimum=np.asarray(raw_minimum, dtype=float),
        raw_maximum=np.asarray(raw_maximum, dtype=float),
        scaled_minimum=ordered_minimum,
        scaled_maximum=ordered_maximum,
    )


def build_feature_taxonomy(
    *,
    dataset: str,
    features: tuple[FeatureSpec, ...],
    bound_estimation: BoundEstimationConfig | None,
    coupling: CouplingConfig | None,
    coupling_rules: tuple[CouplingRule, ...],
) -> FeatureTaxonomy:
    """Derive the runtime masks and intervals from already validated feature metadata."""
    items = list(features)
    return FeatureTaxonomy(
        schema_version=2,
        dataset=dataset,
        feature_groups=_build_groups(items),
        actuator_constraints=_build_actuator_constraints(items),
        coupling_rules=list(coupling_rules),
        features=features,
        bound_estimation=bound_estimation,
        coupling=coupling,
    )


def _validate_archive_columns(features: list[FeatureSpec]) -> None:
    """Keep the registered benchmark column mapping strict at the legacy loader."""
    for feature in features:
        if feature.name.startswith("op_setting_") and (
            feature.cmapss_column != feature.name or feature.group != "immutable_operational"
        ):
            raise ValueError("C-MAPSS operating settings must map to immutable operational inputs")
        if feature.name.startswith("sensor_"):
            suffix = feature.name.removeprefix("sensor_")
            if not suffix.isdigit() or feature.cmapss_column != f"s{suffix}":
                raise ValueError(
                    f"C-MAPSS sensor mapping for {feature.name!r} must use column s{suffix}"
                )


def load_taxonomy(path: Path, *, expected_sha256: str | None = None) -> FeatureTaxonomy:
    """Load and validate feature taxonomy YAML."""
    import hashlib

    data = path.read_bytes()
    if expected_sha256 is not None and hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("taxonomy changed after fingerprinting; reload the complete bundle")
    raw: Any = yaml.safe_load(data.decode("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("feature taxonomy root must be a mapping")
    if "features" in raw:
        feature_specs = [FeatureSpec.model_validate(item) for item in raw["features"]]
        _validate_archive_columns(feature_specs)
        if len({spec.name for spec in feature_specs}) != len(feature_specs):
            raise ValueError("duplicate feature names in taxonomy metadata")
        groups = _build_groups(feature_specs)
        actuator_constraints = _build_actuator_constraints(feature_specs)
        payload = {
            **raw,
            "feature_groups": groups.model_dump(),
            "actuator_constraints": {
                name: constraint.model_dump() for name, constraint in actuator_constraints.items()
            },
            "features": tuple(feature_specs),
        }
        return FeatureTaxonomy.model_validate(payload)
    return FeatureTaxonomy.model_validate(raw)
