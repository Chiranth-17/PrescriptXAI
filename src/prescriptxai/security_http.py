"""ASGI authentication for the API and the Streamlit HTTP/WebSocket server."""

from __future__ import annotations

import asyncio
import json
import secrets
from time import monotonic
from urllib.parse import parse_qs

from starlette.concurrency import run_in_threadpool
from starlette.requests import HTTPConnection, Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from prescriptxai.security import AuthStore, Session

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_LOGIN_HTML = """<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Sign in to PrescriptXAI</title>
<h1>Sign in to PrescriptXAI</h1>
<form method="post" action="/auth/login">
<label>User <input name="username" autocomplete="username" required></label>
<label>Password <input name="password" type="password" autocomplete="current-password"
maxlength="256" required></label>
<button type="submit">Sign in</button>
</form></html>"""


async def _form_fields(request: Request) -> dict[str, object]:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 4096:
            raise ValueError("authentication payload exceeds 4096 bytes")
        body.extend(chunk)
    content_type = request.headers.get("content-type", "").partition(";")[0].strip()
    if content_type == "application/json":
        data: object = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("authentication requires an object")
        return data
    if content_type != "application/x-www-form-urlencoded":
        raise ValueError("unsupported authentication content type")
    fields = parse_qs(body.decode(), keep_blank_values=True, max_num_fields=2, strict_parsing=True)
    if any(len(values) != 1 for values in fields.values()):
        raise ValueError("duplicate authentication field")
    return {name: values[0] for name, values in fields.items()}


