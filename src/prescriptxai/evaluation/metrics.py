"""Evaluation summaries with separate model and physical validity rates."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field

import numpy as np
from numpy.typing import NDArray
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
    counterfactual_signs: Mapping[str, int] = field(default_factory=dict)
    frozen_feature_violations: int = 0
    actuator_bound_violations: int = 0
    rate_limit_violations: int = 0
    recourse_feasible: bool = False
    true_model_grid_ms: float = 0.0
    true_model_evaluations: int = 0
    inference_ms: float | None = None
    backend_pipeline_ms: float | None = None
    effective_solver_settings: Mapping[str, int | float | bool | str | None] = field(
        default_factory=dict
    )
    candidate_state: Mapping[str, float] = field(default_factory=dict)
    final_mahalanobis_distance: float | None = None
    engineering_only_fallback: bool = False
    dependent_sensor_count: int | None = None
    dependent_residual_violation_count: int | None = None
    searched_candidate_states: tuple[Mapping[str, float], ...] = ()


@dataclass(frozen=True)
class EngineBootstrapInterval:
    """Percentile confidence interval resampling whole engines, not individual cycles."""

    estimate: float
    lower: float
    upper: float
    engine_count: int
    observation_count: int
    replicate_count: int
    seed: int


def engine_bootstrap_interval(
    engine_ids: Sequence[int],
    values: Sequence[float | bool],
    *,
    seed: int,
    replicates: int = 2_000,
    confidence: float = 0.95,
    statistic: Callable[[NDArray[np.float64]], float] = np.mean,
) -> EngineBootstrapInterval:
    """Compute a deterministic percentile interval by resampling engine clusters.

    Every state for a sampled engine is carried into that replicate, including repeated copies
    when the engine is sampled more than once. This preserves within-engine dependence.
    """
    engines = np.asarray(engine_ids)
    observations = np.asarray(values, dtype=np.float64)
    if engines.ndim != 1 or observations.ndim != 1 or engines.shape != observations.shape:
        raise ValueError("engine_ids and values must be matching one-dimensional vectors")
    if len(engines) == 0:
        raise ValueError("engine bootstrap requires at least one observation")
    if not np.isfinite(engines.astype(np.float64)).all() or not np.isfinite(observations).all():
        raise ValueError("engine IDs and values must be finite")
    if replicates < 100:
        raise ValueError("replicates must be at least 100")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    unique_engines = np.unique(engines)
    grouped = {
        engine: observations[engines == engine]
        for engine in unique_engines
    }
    rng = np.random.default_rng(seed)
    estimates: NDArray[np.float64] = np.empty(replicates, dtype=np.float64)
    for index in range(replicates):
        sampled = rng.choice(unique_engines, size=len(unique_engines), replace=True)
        sample = np.concatenate([grouped[engine] for engine in sampled])
        estimates[index] = float(statistic(sample))
    estimate = float(statistic(observations))
    if not np.isfinite(estimates).all() or not np.isfinite(estimate):
        raise ValueError("bootstrap statistic must return finite values")
    tail = (1.0 - confidence) / 2.0
    lower, upper = np.quantile(estimates, [tail, 1.0 - tail])
    return EngineBootstrapInterval(
        estimate=estimate,
        lower=float(lower),
        upper=float(upper),
        engine_count=len(unique_engines),
        observation_count=len(observations),
        replicate_count=replicates,
        seed=seed,
    )


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
    recourse_feasibility_rate: MetricResult
    successful_recourse_count: int
    successful_recourse_rate: MetricResult
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
    *,
    inference_samples_ms: Sequence[float] | None = None,
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
    recourse_feasibility_rate = rate(lambda record: record.recourse_feasible)
    successful_records = [
        record
        for record in records
        if record.model_valid
        and record.recourse_feasible
        and record.tier2_plausible
        and record.tier3_engineering_valid
        and record.tier4_coupling_valid
    ]
    successful_recourse_rate = rate(
        lambda record: (
            record.model_valid
            and record.recourse_feasible
            and record.tier2_plausible
            and record.tier3_engineering_valid
            and record.tier4_coupling_valid
        )
    )
    average_sparsity = (
        float(np.mean([record.changed_features for record in successful_records]))
        if successful_records
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
                and record.recourse_feasible
                and record.tier3_engineering_valid
                and record.tier4_coupling_valid
            )
        ),
        "omit_tier3": rate(
            lambda record: (
                record.model_valid
                and record.recourse_feasible
                and record.tier2_plausible
                and record.tier4_coupling_valid
            )
        ),
        "omit_tier4": rate(
            lambda record: (
                record.model_valid
                and record.recourse_feasible
                and record.tier2_plausible
                and record.tier3_engineering_valid
            )
        ),
        "model_only": valid_rate,
    }
    latency = {
        "ingestion": summarize_latency(
            [] if ingestion_ms is None else [ingestion_ms], None, config.ingestion_max_ms
        ),
        "inference_per_row": summarize_latency(
            (
                inference_samples_ms
                if inference_samples_ms is not None
                else ([] if inference_ms_per_row is None else [inference_ms_per_row])
            ),
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
            [
                record.backend_pipeline_ms
                if record.backend_pipeline_ms is not None
                else record.optimization_ms + record.validation_ms
                for record in records
            ],
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
        recourse_feasibility_rate=MetricResult(
            recourse_feasibility_rate, "reported separately", None
        ),
        successful_recourse_count=len(successful_records),
        successful_recourse_rate=MetricResult(
            successful_recourse_rate, "reported separately", None
        ),
        physical_plausibility_rate=MetricResult(
            physical_rate, "joint Tiers 2–4; no separate synopsis target", None
        ),
        tier2_plausibility_rate=_rate(tier2_rate, config.physical_plausibility_rate, ">="),
        tier3_engineering_rate=MetricResult(tier3_rate, "no target specified", None),
        tier4_coupling_rate=MetricResult(tier4_rate, "no target specified", None),
        average_sparsity=_rate(average_sparsity, float(config.average_sparsity_max), "<="),
        mean_risk_reduction=_rate(risk_reduction, config.mean_risk_drop_min, ">="),
        ablation_acceptance_rates=ablations,
        latency=latency,
    )
