"""Real searches, exact resume, finite reference and saved report generation on test-only data."""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from fixtures.experiments import fitted_experiment
from prescriptxai.evaluation.ablations import ablation_policies, ladder_policies
from prescriptxai.evaluation.diagnostics import controllable_leverage, reference_search
from prescriptxai.evaluation.experiments import (
    ExperimentStore,
    content_hash,
    file_hash,
    load_study,
    mark_stage_complete,
    source_revision,
)
from prescriptxai.evaluation.latency import benchmark_serial_checkpointed
from prescriptxai.evaluation.report import (
    sensitivity_comparison_variant,
    summarize_experiment_group,
    write_study_report,
)
from prescriptxai.evaluation.runner import (
    execute_experiment_cases,
    make_cases,
    observed_alert_cohort,
    run_experiment_case,
)
from prescriptxai.pipeline import PrescriptXAI


def test_actual_queries_resume_report_and_oracle(tmp_path: Path) -> None:
    """Retain exact inputs, execute real optimization and regenerate a report without rerunning."""
    config, frame = fitted_experiment(tmp_path)
    pipeline = PrescriptXAI.from_config(config)
    alerts, contexts, accounting = observed_alert_cohort(pipeline, frame)
    assert accounting["alert_rows"] == 3 and alerts.first_alert.sum() == 1
    cases = list(
        make_cases(
            config,
            tmp_path / "config.yaml",
            alerts,
            contexts,
            dataset="fixture",
            model="mlp",
            population="test",
            protocol="v1",
            variant="full",
            mode="fast",
            seeds=[17, 18],
            free_rate_fraction=1,
        )
    )
    frozen = tmp_path / "config.yaml"
    frozen.write_text("test-only config fingerprint", encoding="utf-8")
    study = load_study(Path("configs/experiments/phase7-study.yaml")).model_copy(
        update={"bootstrap_replicates": 100}
    )
    study_file = tmp_path / "study.yaml"
    study_file.write_text(yaml.safe_dump(study.model_dump(mode="json")), encoding="utf-8")
    manifest = {
        "run_id": "fixture",
        "git_hash": source_revision(require_clean=False),
        "frozen_config_path": str(frozen),
        "frozen_config_sha256": file_hash(frozen),
        "configuration": study.model_dump(mode="json"),
        "headline_safe_threshold": 0.2,
        "study_path": str(study_file),
        "study_file_sha256": file_hash(study_file),
    }
    directory = tmp_path / "run"
    store = ExperimentStore(directory, manifest)
    assert execute_experiment_cases(cases, store, workers=1, cpu_threads=1) == 6
    assert execute_experiment_cases(cases, store, workers=1, cpu_threads=1) == 0
    records = store.records()
    assert len(records) == 6 and all(r.risk_after <= 0.2 for r in records)
    again = run_experiment_case(cases[0])
    assert again.model_dump(exclude={"timings"}) == records[
        0
        if records[0].case_id == cases[0].case_id
        else next(i for i, r in enumerate(records) if r.case_id == cases[0].case_id)
    ].model_dump(exclude={"timings"})
    store.register_case(cases[0])
    changed = cases[0].model_copy(update={"rul": 100})
    with pytest.raises(ValueError, match="identity"):
        store.register_case(changed)
    sensitivity = config.model_copy(deep=True)
    sensitivity.recourse.rate_horizon_steps = 2
    k_case = next(
        make_cases(
            sensitivity,
            frozen,
            alerts.iloc[:1],
            contexts,
            dataset="fixture",
            model="mlp",
            population="test",
            protocol="v1",
            variant="sensitivity-horizon-K-2",
            mode="fast",
            seeds=[17],
            free_rate_fraction=1,
        )
    )
    store.register_case(k_case)
    store.save(run_experiment_case(k_case))
    failed_config = config.model_copy(deep=True)
    failed_config.recourse.max_scaled_distance = 0.01
    failed_case = next(
        make_cases(
            failed_config,
            frozen,
            alerts.iloc[:1],
            contexts,
            dataset="fixture",
            model="mlp",
            population="test",
            protocol="v1",
            variant="failure_scope",
            policy=ablation_policies()["full"],
            mode="fast",
            seeds=[17],
            free_rate_fraction=1,
        )
    )
    failed = run_experiment_case(failed_case)
    assert not failed.joint
    store.register_case(failed_case)
    store.save(failed)
    store.close()
    parallel_store = ExperimentStore(tmp_path / "parallel", manifest)
    assert execute_experiment_cases(cases[:2], parallel_store, workers=2, cpu_threads=1) == 2
    assert {r.case_id for r in parallel_store.records()} == {c.case_id for c in cases[:2]}
    parallel_store.close()
    oracle = reference_search(failed_case, failed, study)
    assert oracle["production_reproduced"] and not oracle["joint_candidate_found"]
    (directory / "reference.json").write_text(
        json.dumps({failed.case_id: {"oracle": oracle}}), encoding="utf-8"
    )
    timing_path = tmp_path / "report-timing"
    benchmark_serial_checkpointed(
        pipeline,
        alerts,
        study.model_copy(update={"latency_runs_per_mode": 3, "latency_warmups_per_mode": 1}),
        timing_path,
        allow_uncommitted_source=True,
    )
    shutil.copyfile(timing_path / "latency.json", directory / "latency.json")
    for stage in ("quality", "diagnostics", "reference", "latency"):
        mark_stage_complete(directory, stage, manifest["git_hash"], 0)
    report = write_study_report(directory, study, safe_threshold=0.2)
    assert not report["complete"] and not any(report["verified_stages"].values())
    assert sensitivity_comparison_variant("sensitivity-Dmax-chi_square-q-0.95") == (
        "ablation-Dmax-method-chi_square"
    )
    assert sensitivity_comparison_variant("sensitivity-Dmax-empirical-q-0.999") == (
        "ablation-Dmax-method-empirical"
    )
    assert sensitivity_comparison_variant("sensitivity-threshold-tau_safe-0.1") == "full"
    assert report["trajectory_health"] == "not evaluated"
    assert (directory / "report.html").is_file() and (directory / "metrics.csv").is_file()
    summary = summarize_experiment_group(
        [r.model_dump() for r in records], study, safe_threshold=0.2
    )
    assert summary["metrics"]["validity"]["ci"]["estimate"] == 1
    assert summary["metrics"]["validity"]["ci"]["engine_count"] == 1
    assert summary["metrics"]["validity"]["seed_std"] == 0
    leverage = controllable_leverage(cases[0])
    assert len(leverage["points"]) == 2
    assert oracle["classification"] == "unresolved_finite_search"
    with pytest.raises(ValueError, match="only for failed"):
        reference_search(cases[0], next(r for r in records if r.case_id == cases[0].case_id), study)
    with pytest.raises(ValueError, match="does not match"):
        reference_search(cases[0].model_copy(update={"case_id": "wrong"}), failed, study)
    frozen.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        write_study_report(directory, study, safe_threshold=0.2)