class SessionGate:
    """Enforce HTTPS, role-scoped sessions and browser request origin."""

    def __init__(
        self, app: ASGIApp, auth: AuthStore, *, dashboard: bool = False, mode: str = "FAST"
    ) -> None:
        self.app, self.auth, self.dashboard, self.mode = app, auth, dashboard, mode
        self.cookie_name = "__Host-psx_dashboard" if dashboard else "__Host-psx_api"

    def _error(self, status: int, detail: str) -> JSONResponse:
        return JSONResponse({"detail": detail, "mode": self.mode}, status_code=status)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Protect both page loads and existing WebSocket sessions."""
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return
        connection = HTTPConnection(scope)
        headers = connection.headers
        secure = scope.get("scheme") in {"https", "wss"}
        trusted_host = headers.get("host", "").lower() == self.auth.host
        origin_ok = headers.get("origin") == self.auth.origin
        authorization = headers.get("authorization")
        cookie = connection.cookies.get(self.cookie_name, "")
        kind, _, bearer = (authorization or "").partition(" ")
        token = bearer if kind.lower() == "bearer" else cookie if authorization is None else ""
        session = self.auth.session(token)

        if scope["type"] == "websocket":
            if not (secure and trusted_host and origin_ok and cookie == token and session):
                await send({"type": "websocket.close", "code": 4401})
                return
            await self._websocket(scope, receive, send, token)
            return

        async def secured_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                if not any(name == b"cache-control" for name, _ in headers):
                    headers.append((b"cache-control", b"no-store"))
                for name, value in (
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                ):
                    if not any(key == name for key, _ in headers):
                        headers.append((name, value))
            await send(message)

        request = Request(scope, receive)
        response: Response
        if not secure or not trusted_host:
            response = self._error(400, "use the configured HTTPS origin")
        elif request.url.path == "/auth/login" and request.method == "GET":
            response = HTMLResponse(_LOGIN_HTML, headers={"Referrer-Policy": "same-origin"})
        elif request.url.path == "/auth/login" and request.method == "POST":
            response = (
                await self._login(request) if origin_ok else self._error(403, "origin denied")
            )
        elif session is None:
            response = self._error(401, "authentication required")
            if (
                self.dashboard
                and request.method == "GET"
                and "text/html" in headers.get("accept", "")
            ):
                response = RedirectResponse("/auth/login", status_code=303)
        elif request.url.path == "/auth/logout" and request.method == "POST":
            response = await self._logout(request, token, session, origin_ok, authorization is None)
        elif (
            request.method not in _SAFE_METHODS
            and authorization is None
            and (
                not origin_ok
                or (
                    not self.dashboard
                    and not secrets.compare_digest(
                        headers.get("x-csrf-token", "").encode(), session.csrf.encode()
                    )
                )
            )
        ):
            response = self._error(403, "CSRF validation failed")
        elif request.url.path == "/auth/admin":
            response = (
                JSONResponse({"accounts": ["operator", "admin"]})
                if session.role == "admin"
                else self._error(403, "administrator required")
            )
        elif request.url.path == "/auth/session":
            self.auth.session(token, touch=True)
            response = HTMLResponse(
                '<!doctype html><html lang="en"><meta charset="utf-8"><title>Session</title>'
                f'<h1>Signed in as {session.role}</h1><a href="/">Return to PrescriptXAI</a>'
                '<form method="post" action="/auth/logout">'
                f'<input type="hidden" name="csrf" value="{session.csrf}">'
                '<button type="submit">Sign out</button></form></html>',
                headers={"Referrer-Policy": "same-origin"},
            )
        elif self.auth.session(token, touch=True) is not None:
            await self.app(scope, receive, secured_send)
            return
        else:
            response = self._error(401, "session expired")
        await response(scope, receive, secured_send)

    async def _login(self, request: Request) -> Response:
        ip = request.client.host if request.client is not None else "unknown"
        if not self.auth.admit_login(ip):
            return self._error(429, "too many login attempts")
        try:
            fields = await _form_fields(request)
        except ValueError:
            return self._error(400, "invalid login request")
        username, password = fields.get("username"), fields.get("password")
        if set(fields) != {"username", "password"} or not (
            isinstance(username, str) and isinstance(password, str)
        ):
            return self._error(400, "invalid login request")
        role = await run_in_threadpool(self.auth.authenticate, username, password)
        if role is None:
            return self._error(401, "invalid credentials")
        issued = self.auth.issue(role)
        if issued is None:
            return self._error(503, "session capacity reached")
        token, session = issued
        response: Response
        if request.headers.get("content-type", "").partition(";")[0].strip() == "application/json":
            response = JSONResponse(
                {"access_token": token, "token_type": "bearer", "role": role, "csrf": session.csrf}
            )
        else:
            response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            self.cookie_name, token, max_age=900, secure=True, httponly=True, samesite="strict"
        )
        return response

    async def _logout(
        self, request: Request, token: str, session: Session, origin_ok: bool, cookie: bool
    ) -> Response:
        if cookie:
            if not origin_ok:
                return self._error(403, "CSRF validation failed")
            csrf = request.headers.get("x-csrf-token")
            if csrf is None:
                try:
                    value = (await _form_fields(request)).get("csrf")
                except ValueError:
                    return self._error(403, "CSRF validation failed")
                csrf = value if isinstance(value, str) else ""
            if not secrets.compare_digest(csrf.encode(), session.csrf.encode()):
                return self._error(403, "CSRF validation failed")
        self.auth.revoke(token)
        response = RedirectResponse("/auth/login", status_code=303)
        response.delete_cookie(self.cookie_name, secure=True, httponly=True, samesite="strict")
        return response

    async def _websocket(self, scope: Scope, receive: Receive, send: Send, token: str) -> None:
        closed = False

        async def finish() -> None:
            nonlocal closed
            if not closed:
                closed = True
                await send({"type": "websocket.close", "code": 4401})

        async def session_receive() -> Message:
            while session := self.auth.session(token):
                timeout = min(session.expires, session.idle_until) - monotonic()
                try:
                    message = await asyncio.wait_for(receive(), timeout=timeout)
                except TimeoutError:
                    continue
                if self.auth.session(token, touch=message["type"] == "websocket.receive"):
                    return message
                break
            await finish()
            return {"type": "websocket.disconnect", "code": 4401}

        async def session_send(message: Message) -> None:
            nonlocal closed
            if not self.auth.session(token):
                await finish()
            elif not closed:
                if message["type"] == "websocket.close":
                    closed = True
                await send(message)

        await self.app(scope, session_receive, session_send)
