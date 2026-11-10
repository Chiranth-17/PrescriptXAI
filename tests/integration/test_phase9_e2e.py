"""One genuine raw-data-to-browser workflow confined to a temporary directory."""

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from fixtures.hardening import PARTITIONS, fit_system
from prescriptxai.api import create_app
from prescriptxai.evaluation.runner import raw_telemetry, validate_evaluation_provenance
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import RecourseResult
from prescriptxai.validation.pipeline import validate_candidate


@pytest.mark.e2e
def test_raw_train_calibrate_validators_recommend_validate_api_dashboard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No stored predictions or fabricated tiers: use the trained temp artifacts throughout."""
    fitted = fit_system(tmp_path)
    service = PrescriptXAI.from_config(fitted.profile)
    bundle = service.engine.model
    assert bundle.training_engine_ids == PARTITIONS[0]
    assert bundle.metrics["calibration"]["fit_engine_ids"] == list(PARTITIONS[1])
    assert service.engine.coupling.training_engine_ids == PARTITIONS[0]
    assert service.engine.coupling.calibration_engine_ids == PARTITIONS[1]
    validate_evaluation_provenance(service.engine, fitted.training.splits.test)
    observations = fitted.training.splits.test
    risks = bundle.predict_risk(observations)
    row = observations.iloc[int(np.argmax(risks))]
    state = raw_telemetry(row)
    direct = service.recommend(state)
    assert direct.alert, "Synthetic fixture must exercise the actual alert/solver path"
    validation = validate_candidate(
        direct.original_state,
        direct.new_state,
        bundle,
        service.engine.taxonomy,
        service.engine.mahalanobis,
        service.config,
        service.engine.coupling,
    ).to_schema()
    assert validation == direct.validation_report
    client = TestClient(create_app(service, local_demo=True))
    response = client.post("/recommend", json={"state": state})
    assert response.status_code == 200, response.text
    api = RecourseResult.model_validate(response.json())
    assert api.status == direct.status and api.validation_report == validation
    assert api.new_state == direct.new_state and api.risk_after == direct.risk_after
    monkeypatch.setenv("PRESCRIPTXAI_DASHBOARD_CONFIG", str(fitted.dashboard))
    app = AppTest.from_string(
        "from prescriptxai.dashboard.app import main\nmain()", default_timeout=60
    ).run()
    assert not app.exception and not app.error
    app.selectbox(key="engine").set_value(int(row.engine_id)).run()
    app.slider(key="cycle").set_value(int(row.cycle)).run()
    app.button(key="recommend").click().run()
    assert not app.exception
    browser = RecourseResult.model_validate_json(app.session_state["solver_result"])
    assert browser.status == direct.status and browser.risk_after == direct.risk_after
    # CSV replay rounds the final binary bit of some raw measurements on this pandas build.
    assert browser.new_state == pytest.approx(direct.new_state, abs=1e-12, rel=1e-12)
    assert browser.validation_report.joint == validation.joint
    for name, tier in validation.model_dump().items():
        if isinstance(tier, dict) and "passed" in tier:
            actual_tier = browser.validation_report.model_dump()[name]
            assert actual_tier["passed"] == tier["passed"]
            assert actual_tier["status"] == tier["status"]
            if tier["measurement"] is not None:
                assert actual_tier["measurement"] == pytest.approx(
                    tier["measurement"], abs=1e-12, rel=1e-12
                )
    assert len(app.get("download_button")) == 3
