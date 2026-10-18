"""Versioned validation evidence survives the integrated recommendation API."""

from pathlib import Path

from fastapi.testclient import TestClient

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.api import create_app
from prescriptxai.config import load_config
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


def test_validation_modes_margins_and_evidence_survive_api() -> None:
    """A real fixture solver response exposes each tier, assumptions, and skipped dynamics."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_changed_features = 1
    config.recourse.max_iterations = 30
    config.recourse.restarts = config.recourse.alpha_steps = 1
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    engine = PrescriptXAIEngine(config, taxonomy, bundle, validator)
    response = TestClient(create_app(engine)).post(
        "/recommend", json={"state": {"actuator": -2.0, "sensor": 2.0}}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "1.1.0"
    assert payload["evidence_level"] == "E3"
    assert payload["plausible"] and payload["constraints_ok"] and payload["joint"]
    assert payload["assumptions"]
    assert payload["tiers"]["simulator"]["status"] == "skipped"
    assert not payload["tiers"]["simulator"]["valid"]
    assert payload["tiers"]["tier1_model"]["margin"] >= 0
    assert payload["tiers"]["tier2_plausibility"]["evidence_level"] == "E2"
