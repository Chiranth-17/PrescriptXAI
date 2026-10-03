"""Evaluation of configured cross-sensor engineering relationships."""

from __future__ import annotations

from collections.abc import Mapping

from prescriptxai.constraints.taxonomy import CouplingRule, FeatureTaxonomy


def evaluate_rule(values: Mapping[str, float], rule: CouplingRule) -> tuple[bool, float]:
    """Return validity and signed rule violation magnitude for one configured relationship."""
    if rule.feature_a not in values or rule.feature_b not in values:
        raise ValueError(f"state is missing a feature required by coupling rule {rule.name!r}")
    value_a = values[rule.feature_a]
    value_b = values[rule.feature_b]
    if rule.relation == "less_than":
        violation = max(0.0, value_a - value_b - rule.tolerance)
    elif rule.relation == "greater_than":
        violation = max(0.0, value_b - value_a - rule.tolerance)
    else:
        if rule.slope is None or rule.intercept is None:
            raise ValueError(f"linear coupling rule {rule.name!r} has no coefficients")
        residual = abs(value_b - (rule.slope * value_a + rule.intercept))
        violation = max(0.0, residual - rule.tolerance)
    return violation == 0.0, violation


def validate_couplings(
    values: Mapping[str, float], taxonomy: FeatureTaxonomy
) -> tuple[bool, tuple[str, ...]]:
    """Check all configured coupling rules; an empty rule set is explicitly unvalidated."""
    if not taxonomy.coupling_rules:
        return False, ("no sensor coupling rules are configured",)
    failures: list[str] = []
    for rule in taxonomy.coupling_rules:
        try:
            valid, violation = evaluate_rule(values, rule)
        except ValueError as error:
            failures.append(str(error))
            continue
        if not valid:
            failures.append(f"{rule.name}: violation={violation:g}")
    return not failures, tuple(failures)
