"""Tier 2: train-distribution Mahalanobis plausibility validator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from prescriptxai.validation.base import TierResult


@dataclass(frozen=True)
class MahalanobisValidator:
    """Regularized covariance fitted from rows of training engines only."""

    feature_names: tuple[str, ...]
    training_engine_ids: tuple[int, ...]
    mean: NDArray[np.float64]
    precision: NDArray[np.float64]
    max_distance: float
    regularization: float

    @classmethod
    def fit(
        cls,
        training_features: NDArray[np.float64],
        feature_names: tuple[str, ...],
        row_engine_ids: NDArray[np.int64],
        expected_training_engine_ids: tuple[int, ...],
        max_distance: float,
        regularization: float,
    ) -> MahalanobisValidator:
        """Fit mean and regularized covariance after checking engine provenance."""
        if training_features.ndim != 2 or training_features.shape[0] < 2:
            raise ValueError("training_features must be a 2-D matrix with at least two rows")
        if training_features.shape[1] != len(feature_names) or not feature_names:
            raise ValueError("feature_names must match the nonempty feature matrix width")
        if not np.isfinite(training_features).all():
            raise ValueError("training features must be finite")
        if row_engine_ids.ndim != 1 or len(row_engine_ids) != len(training_features):
            raise ValueError("row_engine_ids must match training feature rows")
        observed_ids = tuple(sorted(int(value) for value in np.unique(row_engine_ids)))
        if observed_ids != tuple(sorted(expected_training_engine_ids)):
            raise ValueError("covariance rows must contain exactly the declared training engines")
        if max_distance <= 0 or regularization <= 0:
            raise ValueError("max_distance and regularization must be positive")
        if len(feature_names) != len(set(feature_names)):
            raise ValueError("feature_names must be unique")
        mean = training_features.mean(axis=0)
        covariance = np.atleast_2d(np.cov(training_features, rowvar=False, ddof=1))
        covariance += np.eye(training_features.shape[1]) * regularization
        precision = np.linalg.pinv(covariance, hermitian=True)
        return cls(
            feature_names,
            observed_ids,
            mean.astype(float),
            precision.astype(float),
            max_distance,
            regularization,
        )

    def distance(self, candidate: NDArray[np.float64]) -> float:
        """Calculate the regularized Mahalanobis distance for one scaled vector."""
        if candidate.ndim != 1 or candidate.shape[0] != len(self.feature_names):
            raise ValueError("candidate vector shape does not match fitted feature names")
        if not np.isfinite(candidate).all():
            raise ValueError("candidate vector must be finite")
        difference = candidate - self.mean
        squared = float(difference @ self.precision @ difference)
        return float(np.sqrt(max(0.0, squared)))

    def validate(self, candidate: NDArray[np.float64]) -> TierResult:
        """Check candidate distance against configured empirical `D_max`."""
        value = self.distance(candidate)
        valid = value <= self.max_distance
        diagnostic = () if valid else (f"Mahalanobis distance {value:.6g} exceeds D_max",)
        return TierResult(valid, diagnostic, measurement=value, limit=self.max_distance)
