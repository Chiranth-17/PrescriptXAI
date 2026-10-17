"""Exact small-subset search to cap changed actuator count."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

from prescriptxai.models.registry import ModelBundle

StateTransform = Callable[[Mapping[str, float]], Mapping[str, float]]


@dataclass(frozen=True)
class SparseCandidate:
    """Candidate state after enforcing the configured actuator count."""

    state: dict[str, float]
    changed_features: tuple[str, ...]
    risk: float
    success: bool
    message: str


def candidate_supports(
    scaled_delta_by_feature: Mapping[str, float],
    feature_names: tuple[str, ...],
    *,
    max_changed_features: int,
    top_m: int,
    max_supports: int,
) -> tuple[tuple[str, ...], ...]:
    """Enumerate deterministic top-k and nearby supports ranked by absolute scaled change."""
    if max_changed_features < 1 or top_m < 1 or max_supports < 1:
        raise ValueError("support limits must be positive")
    ranked = [
        name
        for name in feature_names
        if name in scaled_delta_by_feature and scaled_delta_by_feature[name] != 0.0
    ]
    ranked.sort(key=lambda name: abs(scaled_delta_by_feature[name]), reverse=True)
    ranked = ranked[: min(top_m, len(ranked))]
    supports: list[tuple[str, ...]] = []
    for size in range(min(max_changed_features, len(ranked)), 0, -1):
        supports.extend(combinations(ranked, size))
    return tuple(supports[:max_supports])


def prune_to_support(
    original_state: Mapping[str, float],
    candidate_state: Mapping[str, float],
    support: tuple[str, ...],
    candidate_transform: StateTransform | None = None,
) -> dict[str, float]:
    """Keep selected control changes and restore all omitted controls before propagation."""
    result = dict(original_state)
    for name in support:
        if name not in original_state or name not in candidate_state:
            raise ValueError(f"support feature {name!r} is missing from a state")
        result[name] = float(candidate_state[name])
    if candidate_transform is not None:
        result = dict(candidate_transform(result))
    return result


def sparsify_candidate(
    bundle: ModelBundle,
    original_state: Mapping[str, float],
    candidate_state: Mapping[str, float],
    actuator_names: tuple[str, ...],
    max_changed_features: int,
    safe_threshold: float,
    candidate_transform: StateTransform | None = None,
) -> SparseCandidate:
    """Find the smallest safe subset among optimized actuator changes.

    Subsets are considered in descending scaled-change magnitude order. Every candidate subset is
    rescored by the fitted calibrated model; no reduced state is assumed to remain valid.
    """
    if max_changed_features < 1:
        raise ValueError("max_changed_features must be positive")
    if not 0 < safe_threshold < 1:
        raise ValueError("safe_threshold must be within (0, 1)")
    changed = [
        name
        for name in actuator_names
        if name not in original_state
        or name not in candidate_state
        or not np.isclose(original_state[name], candidate_state[name], rtol=0, atol=0)
    ]
    if any(name not in original_state or name not in candidate_state for name in changed):
        raise ValueError("original and candidate states must include every actuator")
    scale_by_name = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
    changed.sort(
        key=lambda name: abs(candidate_state[name] - original_state[name]) / scale_by_name[name],
        reverse=True,
    )
    limit = min(max_changed_features, len(changed))
    original_state_dict = dict(original_state)
    original_risk = float(bundle.predict_risk(pd.DataFrame([original_state_dict]))[0])
    best_state = original_state_dict
    best_changed: tuple[str, ...] = ()
    best_risk = original_risk
    for count in range(1, limit + 1):
        for selected in combinations(changed, count):
            trial = dict(original_state)
            for name in selected:
                trial[name] = candidate_state[name]
            scored_state = dict(candidate_transform(trial)) if candidate_transform else trial
            risk = float(bundle.predict_risk(pd.DataFrame([scored_state]))[0])
            if risk <= safe_threshold:
                return SparseCandidate(
                    scored_state, tuple(selected), risk, True, "safe sparse candidate"
                )
            if risk < best_risk:
                best_state = scored_state
                best_changed = tuple(selected)
                best_risk = risk
    return SparseCandidate(
        best_state,
        best_changed,
        best_risk,
        False,
        "no safe candidate exists within the configured changed-feature limit; "
        "returning the lowest-risk sparse candidate",
    )
