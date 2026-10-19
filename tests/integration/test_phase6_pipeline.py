"""Exercise the public decision pipeline on explicitly synthetic logic fixtures."""

import json
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
from fastapi.testclient import TestClient
from pydantic import ValidationError

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.api import create_app
from prescriptxai.config import load_config
from prescriptxai.evaluation.latency import benchmark_pipeline, summarize_latency
from prescriptxai.models.torch_models import LSTMFailureModel, MLPFailureModel
from prescriptxai.pipeline import (
    FeatureError,
    HistoryError,
    InputError,
    PrescriptXAI,
    PrescriptXAIEngine,
    UnitError,
)
from prescriptxai.schemas import FeatureDelta, InputContext, RecourseResult, TierValidation
from prescriptxai.validation.base import CheckResult
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


@pytest.fixture
def service() -> PrescriptXAI:
    """Fit real scaler/covariance around a test-only deterministic predictor."""
    model, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.search_mode = "fast"
    config.recourse.max_iterations = 15
    config.recourse.restarts = config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = 1
    config.recourse.support_search_limit = 1
    config.evaluation.bootstrap_replicates = 100
    validator = fit_mahalanobis_validator(training, model, model.training_engine_ids, config)
    return PrescriptXAI(PrescriptXAIEngine(config, taxonomy, model, validator))


def comparable(result: RecourseResult) -> dict[str, object]:
    """Exclude wall time and request identity from deterministic content comparisons."""
    return result.model_dump(mode="json", exclude={"run_id", "timings"})


@pytest.mark.parametrize("mode", ["fast", "thorough"])
def test_public_contract_and_reproducibility(service: PrescriptXAI, mode: str) -> None:
    """Both modes expose true risks, deltas, independent evidence and fixed-seed results."""
    state = {"actuator": -2.0, "sensor": 2.0}
    result = service.recommend(state, mode=mode)
    again = service.recommend(pd.Series(state), mode=mode)
    assert comparable(result) == comparable(again)
    assert RecourseResult.model_validate_json(result.model_dump_json()) == result
    assert result.status == "RECOVERABLE"
    assert result.risk_after <= service.config.tau_safe
    assert result.evidence_level == "E3" and result.proxy_assumptions and result.assumptions
    assert result.mode == mode.upper() and result.config_hash and result.solver_settings
    assert all(v is None or v >= 0 for v in result.timings.model_dump().values())
    assert service.engine.config.recourse.search_mode == "fast"
    explanation = service.explain_result(result)
    assert explanation.actions and "Increase actuator" in explanation.actions[0]
    assert explanation.verdict["joint"]
    assert service.info()["feature_names"] == ("actuator", "sensor")


def test_gate_exact_boundary_and_zero_action(service: PrescriptXAI) -> None:
    """Compare equality at the configured gate using the actual fixture's measured risk."""
    state = {"actuator": -2.0, "sensor": 2.0}
    risk = service.assess(state).risk
    service.config.tau_danger = risk
    assert service.recommend(state).alert
    service.config.tau_danger = np.nextafter(risk, 1.0)
    result = service.recommend(state)
    assert result.status == "NO_INTERVENTION" and result.triage is None
    assert result.original_state == result.new_state and not result.delta_per_feature
    assert not result.validation_report.model_valid
    assert result.timings.optimization_ms == 0
    # Set the measured sigmoid value exactly at each requested threshold via calibration-free input.
    mean, scale = (
        service.engine.model.scaler.scaler.mean_[0],
        service.engine.model.scaler.scaler.scale_[0],
    )
    for probability in (0.8, 0.79):
        raw = mean + scale * np.log(1 / probability - 1) / 5
        service.config.tau_danger = 0.8
        assessed = service.assess({"actuator": raw, "sensor": 2})
        assert assessed.risk == pytest.approx(probability)
        assert assessed.alert == (probability >= 0.8)
        if probability == 0.79:
            assert not assessed.alert


def test_below_gate_out_of_bounds_is_not_feasible(service: PrescriptXAI) -> None:
    """Zero intervention cannot conceal an already invalid proxy actuator."""
    result = service.recommend({"actuator": 20, "sensor": 2})
    assert result.status == "NO_INTERVENTION"
    assert not result.action_feasible and not result.validation_report.tier3_engineering.passed


