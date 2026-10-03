"""Auditable persistence and loading for trained risk model bundles."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.calibration import CalibratedClassifierCV

from prescriptxai.data.preprocess import FittedFeatureScaler

LOGGER = logging.getLogger(__name__)
_ARTIFACT_VERSION = 1


@dataclass
class ModelBundle:
    """Calibrated estimator, training-only scaler, and provenance metadata."""

    estimator: CalibratedClassifierCV
    scaler: FittedFeatureScaler
    feature_names: tuple[str, ...]
    training_engine_ids: tuple[int, ...]
    model_type: str
    seed: int
    artifact_version: int = _ARTIFACT_VERSION

    def predict_risk(self, frame: pd.DataFrame) -> NDArray[np.float64]:
        """Return calibrated failure probabilities for raw-unit telemetry rows."""
        missing = set(self.feature_names) - set(frame.columns)
        if missing:
            raise ValueError(f"input is missing model features: {sorted(missing)}")
        matrix = self.scaler.transform(frame[list(self.feature_names)])
        probabilities = self.estimator.predict_proba(matrix)
        classes = list(self.estimator.classes_)
        if 1 not in classes:
            raise ValueError("trained classifier does not contain the failure class")
        risk = probabilities[:, classes.index(1)]
        if not np.isfinite(risk).all() or ((risk < 0) | (risk > 1)).any():
            raise ValueError("calibrated risk probabilities must be finite and within [0, 1]")
        return cast(NDArray[np.float64], risk)


def save_model_bundle(bundle: ModelBundle, path: Path) -> Path:
    """Persist a model bundle and its feature/split provenance."""
    if bundle.artifact_version != _ARTIFACT_VERSION:
        raise ValueError(f"unsupported artifact version: {bundle.artifact_version}")
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    LOGGER.info("Saved %s risk artifact to %s", bundle.model_type, path)
    return path


def load_model_bundle(path: Path, expected_features: tuple[str, ...] | None = None) -> ModelBundle:
    """Load a fitted model bundle and optionally enforce feature order."""
    if not path.is_file():
        raise FileNotFoundError(path)
    loaded: Any = joblib.load(path)
    if not isinstance(loaded, ModelBundle):
        raise ValueError("artifact does not contain a PrescriptXAI ModelBundle")
    if loaded.artifact_version != _ARTIFACT_VERSION:
        raise ValueError(f"unsupported artifact version: {loaded.artifact_version}")
    if expected_features is not None and expected_features != loaded.feature_names:
        raise ValueError("artifact feature order does not match the expected feature order")
    return loaded
