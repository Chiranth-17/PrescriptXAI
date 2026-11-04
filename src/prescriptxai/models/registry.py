"""Auditable persistence and loading for trained risk model bundles."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray

from prescriptxai.artifacts import (
    ArtifactLoadError,
    load_trusted_joblib,
    trusted_artifact_bytes,
    validate_engine_ids,
)
from prescriptxai.data.preprocess import FittedFeatureScaler
from prescriptxai.models.base import FailureModel
from prescriptxai.models.calibration import ProbabilityCalibrator
from prescriptxai.models.torch_models import LSTMFailureModel, MLPFailureModel
from prescriptxai.models.xgb_model import XGBFailureModel

LOGGER = logging.getLogger(__name__)
_ARTIFACT_VERSION = 3

# Audited pre-hardening fitted bytes only; fitting commit alone cannot prove map identity.
# Provenance and source-method hashes: docs/phase12_regression_repair.md.
_LEGACY_TENSOR_MAP_ARTIFACTS = {
    "cc3b3c2028a4d4a568cd554d1c2cf360bcd9fe237ecfd4afe5d628d3ca40d8bd":
        "fa5adcbe914f95e6efe25f4edc8f8f50a234881a",
    "c52728e242d0c14b536eae5a8b579fa9003b6e25d9e28cb33c2c225ec0948732":
        "4a8275a788c9998d80acf07f3e7e9dfe2fcbe179",
    "1cd9ba2cb4515108d6709566637658dfaff4130d897e35214cc1267c061acf09":
        "4a8275a788c9998d80acf07f3e7e9dfe2fcbe179",
    "8ac30f13ea83291bb3240b66d4b36b985d8ca9d54ce9d0edc43286836f061a6f":
        "4a8275a788c9998d80acf07f3e7e9dfe2fcbe179",
    "ff39f9e7c567384abfb2866c2f688fe2622aead1ec11f67a5e8ef81e31fc6eb2":
        "4a8275a788c9998d80acf07f3e7e9dfe2fcbe179",
    "0deaf3ecfbe3fe72dafe4f0b20453d374f31752653acb590a814df963a6e0fe1":
        "4a8275a788c9998d80acf07f3e7e9dfe2fcbe179",
    "93aa5d70bffc72fa08bf7fb97d4fbe3f780f1f98251239af0750f97ba645b0df":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "6321caec653f39b9455bf4f98743c32860019fdd020bfcb8c73e67fed46a2f2d":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "24175d136f50883eb6de94b4518c79d4d54653606daa6cf4c9c545eaa560be94":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "d07410a4c3905907fe7aae1f452822940062de773f5f301cc1683b11873c52d1":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "d5caef362ad819901c8fb294bb89d8d6553937529af9eaf6231d787de490ddbe":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "70a9cef8682e80e605a0b7bbdc36b080f14e03c98b930d6c8b4156f65cf6a6f5":
        "473672b1b8103fb4468184145aa3bc2d82f63e8e",
    "a8ef6ef286a0183cb2c3e849e8389cdaa30fa27d0b74300ded1114dfac39e115":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "6aef340db4b4ede98f7e00c04bb055ed523b348e6dca2557c6563e6a54f84072":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "0875168613600c6b4419353f030576324196524238f00690e240d44dcc68ff01":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "fd2d57e20b5010eea9c2b52a49453aea5b73baf3854cba999c71a700c3c38776":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "41ca030f7ad766bb8b6a6c14a600f8419253ce59f5fbbc66db4e97233db525ed":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "2f16756d78a176f9d003bc1133924097a38663e37107d5ae6232ac549ddb4b5f":
        "473672b1b8103fb4468184145aa3bc2d82f63e8e",
    "0c4bc911a5ce9117ac1e0759c8fe38579beb5e83330acac4a39029193de1db1d":
        "0c0b6e1d37aafaed66cc61d9ac23f768c0529442",
    "b4dd48313de2f8f9e7534f7b158fd30a9b6e7b49671bed34bdcc70ffe5984f3a":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "a3af5d05aed54ce453dc1063cbe2960a6609572b253d99aea9a6055e761b388a":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "98fcd4ecf5de50b59337854c22bdeec45ed551d06c51d5b44a31f2d4a454939b":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "53517dfe09f50874e1588a024890ba767552e67fcd7f194b347d3a509e9ac382":
        "4ffb038c579039b557b3e6695d429001a293f043",
    "fcc168c9ad8f264317c24213fb058d3aaf8e44724ad486c7b3668d91da76beda":
        "4ffb038c579039b557b3e6695d429001a293f043",
}


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
        ordered = (
            frame if tuple(frame.columns) == self.feature_names else frame[list(self.feature_names)]
        )
        matrix = self.scaler.transform(ordered)
        probabilities = np.asarray(self.estimator.predict_proba(matrix), dtype=np.float64)
        if probabilities.ndim == 1:
            risk = probabilities
        elif probabilities.ndim == 2:
            classes = list(getattr(self.estimator, "classes_", [0, 1]))
            if probabilities.shape != (len(frame), len(classes)):
                raise ValueError("model probabilities must match input rows and declared classes")
            if 1 not in classes:
                raise ValueError("trained classifier does not contain the failure class")
            risk = probabilities[:, classes.index(1)]
        else:
            raise ValueError("model returned probabilities with an invalid shape")
        if risk.shape != (len(frame),):
            raise ValueError("model probabilities must match input rows")
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
        if (
            risk.shape != (len(raw_sequences),)
            or not np.isfinite(risk).all()
            or ((risk < 0) | (risk > 1)).any()
        ):
            raise ValueError("sequence model returned invalid probabilities")
        return risk

    def torch_forward(self, scaled_tensor: torch.Tensor) -> torch.Tensor:
        """Forward scaled inputs through a differentiable estimator and calibration map."""
        if not getattr(self.estimator, "supports_gradients", False):
            if self.surrogate is None:
                raise TypeError(
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
            raise TypeError("this bundle does not have a differentiable model path")
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
    # Bind migration to the very bytes decoded, even when a caller supplied no fingerprint.
    artifact_digest = expected_sha256
    if artifact_digest is None:
        artifact_digest = hashlib.sha256(trusted_artifact_bytes(path)).hexdigest()
    loaded: Any = load_trusted_joblib(path, artifact_digest)
    if not isinstance(loaded, ModelBundle):
        raise ValueError("artifact does not contain a PrescriptXAI ModelBundle")
    try:
        _verify_model_structure(loaded, require_calibrated)
        _resolve_calibration_arithmetic(loaded, artifact_digest)
    except (AttributeError, TypeError, KeyError, IndexError) as error:
        raise ArtifactLoadError("model artifact contains malformed fitted metadata") from error
    if expected_features is not None and expected_features != loaded.feature_names:
        raise ValueError("artifact feature order does not match the expected feature order")
    return loaded



def _resolve_calibration_arithmetic(bundle: ModelBundle, artifact_digest: str) -> None:
    """Migrate unversioned maps in memory using audited bytes, never observed outcomes."""
    calibrator = bundle.calibrator
    if calibrator is None or hasattr(calibrator, "tensor_map_version"):
        return
    legacy_source = _LEGACY_TENSOR_MAP_ARTIFACTS.get(artifact_digest)
    if legacy_source is not None:
        if bundle.git_commit != legacy_source:
            raise ArtifactLoadError("legacy calibration artifact fitting provenance differs")
        calibrator.tensor_map_version = 1
        LOGGER.info("Resolved audited legacy calibration map v1 for artifact %s", artifact_digest)
    else:
        # Some post-hardening fits also lack a version. Keep their prior v2 behavior.
        calibrator.tensor_map_version = 2
        LOGGER.warning(
            "Unversioned calibration artifact %s: preserving current map v2; "
            "original numerical contract is unverified", artifact_digest
        )


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
    model_ids = validate_engine_ids(bundle.training_engine_ids, "model fitting provenance")
    scaler_ids = validate_engine_ids(bundle.scaler.training_engine_ids, "scaler fitting provenance")
    if model_ids != scaler_ids:
        raise ArtifactLoadError("model and scaler training-engine provenance differs")
    calibration_metadata = (bundle.metrics or {}).get("calibration")
    if isinstance(calibration_metadata, dict) and calibration_metadata.get("fit_engine_ids"):
        validate_engine_ids(
            calibration_metadata["fit_engine_ids"], "calibration fitting provenance"
        )
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
