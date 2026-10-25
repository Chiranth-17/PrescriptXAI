"""Exercise the installed workflow orchestration using real temporary raw telemetry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from fixtures.hardening import raw_fixture
from prescriptxai.api import create_app
from prescriptxai.cli import app
from prescriptxai.config import load_config
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.reproduce import reproduce


def _profile(directory: Path) -> Path:
    """Configure a short real fit, retaining scientific thresholds and every fixture engine."""
    _, config, taxonomy = raw_fixture(directory)
    config.model_choice = config.model.risk_estimator = "xgboost"
    config.model.xgb_n_estimators = 20
    config.data.root = config.paths.raw_data = directory
    config.data.archive_name = "raw.zip"
    config.data.expected_row_counts = {}
    output = directory / "artifacts" / "reproduction"
    config.artifacts.model = config.paths.model = output / "model.joblib"
    config.artifacts.mahalanobis = config.paths.mahalanobis = output / "validator.joblib"
    config.artifacts.coupling = output / "coupling.joblib"
    config.artifacts.evaluation_report = config.paths.evaluation_report = output / "evaluation.json"
    config.data.processed_root = config.paths.processed_data = output / "processed"
    config.evaluation.max_queries = 2
    config.evaluation.bootstrap_replicates = 20
    config.pipeline.taxonomy_path = directory / "features.yaml"
    config.pipeline.taxonomy_path.write_text(
        yaml.safe_dump(taxonomy.model_dump(mode="json")), encoding="utf-8"
    )
    profile = directory / "profile.yaml"
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    return profile


@pytest.mark.e2e
def test_real_reproduce_command_writes_loadable_hashed_artifacts(tmp_path: Path) -> None:
    """Raw ZIP -> prepare -> fit/calibrate -> validators -> evaluation -> serving, no mocks."""
    profile = _profile(tmp_path)
    result = CliRunner().invoke(app, ["reproduce", "--config", str(profile)])
    assert result.exit_code == 0, result.output
    root = tmp_path / "artifacts/reproduction"
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert [stage["name"] for stage in manifest["stages"]] == [
        "data_prepare",
        "train_and_calibrate",
        "fit_validators",
        "evaluate",
        "report",
    ]
    assert all(stage["status"] == "complete" for stage in manifest["stages"])
    for name, digest in manifest["output_sha256"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    assert (
        len(manifest["engine_partitions"]["train"])
        + len(manifest["engine_partitions"]["validation"])
        + len(manifest["engine_partitions"]["test"])
        == 8
    )
    assert manifest["configuration_sha256"] == hashlib.sha256(profile.read_bytes()).hexdigest()
    service = PrescriptXAI.from_config(profile)
    response = TestClient(create_app(service)).get("/health")
    assert response.status_code == 200
    report = json.loads((root / "evaluation.json").read_text())
    assert report["provenance"]["reproduction_run_id"] == manifest["run_id"]
    snapshot = (root / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="refusing to replace"):
        reproduce(profile)
    assert (root / "manifest.json").read_bytes() == snapshot


def test_reproduction_preflight_rejects_unsupported_or_uncontained_outputs(tmp_path: Path) -> None:
    """Unsafe path layouts and unsupported model families fail before output creation."""
    profile = _profile(tmp_path)
    config = load_config(profile)
    config.model_choice = config.model.risk_estimator = "torch"
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    with pytest.raises(ValueError, match="XGBoost"):
        reproduce(profile)
    config.model_choice = config.model.risk_estimator = "xgboost"
    config.artifacts.coupling = None
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    with pytest.raises(ValueError, match="explicit coupling"):
        reproduce(profile)
    config.artifacts.coupling = tmp_path / "elsewhere.joblib"
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    with pytest.raises(ValueError, match="within the model artifact"):
        reproduce(profile)
    assert not (tmp_path / "artifacts/reproduction").exists()


def test_failed_reproduction_keeps_stage_evidence_and_cannot_replace_it(tmp_path: Path) -> None:
    """Corrupt actual input yields a readable command error and an immutable failed-run record."""
    profile = _profile(tmp_path)
    (tmp_path / "raw.zip").write_bytes(b"corrupt input")
    result = CliRunner().invoke(app, ["reproduce", "--config", str(profile)])
    assert result.exit_code == 2 and "data_prepare failed" in result.output
    assert "Traceback" not in result.output
    manifest = json.loads((tmp_path / "artifacts/reproduction/manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert manifest["failed_stage"] == "data_prepare"
    assert manifest["stages"][0]["error_type"] == "DatasetDownloadError"
