"""Physical bound projection, violation reporting, and rate-limit checks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

import numpy as np

from prescriptxai.constraints.taxonomy import (
    ActuatorConstraint,
    BoundVectors,
    FeatureSpec,
    FeatureTaxonomy,
)


@dataclass(frozen=True)
class BoundViolation:
    """One explainable bound or rate violation."""

    feature: str
    reason: str
    margin: float


def allowed_interval(current: float, constraint: ActuatorConstraint) -> tuple[float, float]:
    """Intersect an actuator's absolute range with its per-step rate limit."""
    lower = max(constraint.minimum, current - constraint.max_change_per_step)
    upper = min(constraint.maximum, current + constraint.max_change_per_step)
    if lower > upper:
        raise ValueError("current actuator state and rate limit have no feasible interval")
    if constraint.direction == "increase_only":
        lower = max(lower, current)
    elif constraint.direction == "decrease_only":
        upper = min(upper, current)
    if lower > upper:
        raise ValueError("direction restriction leaves no feasible interval")
    return lower, upper


def _clip_with_direction(
    value: float,
    lower: float,
    upper: float,
    *,
    direction: str,
    reference: float | None = None,
) -> float:
    """Clip a scalar to bounds while honoring optional directional restrictions."""
    clipped = float(np.clip(value, lower, upper))
    if reference is None or direction == "any":
        return clipped
    if direction == "increase_only":
        return max(clipped, reference)
    return min(clipped, reference)


def project_feature_to_bounds(
    value: float,
    spec: FeatureSpec,
    *,
    reference: float | None = None,
) -> float:
    """Project one raw feature value into configured physical bounds."""
    if spec.bounds.minimum is None or spec.bounds.maximum is None:
        raise ValueError(f"bounds for feature {spec.name!r} are unresolved")
    return _clip_with_direction(
        value,
        spec.bounds.minimum,
        spec.bounds.maximum,
        direction=spec.direction,
        reference=reference,
    )


def project_state_to_bounds(
    values: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
    *,
    reference: Mapping[str, float] | None = None,
    features: tuple[str, ...] | None = None,
) -> dict[str, float]:
    """Project selected features into physical bounds; unspecified keys pass through."""
    specs = taxonomy.feature_by_name()
    if not specs:
        return dict(values)
    target = features or tuple(specs)
    projected = dict(values)
    for name in target:
        spec = specs.get(name)
        if spec is None or name not in projected:
            continue
        ref = None if reference is None else reference.get(name)
        projected[name] = project_feature_to_bounds(projected[name], spec, reference=ref)
    return projected


def project_vector_to_bounds(
    values: np.ndarray,
    bounds: BoundVectors,
) -> np.ndarray:
    """Clip a vector aligned to ``bounds.feature_names``; idempotent under repetition."""
    if values.shape != bounds.raw_minimum.shape:
        raise ValueError("values must align with bound vectors")
    return cast(np.ndarray, np.clip(values, bounds.raw_minimum, bounds.raw_maximum))


def check_bound_violations(
    values: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
    *,
    features: tuple[str, ...] | None = None,
) -> tuple[BoundViolation, ...]:
    """Report absolute physical bound violations with human-readable reasons."""
    specs = taxonomy.feature_by_name()
    target = features or tuple(specs)
    violations: list[BoundViolation] = []
    for name in target:
        spec = specs.get(name)
        if spec is None or name not in values:
            continue
        value = float(values[name])
        if not np.isfinite(value):
            violations.append(BoundViolation(name, "value is not finite", margin=float("inf")))
            continue
        if spec.bounds.minimum is None or spec.bounds.maximum is None:
            violations.append(
                BoundViolation(name, "physical bounds are unresolved", margin=float("inf"))
            )
            continue
        if value < spec.bounds.minimum:
            violations.append(
                BoundViolation(
                    name,
                    f"below physical minimum ({spec.bounds.minimum:g} {spec.unit})",
                    margin=spec.bounds.minimum - value,
                )
            )
        elif value > spec.bounds.maximum:
            violations.append(
                BoundViolation(
                    name,
                    f"above physical maximum ({spec.bounds.maximum:g} {spec.unit})",
                    margin=value - spec.bounds.maximum,
                )
            )
    return tuple(violations)


def check_rate_violations(
    initial: Mapping[str, float],
    candidate: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
) -> tuple[BoundViolation, ...]:
    """Report per-step rate and directional violations for controllable proxies."""
    violations: list[BoundViolation] = []
    for name, constraint in taxonomy.actuator_constraints.items():
        if name not in initial or name not in candidate:
            violations.append(
                BoundViolation(name, "missing initial or candidate value", margin=float("inf"))
            )
            continue
        current = float(initial[name])
        proposed = float(candidate[name])
        delta = proposed - current
        if constraint.direction == "increase_only" and delta < 0:
            violations.append(
                BoundViolation(name, "decrease violates increase_only direction", margin=-delta)
            )
        if constraint.direction == "decrease_only" and delta > 0:
            violations.append(
                BoundViolation(name, "increase violates decrease_only direction", margin=delta)
            )
        if abs(delta) > constraint.max_change_per_step + 1e-12:
            violations.append(
                BoundViolation(
                    name,
                    f"per-step change {delta:g} exceeds limit {constraint.max_change_per_step:g}",
                    margin=abs(delta) - constraint.max_change_per_step,
                )
            )
        try:
            lower, upper = allowed_interval(current, constraint)
        except ValueError:
            violations.append(
                BoundViolation(name, "no feasible rate-limited interval", margin=float("inf"))
            )
            continue
        if not lower <= proposed <= upper:
            violations.append(
                BoundViolation(
                    name,
                    f"outside feasible interval [{lower:g}, {upper:g}]",
                    margin=min(proposed - upper, lower - proposed),
                )
            )
    return tuple(violations)


def raw_bounds_to_scaled(
    raw_minimum: float,
    raw_maximum: float,
    *,
    mean: float,
    scale: float,
) -> tuple[float, float]:
    """Convert one feature's raw bounds to scaled coordinates."""
    scaled_minimum = (raw_minimum - mean) / scale
    scaled_maximum = (raw_maximum - mean) / scale
    return min(scaled_minimum, scaled_maximum), max(scaled_minimum, scaled_maximum)


def scaled_bounds_to_raw(
    scaled_minimum: float,
    scaled_maximum: float,
    *,
    mean: float,
    scale: float,
) -> tuple[float, float]:
    """Convert scaled bounds back to raw coordinates."""
    raw_minimum = mean + scaled_minimum * scale
    raw_maximum = mean + scaled_maximum * scale
    return min(raw_minimum, raw_maximum), max(raw_minimum, raw_maximum)
