"""Mathematical components of the scaled-space recourse objective."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def prediction_flip_loss(risk: float, safe_threshold: float) -> float:
    """Squared hinge penalty for risk above the configured safe threshold."""
    if not np.isfinite(risk) or not 0 <= risk <= 1:
        raise ValueError("risk must be finite and within [0, 1]")
    if not 0 < safe_threshold < 1:
        raise ValueError("safe_threshold must be within (0, 1)")
    return float(max(0.0, risk - safe_threshold) ** 2)


def scaled_l1_distance(candidate: NDArray[np.float64], original: NDArray[np.float64]) -> float:
    """Return L1 distance in scaled feature space, validating aligned finite vectors."""
    if candidate.ndim != 1 or original.ndim != 1 or candidate.shape != original.shape:
        raise ValueError("candidate and original must be same-shaped one-dimensional vectors")
    if not np.isfinite(candidate).all() or not np.isfinite(original).all():
        raise ValueError("candidate and original vectors must be finite")
    return float(np.abs(candidate - original).sum())


def recourse_objective(
    candidate: NDArray[np.float64],
    original: NDArray[np.float64],
    predicted_risk: float,
    safe_threshold: float,
    prediction_weight: float,
) -> float:
    """Compute scaled L1 change plus weighted prediction-flip loss."""
    if prediction_weight <= 0 or not np.isfinite(prediction_weight):
        raise ValueError("prediction_weight must be positive and finite")
    return scaled_l1_distance(candidate, original) + prediction_weight * prediction_flip_loss(
        predicted_risk, safe_threshold
    )
