"""Engine-grouped probability calibration."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import GroupKFold

from prescriptxai.config import ModelConfig
from prescriptxai.models.base import RiskEstimator


def fit_group_calibrator(
    estimator: RiskEstimator,
    features: NDArray[np.float64],
    labels: NDArray[np.int64],
    engine_ids: NDArray[np.int64],
    config: ModelConfig,
) -> CalibratedClassifierCV:
    """Fit calibration with all folds grouped by engine ID.

    Every calibration row belongs to a training engine. GroupKFold ensures an engine's cycles
    cannot appear in both the estimator-fit and held-out calibration fold.
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
