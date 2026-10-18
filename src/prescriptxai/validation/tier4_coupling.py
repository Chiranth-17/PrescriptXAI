"""Tier 4: learned sensor coupling and configured relationship checks."""

from collections.abc import Mapping
from copy import deepcopy

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.metrics import r2_score

from prescriptxai.constraints.coupling import (
    SensorCouplingModel,
    evaluate_rule,
    validate_couplings,
)
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.validation.base import CheckResult, TierResult


def validate_sensor_coupling(
    candidate: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
    coupling: SensorCouplingModel | None = None,
) -> TierResult:
    """Evaluate learned residual bounds and configured coupling rules."""
    if coupling is None:
        rules = tuple(evaluate_rule(candidate, rule) for rule in taxonomy.coupling_rules)
        valid, diagnostics = validate_couplings(candidate, taxonomy)
    else:
        if not getattr(coupling, "calibration_engine_ids", ()):
            return TierResult.skipped("coupling residual thresholds lack validation calibration")
        rules = coupling.evaluate_all_constraints(candidate, taxonomy)
        valid = bool(rules) and all(rule.passed for rule in rules)
        diagnostics = tuple(rule.explanation for rule in rules if not rule.passed)
    checks = tuple(
        CheckResult(
            rule.name,
            rule.passed,
            rule.margin,
            rule.explanation,
        )
        for rule in rules
    )
    return TierResult(
        valid,
        diagnostics,
        margin=min((rule.margin for rule in rules), default=None),
        evidence_level="E3",
        checks=checks,
    )


def calibrate_coupling_thresholds(
    coupling: SensorCouplingModel,
    validation_frame: pd.DataFrame,
    validation_engine_ids: tuple[int, ...],
    *,
    reference_distribution: str,
    min_rul: int,
    evaluation_engine_ids: tuple[int, ...] = (),
) -> SensorCouplingModel:
    """Copy propagation unchanged and calibrate residual scales on held-out validation engines.

    Absolute residual limits remain ``k * std(validation residuals)``. Bias, R² and exceedances
    are recorded, so a bad fit or a biased residual distribution is not concealed by calibration.
    """
    if "engine_id" not in validation_frame or validation_frame.empty:
        raise ValueError("validation calibration requires nonempty engine-provenance rows")
    declared = tuple(sorted(validation_engine_ids))
    observed = tuple(sorted(int(value) for value in validation_frame.engine_id.unique()))
    if not declared or len(set(declared)) != len(declared) or observed != declared:
        raise ValueError("calibration rows must contain exactly the validation engines")
    if set(declared) & (set(coupling.training_engine_ids) | set(evaluation_engine_ids)):
        raise ValueError("validation calibration engines overlap fitting or evaluation engines")
    frame = validation_frame
    if reference_distribution == "healthy_to_moderate":
        if "rul" not in frame:
            raise ValueError("healthy-to-moderate calibration requires RUL")
        frame = frame.loc[frame.rul > min_rul]
    elif reference_distribution != "all_cycles":
        raise ValueError("unknown coupling calibration reference distribution")
    if len(frame) < 2:
        raise ValueError("calibration reference must contain at least two rows")
    required = coupling.predictor_features + coupling.dependent_features
    values = frame.loc[:, required].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("coupling calibration features must be finite")
    calibrated = deepcopy(coupling)
    metrics: dict[str, object] = {}
    predictors = frame.loc[:, coupling.predictor_features].to_numpy(dtype=float)
    for target in coupling.dependent_features:
        actual = frame[target].to_numpy(dtype=float)
        predicted = np.asarray(coupling.models[target].predict(predictors), dtype=float)
        residual = actual - predicted
        standard_deviation = float(np.std(residual, ddof=1))
        calibrated.residual_std[target] = standard_deviation
        threshold = coupling.residual_sigma_k * standard_deviation
        metrics[target] = {
            "r2": float(r2_score(actual, predicted)),
            "residual_mean": float(np.mean(residual)),
            "residual_std": standard_deviation,
            "threshold": threshold,
            "share_beyond_threshold": float(np.mean(np.abs(residual) > threshold)),
        }
    calibrated.calibration_engine_ids = declared
    calibrated.calibration_report = {
        "engine_ids": list(declared),
        "engine_count": len(declared),
        "reference_engine_ids": sorted(int(value) for value in frame.engine_id.unique()),
        "row_count": len(frame),
        "reference_distribution": reference_distribution,
        "min_rul_exclusive": min_rul,
        "sigma_multiplier": coupling.residual_sigma_k,
        "per_sensor": metrics,
    }
    return calibrated


def coupling_pass_mask(
    rows: NDArray[np.float64],
    feature_names: tuple[str, ...],
    initial: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
    coupling: SensorCouplingModel | None,
) -> NDArray[np.bool_]:
    """Prefilter grid rows with batched true teachers; exact scalar checks decide acceptance.

    Omitted dependent channels retain their observed initial values. Roundoff-near-boundary
    rows remain eligible for exact scalar checking, so vectorization never relaxes final limits.
    """
    values: dict[str, NDArray[np.float64]] = {
        name: np.full(len(rows), value, dtype=float) for name, value in initial.items()
    }
    values.update({name: rows[:, index] for index, name in enumerate(feature_names)})
    passed: NDArray[np.bool_] = np.ones(len(rows), dtype=bool)
    if coupling is not None:
        if not getattr(coupling, "calibration_engine_ids", ()):
            return np.zeros(len(rows), dtype=bool)
        predictors = np.column_stack([values[name] for name in coupling.predictor_features])
        for target in coupling.dependent_features:
            predicted = np.asarray(coupling.models[target].predict(predictors), dtype=float)
            actual = values[target]
            limit = coupling.residual_sigma_k * coupling.residual_std[target]
            residual = np.abs(actual - predicted)
            rounding = np.spacing(np.abs(actual) + np.abs(predicted) + 1) * (
                len(coupling.predictor_features) + 1
            )
            passed &= residual <= limit + 1e-12 + rounding
    elif not taxonomy.coupling_rules:
        return np.zeros(len(rows), dtype=bool)
    for rule in taxonomy.coupling_rules:
        if rule.feature_a not in values or rule.feature_b not in values:
            if coupling is None:
                passed[:] = False
            continue
        a, b = values[rule.feature_a], values[rule.feature_b]
        if rule.relation == "less_than":
            margin = b - a + rule.tolerance
        elif rule.relation == "greater_than":
            margin = a - b + rule.tolerance
        else:
            assert rule.slope is not None and rule.intercept is not None
            margin = rule.tolerance - np.abs(b - (rule.slope * a + rule.intercept))
        passed &= margin >= -1e-12 - np.spacing(np.abs(a) + np.abs(b) + 1)
    return passed
