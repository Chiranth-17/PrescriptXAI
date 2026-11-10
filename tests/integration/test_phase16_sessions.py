"""Exercise real HTTP and WebSocket authentication boundaries."""

from __future__ import annotations

import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from prescriptxai import security, security_http
from prescriptxai.api import create_app
from prescriptxai.security import AuthStore, hash_password
from prescriptxai.security_http import SessionGate
from prescriptxai.workspace import launch_dashboard

_ORIGIN = "https://testserver"
_OPERATOR = "operator"
_ADMIN = "admin"


@pytest.fixture(scope="module")
def passwords() -> dict[str, str]:
    """Generate distinct per-run credentials instead of storing fixture secrets."""
    return {_OPERATOR: secrets.token_urlsafe(24), _ADMIN: secrets.token_urlsafe(24)}


@pytest.fixture(scope="module")
def verifiers(passwords: dict[str, str]) -> dict[str, str]:
    """Generate the same salted verifier format an administrator uses."""
    return {role: hash_password(password) for role, password in passwords.items()}


@pytest.fixture
def credentials(monkeypatch: pytest.MonkeyPatch, verifiers: dict[str, str]) -> None:
    """Configure isolated serving credentials for a single test."""
    monkeypatch.setenv("PRESCRIPTXAI_AUTH_ORIGIN", _ORIGIN)
    monkeypatch.setenv("PRESCRIPTXAI_OPERATOR_PASSWORD_HASH", verifiers[_OPERATOR])
    monkeypatch.setenv("PRESCRIPTXAI_ADMIN_PASSWORD_HASH", verifiers[_ADMIN])


def test_service_refuses_unconfigured_and_default_credentials(
    credentials: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Default launch requires credentials and explicit demo is loopback-only."""
    monkeypatch.delenv("PRESCRIPTXAI_AUTH_ORIGIN")
    with pytest.raises(ValueError, match="PRESCRIPTXAI_AUTH_ORIGIN"):
        create_app()
    monkeypatch.setenv("PRESCRIPTXAI_AUTH_ORIGIN", _ORIGIN)
    salt = bytes(16)
    digest = security._password_digest("admin", salt).hex()
    monkeypatch.setenv(
        "PRESCRIPTXAI_ADMIN_PASSWORD_HASH", f"pbkdf2-sha256:600000:{salt.hex()}:{digest}"
    )
    with pytest.raises(ValueError, match="uses a default password"):
        create_app()
    config = tmp_path / "dashboard.yaml"
    config.write_text("profiles: {}")
    with pytest.raises(ValueError, match="loopback"):
        launch_dashboard(config, "0.0.0.0", 8501, local_demo=True)


def test_api_sessions_require_origin_and_csrf_and_enforce_roles(
    credentials: None, passwords: dict[str, str]
) -> None:
    """A genuine login protects data, role boundaries and signed-out requests."""
    app = create_app()
    assert TestClient(app).get("/version").status_code == 400
    with TestClient(app, base_url=_ORIGIN) as client:
        assert client.get("/version").status_code == 401
        assert client.get("/version", headers={"host": "foreign.example"}).status_code == 400
        payload = {"username": _OPERATOR, "password": passwords[_OPERATOR]}
        assert client.post("/auth/login", json=payload).status_code == 403
        login = client.post("/auth/login", headers={"Origin": _ORIGIN}, json=payload)
        assert login.status_code == 200
        cookie = login.headers["set-cookie"].lower()
        assert all(x in cookie for x in ("__host-", "secure", "httponly", "samesite=strict"))
        assert login.headers["cache-control"] == "no-store"
        assert login.json()["role"] == _OPERATOR
        assert client.get("/machines").status_code == 200
        assert client.get("/auth/admin").status_code == 403
        assert client.get("/auth/session").status_code == 200
        token = login.json()["access_token"]
        csrf = login.json()["csrf"]
        same_origin = {"Origin": _ORIGIN}
        assert client.post("/assess", headers=same_origin, json={}).status_code == 403
        assert (
            client.post(
                "/assess", headers={**same_origin, "X-CSRF-Token": csrf}, json={}
            ).status_code
            == 422
        )
        assert (
            client.post("/auth/logout", headers=same_origin, json={"csrf": "wrong"}).status_code
            == 403
        )
        assert (
            client.post(
                "/auth/logout", headers=same_origin, data={"csrf": csrf}, follow_redirects=False
            ).status_code
            == 303
        )
        assert (
            client.get("/version", headers={"Authorization": f"Bearer {token}"}).status_code == 401
        )
        admin = client.post(
            "/auth/login",
            headers=same_origin,
            json={"username": _ADMIN, "password": passwords[_ADMIN]},
        )
        assert admin.status_code == 200
        bearer = {"Authorization": "Bearer " + admin.json()["access_token"]}
        assert client.get("/auth/admin", headers=bearer).json() == {"accounts": [_OPERATOR, _ADMIN]}
        assert client.post("/assess", headers=bearer, json={}).status_code == 422
        assert (
            client.post("/auth/logout", headers=bearer, follow_redirects=False).status_code == 303
        )


def test_login_burst_has_a_bounded_attempt_window(credentials: None) -> None:
    """Reject a sustained credential attack even when user names keep changing."""
    client = TestClient(create_app(), base_url=_ORIGIN)
    for attempt in range(6):
        response = client.post(
            "/auth/login",
            headers={"Origin": _ORIGIN},
            json={"username": f"unknown-{attempt}", "password": "invalid"},
        )
        assert response.status_code == 401
    rejected = client.post(
        "/auth/login",
        headers={"Origin": _ORIGIN},
        json={"username": _OPERATOR, "password": "invalid"},
    )
    assert rejected.status_code == 429
    assert rejected.json()["detail"] == "too many login attempts"


def test_websocket_requires_session_and_closes_on_idle_expiry(
    credentials: None, passwords: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Check dashboard upgrades, cross-origin refusal and live session expiration."""
    clock = [1000.0]
    monkeypatch.setattr(security, "monotonic", lambda: clock[0])
    monkeypatch.setattr(security_http, "monotonic", lambda: clock[0])

    async def echo(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                await websocket.send_text(await websocket.receive_text())
        except WebSocketDisconnect:
            return

    frontend = Starlette(routes=[WebSocketRoute("/_stcore/stream", echo)])
    client = TestClient(
        SessionGate(frontend, AuthStore.from_environment(), dashboard=True), base_url=_ORIGIN
    )
    login_page = client.get("/", headers={"Accept": "text/html"}, follow_redirects=False)
    assert login_page.headers["location"] == "/auth/login"
    assert "Sign in" in client.get("/auth/login").text
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("wss://testserver/_stcore/stream", headers={"Origin": _ORIGIN}),
    ):
        pytest.fail("unauthenticated socket opened")
    login = client.post(
        "/auth/login",
        headers={"Origin": _ORIGIN},
        follow_redirects=False,
        data={"username": _OPERATOR, "password": passwords[_OPERATOR]},
    )
    assert login.status_code == 303
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(
            "wss://testserver/_stcore/stream", headers={"Origin": "https://foreign.example"}
        ),
    ):
        pytest.fail("cross-origin socket opened")
    with client.websocket_connect(
        "wss://testserver/_stcore/stream", headers={"Origin": _ORIGIN}
    ) as websocket:
        websocket.send_text("preview")
        assert websocket.receive_text() == "preview"
        clock[0] += 301
        websocket.send_text("expired")
        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_text()
        assert error.value.code == 4401
