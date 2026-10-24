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

from prescriptxai.artifacts import ArtifactLoadError, load_trusted_joblib
from prescriptxai.data.preprocess import FittedFeatureScaler
from prescriptxai.models.base import FailureModel
from prescriptxai.models.calibration import ProbabilityCalibrator
from prescriptxai.models.torch_models import LSTMFailureModel, MLPFailureModel
from prescriptxai.models.xgb_model import XGBFailureModel

LOGGER = logging.getLogger(__name__)
_ARTIFACT_VERSION = 3


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
    resolved_bounds: dict[str, tuple[float, float]] | None = None
    resolved_rate_limits: dict[str, float] | None = None
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
    if bundle.resolved_rate_limits is not None and any(
        not name or not np.isfinite(limit) or limit < 0
        for name, limit in bundle.resolved_rate_limits.items()
    ):
        raise ValueError("resolved actuator rate limits must be named, finite, and nonnegative")
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    LOGGER.info("Saved %s risk artifact to %s", bundle.model_type, path)
    return path


def load_model_bundle(
    path: Path,
    expected_features: tuple[str, ...] | None = None,
    *,
    require_calibrated: bool = False,
    expected_sha256: str | None = None,
) -> ModelBundle:
    """Load a fitted model bundle and optionally enforce feature order."""
    if not path.is_file():
        raise FileNotFoundError(path)
    loaded: Any = load_trusted_joblib(path, expected_sha256)
    if not isinstance(loaded, ModelBundle):
        raise ValueError("artifact does not contain a PrescriptXAI ModelBundle")
    try:
        _verify_model_structure(loaded, require_calibrated)
    except (AttributeError, TypeError, KeyError, IndexError) as error:
        raise ArtifactLoadError("model artifact contains malformed fitted metadata") from error
    if expected_features is not None and expected_features != loaded.feature_names:
        raise ValueError("artifact feature order does not match the expected feature order")
    return loaded


def _verify_model_structure(bundle: ModelBundle, require_calibrated: bool) -> None:
    """Reject internally corrupt metadata before it reaches an operator request."""
    if bundle.artifact_version != _ARTIFACT_VERSION:
        raise ValueError(f"unsupported artifact version: {bundle.artifact_version}")
    if not isinstance(bundle.scaler, FittedFeatureScaler):
        raise ArtifactLoadError("model artifact has no fitted feature scaler")
    names = bundle.feature_names
    if (
        not isinstance(names, tuple)
        or not names
        or not all(isinstance(name, str) and name for name in names)
        or len(names) != len(set(names))
    ):
        raise ArtifactLoadError("model artifact feature list must be nonempty and unique")
    if names != bundle.scaler.feature_names:
        raise ArtifactLoadError("artifact model and scaler feature lists do not match")
    if bundle.resolved_rate_limits is not None and any(
        not name or not np.isfinite(limit) or limit < 0
        for name, limit in bundle.resolved_rate_limits.items()
    ):
        raise ArtifactLoadError("artifact contains invalid resolved actuator rate limits")
    if set(bundle.training_engine_ids) != set(bundle.scaler.training_engine_ids):
        raise ArtifactLoadError("model and scaler training-engine provenance differs")
    scale = np.asarray(bundle.scaler.scaler.scale_, dtype=float)
    mean = np.asarray(bundle.scaler.scaler.mean_, dtype=float)
    if (
        scale.shape != (len(names),)
        or mean.shape != scale.shape
        or not np.isfinite(scale).all()
        or not np.isfinite(mean).all()
        or (scale <= 0).any()
    ):
        raise ArtifactLoadError("model artifact has invalid fitted scaler statistics")
    if not isinstance(bundle.model_type, str) or not callable(
        getattr(bundle.estimator, "predict_proba", None)
    ):
        raise ArtifactLoadError("model artifact has no compatible predictor")
    for predictor in (bundle.estimator, bundle.surrogate):
        if isinstance(predictor, (MLPFailureModel, LSTMFailureModel)):
            if predictor.network_ is None or predictor.n_features_in_ != len(names):
                raise ArtifactLoadError("model artifact has an unfitted or incompatible predictor")
            if any(
                not torch.isfinite(parameter).all() for parameter in predictor.network_.parameters()
            ):
                raise ArtifactLoadError("model artifact has nonfinite fitted predictor parameters")
        elif isinstance(predictor, XGBFailureModel) and (
            predictor.estimator is None
            or predictor.estimator.get_booster().num_features() != len(names)
        ):
            raise ArtifactLoadError(
                "model artifact has an unfitted or incompatible XGBoost predictor"
            )
    if require_calibrated and bundle.calibrator is None:
        raise ArtifactLoadError("model artifact is missing its required fitted calibrator")
    if bundle.calibrator is not None:
        if not isinstance(bundle.calibrator, ProbabilityCalibrator):
            raise ArtifactLoadError("model artifact contains an invalid calibrator")
        if bundle.calibrator.method not in {"sigmoid", "temperature", "isotonic"}:
            raise ArtifactLoadError("model artifact contains an unknown calibration method")
        if bundle.calibrator.method == "temperature" and (
            bundle.calibrator.temperature is None
            or not np.isfinite(bundle.calibrator.temperature)
            or bundle.calibrator.temperature <= 0
        ):
            raise ArtifactLoadError("model artifact has an invalid fitted calibration temperature")
        if bundle.calibrator.method == "sigmoid" and (
            bundle.calibrator.slope is None
            or bundle.calibrator.intercept is None
            or not np.isfinite([bundle.calibrator.slope, bundle.calibrator.intercept]).all()
            or bundle.calibrator.slope < 0
        ):
            raise ArtifactLoadError("model artifact has invalid fitted calibration coefficients")
        calibrated = bundle.calibrator.transform(np.asarray([0.25, 0.75]))
        if not np.isfinite(calibrated).all() or ((calibrated < 0) | (calibrated > 1)).any():
            raise ArtifactLoadError("model artifact contains invalid calibrated probabilities")
