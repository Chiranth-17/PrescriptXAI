"""Actual component-removal searches and historical fixed-candidate acceptance summaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from prescriptxai.config import AppConfig
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import (
    ActuatorConstraint,
    BoundsSpec,
    FeatureGroup,
    FeatureTaxonomy,
    RateLimitSpec,
)
from prescriptxai.evaluation.metrics import EvaluationRecord
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.optimizer import OptimizationResult, RecourseOptimizer
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator


@dataclass(frozen=True)
class SearchPolicy:
    """Explicit research-only search removals; reporting always uses original constraints."""

    freeze_immutable: bool = True
    physical_bounds: bool = True
    rate_limits: bool = True
    propagate_dependents: bool = True
    free_dependents: bool = False
    enforce_sparsity: bool = True
    check_distribution: bool = True
    check_coupling: bool = True
    validation_in_loop: bool = True


def ablation_policies() -> dict[str, SearchPolicy]:
    """Return true one-component removal policies, not post-hoc acceptance masks."""
    full = SearchPolicy()
    return {
        "full": full,
        "no_immutable_freezing": replace(full, freeze_immutable=False),
        "no_bounds": replace(full, physical_bounds=False),
        "no_mahalanobis": replace(full, check_distribution=False),
        "no_coupling_propagation": replace(full, propagate_dependents=False),
        "no_sparsity": replace(full, enforce_sparsity=False),
        "no_validation_in_loop": replace(full, validation_in_loop=False),
    }


def ladder_policies() -> dict[str, SearchPolicy]:
    """Define nested L0–L7 search spaces with one constraint group added per stage."""
    policy = SearchPolicy(False, False, False, False, True, False, False, False)
    result = {"L0_all_free": policy}
    for name, changes in (
        ("L1_immutable", {"freeze_immutable": True}),
        ("L2_bounds", {"physical_bounds": True}),
        ("L3_rates", {"rate_limits": True}),
        ("L4_propagation", {"propagate_dependents": True, "free_dependents": False}),
        ("L5_sparsity", {"enforce_sparsity": True}),
        ("L6_mahalanobis", {"check_distribution": True}),
        ("L7_coupling", {"check_coupling": True}),
    ):
        policy = replace(policy, **changes)
        result[name] = policy
    return result


def search_taxonomy(
    taxonomy: FeatureTaxonomy,
    bundle: ModelBundle,
    initial: Mapping[str, float],
    config: AppConfig,
    policy: SearchPolicy,
    free_rate_fraction: float,
) -> FeatureTaxonomy:
    """Build an explicitly unsafe experimental search map without mutating reporting taxonomy.

    Deliberate immutable-removal experiments use copies of immutable input specifications. Their
    original group remains authoritative in all final checks and reports. Model input context IDs
    and cycle are never added to a predictor that did not use them.
    """
    result = taxonomy.model_copy(deep=True)
    controls = set(result.feature_groups.controllable_actuators.features)
    if not policy.freeze_immutable:
        controls |= set(result.feature_groups.immutable_operational.features)
        controls |= set(result.feature_groups.immutable_environmental.features)
    if policy.free_dependents:
        controls |= set(result.feature_groups.dependent_sensors.features)
    controls &= set(bundle.feature_names)
    groups = result.feature_groups.model_copy(deep=True)
    for field_name in type(groups).model_fields:
        group = getattr(groups, field_name)
        names = [n for n in group.features if n not in controls]
        setattr(groups, field_name, FeatureGroup(features=names))
    original_order = taxonomy.feature_groups.controllable_actuators.features
    ordered = [n for n in original_order if n in controls]
    ordered += [n for n in bundle.feature_names if n in controls and n not in ordered]
    groups.controllable_actuators = FeatureGroup(features=ordered)
    scales = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
    specs = []
    constraints = {}
    for spec in result.features:
        if spec.name not in controls:
            specs.append(spec)
            continue
        width = float(scales[spec.name]) * config.recourse.max_scaled_distance
        lower, upper = spec.bounds.minimum, spec.bounds.maximum
        if lower is None or upper is None:
            raise ValueError("experiment requires resolved train-only bounds")
        original = result.actuator_constraints.get(spec.name)
        if not policy.physical_bounds:
            lower, upper = initial[spec.name] - width, initial[spec.name] + width
        rate = (
            original.max_change_per_step
            if original is not None and policy.rate_limits
            else width * free_rate_fraction
        )
        constraints[spec.name] = ActuatorConstraint(
            minimum=lower,
            maximum=upper,
            max_change_per_step=rate,
            direction=original.direction if original else "any",
        )
        specs.append(
            spec.model_copy(
                update={
                    "group": "controllable",
                    "bounds": BoundsSpec(minimum=lower, maximum=upper),
                    "max_rate_of_change": RateLimitSpec(absolute=rate),
                }
            )
        )
    return result.model_copy(
        update={
            "features": tuple(specs),
            "feature_groups": groups,
            "actuator_constraints": constraints,
        }
    )


def run_ablation_search(
    state: dict[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    config: AppConfig,
    coupling: SensorCouplingModel | None,
    validator: MahalanobisValidator,
    policy: SearchPolicy,
    *,
    free_rate_fraction: float,
) -> OptimizationResult:
    """Rerun the production algorithm under an explicit component-removal policy."""
    local = config.model_copy(deep=True)
    search = search_taxonomy(taxonomy, bundle, state, local, policy, free_rate_fraction)
    if not policy.enforce_sparsity:
        local.recourse.max_changed_features = len(
            search.active_controllable_feature_names(bundle.feature_names)
        )
    return RecourseOptimizer(
        bundle,
        search,
        coupling,
        validator,
        validate_plausibility=policy.validation_in_loop,
        check_distribution=policy.check_distribution,
        check_coupling=policy.check_coupling,
        propagate_dependents=policy.propagate_dependents,
        grid_support_cap=(config.recourse.k_max if not policy.enforce_sparsity else None),
    ).solve(state, local)


def ablation_acceptance_rates(records: tuple[EvaluationRecord, ...]) -> dict[str, float | None]:
    """Measure how many model-valid candidates pass if a physical tier is omitted.

    These are counterfactual acceptance rates, not physical-validity claims. Each key names the
    omitted check; the full validation metrics remain unchanged.
    """
    count = len(records)
    if count == 0:
        return {"omit_tier2": None, "omit_tier3": None, "omit_tier4": None, "model_only": None}
    return {
        "omit_tier2": sum(
            r.model_valid and r.tier3_engineering_valid and r.tier4_coupling_valid for r in records
        )
        / count,
        "omit_tier3": sum(
            r.model_valid and r.tier2_plausible and r.tier4_coupling_valid for r in records
        )
        / count,
        "omit_tier4": sum(
            r.model_valid and r.tier2_plausible and r.tier3_engineering_valid for r in records
        )
        / count,
        "model_only": sum(r.model_valid for r in records) / count,
    }
