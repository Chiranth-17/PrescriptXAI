"""Transport security tests for public API responses."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prescriptxai.api import create_app
from prescriptxai.config import load_config


def test_security_headers_cover_responses_and_preflights() -> None:
    """Verify security headers on data, schema errors, and allowed or rejected origins."""
    config = load_config(Path("configs/default.yaml"))
    config.api.cors_origins = ["https://operator.example"]
    client = TestClient(create_app(config=config, local_demo=True))
    allowed, rejected = (
        client.options(
            "/assess",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
        for origin in ("https://operator.example", "https://foreign.example")
    )
    assert allowed.headers["access-control-allow-origin"] == "https://operator.example"
    assert "access-control-allow-origin" not in rejected.headers
    assert rejected.json() == {"detail": "CORS preflight rejected", "mode": "FAST"}
    schema_error = client.post("/assess", json={"state": {}})
    assert schema_error.status_code == 422
    for response in (client.get("/version"), schema_error, allowed, rejected):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("field", ["cors_origins", "cors_methods", "cors_headers"])
def test_application_refuses_wildcard_cors(field: str) -> None:
    """Reject wildcard policy before binding a listener."""
    config = load_config(Path("configs/default.yaml"))
    setattr(config.api, field, ["*"])
    with pytest.raises(ValueError, match="requires explicit origins"):
        create_app(config=config, local_demo=True)


def test_unexpected_api_error_does_not_expose_exception_details() -> None:
    """Inject an endpoint failure and check its public JSON response."""
    app = create_app(local_demo=True)

    @app.get("/test-fault")
    def fault() -> None:
        raise RuntimeError("internal path and failure details")

    response = TestClient(app).get("/test-fault")
    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error", "mode": "FAST"}
    assert response.headers["x-content-type-options"] == "nosniff"
