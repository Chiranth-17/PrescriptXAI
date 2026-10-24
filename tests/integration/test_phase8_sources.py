"""Real fitted artifact adapters, observed-history provenance and selection lifecycle."""

import json
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pandas as pd
import pytest
import yaml
from fastapi.testclient import TestClient

from integration.test_phase6_artifacts_cli import fitted_config  # noqa: F401
from prescriptxai.api import create_app
from prescriptxai.config import load_config
from prescriptxai.dashboard.backend import Backend, OperatorError, direct_service, profile_identity
from prescriptxai.dashboard.data import file_identity, observed_state, saved_json, telemetry
from prescriptxai.dashboard.state import (
    DashboardSettings,
    load_settings,
    parse_state_document,
    save_result,
    select_session,
)
from prescriptxai.schemas import InputContext


def test_direct_adapter_uses_real_fitted_artifacts(fitted_config: Path) -> None:  # noqa: F811
    """Load the genuine fixture model and match its public assessment/recommendation."""
    settings = DashboardSettings(profiles={"FD001": {"MLP": fitted_config}})
    identity = profile_identity(fitted_config)
    adapter = Backend(fitted_config, identity, settings)
    info = adapter.info()
    assert info["artifact_identity"] is not None
    state = {"actuator": 2.0, "sensor": 2.0}
    result = adapter.call("recommend", state, InputContext(), "fast")
    direct = direct_service(str(fitted_config), identity).recommend(state)
    assert result.risk_after == direct.risk_after
    assert result.validation_report == direct.validation_report
    assert adapter.call("assess", state, InputContext(), "fast").risk == direct.risk_before
    assert adapter.call("validate-controls", state, InputContext(), "fast", {}).risk_after >= 0
    with pytest.raises(OperatorError, match="missing"):
        adapter.call("assess", {}, InputContext(), "fast")
    with pytest.raises(OperatorError, match="unavailable"):
        profile_identity(fitted_config.parent / "absent.yaml")
    original = fitted_config.read_text(encoding="utf-8")
    fitted_config.write_text(original + "\n# modified source\n", encoding="utf-8")
    assert profile_identity(fitted_config) != identity


def test_observed_state_excludes_labels_and_preserves_actual_prefix(tmp_path: Path) -> None:
    """Use consecutive prior same-unit records in exact feature order, never labels/future."""
    frame = pd.DataFrame(
        [
            {"engine_id": e, "cycle": c, "a": e + c, "b": e - c, "rul": 99, "y": 1}
            for e in (1, 2)
            for c in (1, 2, 3)
        ]
    )
    path = tmp_path / "observed.csv"
    frame.to_csv(path, index=False)
    loaded = telemetry(str(path), "FD001", "test", file_identity(path))
    info = {
        "feature_names": ["b", "a"],
        "history_rows": 2,
        "feature_groups": {"controls": {"features": ["a"]}},
    }
    state, context = observed_state(loaded, 2, 3, info)
    assert state == {"a": 5.0, "b": -1.0}
    assert context.history == ((1.0, 3.0), (0.0, 4.0))
    assert context.engine_id == 2 and context.cycle == 3
    malformed = loaded.copy()
    malformed["a"] = malformed.a.astype(object)
    malformed.loc[(malformed.engine_id == 2) & (malformed.cycle == 3), "a"] = True
    with pytest.raises(OperatorError, match="Boolean telemetry"):
        observed_state(malformed, 2, 3, info)
    malformed.loc[(malformed.engine_id == 2) & (malformed.cycle == 3), "a"] = 5.0
    malformed.loc[(malformed.engine_id == 2) & (malformed.cycle == 1), "a"] = True
    with pytest.raises(OperatorError, match="Boolean history"):
        observed_state(malformed, 2, 3, info)
    malformed.loc[(malformed.engine_id == 2) & (malformed.cycle == 1), "a"] = float("inf")
    with pytest.raises(OperatorError, match="finite measurements"):
        observed_state(malformed, 2, 3, info)
    with pytest.raises(OperatorError, match="prior LSTM"):
        observed_state(loaded, 2, 2, info)
    with pytest.raises(OperatorError, match="no observed"):
        observed_state(loaded, 2, 4, info)
    with pytest.raises(OperatorError, match="missing features"):
        observed_state(loaded.drop(columns="a"), 2, 3, info)
    frame.iloc[:0].to_csv(path, index=False)
    with pytest.raises(OperatorError, match="observed"):
        telemetry(str(path), "FD001", "test", file_identity(path))
    frame.iloc[[0, 0]].to_csv(path, index=False)
    with pytest.raises(OperatorError, match="Duplicate"):
        telemetry(str(path), "FD001", "test", file_identity(path))


