"""Corrupt and untrusted artifacts fail before any operator-facing inference."""

import hashlib
import pickle
from dataclasses import replace
from pathlib import Path

import joblib
import numpy as np
import pytest
import torch

from integration.test_phase6_artifacts_cli import fitted_config  # noqa: F401
from prescriptxai.artifacts import ArtifactLoadError, load_trusted_joblib, load_trusted_pickle
from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.models.registry import load_model_bundle
from prescriptxai.pipeline import ArtifactError, PrescriptXAI
from prescriptxai.validation.pipeline import load_mahalanobis_validator
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator


def test_untrusted_paths_are_rejected_before_decoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No caller-controlled upload/file path implicitly grants pickle execution trust."""
    monkeypatch.delenv("PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS", raising=False)
    path = tmp_path / "untrusted.joblib"
    path.write_bytes(pickle.dumps({"harmless": "probe"}))
    for loader in (load_trusted_joblib, load_trusted_pickle, load_model_bundle):
        with pytest.raises(ValueError, match="trusted"):
            loader(path)


def test_artifact_identity_rejects_replacement_and_nonfiles(tmp_path: Path) -> None:
    """The bytes actually decoded must match the facade's fingerprint, never a later file."""
    path = tmp_path / "local.joblib"
    joblib.dump({"version": 1}, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    joblib.dump({"version": 2}, path)
    with pytest.raises(ArtifactLoadError, match="changed"):
        load_trusted_joblib(path, expected_sha256=digest)
    with pytest.raises(ArtifactLoadError, match="regular file"):
        load_trusted_joblib(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_trusted_joblib(tmp_path / "missing")


@pytest.mark.parametrize("payload", [b"", b"not a pickle", pickle.dumps({"wrong": "type"})])
def test_corrupt_model_is_a_typed_facade_failure(fitted_config: Path, payload: bytes) -> None:  # noqa: F811
    """EOF, invalid pickle and wrong objects cannot leak raw decoder exceptions."""
    config = load_config(fitted_config)
    config.artifacts.model.write_bytes(payload)
    with pytest.raises(ArtifactError):
        PrescriptXAI.from_config(config)


@pytest.mark.parametrize("fault", ["calibrator", "scaler", "provenance", "features", "temperature"])
def test_internally_corrupt_model_is_rejected(fitted_config: Path, fault: str) -> None:  # noqa: F811
    """Valid pickle encoding does not imply valid scientific metadata or calibration."""
    config = load_config(fitted_config)
    bundle = load_model_bundle(config.artifacts.model)
    if fault == "calibrator":
        bundle.calibrator = None
    elif fault == "scaler":
        bundle.scaler = None  # type: ignore[assignment]
    elif fault == "provenance":
        bundle.scaler.training_engine_ids = (999999,)
    elif fault == "features":
        bundle.feature_names = ("actuator", "unknown")
    else:
        assert bundle.calibrator is not None
        bundle.calibrator.method, bundle.calibrator.temperature = "temperature", -1.0
    joblib.dump(bundle, config.artifacts.model)
    with pytest.raises(ArtifactError):
        PrescriptXAI.from_config(config)


@pytest.mark.parametrize("fault", ["top_factor", "regime_factor", "regime_mean", "cutoff"])
def test_invalid_covariance_fails_at_load(fitted_config: Path, fault: str) -> None:  # noqa: F811
    """Singular/nonfinite fitted factors fail clearly before a raw linear-algebra error."""
    config = load_config(fitted_config)
    validator = load_mahalanobis_validator(config.artifacts.mahalanobis)
    if fault == "top_factor":
        validator.covariance_cholesky[:] = 0
    elif fault == "regime_factor":
        validator.regime_statistics[0] = replace(
            validator.regime_statistics[0], cholesky=np.zeros((2, 2))
        )
    elif fault == "regime_mean":
        validator.regime_statistics[0] = replace(
            validator.regime_statistics[0], mean=np.asarray([float("nan"), 0])
        )
    else:
        validator = replace(validator, max_distance=float("nan"))
    joblib.dump(validator, config.artifacts.mahalanobis)
    with pytest.raises(ArtifactError, match="covariance|cutoff"):
        PrescriptXAI.from_config(config)


@pytest.mark.parametrize("fault", ["network", "width", "parameters"])
def test_unfitted_or_corrupt_primary_is_not_reported_ready(
    fitted_config: Path,  # noqa: F811
    fault: str,
) -> None:
    """A callable method alone cannot establish that a persisted predictor can run."""
    config = load_config(fitted_config)
    bundle = load_model_bundle(config.artifacts.model)
    if fault == "network":
        bundle.estimator.network_ = None
    elif fault == "width":
        bundle.estimator.n_features_in_ = 999
    else:
        with torch.no_grad():
            next(bundle.estimator.network_.parameters()).fill_(float("nan"))
    joblib.dump(bundle, config.artifacts.model)
    with pytest.raises(ArtifactError, match="predictor"):
        PrescriptXAI.from_config(config)


@pytest.mark.parametrize("fault", ["clusterer", "scaler", "centers", "scale"])
def test_multiregime_artifacts_require_the_fitted_assigner(tmp_path: Path, fault: str) -> None:
    """Removing the regime model cannot silently turn FD002 into global-regime validation."""
    rng = np.random.default_rng(17)
    validator = MahalanobisValidator.fit(
        rng.normal(size=(36, 2)),
        ("a", "b"),
        np.repeat([1, 2, 3, 4], 9),
        (1, 2, 3, 4),
        5.0,
        1e-6,
        operating_settings=np.repeat(np.eye(6, 3) + np.arange(6)[:, None], 6, axis=0),
        regime_k=6,
    )
    if fault == "clusterer":
        validator = replace(validator, clusterer=None)
    elif fault == "scaler":
        validator = replace(validator, settings_scaler=None)
    elif fault == "centers":
        assert validator.clusterer is not None
        validator.clusterer.cluster_centers_[:] = float("nan")
    else:
        assert validator.settings_scaler is not None
        validator.settings_scaler.scale_[:] = 0
    path = tmp_path / "multiregime.joblib"
    joblib.dump(validator, path)
    with pytest.raises(ValueError, match="regime"):
        load_mahalanobis_validator(path)


def test_taxonomy_bytes_match_the_fingerprinted_masks(fitted_config: Path) -> None:  # noqa: F811
    """The taxonomy's actual parsed bytes, including masks/directions, determine identity."""
    path = load_config(fitted_config).pipeline.taxonomy_path
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.write_bytes(path.read_bytes() + b"\n# owner update after fingerprint\n")
    with pytest.raises(ValueError, match="taxonomy changed"):
        load_taxonomy(path, expected_sha256=digest)


@pytest.mark.parametrize("fault", ["infinite_weight", "conflicting_threshold"])
def test_mutated_appconfig_is_revalidated_before_loading(
    fitted_config: Path,  # noqa: F811
    fault: str,
) -> None:
    """Passing an AppConfig object cannot bypass the checks applied to the same YAML."""
    config = load_config(fitted_config)
    if fault == "infinite_weight":
        config.recourse.gamma = float("inf")
    else:
        config.model.safe_threshold = 0.9
    with pytest.raises(ArtifactError, match="configur"):
        PrescriptXAI.from_config(config)
