"""Auditable persistence and loading for trained risk model bundles."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray

from prescriptxai.data.preprocess import FittedFeatureScaler
from prescriptxai.models.base import FailureModel
from prescriptxai.models.calibration import ProbabilityCalibrator

LOGGER = logging.getLogger(__name__)
_ARTIFACT_VERSION = 2


@dataclass
class ModelBundle:
    """Calibrated estimator, training-only scaler, and provenance metadata."""

    estimator: Any
    scaler: FittedFeatureScaler
    feature_names: tuple[str, ...]
    training_engine_ids: tuple[int, ...]
    model_type: str
    seed: int
    calibrator: ProbabilityCalibrator | None = None
    surrogate: FailureModel | None = None
    scaler_reference: str | None = None
    config_hash: str = ""
    git_commit: str | None = None
    metrics: dict[str, object] | None = None
    artifact_version: int = _ARTIFACT_VERSION

    @property
    def supports_gradients(self) -> bool:
        """Whether this bundle has a differentiable primary model or fitted surrogate."""
        return bool(
            getattr(self.estimator, "supports_gradients", False) or self.surrogate is not None
        )

    def predict_risk(self, frame: pd.DataFrame) -> NDArray[np.float64]:
        """Return calibrated failure probabilities for raw-unit telemetry rows."""
        if hasattr(self.estimator, "window"):
            raise ValueError(
                "LSTM prediction requires a telemetry history window; use predict_risk_sequence"
            )
        missing = set(self.feature_names) - set(frame.columns)
        if missing:
            raise ValueError(f"input is missing model features: {sorted(missing)}")
        matrix = self.scaler.transform(frame[list(self.feature_names)])
        probabilities = np.asarray(self.estimator.predict_proba(matrix), dtype=np.float64)
        if probabilities.ndim == 1:
            risk = probabilities
        elif probabilities.ndim == 2:
            classes = list(getattr(self.estimator, "classes_", [0, 1]))
            if 1 not in classes:
                raise ValueError("trained classifier does not contain the failure class")
            risk = probabilities[:, classes.index(1)]
        else:
            raise ValueError("model returned probabilities with an invalid shape")
        if self.calibrator is not None:
            risk = self.calibrator.transform(risk)
        if not np.isfinite(risk).all() or ((risk < 0) | (risk > 1)).any():
            raise ValueError("calibrated risk probabilities must be finite and within [0, 1]")
        return np.asarray(risk, dtype=np.float64)

    def predict_risk_sequence(self, raw_sequences: NDArray[np.float64]) -> NDArray[np.float64]:
        """Predict a sequence model from raw ``(n, window, features)`` telemetry."""
        if not hasattr(self.estimator, "window"):
            raise ValueError("sequence prediction is available only for an LSTM model")
        if raw_sequences.ndim != 3 or raw_sequences.shape[2] != len(self.feature_names):
            raise ValueError("raw sequence must have shape (n, window, configured features)")
        if not np.isfinite(raw_sequences).all():
            raise ValueError("sequence features must be finite")
        scaled = self.scaler.scaler.transform(raw_sequences.reshape(-1, raw_sequences.shape[2]))
        scaled_sequences = scaled.reshape(raw_sequences.shape)
        risk = np.asarray(self.estimator.predict_proba(scaled_sequences), dtype=np.float64)
        if self.calibrator is not None:
            risk = self.calibrator.transform(risk)
        if risk.shape != (len(raw_sequences),) or not np.isfinite(risk).all():
            raise ValueError("sequence model returned invalid probabilities")
        return risk

    def torch_forward(self, scaled_tensor: torch.Tensor) -> torch.Tensor:
        """Forward scaled inputs through a differentiable estimator and calibration map."""
        if not getattr(self.estimator, "supports_gradients", False):
            if self.surrogate is None:
                raise NotImplementedError(
                    "this bundle has no differentiable predictor or surrogate"
                )
            raw = self.surrogate.torch_forward(scaled_tensor)
        else:
            raw = self.estimator.torch_forward(scaled_tensor)
        if self.calibrator is not None:
            if not isinstance(raw, torch.Tensor):
                raise TypeError("differentiable predictor must return a torch tensor")
            return self.calibrator.transform_tensor(raw)
        return raw

    def predict_risk_with_gradient(
        self, frame: pd.DataFrame
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return calibrated risk and derivatives with respect to scaled model inputs."""
        if not self.supports_gradients:
            raise NotImplementedError("this bundle does not have a differentiable model path")
        if hasattr(self.estimator, "window"):
            raise ValueError("LSTM gradients require a sequence history window")
        matrix = self.scaler.transform(frame[list(self.feature_names)])
        tensor = torch.tensor(matrix, dtype=torch.float32, requires_grad=True)
        risk = self.torch_forward(tensor)
        gradient = torch.autograd.grad(risk.sum(), tensor)[0]
        risk_values: NDArray[np.float64] = np.asarray(risk.detach().cpu().numpy(), dtype=np.float64)
        gradient_values: NDArray[np.float64] = np.asarray(
            gradient.detach().cpu().numpy(), dtype=np.float64
        )
        if not np.isfinite(risk_values).all() or not np.isfinite(gradient_values).all():
            raise ValueError("differentiable model produced non-finite risk or gradients")
        return risk_values, gradient_values


def save_model_bundle(bundle: ModelBundle, path: Path) -> Path:
    """Persist a model bundle and its feature/split provenance."""
    if bundle.artifact_version != _ARTIFACT_VERSION:
        raise ValueError(f"unsupported artifact version: {bundle.artifact_version}")
    if bundle.feature_names != bundle.scaler.feature_names:
        raise ValueError("model feature order does not match the embedded fitted scaler")
    if not bundle.feature_names or len(bundle.feature_names) != len(set(bundle.feature_names)):
        raise ValueError("model artifact feature list must be nonempty and unique")
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
    if loaded.feature_names != loaded.scaler.feature_names:
        raise ValueError("artifact model and scaler feature lists do not match")
    if expected_features is not None and expected_features != loaded.feature_names:
        raise ValueError("artifact feature order does not match the expected feature order")
    return loaded
