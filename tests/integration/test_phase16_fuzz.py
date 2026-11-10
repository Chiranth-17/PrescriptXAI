"""Exercise the published request schemas with deterministic HTTP fuzzing."""

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from prescriptxai.api import create_app

_WRITES = (
    ("/assess", "state"),
    ("/recommend", "state"),
    ("/recommend/batch", "states"),
    ("/validate-controls", "state"),
    ("/simulate/risk", "rows"),
    ("/simulate/prescribe", "rows"),
    ("/machines/cmapss_fd001/assess", "rows"),
    ("/machines/cmapss_fd001/recommend", "rows"),
    ("/machines/cmapss_fd001/validate-controls", "rows"),
    ("/machines/cmapss_fd001/feedback", "rows"),
    ("/feedback", "rows"),
)
_READS = {
    "/health": 503,
    "/config": 503,
    "/version": 200,
    "/machines": 200,
    "/machines/cmapss_fd001/spec": 200,
    "/machines/cmapss_fd001/scenarios": 200,
    "/feedback/summary?machine_id=cmapss_fd001": 200,
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Use the explicit local mode to exercise schema checks beyond authentication."""
    return TestClient(create_app(local_demo=True))


@pytest.mark.parametrize("path,field", _WRITES)
@given(value=st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=30)))
@settings(max_examples=12, deadline=None, derandomize=True)
def test_post_schemas_reject_invalid_container_types(
    client: TestClient, path: str, field: str, value: object
) -> None:
    """Reach the declared schema of every scientific or feedback POST route."""
    response = client.post(path, json={field: value})
    assert response.status_code == 422
    payload = response.json()
    assert payload["mode"] == "FAST"
    assert any(error["loc"] == ["body", field] for error in payload["errors"])
    assert "input" not in payload["errors"][0] and "Traceback" not in response.text


@pytest.mark.parametrize("path,field", _WRITES)
@given(number=st.sampled_from(("NaN", "Infinity", "-Infinity", "1e400", "-1e400")))
@settings(max_examples=5, deadline=None, derandomize=True)
def test_nonfinite_json_is_rejected_before_any_route_loads_a_model(
    client: TestClient, path: str, field: str, number: str
) -> None:
    """Reject non-standard constants and overflowing exponents even when nested."""
    response = client.post(
        path,
        content=f'{{"{field}":[{{"value":{number}}}]}}',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert "nonfinite numbers" in response.json()["detail"]


@pytest.mark.parametrize(("path", "expected"), _READS.items())
@given(request_id=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=60))
@settings(max_examples=8, deadline=None, derandomize=True)
def test_get_routes_return_safe_request_ids(
    client: TestClient, path: str, expected: int, request_id: str
) -> None:
    """Exercise each read route's input header without exposing unsafe identifiers."""
    response = client.get(path, headers={"X-Request-ID": request_id})
    assert response.status_code == expected
    value = response.headers["x-request-id"]
    assert value and all(char.isalnum() or char in "-_" for char in value)
    assert response.headers["x-content-type-options"] == "nosniff"


@given(name=st.text(alphabet="abc123", min_size=1, max_size=12))
@settings(max_examples=12, deadline=None, derandomize=True)
def test_machine_get_routes_reject_unknown_scope(client: TestClient, name: str) -> None:
    """A request cannot change the selected machine by guessing a different identifier."""
    machine = f"fuzz_{name}"
    for path in (
        f"/machines/{machine}/spec",
        f"/machines/{machine}/scenarios",
        f"/feedback/summary?machine_id={machine}",
    ):
        response = client.get(path)
        assert response.status_code == 404
        assert response.json()["detail"] == "unknown machine"
