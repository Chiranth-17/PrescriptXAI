"""Deployment digests are checked before a trusted serialized bundle is decoded."""

import hashlib
import json
from pathlib import Path

import joblib
import pytest

from prescriptxai.artifacts import (
    ArtifactLoadError,
    load_trusted_joblib,
    require_deployment_manifest,
)


def test_hosted_loader_refuses_unlisted_and_replaced_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even a valid replacement object must fail the independently supplied checksum."""
    root = tmp_path / "models"
    root.mkdir()
    model = root / "model.joblib"
    other = root / "replacement.joblib"
    manifest = tmp_path / "manifest.json"
    monkeypatch.setenv("PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS", str(root))
    monkeypatch.delenv("PRESCRIPTXAI_ARTIFACT_MANIFEST", raising=False)
    with pytest.raises(ArtifactLoadError, match="set PRESCRIPTXAI_ARTIFACT_MANIFEST"):
        require_deployment_manifest()
    joblib.dump({"data": [1, 2, 3]}, model)
    joblib.dump({"data": [3, 2, 1]}, other)
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    manifest.write_text(json.dumps({"schema_version": 1, "files": {str(model): digest}}))
    monkeypatch.setenv("PRESCRIPTXAI_ARTIFACT_MANIFEST", str(manifest))
    require_deployment_manifest()
    assert load_trusted_joblib(model) == {"data": [1, 2, 3]}
    with pytest.raises(ArtifactLoadError, match="missing from"):
        load_trusted_joblib(other)
    model.write_bytes(other.read_bytes())
    with pytest.raises(ArtifactLoadError, match="differs from"):
        load_trusted_joblib(model)
