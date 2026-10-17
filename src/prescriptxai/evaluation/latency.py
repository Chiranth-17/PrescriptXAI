"""Measured latency summaries against configured targets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LatencyMetric:
    """Observed latency distribution and target assessment for one stage."""

    mean_ms: float | None
    median_ms: float | None
    p95_ms: float | None
    target_min_ms: float | None
    target_max_ms: float | None
    passed: bool | None
    upper_budget_passed: bool | None = None
    below_target_range: bool | None = None


def summarize_latency(
    samples_ms: Sequence[float],
    target_min_ms: float | None,
    target_max_ms: float | None,
) -> LatencyMetric:
    """Summarize measured milliseconds; an absent sample is unmeasured, not zero."""
    if target_min_ms is not None and target_min_ms < 0:
        raise ValueError("target_min_ms must not be negative")
    if target_max_ms is not None and target_max_ms <= 0:
        raise ValueError("target_max_ms must be positive")
    if target_min_ms is not None and target_max_ms is not None and target_min_ms > target_max_ms:
        raise ValueError("target_min_ms must not exceed target_max_ms")
    if not samples_ms:
        return LatencyMetric(None, None, None, target_min_ms, target_max_ms, None)
    samples = np.asarray(samples_ms, dtype=float)
    if not np.isfinite(samples).all() or (samples < 0).any():
        raise ValueError("latency samples must be finite and non-negative")
    mean = float(samples.mean())
    passed = (target_min_ms is None or mean >= target_min_ms) and (
        target_max_ms is None or mean <= target_max_ms
    )
    return LatencyMetric(
        mean,
        float(np.median(samples)),
        float(np.percentile(samples, 95)),
        target_min_ms,
        target_max_ms,
        passed,
        None if target_max_ms is None else mean <= target_max_ms,
        None if target_min_ms is None else mean < target_min_ms,
    )
