"""Tier 3: actuator bounds, rate limits, and immutable-feature checks."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from prescriptxai.constraints.bounds import check_bound_violations, check_rate_violations
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.validation.base import TierResult


def validate_engineering(
    initial: Mapping[str, float],
    candidate: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
    *,
    horizon_steps: int = 1,
) -> TierResult:
    """Check actuator bounds/rates and freeze immutable operating/context fields.

    ``horizon_steps`` multiplies the configured one-step telemetry rate limit. Values above one
    are sensitivity assumptions, not verified physical actuator dynamics.
    """
    groups = taxonomy.feature_groups.model_dump()
    declared = {name for group in groups.values() for name in group["features"]}
    missing = (declared - set(initial)) | (declared - set(candidate))
    if missing:
        return TierResult(False, (f"state is missing configured features: {sorted(missing)}",))
    non_finite = [name for name in declared if not np.isfinite(candidate[name])]
    if non_finite:
        return TierResult(False, (f"candidate has non-finite values: {sorted(non_finite)}",))
    immutable = taxonomy.immutable_feature_names()
    failures: list[str] = []
    for name in sorted(declared & immutable):
        if not np.isclose(initial[name], candidate[name], rtol=0, atol=0):
            failures.append(f"immutable feature {name} changed")
    # Percentile bounds on measured sensors describe the empirical operating distribution, not
    # actuator limits. Immutable and dependent telemetry is handled by its own freeze/propagation,
    # Tier 2, and Tier 4 checks. Tier 3 therefore applies hard physical bounds only to controls.
    actuator_names = tuple(taxonomy.actuator_constraints)
    bound_violations = check_bound_violations(
        candidate, taxonomy, features=actuator_names
    )
    failures.extend(f"{item.feature}: {item.reason}" for item in bound_violations)
    rate_violations = check_rate_violations(
        initial, candidate, taxonomy, horizon_steps=horizon_steps
    )
    failures.extend(f"{item.feature}: {item.reason}" for item in rate_violations)
    return TierResult(not failures, tuple(failures))
