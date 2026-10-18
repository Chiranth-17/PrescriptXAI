"""Measured latency summaries against configured targets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from time import perf_counter_ns
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict


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
    p95 = float(np.percentile(samples, 95))
    passed = None if target_max_ms is None else p95 <= target_max_ms
    return LatencyMetric(
        mean,
        float(np.median(samples)),
        float(np.percentile(samples, 95)),
        target_min_ms,
        target_max_ms,
        passed,
        None if target_max_ms is None else p95 <= target_max_ms,
        None if target_min_ms is None else mean < target_min_ms,
    )


if TYPE_CHECKING:
    from prescriptxai.pipeline import PrescriptXAI


class StageLatency(BaseModel):
    """Unpadded observed stage quantiles; absent stages stay explicitly unmeasured."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    count: int
    engine_count: int
    p50_ms: float | None
    p95_ms: float | None
    p99_ms: float | None
    upper_budget_ms: float
    passed: bool | None
    p95_engine_ci: dict[str, float | int] | None


class LatencyReport(BaseModel):
    """Both modes, raw timings and separate quality/evidence on the same queries."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    modes: dict[str, dict[str, StageLatency]]
    metadata: dict[str, object]
    results: dict[str, list[dict[str, object]]]


def benchmark_pipeline(
    pipeline: PrescriptXAI,
    frame: pd.DataFrame,
    *,
    warmup_frame: pd.DataFrame | None = None,
    metadata: dict[str, object] | None = None,
) -> LatencyReport:
    """Time actual serial calls, including failures; never sum stage percentiles."""
    from prescriptxai.evaluation.metrics import engine_bootstrap_interval

    if frame.empty or "engine_id" not in frame:
        raise ValueError("latency bench requires nonempty rows with real engine_id provenance")
    config = pipeline.config
    warm = frame if warmup_frame is None else warmup_frame
    if warm.empty:
        raise ValueError("warmup_frame must be nonempty")
    modes: dict[str, dict[str, StageLatency]] = {}
    results: dict[str, list[dict[str, object]]] = {}
    budgets = {
        "ingestion_ms": config.latency_budget.ingestion_max_ms,
        "inference_ms": config.latency_budget.inference_max_ms,
        "optimization_ms": config.latency_budget.optimization_max_ms,
        "validation_ms": config.latency_budget.validation_max_ms,
        "pipeline_ms": config.latency_budget.pipeline_max_ms,
        "dashboard_ms": config.latency_budget.dashboard_max_ms,
    }
    for mode in ("fast", "thorough"):
        selected: Literal["fast", "thorough"] = mode
        for index in range(config.pipeline.benchmark_warmups):
            pipeline.recommend(warm.iloc[index % len(warm)], mode=selected)
        records = []
        total_samples = []
        for _ in range(config.pipeline.benchmark_repeats):
            for _, row in frame.iterrows():
                started = perf_counter_ns()
                result = pipeline.recommend(row, mode=selected)
                total = (perf_counter_ns() - started) / 1e6
                total_samples.append(total)
                records.append(
                    result.model_copy(
                        update={"timings": result.timings.model_copy(update={"pipeline_ms": total})}
                    )
                )
        results[mode.upper()] = [r.model_dump(mode="json") for r in records]
        modes[mode.upper()] = {}
        for index, (stage, budget) in enumerate(budgets.items()):
            samples = (
                total_samples
                if stage == "pipeline_ms"
                else [getattr(r.timings, stage) for r in records]
            )
            present = [
                (int(r.original_state["engine_id"]), float(value))
                for r, value in zip(records, samples, strict=True)
                if value is not None
            ]
            values = np.asarray([v for _, v in present], dtype=float)
            ids = np.asarray([i for i, _ in present], dtype=np.int64)
            interval = (
                engine_bootstrap_interval(
                    ids,
                    values,
                    seed=config.seed + index,
                    replicates=config.evaluation.bootstrap_replicates,
                    statistic=lambda x: float(np.quantile(x, 0.95)),
                )
                if len(values)
                else None
            )
            p95 = float(np.quantile(values, 0.95)) if len(values) else None
            modes[mode.upper()][stage] = StageLatency(
                count=len(values),
                engine_count=len(np.unique(ids)),
                p50_ms=float(np.quantile(values, 0.5)) if len(values) else None,
                p95_ms=p95,
                p99_ms=float(np.quantile(values, 0.99)) if len(values) else None,
                upper_budget_ms=budget,
                passed=None if p95 is None else p95 <= budget,
                p95_engine_ci=asdict(interval) if interval else None,
            )
    return LatencyReport(
        modes=modes,
        results=results,
        metadata={
            "config_hash": pipeline.config_hash,
            "model_version": pipeline.model_version,
            "seed": config.seed,
            "K": config.recourse.rate_horizon_steps,
            "k_max": config.recourse.k_max,
            "D_max": pipeline.engine.mahalanobis.max_distance,
            "warmups_excluded_per_mode": config.pipeline.benchmark_warmups,
            "repetitions": config.pipeline.benchmark_repeats,
            "scope": "warm serial backend; UI and startup unmeasured",
            **(metadata or {}),
        },
    )
