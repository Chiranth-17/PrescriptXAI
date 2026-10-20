"""Measured latency summaries against configured targets."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import TYPE_CHECKING, Any, Literal

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
    from prescriptxai.evaluation.experiments import StudyConfig
    from prescriptxai.pipeline import PrescriptXAI


def benchmark_serial_checkpointed(
    pipeline: PrescriptXAI,
    frame: pd.DataFrame,
    study: StudyConfig,
    directory: Path,
    *,
    allow_uncommitted_source: bool = False,
) -> dict[str, Any]:
    """Measure actual warm serial public calls with a transactional checkpoint per sample.

    Warmups are repeated after resume and excluded. Quality/training/test workers must be stopped
    by the orchestrator before this stage. No result cache replaces recommendation execution.
    """
    import json
    import sqlite3

    from prescriptxai.evaluation.experiments import (
        content_hash,
        file_hash,
        mark_stage_complete,
        runtime_manifest,
        source_revision,
    )
    from prescriptxai.evaluation.metrics import engine_bootstrap_interval
    from prescriptxai.evaluation.runner import raw_telemetry

    if frame.empty or not {"engine_id", "cycle"}.issubset(frame):
        raise ValueError("serial benchmark requires real nonempty engine/cycle rows")
    directory.mkdir(parents=True, exist_ok=True)
    artifacts = [
        pipeline.config.artifacts.model,
        pipeline.config.artifacts.mahalanobis,
        pipeline.config.pipeline.taxonomy_path,
    ]
    if pipeline.config.artifacts.coupling is not None:
        artifacts.append(pipeline.config.artifacts.coupling)
    source = source_revision(require_clean=not allow_uncommitted_source)
    origin_path = directory / "manifest.json"
    if origin_path.exists():
        origin = json.loads(origin_path.read_text(encoding="utf-8"))
        if origin["git_hash"] != source or origin["configuration"] != study.model_dump(mode="json"):
            raise ValueError("latency source/study differs from original run manifest")
    signature = content_hash(
        {
            "config": pipeline.config.model_dump(mode="json"),
            "study": study.model_dump(mode="json"),
            "rows": frame.to_dict(orient="records"),
            "source": source,
            "allow_uncommitted_source": allow_uncommitted_source,
            "runtime": runtime_manifest(),
            "artifact_hashes": {str(p): file_hash(p) for p in artifacts},
            "code_hashes": {str(p): file_hash(p) for p in Path(__file__).parents[1].rglob("*.py")},
        }
    )
    identity = directory / "latency-identity.json"
    if (
        identity.exists()
        and json.loads(identity.read_text(encoding="utf-8"))["sha256"] != signature
    ):
        raise ValueError("latency resume workload/config mismatch")
    identity.write_text(json.dumps({"sha256": signature}), encoding="utf-8")
    database = sqlite3.connect(directory / "latency.sqlite3")
    database.execute(
        "CREATE TABLE IF NOT EXISTS samples "
        "(mode TEXT, idx INTEGER, payload TEXT, PRIMARY KEY(mode,idx))"
    )
    budgets = {
        "ingestion_ms": pipeline.config.latency_budget.ingestion_max_ms,
        "inference_ms": pipeline.config.latency_budget.inference_max_ms,
        "optimization_ms": pipeline.config.latency_budget.optimization_max_ms,
        "validation_ms": pipeline.config.latency_budget.validation_max_ms,
        "pipeline_ms": pipeline.config.latency_budget.pipeline_max_ms,
        "dashboard_ms": pipeline.config.latency_budget.dashboard_max_ms,
    }
    result: dict[str, Any] = {
        "modes": {},
        "warmups_excluded_per_invocation_per_mode": study.latency_warmups_per_mode,
        "workload": "all validation alerts, fixed engine/cycle order, cycled",
        "scope": "warm serial backend; UI/startup unmeasured",
        "identity": signature,
        "allow_uncommitted_source": allow_uncommitted_source,
        "labels": {
            "config_hash": pipeline.config_hash,
            "git_hash": source,
            "protocol": next(iter(study.d_max_versions)),
            "k_max": pipeline.config.recourse.k_max,
            "K": pipeline.config.recourse.rate_horizon_steps,
            "D_max_version": next(iter(study.d_max_versions)),
            "D_max": pipeline.engine.mahalanobis.max_distance,
            "population": "development_all_alerts_repeated_fixed_order",
        },
    }
    try:
        for mode in ("fast", "thorough"):
            selected: Literal["fast", "thorough"] = mode
            done = {i for (i,) in database.execute("SELECT idx FROM samples WHERE mode=?", (mode,))}
            if len(done) < study.latency_runs_per_mode:
                for i in range(study.latency_warmups_per_mode):
                    pipeline.recommend(raw_telemetry(frame.iloc[i % len(frame)]), mode=selected)
            for i in range(study.latency_runs_per_mode):
                if i in done:
                    continue
                state = raw_telemetry(frame.iloc[i % len(frame)])
                start = perf_counter_ns()
                recommendation = pipeline.recommend(state, mode=selected)
                total = (perf_counter_ns() - start) / 1e6
                payload = {
                    "engine_id": int(state["engine_id"]),
                    "cycle": int(state["cycle"]),
                    "status": recommendation.status,
                    "true_risk": recommendation.risk_after,
                    "timings": {**recommendation.timings.model_dump(), "pipeline_ms": total},
                }
                with database:
                    database.execute(
                        "INSERT INTO samples VALUES (?,?,?)", (mode, i, json.dumps(payload))
                    )
            records = [
                json.loads(p)
                for (p,) in database.execute(
                    "SELECT payload FROM samples WHERE mode=? ORDER BY idx", (mode,)
                )
            ]
            stages = {}
            for stage, budget in budgets.items():
                available = [
                    (r["engine_id"], r["timings"][stage])
                    for r in records
                    if r["timings"].get(stage) is not None
                ]
                ids = np.asarray([v[0] for v in available])
                values = np.asarray([v[1] for v in available], dtype=float)
                p95 = float(np.quantile(values, 0.95)) if len(values) else None
                interval = (
                    engine_bootstrap_interval(
                        ids,
                        values,
                        seed=study.diagnostic_seed,
                        replicates=study.bootstrap_replicates,
                        confidence=study.bootstrap_confidence,
                        statistic=lambda x: float(np.quantile(x, 0.95)),
                    )
                    if len(values)
                    else None
                )
                stages[stage] = {
                    "count": len(values),
                    "engine_count": len(np.unique(ids)),
                    "p50_ms": float(np.quantile(values, 0.5)) if len(values) else None,
                    "p95_ms": p95,
                    "p99_ms": float(np.quantile(values, 0.99)) if len(values) else None,
                    "upper_budget_ms": budget,
                    "passed": None if p95 is None else p95 <= budget,
                    "p95_engine_ci": asdict(interval) if interval else None,
                }
            result["modes"][mode.upper()] = stages
    finally:
        database.close()
    (directory / "latency.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8"
    )
    mark_stage_complete(
        directory, "latency", source, study.latency_runs_per_mode * len(result["modes"])
    )
    return result


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
