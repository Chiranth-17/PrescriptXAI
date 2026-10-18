"""Tier 3: actuator bounds, rate limits, and immutable-feature checks."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from prescriptxai.constraints.bounds import check_bound_violations, check_rate_violations
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.validation.base import CheckResult, TierResult


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
    non_finite = [
        name
        for name in declared
        if not np.isfinite(candidate[name]) or not np.isfinite(initial[name])
    ]
    if non_finite:
        return TierResult(
            False,
            (f"initial/candidate has non-finite values: {sorted(non_finite)}",),
            evidence_level="E3",
        )
    immutable = taxonomy.immutable_feature_names()
    failures: list[str] = []
    checks: list[CheckResult] = []
    for name in sorted(declared & immutable):
        if not np.isclose(initial[name], candidate[name], rtol=0, atol=0):
            failures.append(f"immutable feature {name} changed")
            checks.append(
                CheckResult(
                    f"immutable_{name}",
                    False,
                    -abs(candidate[name] - initial[name]),
                    failures[-1],
                    name,
                )
            )
    # Percentile bounds on measured sensors describe the empirical operating distribution, not
    # actuator limits. Immutable and dependent telemetry is handled by its own freeze/propagation,
    # Tier 2, and Tier 4 checks. Tier 3 therefore applies hard physical bounds only to controls.
    actuator_names = tuple(taxonomy.actuator_constraints)
    # Identifiers are immutable labels, including namespaced official-test engine IDs. Their
    # arbitrary display range is not a physical constraint; cycle-domain bounds still apply.
    specs = taxonomy.feature_by_name()
    context_names = tuple(
        name
        for name in taxonomy.feature_groups.context.features
        if specs[name].unit != "identifier"
    )
    bound_violations = check_bound_violations(
        candidate, taxonomy, features=actuator_names + context_names
    )
    failures.extend(f"{item.feature}: {item.reason}" for item in bound_violations)
    rate_violations = check_rate_violations(
        initial, candidate, taxonomy, horizon_steps=horizon_steps
    )
    failures.extend(f"{item.feature}: {item.reason}" for item in rate_violations)
    for kind, violations in (("bounds", bound_violations), ("rate", rate_violations)):
        checks.extend(
            CheckResult(
                f"{kind}_{item.feature}",
                False,
                -abs(item.margin) if np.isfinite(item.margin) else None,
                f"{item.feature}: {item.reason}",
                item.feature,
            )
            for item in violations
        )
    finite_margins = [check.margin for check in checks if check.margin is not None]
    return TierResult(
        not failures,
        tuple(failures),
        margin=min(finite_margins, default=None),
        evidence_level="E3",
        checks=tuple(checks),
    )
