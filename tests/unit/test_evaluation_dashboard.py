"""Unit tests for measured metrics, evaluation latency, and upload state parsing."""

import json
from pathlib import Path

import pytest

from prescriptxai.config import load_config
from prescriptxai.dashboard.state import parse_state_document
from prescriptxai.evaluation.ablations import ablation_acceptance_rates
from prescriptxai.evaluation.latency import summarize_latency
from prescriptxai.evaluation.metrics import EvaluationRecord, calculate_metrics


def _record(
    engine_id: int,
    model_valid: bool,
    tier2: bool,
    tier3: bool,
    tier4: bool,
    delta_count: int,
) -> EvaluationRecord:
    """Create a unit-test record, never used as a report or benchmark output."""
    return EvaluationRecord(
        engine_id=engine_id,
        cycle=100,
        initial_risk=0.9,
        final_risk=0.15 if model_valid else 0.9,
        model_valid=model_valid,
        tier2_plausible=tier2,
        tier3_engineering_valid=tier3,
        tier4_coupling_valid=tier4,
        changed_features=delta_count,
        optimization_ms=1300,
        validation_ms=40,
        solver_success=model_valid,
        message="fixture",
    )


def test_metrics_keep_model_and_physical_validity_separate() -> None:
    """A model-valid candidate can fail physical tiers without being counted plausible."""
    config = load_config(Path("configs/default.yaml")).evaluation
    records = (
        _record(1, True, True, True, True, 2),
        _record(2, True, False, True, True, 4),
        _record(3, False, True, False, False, 0),
    )

    summary = calculate_metrics(records, 7, 5, 8, config)

    assert summary.evaluated_states == 3
    assert summary.eligible_high_risk_states == 7
    assert summary.recourse_validity_rate.value == pytest.approx(2 / 3)
    assert summary.physical_plausibility_rate.value == pytest.approx(1 / 3)
    assert summary.average_sparsity.value == pytest.approx(3)
    assert summary.mean_risk_reduction.value == pytest.approx(0.5)
    assert summary.latency["dashboard"].mean_ms is None
    assert summary.latency["dashboard"].passed is None


def test_empty_evaluation_stays_unmeasured_and_ablation_names_are_explicit() -> None:
    """Zero high-risk attempts are not reported as a passing zero or a failing zero."""
    config = load_config(Path("configs/default.yaml")).evaluation

    summary = calculate_metrics((), 0, None, None, config)

    assert summary.recourse_validity_rate.value is None
    assert summary.recourse_validity_rate.passed is None
    assert summary.physical_plausibility_rate.value is None
    assert set(ablation_acceptance_rates(())) == {
        "omit_tier2",
        "omit_tier3",
        "omit_tier4",
        "model_only",
    }


def test_latency_uses_measured_values_and_rejects_nan() -> None:
    """Latency target status is computed from samples; NaN cannot look like a pass."""
    measured = summarize_latency([2.0, 4.0, 6.0], None, 5.0)
    assert measured.mean_ms == 4.0
    assert measured.passed
    with pytest.raises(ValueError, match="finite and non-negative"):
        summarize_latency([float("nan")], None, 5.0)


def test_state_upload_parses_json_and_rejects_missing_or_nonfinite_values() -> None:
    """Uploaded states remain flat, feature-complete, and finite."""
    required = {"engine_id", "cycle", "actuator", "sensor"}
    raw = {"engine_id": 4, "cycle": 99, "actuator": 0.5, "sensor": 2}
    state = parse_state_document(json.dumps(raw), "state.json", required)

    assert state["actuator"] == 0.5
    with pytest.raises(ValueError, match="missing configured fields"):
        parse_state_document('{"actuator": 0.5}', "state.json", required)
    with pytest.raises(ValueError, match="finite numbers"):
        parse_state_document('{"actuator": NaN}', "state.json", {"actuator"})


def test_state_upload_rejects_csv_with_multiple_rows_and_unknown_suffix() -> None:
    """The operator UI requires exactly one state and a supported file type."""
    with pytest.raises(ValueError, match="exactly one state row"):
        parse_state_document("actuator,sensor\n0.5,2\n0.6,2.1\n", "state.csv", {"actuator"})
    with pytest.raises(ValueError, match="must be JSON or CSV"):
        parse_state_document("{}", "state.txt", set())
