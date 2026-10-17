"""Integration tests for API, evaluation sampling, and report serialization."""

import json
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from typer.testing import CliRunner

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.api import create_app
from prescriptxai.cli import app
from prescriptxai.config import load_config
from prescriptxai.evaluation.report import write_evaluation_report
from prescriptxai.evaluation.runner import evaluate_states
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


def test_cli_help_lists_configured_workflows() -> None:
    """Expose the implemented workflow commands from the installed CLI entrypoint."""
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "recommend" in result.stdout
    assert "evaluate" in result.stdout


def test_dashboard_empty_state_shows_dataset_and_configuration_limits() -> None:
    """The real operator UI explains static-data and missing actuator limitations."""
    dashboard_path = Path(__file__).resolve().parents[2] / "src/prescriptxai/dashboard/app.py"
    app_test = AppTest.from_file(dashboard_path).run(timeout=30)
    assert not app_test.exception
    assert any(
        "does not establish real-machine safety or RUL extension" in item.value
        for item in app_test.warning
    )
    assert any(
        "Configured controllable channels are C-MAPSS telemetry proxies" in item.value
        for item in app_test.info
    )


def _engine() -> PrescriptXAIEngine:
    """Build the explicitly synthetic engine used for API/evaluation wiring tests."""
    model, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_scaled_distance = 3.0
    config.recourse.max_iterations = 100
    validator = fit_mahalanobis_validator(training, model, model.training_engine_ids, config)
    return PrescriptXAIEngine(config, taxonomy, model, validator)


def test_api_health_recommend_and_invalid_state() -> None:
    """The service returns each tier separately and rejects incomplete machine states."""
    client = TestClient(create_app(_engine()))

    health = client.get("/health")
    response = client.post("/recommend", json={"state": {"actuator": -2, "sensor": 2}})
    invalid = client.post("/recommend", json={"state": {"actuator": -2}})

    assert health.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert body["outcome"]["model_valid"] is True
    assert body["actuator_constraints_feasible"] is True
    assert body["original_state"]["actuator"] == -2.0
    assert body["new_state"]["actuator"] > -2.0
    assert "tier1_model" in body["tiers"]
    assert "tier4_coupling" in body["tiers"]
    assert invalid.status_code == 422


def test_evaluation_samples_deterministically_and_writes_measured_reports(tmp_path: Path) -> None:
    """Evaluation uses only high-risk rows, honors query limits, and reports its actual records."""
    engine = _engine()
    engine.config.evaluation.max_queries = 2
    rows = pd.DataFrame(
        [
            {"engine_id": engine_id, "cycle": cycle, "actuator": actuator, "sensor": 2.0}
            for engine_id in range(10, 14)
            for cycle, actuator in (
                (1, -2.0),
                (2, -1.5),
                (3, 2.0),
                (4, -20.0),
            )
        ]
    )

    run = evaluate_states(engine, rows, ingestion_ms=8.0)
    repeated = evaluate_states(engine, rows, ingestion_ms=8.0)
    json_path = tmp_path / "evaluation.json"
    markdown_path = tmp_path / "evaluation.md"
    write_evaluation_report(run, json_path, markdown_path)
    serialized = json.loads(json_path.read_text(encoding="utf-8"))

    assert run.summary.eligible_high_risk_states > run.summary.evaluated_states
    assert run.summary.evaluated_states == 2
    assert run.infeasible_high_risk_states == 4
    assert all(record.actuator_bound_violations == 0 for record in run.records)
    assert all(record.rate_limit_violations == 0 for record in run.records)
    assert all(record.frozen_feature_violations == 0 for record in run.records)
    assert [record.engine_id for record in run.records] == [
        record.engine_id for record in repeated.records
    ]
    assert len(serialized["records"]) == 2
    assert markdown_path.is_file()
    assert "Model validity and physical plausibility" in markdown_path.read_text(encoding="utf-8")
