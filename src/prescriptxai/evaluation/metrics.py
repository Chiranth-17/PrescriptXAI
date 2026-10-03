"""Evaluation summaries with separate model and physical validity rates."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass

import numpy as np

from prescriptxai.config import EvaluationConfig
from prescriptxai.evaluation.latency import LatencyMetric, summarize_latency


@dataclass(frozen=True)
class EvaluationRecord:
    """One high-risk held-out machine-state evaluation."""

    engine_id: int
    cycle: int
    initial_risk: float
    final_risk: float
    model_valid: bool
    tier2_plausible: bool
    tier3_engineering_valid: bool
    tier4_coupling_valid: bool
    changed_features: int
    optimization_ms: float
    validation_ms: float
    solver_success: bool
    message: str


@dataclass(frozen=True)
class MetricResult:
    """Observed value and configurable target assessment."""

    value: float | None
    target: str
    passed: bool | None


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregated metrics, denominators, latency, and ablation acceptance rates."""

    eligible_high_risk_states: int
    evaluated_states: int
    model_valid_count: int
    physically_plausible_count: int
    recourse_validity_rate: MetricResult
    physical_plausibility_rate: MetricResult
    tier2_plausibility_rate: MetricResult
    tier3_engineering_rate: MetricResult
    tier4_coupling_rate: MetricResult
    average_sparsity: MetricResult
    mean_risk_reduction: MetricResult
    ablation_acceptance_rates: Mapping[str, float | None]
    latency: Mapping[str, LatencyMetric]

    def to_dict(self) -> dict[str, object]:
        """Convert nested metric dataclasses into JSON-ready mappings."""
        return asdict(self)


def _rate(value: float | None, target: float, comparator: str) -> MetricResult:
    """Create a pass/fail rate using a configured inclusive threshold."""
    passed = None if value is None else (value >= target if comparator == ">=" else value <= target)
    return MetricResult(value, f"{comparator} {target:g}", passed)


def calculate_metrics(
    records: tuple[EvaluationRecord, ...],
    eligible_high_risk_states: int,
    inference_ms_per_row: float | None,
    ingestion_ms: float | None,
    config: EvaluationConfig,
) -> EvaluationSummary:
    """Calculate actual-run metrics; no attempts produce unmeasured values, not fabricated zeros."""
    count = len(records)

    def rate(predicate: Callable[[EvaluationRecord], bool]) -> float | None:
        """Compute a Boolean record rate, leaving empty samples unmeasured."""
        if count == 0:
            return None
        return float(np.mean([predicate(record) for record in records]))

    valid_rate = rate(lambda record: record.model_valid)
    physical_rate = rate(
        lambda record: (
            record.tier2_plausible
            and record.tier3_engineering_valid
            and record.tier4_coupling_valid
        )
    )
    tier2_rate = rate(lambda record: record.tier2_plausible)
    tier3_rate = rate(lambda record: record.tier3_engineering_valid)
    tier4_rate = rate(lambda record: record.tier4_coupling_valid)
    valid_records = [record for record in records if record.model_valid]
    average_sparsity = (
        float(np.mean([record.changed_features for record in valid_records]))
        if valid_records
        else None
    )
    risk_reduction = (
        float(np.mean([record.initial_risk - record.final_risk for record in records]))
        if records
        else None
    )
    ablations = {
        "omit_tier2": rate(
            lambda record: (
                record.model_valid
                and record.tier3_engineering_valid
                and record.tier4_coupling_valid
            )
        ),
        "omit_tier3": rate(
            lambda record: (
                record.model_valid and record.tier2_plausible and record.tier4_coupling_valid
            )
        ),
        "omit_tier4": rate(
            lambda record: (
                record.model_valid and record.tier2_plausible and record.tier3_engineering_valid
            )
        ),
        "model_only": valid_rate,
    }
    latency = {
        "ingestion": summarize_latency(
            [] if ingestion_ms is None else [ingestion_ms], None, config.ingestion_max_ms
        ),
        "inference_per_row": summarize_latency(
            [] if inference_ms_per_row is None else [inference_ms_per_row],
            None,
            config.inference_max_ms,
        ),
        "optimization": summarize_latency(
            [record.optimization_ms for record in records],
            config.optimization_min_ms,
            config.optimization_max_ms,
        ),
        "validation": summarize_latency(
            [record.validation_ms for record in records], None, config.validation_max_ms
        ),
        "pipeline": summarize_latency(
            [record.optimization_ms + record.validation_ms for record in records],
            config.pipeline_min_ms,
            config.pipeline_max_ms,
        ),
        "dashboard": summarize_latency([], None, config.dashboard_max_ms),
    }
    return EvaluationSummary(
        eligible_high_risk_states=eligible_high_risk_states,
        evaluated_states=count,
        model_valid_count=sum(record.model_valid for record in records),
        physically_plausible_count=sum(
            record.tier2_plausible
            and record.tier3_engineering_valid
            and record.tier4_coupling_valid
            for record in records
        ),
        recourse_validity_rate=_rate(valid_rate, config.recourse_validity_rate, ">="),
        physical_plausibility_rate=_rate(physical_rate, config.physical_plausibility_rate, ">="),
        tier2_plausibility_rate=MetricResult(
            tier2_rate, "no separate Tier 2 target specified", None
        ),
        tier3_engineering_rate=MetricResult(tier3_rate, "no target specified", None),
        tier4_coupling_rate=MetricResult(tier4_rate, "no target specified", None),
        average_sparsity=_rate(average_sparsity, float(config.average_sparsity_max), "<="),
        mean_risk_reduction=_rate(risk_reduction, config.mean_risk_drop_min, ">="),
        ablation_acceptance_rates=ablations,
        latency=latency,
    )
