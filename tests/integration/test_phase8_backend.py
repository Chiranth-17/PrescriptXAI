"""Shared operator control previews use genuine library scoring and validation."""

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.api import create_app
from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import FeatureTaxonomy, load_taxonomy
from prescriptxai.models.torch_models import LSTMFailureModel
from prescriptxai.pipeline import (
    ArtifactError,
    FeatureError,
    InputError,
    PrescriptXAI,
    PrescriptXAIEngine,
)
from prescriptxai.schemas import InputContext, RecourseResult
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


@pytest.fixture
def preview_service() -> PrescriptXAI:
    """Use the existing explicit logic fixture with genuinely fitted scale/covariance."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_iterations = 15
    config.recourse.alpha_steps = config.recourse.restarts = 1
    config.recourse.l1_escalation_steps = config.recourse.support_search_limit = 1
    config.recourse.search_mode = "fast"
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    return PrescriptXAI(PrescriptXAIEngine(config, taxonomy, bundle, validator))


def test_manual_preview_matches_solver_candidate_and_frozen_contract(
    preview_service: PrescriptXAI,
) -> None:
    """Revalidate a real solved candidate, preserving all v2 result evidence and deltas."""
    state = {"actuator": -2.0, "sensor": 2.0}
    solved = preview_service.recommend(state)
    result = preview_service.validate_controls(state, {"actuator": solved.new_state["actuator"]})
    assert result.status == solved.status == "RECOVERABLE"
    assert result.risk_before == solved.risk_before
    assert result.risk_after == solved.risk_after
    assert result.validation_report == solved.validation_report
    assert result.delta_per_feature == solved.delta_per_feature
    assert result.timings.optimization_ms == 0
    assert result.solver_settings["manual_preview"] is True
    assert RecourseResult.model_validate_json(result.model_dump_json()) == result
    assert result.schema_version == result.validation_report.schema_version == "2.0.0"
    assert any("no optimization" in item for item in result.warnings)


@pytest.mark.parametrize("controls", [{"sensor": 1.0}, {"unknown": 1.0}])
def test_manual_preview_rejects_noncontrols(
    preview_service: PrescriptXAI, controls: dict[str, float],
) -> None:
    """Frozen and unknown fields cannot be edited as if they were controls."""
    with pytest.raises(FeatureError, match="only configured"):
        preview_service.validate_controls({"actuator": -2.0, "sensor": 2.0}, controls)


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), True, None, "invalid", 10**1000, 1e308]
)
def test_manual_preview_rejects_bad_measurements(
    preview_service: PrescriptXAI, value: object,
) -> None:
    """Malformed controls fail with a typed input error before prediction."""
    with pytest.raises(InputError):
        preview_service.validate_controls(
            {"actuator": -2.0, "sensor": 2.0}, {"actuator": value},  # type: ignore[dict-item]
        )


def test_manual_preview_partial_failure_and_no_intervention(preview_service: PrescriptXAI) -> None:
    """Manual risk reduction does not hide remaining risk or proxy constraint failures."""
    state = {"actuator": -2.0, "sensor": 2.0}
    scaler = preview_service.engine.model.scaler.scaler
    target_risk = 0.4
    partial_control = scaler.mean_[0] + scaler.scale_[0] * np.log(1 / target_risk - 1) / 5
    partial = preview_service.validate_controls(state, {"actuator": partial_control})
    assert partial.status == "PARTIAL"
    assert partial.risk_after == pytest.approx(target_risk)
    assert partial.failure is not None and partial.failure.risk_reached > partial.tau_safe
    failure = preview_service.validate_controls(state, {"actuator": 100.0})
    assert failure.status == "ESCALATE" and not failure.action_feasible
    assert not failure.validation_report.tier3_engineering.passed
    assert failure.failure is not None and failure.failure.closest_candidate["actuator"] == 100
    safe_state = {"actuator": 2.0, "sensor": 2.0}
    unchanged = preview_service.validate_controls(safe_state, {})
    assert unchanged.status == "NO_INTERVENTION" and not unchanged.delta_per_feature
    with pytest.raises(InputError, match="below the alert"):
        preview_service.validate_controls(safe_state, {"actuator": 2.1})


@pytest.mark.parametrize("mode", [[], {"mode": "fast"}, "", True, np.asarray([1, 2])])
def test_library_modes_reject_malformed_types(preview_service: PrescriptXAI, mode: object) -> None:
    """Invalid direct-library modes produce typed errors rather than truth/set failures."""
    state = {"actuator": -2.0, "sensor": 2.0}
    for method in (preview_service.assess, preview_service.recommend):
        with pytest.raises(InputError, match="mode"):
            method(state, mode=mode)  # type: ignore[arg-type]
    with pytest.raises(InputError, match="mode"):
        preview_service.validate_controls(state, {}, mode=mode)  # type: ignore[arg-type]


def test_missing_required_coupling_fails_closed(preview_service: PrescriptXAI) -> None:
    """A declared learned coupling model cannot silently fall back to weaker YAML checks."""
    preview_service.engine.taxonomy.coupling = load_taxonomy(Path("configs/features.yaml")).coupling
    state = {"actuator": -2.0, "sensor": 2.0}
    with pytest.raises(ArtifactError, match="coupling model is unavailable"):
        preview_service.validate_controls(state, {"actuator": 0.5})
    response = TestClient(create_app(preview_service, local_demo=True)).post(
        "/validate-controls", json={"state": state, "controls": {"actuator": 0.5}},
    )
    assert response.status_code == 503 and response.json()["error_type"] == "ArtifactError"
    assert "Traceback" not in response.text


def test_manual_api_uses_library_and_typed_errors(preview_service: PrescriptXAI) -> None:
    """The optional API preview path has exact decision parity and no raw operator traceback."""
    client = TestClient(create_app(preview_service, local_demo=True))
    state = {"actuator": -2.0, "sensor": 2.0}
    controls = {"actuator": 0.5}
    direct = preview_service.validate_controls(state, controls)
    response = client.post("/validate-controls", json={"state": state, "controls": controls})
    assert response.status_code == 200
    result = RecourseResult.model_validate(response.json())
    assert result.risk_after == direct.risk_after and result.status == direct.status
    assert result.validation_report == direct.validation_report
    invalid = client.post("/validate-controls", json={"state": state, "controls": {"sensor": 1}})
    assert invalid.status_code == 422 and invalid.json()["error_type"] == "FeatureError"
    boolean = client.post(
        "/validate-controls", json={"state": state, "controls": {"actuator": True}}
    )
    assert boolean.status_code == 422 and "boolean" in boolean.text
    missing = TestClient(create_app(local_demo=True)).post(
        "/validate-controls", json={"state": state, "controls": controls}
    )
    assert missing.status_code == 503
    information = client.get("/config").json()
    assert information["dataset"] == preview_service.config.data.dataset
    assert information["history_rows"] == 0
    assert information["scaling"]["feature_names"] == ["actuator", "sensor"]


def test_manual_support_limit_is_independent_of_tier_results(
    preview_service: PrescriptXAI,
) -> None:
    """Editing more than k controls returns an explicit support failure, never an acceptance."""
    data = preview_service.engine.taxonomy.model_dump(mode="json")
    data["feature_groups"]["controllable_actuators"]["features"].append("sensor")
    data["feature_groups"]["dependent_sensors"]["features"] = []
    data["features"][1]["group"] = "controllable"
    data["features"][1]["max_rate_of_change"] = {"absolute": 4.0}
    data["actuator_constraints"]["sensor"] = {
        "minimum": 0.0, "maximum": 10.0, "max_change_per_step": 4.0,
    }
    preview_service.engine.taxonomy = FeatureTaxonomy.model_validate(data)
    preview_service.config.recourse.max_changed_features = 1
    result = preview_service.validate_controls(
        {"actuator": -2.0, "sensor": 2.0}, {"actuator": 0.5, "sensor": 2.1}
    )
    assert not result.action_feasible and result.status == "ESCALATE"
    assert result.failure is not None and result.failure.reason == "manual_sparsity_exceeded"
    assert len(result.action_features) == 2


def test_manual_lstm_keeps_the_supplied_observed_prefix(preview_service: PrescriptXAI) -> None:
    """Preview uses the fixed observed sequence rather than a repeated snapshot surrogate."""
    from prescriptxai.pipeline import HistoryError

    features = np.random.default_rng(17).normal(size=(8, 3, 2))
    estimator = LSTMFailureModel(window=3, hidden_dims=(4,), epochs=2, batch_size=8, seed=17)
    estimator.fit(features, np.asarray([0, 1] * 4))
    preview_service.engine.model.estimator = estimator
    history = ((-1.0, 2.0), (-1.5, 2.0))
    context = InputContext(history=history)
    state = {"actuator": -2.0, "sensor": 2.0}
    observed_risk = preview_service.assess(state, context).risk
    preview_service.config.tau_danger = observed_risk
    result = preview_service.validate_controls(state, {"actuator": -1.9}, context)
    assert result.risk_before == observed_risk
    assert result.risk_after == preview_service.assess(result.new_state, context).risk
    assert context.history == history
    with pytest.raises(HistoryError, match="actual prior history"):
        preview_service.validate_controls(state, {"actuator": -1.9})
