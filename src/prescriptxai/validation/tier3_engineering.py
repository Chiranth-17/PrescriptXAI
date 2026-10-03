"""Tier 3: actuator bounds, rate limits, and immutable-feature checks."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from prescriptxai.constraints.bounds import allowed_interval
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.validation.base import TierResult


def validate_engineering(
    initial: Mapping[str, float], candidate: Mapping[str, float], taxonomy: FeatureTaxonomy
) -> TierResult:
    """Check all configured actuator and feature-freezing engineering rules."""
    groups = taxonomy.feature_groups.model_dump()
    declared = {name for group in groups.values() for name in group["features"]}
    missing = (declared - set(initial)) | (declared - set(candidate))
    if missing:
        return TierResult(False, (f"state is missing configured features: {sorted(missing)}",))
    non_finite = [name for name in declared if not np.isfinite(candidate[name])]
    if non_finite:
        return TierResult(False, (f"candidate has non-finite values: {sorted(non_finite)}",))
    actuators = set(taxonomy.feature_groups.controllable_actuators.features)
    failures: list[str] = []
    for name in sorted(declared - actuators):
        if not np.isclose(initial[name], candidate[name], rtol=0, atol=0):
            failures.append(f"immutable/dependent feature {name} changed")
    for name, constraint in taxonomy.actuator_constraints.items():
        value = candidate[name]
        if not np.isfinite(value):
            failures.append(f"actuator {name} is non-finite")
            continue
        if not constraint.minimum <= value <= constraint.maximum:
            failures.append(f"actuator {name} violates absolute bounds")
        try:
            lower, upper = allowed_interval(initial[name], constraint)
        except ValueError:
            failures.append(f"actuator {name} has no feasible rate-limited interval")
            continue
        if not lower <= value <= upper:
            failures.append(f"actuator {name} violates rate limit")
    return TierResult(not failures, tuple(failures))
