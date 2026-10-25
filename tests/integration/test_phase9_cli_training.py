"""Actual CLI training and held-out reporting from a temporary raw archive."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from fixtures.hardening import raw_fixture
from prescriptxai.cli import app
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.data.cmapss import to_model_frame
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.models.registry import load_model_bundle
from prescriptxai.validation.tier4_coupling import calibrate_coupling_thresholds


@pytest.mark.e2e
def test_cli_raw_train_calibration_plots_and_evaluate_saved_report(tmp_path: Path) -> None:
    """Train the real requested model and report its persisted test partition."""
    raw, config, taxonomy = raw_fixture(tmp_path)
    config.data.root = config.paths.raw_data = tmp_path
    config.data.archive_name = "raw.zip"
    config.artifacts.model = config.paths.model = tmp_path / "model.joblib"
    config.artifacts.mahalanobis = config.paths.mahalanobis = tmp_path / "validator.joblib"
    config.artifacts.evaluation_report = config.paths.evaluation_report = tmp_path / "report.json"
    config.evaluation.bootstrap_replicates = 100
    config.evaluation.max_queries = 2
    config.pipeline.taxonomy_path = tmp_path / "features.yaml"
    config.pipeline.taxonomy_path.write_text(
        yaml.safe_dump(taxonomy.model_dump(mode="json")), encoding="utf-8"
    )
    profile = tmp_path / "pipeline.yaml"
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    runner = CliRunner()
    trained = runner.invoke(
        app,
        [
            "train",
            "--model",
            "mlp",
            "--config",
            str(profile),
            "--features",
            str(config.pipeline.taxonomy_path),
        ],
    )
    assert trained.exit_code == 0, trained.output
    paths = json.loads(trained.stdout)
    for name in ("model_artifact", "mahalanobis_artifact", "calibration_png", "calibration_html"):
        assert Path(paths[name]).is_file()
    bundle = load_model_bundle(Path(paths["model_artifact"]), require_calibrated=True)
    partitions = bundle.metrics["split_engines"]
    assert not set(partitions["train"]) & set(partitions["test_holdout"])
    labeled = add_training_labels(to_model_frame(raw), config.data.rul_cap, config.horizon_H)
    coupling = SensorCouplingModel.fit(
        labeled,
        taxonomy,
        training_engine_ids=bundle.training_engine_ids,
        failure_horizon=config.horizon_H,
        seed=config.seed,
    )
    validation_ids = tuple(partitions["validation"])
    coupling = calibrate_coupling_thresholds(
        coupling,
        labeled.loc[labeled.engine_id.isin(validation_ids)],
        validation_ids,
        reference_distribution="all_cycles",
        min_rul=0,
        evaluation_engine_ids=tuple(partitions["test_holdout"]),
    )
    config.artifacts.coupling = tmp_path / "explicit-coupling.joblib"
    coupling.save(config.artifacts.coupling)
    config.artifacts.model = config.paths.model = Path(paths["model_artifact"])
    config.artifacts.mahalanobis = config.paths.mahalanobis = Path(paths["mahalanobis_artifact"])
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    evaluated = runner.invoke(
        app,
        ["evaluate", "--config", str(profile), "--features", str(config.pipeline.taxonomy_path)],
    )
    assert evaluated.exit_code == 0, evaluated.output
    report = json.loads(config.artifacts.evaluation_report.read_text(encoding="utf-8"))
    assert report["provenance"]["holdout_engine_ids"] == sorted(partitions["test_holdout"])
    assert len(report["records"]) == 2
    assert all(row["engine_id"] in partitions["test_holdout"] for row in report["records"])
    fingerprint = report["provenance"]["artifact_fingerprints"]["coupling"]
    assert Path(fingerprint["path"]) == config.artifacts.coupling
    assert (
        fingerprint["sha256"] == hashlib.sha256(config.artifacts.coupling.read_bytes()).hexdigest()
    )
    assert config.artifacts.evaluation_report.with_suffix(".md").is_file()
