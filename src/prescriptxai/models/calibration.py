"""Validation-only probability calibration and reliability diagnostics."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray
from scipy.optimize import minimize
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import GroupKFold

from prescriptxai.config import ModelConfig
from prescriptxai.models.base import RiskEstimator


class ProbabilityCalibrator:
    """Monotone post-hoc calibration map fitted on validation-engine predictions only."""

    def __init__(self, method: str) -> None:
        if method not in {"isotonic", "sigmoid", "temperature"}:
            raise ValueError("calibration method must be isotonic, sigmoid, or temperature")
        self.method = method
        self.model: IsotonicRegression | None = None
        self.slope: float | None = None
        self.intercept: float | None = None
        self.temperature: float | None = None

    def fit(
        self, probabilities: NDArray[np.float64], labels: NDArray[np.int64]
    ) -> ProbabilityCalibrator:
        """Fit isotonic, Platt sigmoid, or temperature scaling using validation rows."""
        raw = _validate_probabilities(probabilities)
        target = np.asarray(labels, dtype=np.float64)
        if target.ndim != 1 or len(target) != len(raw):
            raise ValueError("calibration labels must be one-dimensional and match probabilities")
        if not np.isfinite(target).all() or not np.isin(target, [0.0, 1.0]).all():
            raise ValueError("calibration labels must be finite binary values")
        if np.unique(target).size != 2:
            raise ValueError("calibration requires both binary classes in validation engines")
        if self.method == "isotonic":
            self.model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            self.model.fit(raw, target)
        else:
            eps = np.finfo(np.float64).eps
            logits = np.log(np.clip(raw, eps, 1.0 - eps) / np.clip(1.0 - raw, eps, 1.0))
            if self.method == "sigmoid":

                def platt_loss(parameters: NDArray[np.float64]) -> float:
                    slope, intercept = parameters
                    calibrated = _sigmoid(slope * logits + intercept)
                    return float(
                        -np.mean(
                            target * np.log(calibrated + eps)
                            + (1 - target) * np.log(1 - calibrated + eps)
                        )
                    )

                fitted = minimize(
                    platt_loss,
                    np.asarray([1.0, 0.0]),
                    method="L-BFGS-B",
                    bounds=((0.0, None), (None, None)),
                )
                if not fitted.success or not np.isfinite(fitted.fun):
                    raise ValueError(f"Platt calibration failed: {fitted.message}")
                self.slope, self.intercept = float(fitted.x[0]), float(fitted.x[1])
            else:

                def temperature_loss(log_temperature: NDArray[np.float64]) -> float:
                    calibrated = _sigmoid(logits / np.exp(log_temperature[0]))
                    return float(
                        -np.mean(
                            target * np.log(calibrated + eps)
                            + (1 - target) * np.log(1 - calibrated + eps)
                        )
                    )

                fitted = minimize(
                    temperature_loss, np.zeros(1), method="L-BFGS-B", bounds=((-8.0, 8.0),)
                )
                if not fitted.success or not np.isfinite(fitted.fun):
                    raise ValueError(f"temperature calibration failed: {fitted.message}")
                self.temperature = float(np.exp(fitted.x[0]))
        return self

    def transform(self, probabilities: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply the fitted monotone calibration map."""
        raw = _validate_probabilities(probabilities)
        if self.method == "isotonic":
            if self.model is None:
                raise ValueError("calibrator has not been fitted")
            calibrated = np.asarray(self.model.predict(raw), dtype=np.float64)
        else:
            logits = np.log(np.clip(raw, 1e-12, 1 - 1e-12) / np.clip(1 - raw, 1e-12, 1))
            if self.method == "sigmoid":
                if self.slope is None or self.intercept is None:
                    raise ValueError("calibrator has not been fitted")
                calibrated = _sigmoid(self.slope * logits + self.intercept)
            else:
                if self.temperature is None:
                    raise ValueError("calibrator has not been fitted")
                calibrated = _sigmoid(logits / self.temperature)
        return np.asarray(calibrated, dtype=np.float64)

    def transform_tensor(self, probabilities: torch.Tensor) -> torch.Tensor:
        """Apply the fitted map while retaining gradients for differentiable predictors."""
        if not torch.is_floating_point(probabilities):
            raise ValueError("probability tensor must use a floating-point dtype")
        if probabilities.ndim != 1 or probabilities.numel() == 0:
            raise ValueError("probabilities must be a nonempty one-dimensional tensor")
        if not torch.isfinite(probabilities).all() or (
            (probabilities < 0) | (probabilities > 1)
        ).any():
            raise ValueError("probabilities must be finite and within [0, 1]")
        # Match the reported NumPy map, including its endpoint rule. Computing in float64
        # represents 1-1e-12 even for float32 predictors; .to() preserves their gradients.
        raw = probabilities.to(dtype=torch.float64)
        logits = torch.log(raw.clamp(1e-12, 1 - 1e-12) / (1 - raw).clamp(1e-12, 1))
        if self.method == "sigmoid":
            if self.slope is None or self.intercept is None:
                raise ValueError("calibrator has not been fitted")
            return torch.sigmoid(self.slope * logits + self.intercept)
        if self.method == "temperature":
            if self.temperature is None:
                raise ValueError("calibrator has not been fitted")
            return torch.sigmoid(logits / self.temperature)
        if self.model is None:
            raise ValueError("calibrator has not been fitted")
        x = torch.as_tensor(
            self.model.X_thresholds_, dtype=raw.dtype, device=raw.device
        )
        y = torch.as_tensor(
            self.model.y_thresholds_, dtype=raw.dtype, device=raw.device
        )
        if len(x) == 1:
            return y[0].expand_as(raw) + raw * 0
        indices = torch.searchsorted(x, raw.contiguous()).clamp(1, len(x) - 1)
        x0, x1 = x[indices - 1], x[indices]
        y0, y1 = y[indices - 1], y[indices]
        fraction = (
            (raw - x0) / (x1 - x0).clamp_min(torch.finfo(raw.dtype).tiny)
        ).clamp(0, 1)
        return y0 + fraction * (y1 - y0)


