"""Shared predictor contract and input validation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class RiskEstimator(Protocol):
    """Estimator contract consumed by the calibration and training pipeline."""

    def fit(self, features: NDArray[np.float64], labels: NDArray[np.int64]) -> RiskEstimator:
        """Fit an estimator to finite feature rows and binary labels."""
        ...

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return class probabilities for each feature row."""
        ...


def validate_feature_matrix(
    features: NDArray[np.float64], expected_features: int | None = None
) -> None:
    """Validate a nonempty finite 2-D feature matrix and optional feature count."""
    if features.ndim != 2:
        raise ValueError("features must be a two-dimensional matrix")
    if features.shape[0] == 0 or features.shape[1] == 0:
        raise ValueError("features must have at least one row and one column")
    if expected_features is not None and features.shape[1] != expected_features:
        raise ValueError(f"expected {expected_features} features, got {features.shape[1]}")
    if not np.isfinite(features).all():
        raise ValueError("features must be finite")


def validate_binary_labels(labels: NDArray[np.int64], row_count: int) -> None:
    """Require one binary label per feature row and both classes for fitting."""
    if labels.ndim != 1 or labels.shape[0] != row_count:
        raise ValueError("labels must be one-dimensional and match the feature row count")
    if not np.isin(labels, [0, 1]).all():
        raise ValueError("labels must contain only 0 and 1")
    if np.unique(labels).size != 2:
        raise ValueError("training labels must contain both classes")