@pytest.mark.parametrize(
    ("raw", "context", "error"),
    [
        ({"actuator": 0}, None, FeatureError),
        ({"actuator": 0, "sensor": 2, "unknown": 1}, None, FeatureError),
        ([1], None, FeatureError),
        ([[1, 2]], None, FeatureError),
        ([0, 2], {"feature_names": ["sensor", "actuator"]}, FeatureError),
        ({"actuator": 0, "sensor": 2}, {"feature_names": ["sensor", "actuator"]}, FeatureError),
        ({"actuator": float("nan"), "sensor": 2}, None, InputError),
        ({"actuator": float("inf"), "sensor": 2}, None, InputError),
        ({"actuator": True, "sensor": 2}, None, InputError),
        ({"actuator": "bad", "sensor": 2}, None, InputError),
        ({"actuator": 0, "sensor": 2}, {"units": {"actuator": "rpm"}}, UnitError),
        ({"actuator": 0, "sensor": 2}, {"telemetry": {"sensor": 3}}, FeatureError),
        ({"actuator": 0, "sensor": 2}, {"history": [[1, 2], [3]]}, HistoryError),
        ({"actuator": 0, "sensor": 2}, {"history": [[1, 2]]}, HistoryError),
        (pd.Series([0, 2], index=["actuator", "actuator"]), None, FeatureError),
    ],
)
def test_precise_input_errors(
    service: PrescriptXAI, raw: object, context: object, error: type[Exception]
) -> None:
    """Reject malformed physical telemetry before inference or optimization."""
    with pytest.raises(error):
        service.recommend(raw, context)


def test_vector_context_and_units(service: PrescriptXAI) -> None:
    """Canonical vectors and explicitly observed context produce the same assessment."""
    context = InputContext(feature_names=("actuator", "sensor"), units={"sensor": "-"})
    assert service.assess([0, 2], context).risk == service.assess({"actuator": 0, "sensor": 2}).risk
    with pytest.raises(InputError, match="mode"):
        service.recommend([0, 2], mode="invalid")


def test_batch_threads_processes_and_memory(service: PrescriptXAI) -> None:
    """Batches preserve order, isolated processes and threads preserve deterministic content."""
    frame = pd.DataFrame([{"actuator": -2.0, "sensor": 2.0}, {"actuator": 2.0, "sensor": 2.0}])
    single = [comparable(service.recommend(row)) for _, row in frame.iterrows()]
    assert [comparable(r) for r in service.recommend_batch(frame)] == single
    assert [comparable(r) for r in service.recommend_batch(frame, workers=2)] == single
    service.config.pipeline.delta_min = 0.4
    assert service.info()["config_hash"] != single[0]["config_hash"]
    assert service.assess(frame.iloc[0]).config_hash == service.info()["config_hash"]
    configured = [comparable(service.recommend(row)) for _, row in frame.iterrows()]
    assert [comparable(r) for r in service.recommend_batch(frame, workers=2)] == configured
    service.config.pipeline.delta_min = 0.3
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(service.recommend, [frame.iloc[0]] * 4))
    assert all(comparable(r) == single[0] for r in results)
    tracemalloc.start()
    large = service.recommend_batch(pd.DataFrame([frame.iloc[1]] * 128))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(large) == 128 and peak < 128 * 1024 * 1024
    for invalid in (pd.DataFrame(), pd.DataFrame([[0, 2]], columns=["actuator", "actuator"])):
        with pytest.raises(FeatureError):
            service.recommend_batch(invalid)
    with pytest.raises(InputError, match="contexts"):
        service.recommend_batch(frame, contexts=[])
    with pytest.raises(InputError, match="workers"):
        service.recommend_batch(frame, workers=0)
    service.config.pipeline.max_batch_rows = 1
    with pytest.raises(InputError, match="max_batch_rows"):
        service.recommend_batch(frame)


@pytest.mark.parametrize("window", [1, 3])
def test_genuine_lstm_fixed_history(service: PrescriptXAI, window: int) -> None:
    """The adapter matches real sequence inference and differentiates only the latest row."""
    rng = np.random.default_rng(17)
    features = rng.normal(size=(8, window, 2))
    model = LSTMFailureModel(window=window, hidden_dims=(4,), epochs=2, batch_size=8, seed=17)
    model.fit(features, np.asarray([0, 1] * 4))
    service.engine.model.estimator = model
    service.engine.model.model_type = "lstm"
    prefix = [[0.0, 2.0] for _ in range(window - 1)]
    context = InputContext(history=prefix)
    before = context.model_dump()
    bundle = service._bundle(context)
    raw = np.asarray([prefix + [[0.5, 2.0]]])
    expected = service.engine.model.predict_risk_sequence(raw)[0]
    assert service.assess({"actuator": 0.5, "sensor": 2}, context).risk == pytest.approx(expected)
    scaled = service.engine.model.scaler.transform(pd.DataFrame([{"actuator": 0.5, "sensor": 2}]))
    tensor = torch.tensor(scaled, dtype=torch.float32, requires_grad=True)
    bundle.torch_forward(tensor).sum().backward()
    assert tensor.grad is not None and torch.isfinite(tensor.grad).all()
    assert context.model_dump() == before
    result = service.recommend({"actuator": 0.5, "sensor": 2}, context)
    assert result.mode == "FAST"
    if window > 1:
        with pytest.raises(HistoryError):
            service.assess([0.5, 2])