def test_session_invalidates_results_and_widgets() -> None:
    """Selection changes remove stale previews while repeated renders preserve edits."""
    session = {
        "control:a": 1,
        "solver_result": "old",
        "preview_result": "old",
        "unrelated": 5,
        "preview_controls": "old-signature",
    }
    assert select_session(session, ("model", 1, 2))
    assert "control:a" not in session and session["unrelated"] == 5
    assert "preview_controls" not in session
    save_result(session, "new")
    assert not select_session(session, ("model", 1, 2))
    assert session["preview_result"] == "new"
    session["control:a"] = 3
    session["preview_controls"] = "old-signature"
    save_result(session, "recomputed")
    assert "control:a" not in session
    assert "preview_controls" not in session


def test_sources_and_settings_fail_explicitly(tmp_path: Path) -> None:
    """Missing/corrupt evidence is unmeasured, never fabricated chart data."""
    assert load_settings(Path("configs/dashboard.yaml")).profiles["FD001"]
    path = tmp_path / "summary.json"
    path.write_text('{"actual": 0.4}', encoding="utf-8")
    assert saved_json(str(path), file_identity(path)) == {"actual": 0.4}
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(OperatorError, match="expected an evidence object"):
        saved_json(str(path), file_identity(path))
    with pytest.raises(OperatorError, match="unavailable"):
        file_identity(tmp_path / "missing.json")
    with pytest.raises(ValueError, match="finite numbers"):
        parse_state_document('{"a": true}', "state.json", {"a"})
    assert parse_state_document('{"a": 1}', "state.json", {"a"}) == {"a": 1.0}


def test_dashboard_sources_import_no_training_runtime() -> None:
    """A fresh process imports only inference/data modules for dashboard resources."""
    code = (
        "import sys,json; import prescriptxai.dashboard.backend; "
        "import prescriptxai.dashboard.data; "
        "import prescriptxai.dashboard.operator; import prescriptxai.dashboard.pages; "
        "print(json.dumps([m for m in sys.modules if m.endswith('.train') "
        "or m.startswith('prescriptxai.evaluation.assets')]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert json.loads(result.stdout.strip()) == []


def test_service_environment_variables_do_not_override_scientific_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Credentials and dashboard source selection are not serialized model settings."""
    original = load_config(Path("configs/default.yaml"))
    monkeypatch.setenv("PRESCRIPTXAI_DASHBOARD_CONFIG", "some-dashboard.yaml")
    monkeypatch.setenv("PRESCRIPTXAI_API_KEY", "fixture-secret")
    assert load_config(Path("configs/default.yaml")) == original


def test_mapped_artifact_bytes_invalidate_resource_identity(fitted_config: Path) -> None:  # noqa: F811
    """Same-path changes to selected mapped artifacts cannot reuse a stale resource key."""
    config = load_config(fitted_config)
    mapped_path = fitted_config.parent / "mapped-model.joblib"
    shutil.copyfile(config.artifacts.model, mapped_path)
    config.pipeline.model_artifacts[config.model_choice] = config.artifacts.model_copy(
        update={"model": mapped_path}
    )
    fitted_config.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    before = profile_identity(fitted_config)
    default_bytes = config.artifacts.model.read_bytes()
    mapped_path.write_bytes(mapped_path.read_bytes() + b"\0")
    assert profile_identity(fitted_config) != before
    assert config.artifacts.model.read_bytes() == default_bytes


def test_actual_http_adapter_matches_direct_and_rejects_errors(fitted_config: Path) -> None:  # noqa: F811
    """Send real HTTP through FastAPI's real service, preserving effective-mode identities."""
    identity = profile_identity(fitted_config)
    service = direct_service(str(fitted_config), identity)
    client = TestClient(create_app(service))

    class Handler(BaseHTTPRequestHandler):
        """Bridge a local socket to the actual ASGI app for portable network parity tests."""

        def dispatch(self) -> None:
            """Forward the exact request and return the service's actual response bytes."""
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            response = client.request(
                self.command, self.path, content=body, headers={"Content-Type": "application/json"}
            )
            self.send_response(response.status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.content)

        do_GET = dispatch
        do_POST = dispatch

        def log_message(self, format: str, *args: object) -> None:
            """Keep local request bodies/credentials out of the test log."""

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        settings = DashboardSettings(
            backend="api",
            api_url=f"http://127.0.0.1:{server.server_port}",
            profiles={"FD001": {"MLP": fitted_config}},
        )
        adapter = Backend(fitted_config, identity, settings)
        state = {"actuator": 2.0, "sensor": 2.0}
        for mode in ("fast", "thorough"):
            assert adapter.info()["artifact_identity"] == service.info()["artifact_identity"]
            assert (
                adapter.call("assess", state, InputContext(), mode).risk
                == service.assess(state).risk
            )
            result = adapter.call("recommend", state, InputContext(), mode)
            assert result.risk_after == service.recommend(state, mode=mode).risk_after
            assert (
                adapter.call("validate-controls", state, InputContext(), mode, {}).risk_after >= 0
            )
        with pytest.raises(OperatorError, match="API 404"):
            adapter.remote("/missing")
        with pytest.raises(OperatorError, match="API 422"):
            adapter.call("assess", {}, InputContext(), "fast")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
