"""Real concurrent HTTP calls and adversarial operator payloads."""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from integration.test_phase6_artifacts_cli import fitted_config  # noqa: F401
from integration.test_phase8_backend import preview_service  # noqa: F401
from prescriptxai.api import create_app
from prescriptxai.cli import app
from prescriptxai.pipeline import InputError, PrescriptXAI
from prescriptxai.schemas import InputContext


@pytest.mark.parametrize(
    "command",
    [
        ["download"],
        ["data", "download"],
        ["data", "prepare"],
        ["constraints", "fit-coupling"],
        ["serve"],
    ],
)
def test_every_operator_command_rejects_missing_configuration_without_a_stack(
    tmp_path: Path,
    command: list[str],
) -> None:
    """The same anticipated-error contract covers preparation, fitting and server startup."""
    response = CliRunner().invoke(app, [*command, "--config", str(tmp_path / "missing.yaml")])
    assert response.exit_code == 2
    assert "missing.yaml" in response.output and "Traceback" not in response.output


@pytest.mark.parametrize(
    "method,path,content",
    [
        ("post", "/assess", b'{"state":{"\xff":0}}'),
        ("get", "/unknown-\u6e29\u5ea6", None),
        ("get", "/assess", None),
    ],
)
def test_framework_parser_and_routing_errors_keep_the_public_mode(
    method: str,
    path: str,
    content: bytes | None,
) -> None:
    """Starlette parser, unknown-path and method errors share the operator error contract."""
    response = TestClient(create_app()).request(
        method, path, content=content, headers={"Content-Type": "application/json"}
    )
    assert response.status_code in {400, 404, 405}
    assert response.json()["mode"] == "FAST"
    assert "Traceback" not in response.text


@pytest.mark.parametrize("field,value", [("history", ((True, 2.0),)), ("engine_id", True)])
def test_mutated_typed_context_is_revalidated_before_measurement_coercion(
    preview_service: PrescriptXAI,  # noqa: F811
    field: str,
    value: object,
) -> None:
    """A previously valid mutable context cannot bypass the raw mapping's strict entry checks."""
    context = InputContext()
    setattr(context, field, value)
    with pytest.raises(InputError, match="boolean"):
        preview_service.assess({"actuator": 2.0, "sensor": 2.0}, context)


@pytest.mark.parametrize("command", ["recommend", "assess", "info", "latency-bench", "evaluate"])
def test_cli_artifact_failures_are_friendly_in_an_actual_process(
    fitted_config: Path,  # noqa: F811
    command: str,
) -> None:
    """An actual command entrypoint must not let rich render the decoder's exception stack."""
    (fitted_config.parent / "model.joblib").write_bytes(b"corrupt")
    arguments = [sys.executable, "-m", "prescriptxai.cli", command]
    if command in {"recommend", "assess"}:
        state = fitted_config.parent / "state.json"
        state.write_text('{"actuator": -2, "sensor": 2}', encoding="utf-8")
        arguments.append(str(state))
    elif command == "latency-bench":
        rows = fitted_config.parent / "states.csv"
        rows.write_text("actuator,sensor\n-2,2\n", encoding="utf-8")
        arguments.append(str(rows))
    arguments.extend(["--config", str(fitted_config)])
    if command == "evaluate":
        arguments.extend(["--features", str(fitted_config.parent / "features.yaml")])
    result = subprocess.run(arguments, env=os.environ, capture_output=True, text=True, timeout=60)
    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "Traceback" not in combined and "site-packages" not in combined
    assert "decode" in combined.lower() or "artifact" in combined.lower()


def test_request_validation_never_discloses_endpoint_source_or_raw_input() -> None:
    """Unicode invalid fields get useful sanitized locations without endpoint stack details."""
    response = TestClient(create_app()).post("/assess", json={"state": {"温度": "private-marker"}})
    assert response.status_code == 422
    body = response.json()
    assert "温度" in response.text and body["detail"]
    assert "private-marker" not in response.text
    for fragment in ("File ", "api.py", str(Path.cwd()), "Traceback"):
        assert fragment not in response.text
    assert body["errors"][0]["loc"] == ["body", "state", "温度"]


def test_cli_raw_json_boolean_cannot_be_converted_into_a_measurement(
    fitted_config: Path,  # noqa: F811
) -> None:
    """Read the real CLI state file, preserving the original invalid scalar type."""
    path = fitted_config.parent / "state.json"
    path.write_text(json.dumps({"actuator": True, "sensor": 2}), encoding="utf-8")
    response = CliRunner().invoke(app, ["assess", str(path), "--config", str(fitted_config)])
    assert response.exit_code != 0
    assert "boolean" in response.output and "Traceback" not in response.output


def test_api_concurrent_requests_keep_results_and_request_ids_isolated(
    preview_service: PrescriptXAI,  # noqa: F811
) -> None:
    """Eight real threaded requests share locked predictors but no request-local state."""
    application = create_app(preview_service)

    def request(index: int) -> tuple[int, dict[str, object], str]:
        """Send an independent HTTP client request against the same fitted service."""
        with TestClient(application) as client:
            response = client.post(
                "/recommend",
                json={"state": {"actuator": -2.0 if index % 2 else 2.0, "sensor": 2.0}},
                headers={"X-Request-ID": f"phase9-{index}"},
            )
            return response.status_code, response.json(), response.headers["x-request-id"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(request, range(8)))
    for index, (status, body, request_id) in enumerate(results):
        assert status == 200 and request_id == body["run_id"] == f"phase9-{index}"
        assert body["status"] == ("RECOVERABLE" if index % 2 else "NO_INTERVENTION")
        assert body["original_state"]["actuator"] == (-2.0 if index % 2 else 2.0)


def test_empty_oversized_batches_and_reordered_dataframes_are_explicit(
    preview_service: PrescriptXAI,  # noqa: F811
) -> None:
    """Bound rows before workers; preserve named column mapping instead of positional guessing."""
    service = preview_service
    client = TestClient(create_app(service))
    with pytest.raises(InputError, match="nonempty"):
        service.recommend_batch(pd.DataFrame(columns=["actuator", "sensor"]))
    assert client.post("/recommend/batch", json={"states": []}).status_code == 422
    service.config.pipeline.max_batch_rows = 3
    frame = pd.DataFrame({"sensor": [2.0] * 4, "actuator": [2.0] * 4})
    with pytest.raises(InputError, match="batch"):
        service.recommend_batch(frame)
    assert (
        client.post("/recommend/batch", json={"states": frame.to_dict("records")}).status_code
        == 422
    )
    left = service.recommend_batch(frame.iloc[:2])
    right = service.recommend_batch(frame.iloc[:2][["actuator", "sensor"]])
    assert [item.new_state for item in left] == [item.new_state for item in right]
    assert all(item.status == "NO_INTERVENTION" for item in left)
    service.config.api.max_payload_bytes = 100
    response = client.post(
        "/assess",
        content=(b'{"state":' + b" " * 1000 + b"{}}"),
        headers={"Content-Length": "1", "Content-Type": "application/json"},
    )
    assert response.status_code == 413 and "byte limit" in response.text
