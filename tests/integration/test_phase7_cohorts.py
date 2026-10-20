"""Build complete study cohorts from an actual fixture archive and independently fitted folds."""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from fixtures.cmapss import write_cmapss_archive
from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.evaluation.assets import (
    dataset_frames,
    prepare_bundle_assets,
    prepare_study_assets,
)
from prescriptxai.evaluation.experiments import file_hash, load_study, source_revision
from prescriptxai.evaluation.study import (
    build_cohorts,
    quality_cases,
    run_quality_stage,
    verify_asset_index,
)
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.models.train import train_risk_model


def test_complete_cohorts_and_verified_asset_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every outer engine is scored only by its held-out fold, even for zero-alert populations."""
    study = load_study(Path("configs/experiments/phase7-study.yaml"))
    taxonomy_text = Path("configs/features.yaml").read_text(encoding="utf-8")
    config = load_config(Path("configs/default.yaml"))
    archive = write_cmapss_archive(tmp_path / "raw/CMAPSSData.zip", train_engine_count=12)
    config.data.root = config.paths.raw_data = archive.parent
    config.model_choice = config.model.risk_estimator = "torch"
    config.model.torch_epochs = 2
    config.model.torch_hidden_dims = [4]
    # The exact-one gate exercises saturated calibrated probabilities at the boundary.
    config.tau_danger = config.model.danger_threshold = 1.0
    config.model.calibration_method = "sigmoid"
    config.recourse.max_iterations = 1
    config.recourse.restarts = config.recourse.alpha_steps = config.recourse.l1_escalation_steps = 1
    config.recourse.support_search_limit = 1
    config.recourse.true_model_grid_enabled = False
    config.validation.feedback_max_refinements = 0
    config.pipeline.taxonomy_path = tmp_path / "configs/features.yaml"
    root = tmp_path / "artifacts/models"
    study.artifact_root = root
    study.datasets = {"FD001": ["mlp"]}
    study.diagnostic_models = []
    study.grouped_folds = 2
    study.workers = 1
    study.solver_seeds = [17]
    study.output_root = tmp_path / "artifacts/experiments"
    config.artifacts.model = config.paths.model = root / "base/model.joblib"
    config.artifacts.mahalanobis = config.paths.mahalanobis = root / "base/mahalanobis-v1.joblib"
    config.artifacts.coupling = root / "base/coupling.joblib"
    directory = tmp_path / "configs/experiments"
    directory.mkdir(parents=True)
    config.pipeline.taxonomy_path.write_text(taxonomy_text, encoding="utf-8")
    for version, cutoff in study.d_max_versions.items():
        local = config.model_copy(deep=True)
        local.validation.mahalanobis_max = cutoff
        local.artifacts.mahalanobis = local.paths.mahalanobis = (
            root / f"base/mahalanobis-{version}.joblib"
        )
        (directory / f"phase7-FD001-mlp-{version}.yaml").write_text(
            yaml.safe_dump(local.model_dump(mode="json")), encoding="utf-8"
        )
    study.frozen_solver_config = directory / "phase7-FD001-mlp-v1.yaml"
    study_path = directory / "study.yaml"
    study_path.write_text(yaml.safe_dump(study.model_dump(mode="json")), encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/evaluation_protocol.md").write_text("Test-only committed study protocol")
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check=True)
    subprocess.run(["git", "add", "configs", "docs"], check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "fixture-only pre-fitting configuration",
        ],
        check=True,
    )
    frame, _ = dataset_frames(config)
    taxonomy = load_taxonomy(config.pipeline.taxonomy_path)
    partitions = {
        "base": (tuple(range(1, 9)), (9, 10), (11, 12)),
        "fold-1": ((7, 8, 9, 10), (11, 12), (1, 2, 3, 4, 5, 6)),
        "fold-2": ((1, 2, 3, 4), (5, 6), (7, 8, 9, 10, 11, 12)),
    }
    index = {"preparation_source": source_revision(), "models": {}}
    for fold, parts in partitions.items():
        trained = train_risk_model(frame, config, taxonomy, "mlp", engine_partitions=parts)
        path = root / fold / "model.joblib"
        save_model_bundle(trained.bundle, path)
        index["models"][f"FD001/mlp/{fold}"] = prepare_bundle_assets(
            config, taxonomy, frame, path, root / fold, study.d_max_versions
        )
    (root / "index.json").write_text(json.dumps(index), encoding="utf-8")
    (root / "preparation.json").write_text(json.dumps({"fixture_only": True}), encoding="utf-8")
    historical = tmp_path / "artifacts/phase6"
    historical.mkdir()
    (historical / "pipeline.json").write_text(json.dumps({"archive_sha256": file_hash(archive)}))
    for name in ("xgboost", "mlp", "lstm"):
        (tmp_path / f"artifacts/FD001-{name}.joblib").write_bytes(
            config.artifacts.model.read_bytes()
        )
    cohorts = build_cohorts(study, index)
    assert len(cohorts) == 10
    assert all(c.accounting["selected_alerts"] == len(c.rows) for c in cohorts)
    assert {c.population for c in cohorts} == {
        "grouped_oof_all_alerts",
        "internal_heldout_all_alerts",
        "official_test_all_alerts",
        "development_all_alerts",
    }
    assert all(case.state["engine_id"] >= 1 for case in quality_cases(cohorts, study))
    assert prepare_study_assets(study) == index
    verify_asset_index(study, index)
    expected_queries = len(list(quality_cases(cohorts, study)))
    result_path = run_quality_stage(study, study_path, "empty-fixture", "quality")
    assert run_quality_stage(study, study_path, "empty-fixture", "quality") == result_path
    run_quality_stage(study, study_path, "empty-fixture", "diagnostics")
    status = json.loads((result_path / "stages.json").read_text())
    assert status["quality"]["observations"] == expected_queries
    assert status["diagnostics"]["complete"]
    changed = Path(index["models"]["FD001/mlp/fold-1"]["paths"]["mahalanobis_v1"])
    changed.write_bytes(b"deliberately corrupt fixture validator")
    with pytest.raises(ValueError, match="changed"):
        build_cohorts(study, index)
    with pytest.raises(ValueError, match="changed"):
        prepare_study_assets(study)
