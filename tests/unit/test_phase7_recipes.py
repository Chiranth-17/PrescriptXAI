"""Preregistered recipe selection, empty cohorts and exact input provenance."""

import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
import yaml

from fixtures.experiments import fitted_experiment
from prescriptxai.evaluation.assets import seal_preparation_inputs
from prescriptxai.evaluation.experiments import (
    ExperimentStore,
    file_hash,
    load_study,
    mark_stage_complete,
    source_revision,
)
from prescriptxai.evaluation.latency import benchmark_serial_checkpointed
from prescriptxai.evaluation.runner import make_cases, observed_alert_cohort, run_experiment_case
from prescriptxai.evaluation.study import (
    Cohort,
    diagnostic_cases,
    effective_asset_config,
    quality_cases,
    run_reference_stage,
    study_manifest,
    verify_asset_index,
)
from prescriptxai.pipeline import PrescriptXAI


def test_recipe_policies_sensitivities_and_empty_alerts(tmp_path: Path) -> None:
    """Select real first alerts before sampling and vary exactly one declared setting."""
    config, frame = fitted_experiment(tmp_path)
    pipeline = PrescriptXAI.from_config(config)
    alerts, contexts, accounting = observed_alert_cohort(pipeline, frame)
    first = alerts.loc[alerts.first_alert]
    cohort = Cohort(
        "FD001/mlp/v1/base/internal_heldout_all_alerts",
        "FD001",
        "mlp",
        "internal_heldout_all_alerts",
        "v1",
        tmp_path / "config.yaml",
        config,
        alerts.iloc[1:],
        contexts,
        accounting,
        pd.DataFrame(
            {
                "engine_id": [1, 1, 2, 2, 3, 3, 4, 4],
                "cycle": [1, 2] * 4,
                "rul": [70] * 8,
                "sensor_1": [-2.0, -1.0, 0.0, 1.0, 2.0, 1.5, 0.5, -0.5],
                "sensor_2": [2.0] * 8,
            }
        ),
        first,
    )
    study = load_study(Path("configs/experiments/phase7-study.yaml")).model_copy(
        update={
            "diagnostic_models": ["FD001/mlp"],
            "horizon_H_grid": [30],
            "reference_distributions": ["all_cycles"],
            "solver_seeds": [17, 18],
            "diagnostic_max_queries": 1,
        }
    )
    quality = list(quality_cases([cohort], study))
    thorough = [c for c in quality if c.mode == "thorough"]
    assert len(quality) == 6 and {c.state["cycle"] for c in thorough} == {1}
    variants = list(diagnostic_cases([cohort], study, {}))
    assert len({c.variant for c in variants}) == len(variants)
    assert any(
        c.variant == "no_mahalanobis" and not c.policy["check_distribution"] for c in variants
    )
    for case in variants:
        if case.variant.startswith("sensitivity-horizon-K-"):
            assert case.config.recourse.rate_horizon_steps == int(case.variant.rsplit("-", 1)[1])
            assert case.config.tau_safe == config.tau_safe
        if case.variant.startswith("sensitivity-threshold"):
            assert (
                case.config.recourse.model_dump()
                == config.recourse.model_copy(update={"search_mode": "fast"}).model_dump()
            )
    assert (
        list(diagnostic_cases([cohort], study.model_copy(update={"diagnostic_models": []}), {}))
        == []
    )
    safe = frame.copy()
    safe.sensor_1 = 2.0
    empty, _, empty_counts = observed_alert_cohort(pipeline, safe)
    assert empty.empty and empty_counts["alert_rows"] == 0 and empty.first_alert.dtype == bool
    assert empty.loc[empty.first_alert].empty


