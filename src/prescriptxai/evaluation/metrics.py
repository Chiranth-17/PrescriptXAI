"""Evaluation summaries with separate model and physical validity rates."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)

from prescriptxai.config import EvaluationConfig
from prescriptxai.evaluation.latency import LatencyMetric, summarize_latency


def predictor_metrics(
    labels: np.ndarray, probabilities: np.ndarray, tau_danger: float
) -> dict[str, object]:
    """Compute held-out binary-prediction and calibrated-probability metrics."""
    target = np.asarray(labels, dtype=np.int64)
    risk = np.asarray(probabilities, dtype=np.float64)
    if target.ndim != 1 or risk.ndim != 1 or len(target) != len(risk) or len(target) == 0:
        raise ValueError("labels and probabilities must be nonempty matching vectors")
    if not np.isin(target, [0, 1]).all():
        raise ValueError("labels must contain only binary values")
    if not np.isfinite(risk).all() or ((risk < 0) | (risk > 1)).any():
        raise ValueError("probabilities must be finite and within [0, 1]")
    if not 0 <= tau_danger <= 1:
        raise ValueError("tau_danger must be in [0, 1]")
    predicted = (risk >= tau_danger).astype(np.int64)
    matrix = confusion_matrix(target, predicted, labels=[0, 1])
    positives = int(target.sum())
    high_risk_recall = float(matrix[1, 1] / positives) if positives else None
    both_classes = np.unique(target).size == 2
    return {
        "sample_count": len(target),
        "positive_count": positives,
        "negative_count": int(len(target) - positives),
        "auroc": float(roc_auc_score(target, risk)) if both_classes else None,
        "auprc": float(average_precision_score(target, risk)) if positives else None,
        "f1_at_tau_danger": float(f1_score(target, predicted, zero_division=0)),
        "brier_score": float(np.mean((risk - target) ** 2)),
        "confusion_matrix_labels_0_1": matrix.astype(int).tolist(),
        "high_risk_recall_at_tau_danger": high_risk_recall,
        "tau_danger": float(tau_danger),
    }


def surrogate_fidelity(
    teacher: np.ndarray,
    surrogate: np.ndarray,
    tau_safe: float = 0.2,
    tau_danger: float = 0.8,
) -> dict[str, object]:
    """Measure probability agreement and threshold decisions on held-out rows."""
    teacher_values = np.asarray(teacher, dtype=np.float64)
    surrogate_values = np.asarray(surrogate, dtype=np.float64)
    if (
        teacher_values.ndim != 1
        or surrogate_values.ndim != 1
        or len(teacher_values) != len(surrogate_values)
        or len(teacher_values) == 0
    ):
        raise ValueError("teacher and surrogate must be nonempty matching probability vectors")
    for name, values in (("teacher", teacher_values), ("surrogate", surrogate_values)):
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError(f"{name} probabilities must be finite and within [0, 1]")
    if not 0 <= tau_safe < tau_danger <= 1:
        raise ValueError("thresholds must satisfy 0 <= tau_safe < tau_danger <= 1")
    correlation = spearmanr(teacher_values, surrogate_values).statistic
    return {
        "sample_count": len(teacher_values),
        "mae": float(np.mean(np.abs(teacher_values - surrogate_values))),
        "rank_correlation": float(correlation) if np.isfinite(correlation) else None,
        "agreement_at_tau_safe": float(
            np.mean((teacher_values <= tau_safe) == (surrogate_values <= tau_safe))
        ),
        "agreement_at_tau_danger": float(
            np.mean((teacher_values >= tau_danger) == (surrogate_values >= tau_danger))
        ),
        "tau_safe": float(tau_safe),
        "tau_danger": float(tau_danger),
    }


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