def test_genuine_mlp_final_singleton_rescore_is_authoritative(service: PrescriptXAI) -> None:
    """Public risk and triage use final singleton scoring after genuine torch grid search."""
    bundle = service.engine.model
    raw = pd.DataFrame({"actuator": [-2, -1, 0, 1, 2], "sensor": [2] * 5})
    estimator = MLPFailureModel(hidden_dims=(8, 4), epochs=20, batch_size=5, seed=17)
    estimator.fit(bundle.scaler.transform(raw), np.asarray([1, 1, 0, 0, 0]))
    bundle.estimator = estimator
    bundle.model_type = "mlp"
    risk = bundle.predict_risk(raw)
    index = int(np.argmax(risk))
    service.config.tau_danger = service.config.model.danger_threshold = float(risk[index]) - 1e-4
    result = service.recommend(raw.iloc[index])
    assert result.alert and result.solver_settings["grid_ran"]
    final = float(bundle.predict_risk(pd.DataFrame([result.new_state]))[0])
    assert result.risk_after == result.validation_report.tier1_model_safety.measurement == final
    assert result.validation_report.model_valid == (final <= service.config.tau_safe)
    if result.failure is not None:
        assert result.failure.risk_reached == final


@pytest.mark.parametrize("status,risk", [("PARTIAL", 0.4), ("ESCALATE", 0.75)])
def test_constructed_triage_and_forgery(service: PrescriptXAI, status: str, risk: float) -> None:
    """Contract triage follows independent tiers and the documented minimum risk drop."""
    result = service.recommend({"actuator": -2, "sensor": 2})
    payload = result.model_dump(exclude_computed_fields=True)
    payload.update(status=status, triage=status, risk_after=risk)
    payload["failure"] = {
        "reason": "fixture",
        "message": "constructed triage",
        "closest_candidate": result.new_state,
        "risk_reached": risk,
        "failing_tiers": ["tier1_model"],
        "suggested_escalation": "maintenance",
    }
    report = result.validation_report.model_dump(exclude_computed_fields=True)
    report["tier1_model_safety"] = TierValidation(passed=False, measurement=risk).model_dump()
    payload["validation_report"] = report
    validated = RecourseResult.model_validate(payload)
    assert validated.status == status and not validated.joint
    explanation = service.explain_result(validated)
    assert bool(explanation.actions) == (status == "PARTIAL")
    assert explanation.warnings
    payload.update(status="RECOVERABLE", triage="RECOVERABLE")
    with pytest.raises(ValidationError, match="triage"):
        RecourseResult.model_validate(payload)
    payload["config_hash"] = ""
    with pytest.raises(ValidationError, match="config_hash"):
        RecourseResult.model_validate(payload)


def test_schema_finite_and_complete(service: PrescriptXAI) -> None:
    """Finite fields, matching evidence and all raw deltas are mandatory."""
    with pytest.raises(ValidationError):
        FeatureDelta(raw_delta=1, percent_change=1, scaled_delta=float("nan"))
    with pytest.raises(ValidationError):
        TierValidation(passed=True, margin=float("inf"))
    with pytest.raises(ValidationError):
        TierValidation(passed=True, checks=(CheckResult("x", True, float("inf"), "bad"),))
    payload = service.recommend({"actuator": -2, "sensor": 2}).model_dump(mode="json")
    payload["joint"] = False
    with pytest.raises(ValidationError, match="joint"):
        RecourseResult.model_validate(payload)
    payload.pop("joint")
    payload["delta_per_feature"] = {}
    with pytest.raises(ValidationError):
        RecourseResult.model_validate(payload)