def test_real_ablation_queries_and_serial_timing(tmp_path: Path) -> None:
    """Every removal runs a real search; timing resumes without replaying completed samples."""
    config, frame = fitted_experiment(tmp_path)
    pipeline = PrescriptXAI.from_config(config)
    alerts, contexts, _ = observed_alert_cohort(pipeline, frame)
    for name, policy in {**ablation_policies(), **ladder_policies()}.items():
        case = next(
            make_cases(
                config,
                tmp_path / "config.yaml",
                alerts.iloc[:1],
                contexts,
                dataset="fixture",
                model="mlp",
                population="test",
                protocol="v1",
                variant=name,
                mode="fast",
                seeds=[17],
                free_rate_fraction=1,
                policy=policy,
            )
        )
        result = run_experiment_case(case)
        assert result.solver_settings["search_policy"] == policy.__dict__
        assert result.sparsity >= result.proxy_sparsity
        assert result.config_hash == content_hash(case.config.model_dump(mode="json"))
    unconstrained = case.model_copy(update={"variant": "unconstrained", "policy": None})
    unconstrained.case_id = content_hash(unconstrained.model_dump(mode="json", exclude={"case_id"}))
    unrestricted = run_experiment_case(unconstrained)
    assert unrestricted.risk_after == pytest.approx(
        float(pipeline.engine.model.predict_risk(pd.DataFrame([unrestricted.candidate]))[0])
    )
    study = load_study(Path("configs/experiments/phase7-study.yaml")).model_copy(
        update={
            "latency_runs_per_mode": 3,
            "latency_warmups_per_mode": 1,
            "bootstrap_replicates": 100,
        }
    )
    measured = benchmark_serial_checkpointed(
        pipeline, alerts, study, tmp_path / "timing", allow_uncommitted_source=True
    )
    assert measured == benchmark_serial_checkpointed(
        pipeline, alerts, study, tmp_path / "timing", allow_uncommitted_source=True
    )
    for stages in measured["modes"].values():
        for stage, value in stages.items():
            if stage == "dashboard_ms":
                assert value["p95_ms"] is None
            else:
                assert value["count"] == 3
                assert 0 <= value["p50_ms"] <= value["p95_ms"] <= value["p99_ms"]
    with pytest.raises(ValueError, match="nonempty"):
        benchmark_serial_checkpointed(pipeline, alerts.iloc[:0], study, tmp_path)
    with pytest.raises(ValueError, match="mismatch"):
        benchmark_serial_checkpointed(
            pipeline, alerts.iloc[:1], study, tmp_path / "timing", allow_uncommitted_source=True
        )
    assert json.loads((tmp_path / "timing/latency.json").read_text())["modes"]
    assert np.isfinite(measured["modes"]["FAST"]["pipeline_ms"]["p95_ms"])
