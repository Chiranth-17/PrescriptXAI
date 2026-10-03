"""Transparent no-action and single-actuator recourse baselines."""

from __future__ import annotations

import pandas as pd

from prescriptxai.config import AppConfig
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.optimizer import OptimizationResult, optimize_recourse


def no_action_baseline(
    initial_state: dict[str, float], bundle: ModelBundle, safe_threshold: float
) -> OptimizationResult:
    """Return an unchanged candidate and its model-only target-risk status."""
    if not 0 < safe_threshold < 1:
        raise ValueError("safe_threshold must be within (0, 1)")
    risk = float(bundle.predict_risk(pd.DataFrame([initial_state]))[0])
    model_valid = risk <= safe_threshold
    return OptimizationResult(
        initial_state,
        (),
        risk,
        risk,
        solver_success=True,
        model_valid=model_valid,
        message=(
            "no-action state meets the model-risk target"
            if model_valid
            else "no-action baseline does not meet the safe-risk target"
        ),
        objective_value=0.0,
    )


def single_actuator_baseline(
    initial_state: dict[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    config: AppConfig,
) -> OptimizationResult:
    """Optimize each actuator alone and return the least scaled-change safe candidate."""
    actuator_names = taxonomy.feature_groups.controllable_actuators.features
    if not actuator_names:
        return optimize_recourse(initial_state, bundle, taxonomy, config)
    one_feature_config = config.model_copy(deep=True)
    one_feature_config.recourse.max_changed_features = 1
    candidates: list[OptimizationResult] = []
    for name in actuator_names:
        one_actuator_taxonomy = taxonomy.model_copy(deep=True)
        one_actuator_taxonomy.feature_groups.controllable_actuators.features = [name]
        one_actuator_taxonomy.actuator_constraints = {
            name: taxonomy.actuator_constraints[name]
        }
        candidates.append(
            optimize_recourse(initial_state, bundle, one_actuator_taxonomy, one_feature_config)
        )
    valid_candidates = [candidate for candidate in candidates if candidate.model_valid]
    if not valid_candidates:
        return min(candidates, key=lambda result: result.final_risk)
    return min(
        valid_candidates,
        key=lambda result: sum(abs(delta.scaled_delta) for delta in result.deltas),
    )