def test_api_routes_and_guardrails(service: PrescriptXAI, monkeypatch: pytest.MonkeyPatch) -> None:
    """All endpoints share the contract, auth, request IDs, CORS and bounded payload errors."""
    service.config.api.cors_origins = ["https://operator.example"]
    client = TestClient(create_app(service))
    for path in ("/health", "/config", "/version", "/openapi.json", "/docs"):
        assert client.get(path).status_code == 200
    state = {"actuator": -2.0, "sensor": 2.0}
    payload = {"state": state, "mode": "thorough"}
    response = client.post("/recommend", json=payload, headers={"X-Request-ID": "request-17"})
    assert response.status_code == 200 and response.json()["mode"] == "THOROUGH"
    assert response.headers["x-request-id"] == response.json()["run_id"] == "request-17"
    assert client.post("/assess", json=payload).json()["mode"] == "THOROUGH"
    batch = client.post("/recommend/batch", json={"states": [state], "mode": "thorough"})
    assert batch.status_code == 200 and batch.json()[0]["new_state"] == response.json()["new_state"]
    for bad in (
        {"state": {}},
        {"state": {"actuator": 0}},
        {"state": state, "context": {"history": [[1, 2], [3]]}},
    ):
        bad["mode"] = "thorough"
        rejected = client.post("/recommend", json=bad)
        assert rejected.status_code == 422 and rejected.json()["mode"] == "THOROUGH"
    assert client.post("/recommend", content="{").status_code == 422
    for malformed_mode in ([], {}, 42, True):
        rejected = client.post("/recommend", json={"state": state, "mode": malformed_mode})
        assert rejected.status_code == 422 and rejected.json()["mode"] == "FAST"
    assert (
        client.post("/recommend", json={"state": {"actuator": True, "sensor": 2}}).status_code
        == 422
    )
    assert (
        client.post(
            "/recommend/batch", json={"states": [{"actuator": True, "sensor": 2}]}
        ).status_code
        == 422
    )
    cors = client.options(
        "/recommend",
        headers={"Origin": "https://operator.example", "Access-Control-Request-Method": "POST"},
    )
    assert (
        cors.status_code == 200
        and cors.headers["access-control-allow-origin"] == "https://operator.example"
    )
    monkeypatch.setenv(service.config.api.api_key_env, "test-secret")
    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"X-API-Key": "test-secret"}).status_code == 200
    monkeypatch.delenv(service.config.api.api_key_env)
    service.config.api.max_payload_bytes = 20
    oversized = client.post(
        "/recommend", content=json.dumps(payload), headers={"Content-Length": "1"}
    )
    assert oversized.status_code == 413
    unavailable = TestClient(create_app(None, service.config))
    for path in ("/health", "/config"):
        assert unavailable.get(path).status_code == 503
    for path, body in (
        ("/assess", {"state": state}),
        ("/recommend", {"state": state}),
        ("/recommend/batch", {"states": [state]}),
    ):
        # Use a separate unloaded config with the ordinary byte limit.
        assert TestClient(create_app()).post(path, json=body).status_code == 503


def test_configured_default_mode_is_shared(service: PrescriptXAI) -> None:
    """Omitted API/library batch modes honor YAML, while an explicit mode overrides it."""
    service.config.pipeline.default_mode = "thorough"
    state = {"actuator": 2, "sensor": 2}
    client = TestClient(create_app(service))
    assert service.recommend_batch(pd.DataFrame([state]))[0].mode == "THOROUGH"
    assert client.post("/recommend", json={"state": state}).json()["mode"] == "THOROUGH"
    assert client.post("/assess", json={"state": state}).json()["mode"] == "THOROUGH"
    assert client.post("/recommend/batch", json={"states": [state]}).json()[0]["mode"] == "THOROUGH"
    assert client.post("/recommend", json={"state": state, "mode": "fast"}).json()["mode"] == "FAST"


@pytest.mark.parametrize(
    "context", [{"telemetry": {"sensor": True}}, {"engine_id": True}, {"history": [[True, 2]]}]
)
def test_boolean_context_is_not_coerced(service: PrescriptXAI, context: dict[str, object]) -> None:
    """Context uses the same strict boolean rule as the observed latest raw state."""
    with pytest.raises(InputError):
        service.assess({"actuator": 2, "sensor": 2}, context)


def test_measured_latency_and_upper_budget_rule(service: PrescriptXAI) -> None:
    """Use actual both-mode calls and engine resampling; a faster stage passes."""
    assert summarize_latency([1, 2], 1200, 1800).passed
    assert not summarize_latency([0] * 90 + [2000] * 10, None, 1800).passed
    frame = pd.DataFrame([{"engine_id": i, "actuator": 2, "sensor": 2} for i in (11, 12)])
    # Engine provenance is recognized via taxonomy context rather than invented model inputs.
    from prescriptxai.constraints.taxonomy import BoundsSpec, FeatureGroup, FeatureSpec

    service.engine.taxonomy.feature_groups.context = FeatureGroup(features=["engine_id"])
    service.engine.taxonomy.features += (
        FeatureSpec(
            name="engine_id",
            label="engine",
            unit="-",
            group="context",
            cmapss_column="unit_id",
            bounds=BoundsSpec(minimum=1, maximum=100),
        ),
    )
    report = benchmark_pipeline(service, frame)
    assert set(report.modes) == {"FAST", "THOROUGH"}
    for stages in report.modes.values():
        assert stages["pipeline_ms"].engine_count == 2
        assert stages["pipeline_ms"].p99_ms >= stages["pipeline_ms"].p50_ms
        assert stages["dashboard_ms"].passed is None
    assert json.loads(report.model_dump_json())["metadata"]["K"] == 1
    with pytest.raises(ValueError, match="warmup"):
        benchmark_pipeline(service, frame, warmup_frame=pd.DataFrame())
