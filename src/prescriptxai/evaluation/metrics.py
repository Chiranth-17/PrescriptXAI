"""Evaluation summaries with separate model and physical validity rates."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

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
from prescriptxai.validation.base import EvidenceLevel


def predictor_metrics(
    labels: np.ndarray, probabilities: np.ndarray, tau_danger: float
) -> dict[str, object]:
    """Compute held-out binary-prediction and calibrated-probability metrics."""
    target = np.asarray(labels, dtype=np.float64)
    risk = np.asarray(probabilities, dtype=np.float64)
    if target.ndim != 1 or risk.ndim != 1 or len(target) != len(risk) or len(target) == 0:
        raise ValueError("labels and probabilities must be nonempty matching vectors")
    if not np.isfinite(target).all() or not np.isin(target, [0, 1]).all():
        raise ValueError("labels must contain only binary values")
    target = target.astype(np.int64)
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
    # None identifies historical unlabelled records; new evaluations retain the validated level.
    evidence_level: EvidenceLevel | None = None


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
    grouped = {engine: observations[engines == engine] for engine in unique_engines}
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


def clustered_ratio_interval(
    engine_ids: Sequence[int],
    numerators: Sequence[float],
    denominators: Sequence[float],
    *,
    seed: int,
    replicates: int,
    confidence: float,
) -> dict[str, float | int | None]:
    r"""Estimate ``sum(n)/sum(d)`` by resampling whole engines jointly.

    Zero-denominator engines remain in the sampling frame. Replicates whose total denominator
    is zero are explicitly counted; an empty conditional population has no fabricated estimate.
    The sufficient-statistic aggregation is exactly equivalent to carrying every state and every
    solver-seed repetition for each sampled engine into the bootstrap replicate.
    """
    ids = np.asarray(engine_ids, dtype=float)
    n, d = np.asarray(numerators, dtype=float), np.asarray(denominators, dtype=float)
    if ids.ndim != 1 or ids.shape != n.shape or ids.shape != d.shape:
        raise ValueError("engine IDs, numerators and denominators must be matching vectors")
    if not np.isfinite(ids).all() or not np.isfinite(n).all() or not np.isfinite(d).all():
        raise ValueError("bootstrap inputs must be finite")
    if np.any(ids % 1) or np.any(d < 0) or np.any((d == 0) & (n != 0)):
        raise ValueError("IDs must be integers and zero denominators must have zero numerator")
    if replicates < 100 or not 0 < confidence < 1:
        raise ValueError("bootstrap requires >=100 replicates and confidence in (0,1)")
    unique = np.unique(ids)
    total_d = float(d.sum())
    if not len(unique) or total_d == 0:
        return {
            "estimate": None,
            "lower": None,
            "upper": None,
            "engine_count": len(unique),
            "observation_count": len(ids),
            "denominator": total_d,
            "replicate_count": 0,
            "zero_denominator_replicates": replicates,
            "seed": seed,
        }
    aggregate = np.asarray([[n[ids == unit].sum(), d[ids == unit].sum()] for unit in unique])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(unique), size=(replicates, len(unique)))
    totals = aggregate[draws].sum(axis=1)
    valid = totals[:, 1] > 0
    estimates = totals[valid, 0] / totals[valid, 1]
    tail = (1 - confidence) / 2
    lower, upper = np.quantile(estimates, [tail, 1 - tail])
    return {
        "estimate": float(n.sum() / total_d),
        "lower": float(lower),
        "upper": float(upper),
        "engine_count": len(unique),
        "observation_count": len(ids),
        "denominator": total_d,
        "replicate_count": int(valid.sum()),
        "zero_denominator_replicates": int((~valid).sum()),
        "seed": seed,
    }


def action_sparsity(
    before: Mapping[str, float],
    after: Mapping[str, float],
    controls: Sequence[str],
    scales: Mapping[str, float],
    tolerance: float,
) -> int:
    """Count directly changed actions using the configured scaled change tolerance."""
    if tolerance < 0 or not np.isfinite(tolerance):
        raise ValueError("change tolerance must be finite and nonnegative")
    if any(not np.isfinite(scales[name]) or scales[name] <= 0 for name in controls):
        raise ValueError("scales must be positive and finite")
    values = [(after[name] - before[name]) / scales[name] for name in controls]
    if not np.isfinite(values).all() or any(scales[name] <= 0 for name in controls):
        raise ValueError("changes must be finite and scales positive")
    return int(np.count_nonzero(np.abs(values) > tolerance))


def state_proximity(
    before: Mapping[str, float],
    after: Mapping[str, float],
    scales: Mapping[str, float],
) -> tuple[float, float]:
    r"""Return L1 distance over retained model features, in raw and scaled units.

    Raw mixed-unit L1 is a descriptive quantity, not a dimensionless physical cost. Dependent
    changes are included; action sparsity is reported separately over directly optimized inputs.
    """
    raw = np.asarray([after[name] - before[name] for name in scales], dtype=float)
    scale = np.asarray(list(scales.values()), dtype=float)
    if not np.isfinite(raw).all() or not np.isfinite(scale).all() or (scale <= 0).any():
        raise ValueError("proximity requires finite states and positive finite scales")
    return float(np.abs(raw).sum()), float(np.abs(raw / scale).sum())


def experiment_metric_values(
    records: Sequence[Mapping[str, Any]],
    headline_safe_threshold: float,
) -> dict[str, tuple[list[float], list[float]]]:
    """Build numerator/denominator vectors without dropping failed queries."""
    n = len(records)
    ones = [1.0] * n
    before = [float(r["risk_before"]) for r in records]
    after = [float(r["risk_after"]) for r in records]
    if not 0 < headline_safe_threshold < 1:
        raise ValueError("safe threshold must be in (0,1)")
    if any(not np.isfinite(p) or not 0 <= p <= 1 for p in before + after):
        raise ValueError("probabilities must be finite and in [0,1]")
    returned = [float(bool(r["returned"])) for r in records]
    plausible = [float(bool(r["tier2"])) for r in records]
    valid = [float(p <= headline_safe_threshold) for p in after]
    tier3, tier4 = ([float(bool(r[key])) for r in records] for key in ("tier3", "tier4"))
    sparsity = [float(r["sparsity"]) for r in records]
    values = {
        "validity": (valid, ones),
        "plausibility_all": (plausible, ones),
        "plausibility_returned": (
            [a * b for a, b in zip(plausible, returned, strict=True)],
            returned,
        ),
        "tier3": (tier3, ones),
        "tier4": (tier4, ones),
        "joint_tiers": (
            [a * b * c * d for a, b, c, d in zip(valid, plausible, tier3, tier4, strict=True)],
            ones,
        ),
        "joint": (
            [
                a * b * c * d * float(bool(r["action_feasible"]))
                for a, b, c, d, r in zip(valid, plausible, tier3, tier4, records, strict=True)
            ],
            ones,
        ),
        "target_relative_validity": (
            [float(float(r["risk_after"]) <= float(r["solver_tau_safe"])) for r in records],
            ones,
        ),
        "joint_target_relative": ([float(bool(r["joint"])) for r in records], ones),
        "sparsity_all": (sparsity, ones),
        "sparsity_returned": ([a * b for a, b in zip(sparsity, returned, strict=True)], returned),
        "risk_reduction": ([a - b for a, b in zip(before, after, strict=True)], ones),
        "raw_l1": ([float(r["raw_l1"]) for r in records], ones),
        "scaled_l1": ([float(r["scaled_l1"]) for r in records], ones),
        "immutable_violations": (
            [float(int(r["immutable_violations"]) > 0) for r in records],
            ones,
        ),
        "bound_violations": ([float(int(r["bound_violations"]) > 0) for r in records], ones),
        "rate_violations": ([float(int(r["rate_violations"]) > 0) for r in records], ones),
    }
    values["risk_gate_eligible"] = (
        [float(r["risk_before"] >= r["solver_tau_danger"]) for r in records],
        ones,
    )
    for status in ("NO_INTERVENTION", "RECOVERABLE", "PARTIAL", "ESCALATE"):
        values[status] = ([float(r["status"] == status) for r in records], ones)
    success = values["joint"][0]
    values["sparsity_success"] = ([a * b for a, b in zip(sparsity, success, strict=True)], success)
    values["proxy_sparsity"] = (
        [float(r.get("proxy_sparsity", r["sparsity"])) for r in records],
        ones,
    )
    available = [float(r.get("surrogate_after") is not None) for r in records]
    values["surrogate_MAE"] = (
        [
            abs(float(r["surrogate_after"]) - float(r["risk_after"]))
            if r.get("surrogate_after") is not None
            else 0.0
            for r in records
        ],
        available,
    )
    values["surrogate_false_safe_share_all"] = (
        [
            float(
                r.get("surrogate_after") is not None
                and r["surrogate_after"] <= headline_safe_threshold
                and r["risk_after"] > headline_safe_threshold
            )
            for r in records
        ],
        ones,
    )
    for stage in sorted({s for r in records for s in r["timings"]}):
        values[f"runtime_{stage}_mean"] = (
            [float(r["timings"].get(stage, 0.0)) for r in records],
            [float(stage in r["timings"]) for r in records],
        )
    for label, violations in (
        ("model_safe_and_immutable_violation", [r["immutable_violations"] > 0 for r in records]),
        ("model_safe_and_bound_violation", [r["bound_violations"] > 0 for r in records]),
        ("model_safe_and_T2_failure", [not r["tier2"] for r in records]),
    ):
        values[label] = ([float(a and b) for a, b in zip(valid, violations, strict=True)], ones)
    return values


def cumulative_funnel(
    records: Sequence[Mapping[str, Any]], safe_threshold: float
) -> dict[str, int]:
    """Count a cumulative alert-to-joint funnel and retain the all-query denominator."""
    bits: NDArray[np.bool_] = np.ones(len(records), dtype=bool)
    counts = {"alerts": len(records)}
    for label, flag in (
        ("candidate_returned", [bool(r["returned"]) for r in records]),
        ("tier1", [float(r["risk_after"]) <= safe_threshold for r in records]),
        ("tier2", [bool(r["tier2"]) for r in records]),
        ("tier3", [bool(r["tier3"]) for r in records]),
        ("tier4", [bool(r["tier4"]) for r in records]),
        ("joint", [bool(r["joint"]) for r in records]),
    ):
        bits &= np.asarray(flag, dtype=bool)
        counts[label] = int(bits.sum())
    return counts