def test_actual_git_manifest_and_seal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use a genuine temporary Git repository and reject changed frozen inputs."""
    study = load_study(Path("configs/experiments/phase7-study.yaml"))
    config, frame = fitted_experiment(tmp_path)
    config.data.root = tmp_path / "raw"
    config.paths.raw_data = config.data.root
    config.data.root.mkdir()
    archive = config.data.root / config.data.archive_name
    archive.write_bytes(b"test-only provenance bytes; not ingested as telemetry")
    config_path = tmp_path / "frozen.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    study.frozen_solver_config = config_path
    study.artifact_root = tmp_path / "assets"
    study.artifact_root.mkdir()
    (study.artifact_root / "preparation.json").write_text("{}", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/evaluation_protocol.md").write_text("Test-only protocol", encoding="utf-8")
    historical_root = tmp_path / "artifacts/phase6"
    historical_root.mkdir(parents=True)
    (historical_root / "pipeline.json").write_text(
        json.dumps({"archive_sha256": file_hash(archive)})
    )
    for model in ("xgboost", "mlp", "lstm"):
        (tmp_path / f"artifacts/FD001-{model}.joblib").write_bytes(
            config.artifacts.model.read_bytes()
        )
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check=True)
    subprocess.run(["git", "add", "frozen.yaml", "features.yaml", "docs"], check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "test-only fixture inputs",
        ],
        check=True,
    )
    revision = source_revision()
    index = {"preparation_source": revision, "models": {}}
    seal_preparation_inputs(study, index)
    seal_preparation_inputs(study, index)
    pipeline = PrescriptXAI.from_config(config)
    alerts, contexts, accounting = observed_alert_cohort(pipeline, frame)
    cohort = Cohort(
        "fixture",
        "FD001",
        "mlp",
        "fixture",
        "v1",
        config_path,
        config,
        alerts,
        contexts,
        accounting,
        frame,
        alerts.loc[alerts.first_alert],
    )
    manifest = study_manifest(study, config_path, index, [cohort], "fixture")
    assert manifest["git_hash"] == revision and manifest["frozen_config_sha256"] == file_hash(
        config_path
    )
    assert manifest["cohorts"]["fixture"]["engine_ids"] == [6]
    failed_config = config.model_copy(deep=True)
    failed_config.recourse.max_scaled_distance = 0.01
    case = next(
        make_cases(
            failed_config,
            config_path,
            alerts.iloc[:1],
            contexts,
            dataset="FD001",
            model="mlp",
            population="paired_internal_diagnostic",
            protocol="v1",
            variant="full",
            mode="fast",
            seeds=[17],
            free_rate_fraction=1,
        )
    )
    record = run_experiment_case(case)
    assert not record.joint
    manifest["expected_queries"] = {"diagnostics": 1, "quality": 0}
    manifest["expected_reference_case_ids"] = [case.case_id]
    store = ExperimentStore(tmp_path / "run", manifest)
    store.register_case(case)
    store.save(record)
    store.close()
    with pytest.raises(ValueError, match="complete verified diagnostic"):
        run_reference_stage(study, tmp_path / "run")
    mark_stage_complete(tmp_path / "run", "diagnostics", revision, 1)
    run_reference_stage(study, tmp_path / "run")
    run_reference_stage(study, tmp_path / "run")
    reference = json.loads((tmp_path / "run/reference.json").read_text())
    assert reference[case.case_id]["oracle"]["production_reproduced"]
    assert reference[case.case_id]["oracle"]["classification"] == "unresolved_finite_search"
    (tmp_path / "src").mkdir()
    (tmp_path / "src/change.py").write_text("# test change", encoding="utf-8")
    with pytest.raises(ValueError, match="commit experimental"):
        source_revision()
    with pytest.raises(ValueError, match="commit experimental"):
        benchmark_serial_checkpointed(pipeline, alerts, study, tmp_path / "dirty-timing")
    assert source_revision(require_clean=False) == revision
    archive.write_bytes(b"changed")
    with pytest.raises(ValueError, match="archive differs"):
        seal_preparation_inputs(study, index)


def test_index_rejects_incomplete_artifacts(tmp_path: Path) -> None:
    """Require complete declared fold coverage before any real scoring begins."""
    study = load_study(Path("configs/experiments/phase7-study.yaml"))
    with pytest.raises(ValueError, match="incomplete"):
        verify_asset_index(study, {"models": {}})
    config, _ = fitted_experiment(tmp_path)
    paths = {
        "model": str(config.artifacts.model),
        "coupling": str(config.artifacts.model),
        "mahalanobis_v1": str(config.artifacts.mahalanobis),
    }
    resolved = effective_asset_config(config, {"paths": paths}, "v1")
    assert resolved.artifacts.model == config.artifacts.model