def _validate_probabilities(probabilities: NDArray[np.float64]) -> NDArray[np.float64]:
    """Require a nonempty finite vector in the unit interval."""
    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("probabilities must be a nonempty one-dimensional array")
    if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError("probabilities must be finite and within [0, 1]")
    return values


def _sigmoid(values: NDArray[np.float64]) -> NDArray[np.float64]:
    """Numerically stable logistic function."""
    clipped = np.clip(values, -700, 700)
    return np.asarray(1.0 / (1.0 + np.exp(-clipped)), dtype=np.float64)


def fit_probability_calibrator(
    probabilities: NDArray[np.float64], labels: NDArray[np.int64], method: str
) -> ProbabilityCalibrator:
    """Fit one calibration map on the caller-supplied validation partition."""
    return ProbabilityCalibrator(method).fit(probabilities, labels)


def calibration_diagnostics(
    labels: NDArray[np.int64], probabilities: NDArray[np.float64], bins: int = 10
) -> dict[str, object]:
    """Return Brier score, equal-width ECE, and per-bin reliability-curve measurements."""
    risk = _validate_probabilities(probabilities)
    target = np.asarray(labels, dtype=np.float64)
    if (
        target.ndim != 1
        or len(target) != len(risk)
        or not np.isfinite(target).all()
        or not np.isin(target, [0, 1]).all()
    ):
        raise ValueError("labels must be a matching one-dimensional binary vector")
    if bins < 2:
        raise ValueError("calibration bins must be at least 2")
    edges = np.linspace(0.0, 1.0, bins + 1)
    indices = np.minimum(np.digitize(risk, edges[1:-1], right=False), bins - 1)
    curve: list[dict[str, float | int]] = []
    ece = 0.0
    for index in range(bins):
        mask = indices == index
        count = int(mask.sum())
        if count == 0:
            continue
        confidence = float(risk[mask].mean())
        observed = float(target[mask].mean())
        ece += count / len(risk) * abs(confidence - observed)
        curve.append(
            {
                "bin": index,
                "count": count,
                "mean_probability": confidence,
                "fraction_positive": observed,
            }
        )
    return {
        "brier_score": float(np.mean((risk - target) ** 2)),
        "ece": float(ece),
        "reliability_curve": curve,
        "bin_count": bins,
        "sample_count": len(risk),
    }


def fit_group_calibrator(
    estimator: RiskEstimator,
    features: NDArray[np.float64],
    labels: NDArray[np.int64],
    engine_ids: NDArray[np.int64],
    config: ModelConfig,
) -> CalibratedClassifierCV:
    """Fit the legacy cross-validated calibrator with folds grouped by engine ID.

    Every calibration row belongs to a training engine. GroupKFold ensures an engine's cycles
    cannot appear in both the estimator-fit and held-out calibration fold. The Phase 2 trainer uses
    :func:`fit_probability_calibrator` on the dedicated validation-engine partition instead.
    """
    if features.shape[0] == 0:
        raise ValueError("cannot calibrate an empty training set")
    if engine_ids.ndim != 1 or len(engine_ids) != len(labels):
        raise ValueError("engine_ids must be one-dimensional and match labels")
    group_count = np.unique(engine_ids).size
    if group_count < config.calibration_folds:
        raise ValueError("training engines must be at least calibration_folds")
    if np.unique(labels).size != 2:
        raise ValueError("calibration requires both binary classes")
    splitter = GroupKFold(n_splits=config.calibration_folds)
    folds = list(splitter.split(features, labels, groups=engine_ids))
    calibrated = CalibratedClassifierCV(
        estimator=estimator,
        method=config.calibration_method,
        cv=folds,
        ensemble=True,
    )
    return calibrated.fit(features, labels)
