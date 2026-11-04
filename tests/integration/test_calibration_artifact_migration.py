"""Byte-identified calibration migration preserves both numerical provenance families."""

import hashlib
from pathlib import Path

import joblib
import numpy as np
import pytest
import torch

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.artifacts import ArtifactLoadError
from prescriptxai.models import registry
from prescriptxai.models.calibration import ProbabilityCalibrator
from prescriptxai.models.registry import load_model_bundle, save_model_bundle


@pytest.fixture
def unversioned_model(tmp_path: Path) -> Path:
    """Persist a real fitted calibrator on the explicitly synthetic unit-test bundle."""
    bundle, _, _ = make_recourse_fixture()
    bundle.calibrator = ProbabilityCalibrator("temperature").fit(
        np.array([0.1, 0.9]), np.array([0, 1])
    )
    del bundle.calibrator.tensor_map_version
    bundle.git_commit = "known-fitting-source"
    path = tmp_path / "bundle.joblib"
    save_model_bundle(bundle, path)
    return path


def test_known_bytes_resolve_legacy_without_rewriting_artifact(
    unversioned_model: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Exact-byte evidence selects legacy arithmetic; serialization preserves that choice."""
    before = unversioned_model.read_bytes()
    digest = hashlib.sha256(before).hexdigest()
    monkeypatch.setattr(registry, "_LEGACY_TENSOR_MAP_ARTIFACTS", {digest: "known-fitting-source"})
    loaded = load_model_bundle(unversioned_model, require_calibrated=True)
    assert loaded.calibrator.tensor_map_version == 1
    assert unversioned_model.read_bytes() == before
    values = torch.tensor([0.0, 0.3, 1.0])
    expected = torch.sigmoid(torch.logit(values.clamp(1e-7, 1 - 1e-7)) /
                             loaded.calibrator.temperature)
    torch.testing.assert_close(loaded.calibrator.transform_tensor(values), expected, atol=0, rtol=0)
    saved = save_model_bundle(loaded, tmp_path / "migrated.joblib")
    assert load_model_bundle(saved).calibrator.tensor_map_version == 1


@pytest.mark.parametrize("source", ["known-fitting-source", "post-hardening-source", None])
def test_unrecognized_bytes_preserve_current_map_even_with_old_source(
    unversioned_model: Path, source: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    """A source string alone cannot identify the arithmetic of a later recalibration."""
    bundle = joblib.load(unversioned_model)
    bundle.git_commit = source
    joblib.dump(bundle, unversioned_model)
    loaded = load_model_bundle(unversioned_model)
    assert loaded.calibrator.tensor_map_version == 2
    assert "original numerical contract is unverified" in caplog.text
    assert loaded.calibrator.transform_tensor(torch.tensor([0.1])).dtype == torch.float64


@pytest.mark.parametrize("version", [1, 2])
def test_explicit_map_version_overrides_provenance_inference(
    unversioned_model: Path, version: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """New or explicitly migrated fits cannot be downgraded by bundle-era metadata."""
    bundle = joblib.load(unversioned_model)
    bundle.calibrator.tensor_map_version = version
    joblib.dump(bundle, unversioned_model)
    digest = hashlib.sha256(unversioned_model.read_bytes()).hexdigest()
    monkeypatch.setattr(registry, "_LEGACY_TENSOR_MAP_ARTIFACTS", {digest: bundle.git_commit})
    assert load_model_bundle(unversioned_model).calibrator.tensor_map_version == version


def test_migration_checks_decoded_bytes_and_fitting_identity(
    unversioned_model: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stale fingerprints and inconsistent declared provenance fail explicitly."""
    digest = hashlib.sha256(unversioned_model.read_bytes()).hexdigest()
    monkeypatch.setattr(registry, "_LEGACY_TENSOR_MAP_ARTIFACTS", {digest: "different-source"})
    with pytest.raises(ArtifactLoadError, match="fitting provenance"):
        load_model_bundle(unversioned_model)
    with pytest.raises(ArtifactLoadError, match="changed"):
        load_model_bundle(unversioned_model, expected_sha256="0" * 64)


@pytest.mark.parametrize("version", [None, 0, 3, True, "1"])
def test_unknown_explicit_version_is_not_a_migration_fallback(
    unversioned_model: Path, version: object
) -> None:
    """Invalid version metadata is rejected by public loading, including NumPy-only callers."""
    bundle = joblib.load(unversioned_model)
    bundle.calibrator.tensor_map_version = version
    joblib.dump(bundle, unversioned_model)
    with pytest.raises(ValueError, match="map version"):
        load_model_bundle(unversioned_model)
