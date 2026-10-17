"""Regression coverage for truthful outcomes, held-out provenance, and measured reports."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.evaluation.latency import summarize_latency
from prescriptxai.evaluation.metrics import EvaluationRecord, calculate_metrics
from prescriptxai.evaluation.report import build_evaluation_provenance, write_evaluation_report
from prescriptxai.evaluation.runner import (
    evaluate_states,
    fitted_engine_provenance,
    validate_evaluation_provenance,
)
from prescriptxai.models.calibration import ProbabilityCalibrator
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.validation.base import TierResult
from prescriptxai.validation.pipeline import ValidationReport, fit_mahalanobis_validator


def _engine() -> tuple[PrescriptXAIEngine, pd.DataFrame]:
    """Use the test-only snapshot model; production artifacts are never mutated."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    return PrescriptXAIEngine(config, taxonomy, bundle, validator), training


def _rows(engine_id: int = 20) -> pd.DataFrame:
    """Return held-out fixture rows with a non-overlapping engine by default."""
    return pd.DataFrame([
        {"engine_id": engine_id, "cycle": 1, "actuator": -1.5, "sensor": 2.0},
        {"engine_id": engine_id, "cycle": 2, "actuator": -1.4, "sensor": 2.0},
    ])


def test_model_safe_physical_candidate_remains_failure_when_action_is_infeasible() -> None:
    """Sparse-action failure returns a usable outcome rather than raising schema validation."""
    report = ValidationReport(*(TierResult(True, ()) for _ in range(4)))
    outcome = report.as_outcome(0.9, 0.1, (), recourse_feasible=False)
    assert outcome.model_valid and outcome.tier2_plausible
    assert not outcome.recourse_feasible
    assert not outcome.success


@pytest.mark.parametrize("component", ["model_training", "calibration_fit", "mahalanobis_training"])
def test_evaluation_rejects_engine_overlap_with_each_fitted_component(component: str) -> None:
    """Changing the runtime split cannot turn fitted engines into evaluation engines."""
    engine, _ = _engine()
    rows = _rows()
    if component == "model_training":
        rows = _rows(engine.model.training_engine_ids[0])
    elif component == "calibration_fit":
        engine.model.calibrator = ProbabilityCalibrator("sigmoid")
        engine.model.metrics = {"calibration": {"fit_engine_ids": [20]}}
    else:
        engine.mahalanobis = replace(engine.mahalanobis, training_engine_ids=(20,))
    with pytest.raises(ValueError, match=component):
        evaluate_states(engine, rows)


def test_evaluation_rejects_invalid_engine_metadata_and_reports_unknown_calibration() -> None:
    """Missing legacy provenance stays unknown and corrupt identities cannot be truncated."""
    engine, _ = _engine()
    rows = _rows()
    engine.model.calibrator = ProbabilityCalibrator("sigmoid")
    assert fitted_engine_provenance(engine)["calibration_fit"] is None
    rows["engine_id"] = 20.5
    with pytest.raises(ValueError, match="finite positive integers"):
        validate_evaluation_provenance(engine, rows)
    with pytest.raises(ValueError, match="engine_id and cycle"):
        validate_evaluation_provenance(engine, rows.drop(columns="cycle"))


def test_report_persists_effective_settings_fingerprints_and_actual_query_timings(
    tmp_path: Path,
) -> None:
    """A tiny end-to-end fixture run yields auditable settings and measured latency samples."""
    engine, _ = _engine()
    rows = _rows()
    source = tmp_path / "input.txt"
    source.write_text("test-only source", encoding="utf-8")
    provenance = build_evaluation_provenance(engine, rows, {"fixture": source})
    run = evaluate_states(engine, rows)
    output = tmp_path / "report.json"
    write_evaluation_report(run, output, output.with_suffix(".md"), provenance=provenance)
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["provenance"]["artifact_fingerprints"]["fixture"]["sha256"] == hashlib.sha256(
        source.read_bytes()
    ).hexdigest()
    assert saved["provenance"]["holdout_engine_ids"] == [20]
    assert saved["provenance"]["fitted_engine_ids"]["model_training"] == [1, 2, 3, 4]
    assert saved["provenance"]["effective_configuration"]["seed"] == engine.config.seed
    assert saved["provenance"]["resolved_taxonomy"]["actuator_constraints"]["actuator"]
    assert len(saved["records"]) == 2
    times = [record.inference_ms for record in run.records]
    assert all(time is not None and time > 0 for time in times)
    assert all(
        record.backend_pipeline_ms is not None
        and record.backend_pipeline_ms >= record.optimization_ms + record.validation_ms
        for record in run.records
    )
    assert run.summary.latency["inference_per_row"].p95_ms == pytest.approx(
        np.percentile(times, 95)
    )
    changed = engine.config.model_copy(deep=True)
    changed.recourse.max_iterations += 1
    engine.config = changed
    updated = build_evaluation_provenance(engine, rows, {"fixture": source})
    assert updated["effective_configuration_sha256"] != provenance["effective_configuration_sha256"]


def test_tier2_owns_synopsis_plausibility_target_and_latency_budget_preserves_range() -> None:
    """Tier 3 failure does not redefine Tier 2; fast runs retain both latency statuses."""
    engine, _ = _engine()
    record = EvaluationRecord(
        20, 1, 0.9, 0.1, True, True, False, True, 2, 20.0, 2.0, True, "fixture"
    )
    summary = calculate_metrics((record,), 1, 4.0, None, engine.config.evaluation,
                                inference_samples_ms=[1.0, 7.0])
    assert summary.tier2_plausibility_rate.value == 1.0
    assert summary.tier2_plausibility_rate.passed is True
    assert summary.physical_plausibility_rate.value == 0.0
    assert summary.physical_plausibility_rate.passed is None
    assert summary.latency["inference_per_row"].p95_ms == pytest.approx(6.7)
    latency = summarize_latency([20.0, 40.0], 1200.0, 1800.0)
    assert latency.passed is False
    assert latency.upper_budget_passed is True
    assert latency.below_target_range is True


def test_mahalanobis_threshold_modes_use_training_distances_and_persist_provenance() -> None:
    """Empirical quantiles are an explicit experiment; fixed mode preserves the configured D_max."""
    engine, training = _engine()
    fixed = engine.mahalanobis
    assert fixed.max_distance == engine.config.validation.mahalanobis_max
    assert fixed.threshold_method == "fixed"
    assert fixed.threshold_quantile is None
    engine.config.validation.d_max_threshold_method = "empirical_quantile"
    engine.config.validation.d_max_quantile = 0.75
    empirical = fit_mahalanobis_validator(
        training, engine.model, engine.model.training_engine_ids, engine.config
    )
    scaled = engine.model.scaler.transform(training[list(engine.model.feature_names)])
    distances = [fixed.distance(row) for row in scaled]
    assert empirical.max_distance == pytest.approx(np.quantile(distances, 0.75))
    assert empirical.threshold_method == "empirical_quantile"
    assert empirical.threshold_quantile == 0.75
    assert empirical.training_engine_ids == engine.model.training_engine_ids
    contaminated = training.copy()
    contaminated.loc[0, "engine_id"] = 50
    with pytest.raises(ValueError, match="exactly the model's training engines"):
        fit_mahalanobis_validator(
            contaminated, engine.model, engine.model.training_engine_ids, engine.config
        )
