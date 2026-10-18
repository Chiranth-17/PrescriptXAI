"""Engine-bootstrap funnels that retain missing candidates and independent tier denominators."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray

from prescriptxai.evaluation.metrics import engine_bootstrap_interval
from prescriptxai.validation.base import EvidenceLevel


@dataclass(frozen=True)
class FunnelObservation:
    """One alert query, including explicit no-candidate failures."""

    engine_id: int
    cycle: int
    candidate_returned: bool
    counterfactual_returned: bool
    tier1: bool
    tier2: bool
    tier3: bool
    tier4: bool
    evidence_level: EvidenceLevel = "none"
    distance: float | None = None
    recourse_feasible: bool = False


@dataclass(frozen=True)
class FunnelRun:
    """Required labels for each result table and machine-readable report."""

    run_id: str
    config_path: str
    config_hash: str
    git_hash: str
    protocol_version: str
    k_max: int
    K: int
    D_max_version: str
    D_max: float
    population: str
    comparison: str


def build_funnel_report(
    observations: Sequence[FunnelObservation],
    metadata: FunnelRun,
    *,
    bootstrap_replicates: int,
    seed: int,
) -> dict[str, object]:
    """Report cumulative and independent rates with whole-engine confidence intervals.

    A diagnostic candidate is distinct from an accepted counterfactual. Report both denominators,
    since strict validation can make returned-counterfactual plausibility 100% by construction.
    Missing candidate queries remain false in every all-query tier rate.
    """
    if bootstrap_replicates < 1 or seed < 0:
        raise ValueError("bootstrap settings must be positive and deterministic")
    keys = [(item.engine_id, item.cycle) for item in observations]
    if len(keys) != len(set(keys)):
        raise ValueError("funnel queries must have unique engine/cycle keys")
    ids = np.asarray([item.engine_id for item in observations], dtype=np.int64)
    available = np.asarray([item.candidate_returned for item in observations], dtype=bool)
    returned = np.asarray([item.counterfactual_returned for item in observations], dtype=bool)
    if np.any(returned & ~available):
        raise ValueError("a returned counterfactual must have a candidate")
    tiers = [
        np.asarray([getattr(item, f"tier{tier}") for item in observations], dtype=bool) & available
        for tier in range(1, 5)
    ]

    def metric(values: np.ndarray, selected: np.ndarray, offset: int) -> dict[str, object]:
        """Keep empty denominators unavailable rather than inventing successful rates."""
        selected_ids = ids[selected]
        selected_values = values[selected]
        output: dict[str, object] = {
            "count": int(selected_values.sum()),
            "denominator": len(selected_values),
            "engine_count": int(len(np.unique(selected_ids))),
            "rate": None,
            "ci": None,
        }
        if len(selected_values):
            interval = engine_bootstrap_interval(
                selected_ids,
                selected_values,
                seed=seed + offset,
                replicates=bootstrap_replicates,
            )
            output.update(rate=interval.estimate, ci=asdict(interval))
        return output

    all_queries: NDArray[np.bool_] = np.ones(len(ids), dtype=bool)
    cumulative = available.copy()
    funnel: dict[str, object] = {
        "alerts": metric(all_queries, all_queries, 0),
        "candidate_returned": metric(available, all_queries, 1),
    }
    for index, passed in enumerate(tiers, start=1):
        cumulative = cumulative & passed
        funnel[f"tier{index}_cumulative"] = metric(cumulative, all_queries, index + 1)
    funnel["joint_success"] = metric(cumulative, all_queries, 6)
    physical = tiers[1] & tiers[2] & tiers[3]
    independent = {
        f"tier{index}_all_queries": metric(passed, all_queries, 10 + index)
        for index, passed in enumerate(tiers, start=1)
    }
    independent.update(
        {
            "tier2_returned_counterfactuals": metric(tiers[1], returned, 20),
            "tier2_diagnostic_candidates": metric(tiers[1], available, 21),
            "physical_tiers2_to4_all_queries": metric(physical, all_queries, 22),
            "joint_tiers1_to4_all_queries": metric(cumulative, all_queries, 23),
            "accepted_counterfactuals": metric(returned, all_queries, 24),
        }
    )
    distances = [item.distance for item in observations if item.distance is not None]
    if not np.isfinite(distances).all():
        raise ValueError("funnel distances must be finite when present")
    return {
        "metadata": asdict(metadata),
        "query_count": len(ids),
        "engine_count": len(np.unique(ids)),
        "missing_candidates": int((~available).sum()),
        "funnel": funnel,
        "independent": independent,
        "distance_distribution": {
            "count": len(distances),
            "mean": float(np.mean(distances)) if distances else None,
            "p50": float(np.quantile(distances, 0.5)) if distances else None,
            "p95": float(np.quantile(distances, 0.95)) if distances else None,
        },
        "evidence_level_counts": {
            level: sum(item.evidence_level == level for item in observations)
            for level in ("none", "E1", "E2", "E3", "E4", "E5")
        },
        "assumptions": [
            "C-MAPSS features are controllable proxies; bounds/rates are documented assumptions.",
            f"Intervention horizon K={metadata.K} is an assumption, not actuator dynamics.",
            "Joint is not compared with the 90% Tier 2 plausibility target.",
        ],
        "observations": [asdict(item) for item in observations],
    }
