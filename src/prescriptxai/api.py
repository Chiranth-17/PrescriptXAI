"""FastAPI service exposing the same frozen public decision-support contract as the CLI."""

from __future__ import annotations

import os
import secrets
from contextvars import Token
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from prescriptxai import __version__
from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.config import AppConfig, load_config
from prescriptxai.logging_utils import bind_run_id, reset_run_id
from prescriptxai.machine_api import machine_router
from prescriptxai.pipeline import ArtifactError, InputError, PrescriptXAI, PrescriptXAIEngine
from prescriptxai.schemas import (
    Assessment,
    BatchRequest,
    RecourseRequest,
    RecourseResult,
    _reject_nonreal_measurement,
)


def _validation_details(error: ValidationError | RequestValidationError) -> dict[str, object]:
    """Expose field locations and reasons without input values, exception context or frames."""
    entries = [
        {"type": item["type"], "loc": list(item["loc"]), "msg": item["msg"]}
        for item in error.errors()
    ]
    return {
        "detail": "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        ),
        "errors": entries,
        "error_type": "RequestValidationError",
    }


class ControlPreviewRequest(RecourseRequest):
    """Original observed state plus named manual raw-unit proxy controls."""

    controls: dict[str, float]

    @field_validator("controls", mode="before")
    @classmethod
    def reject_boolean_controls(cls, value: object) -> object:
        """Reject booleans before numeric coercion can hide an invalid measurement."""
        if isinstance(value, dict):
            for item in value.values():
                _reject_nonreal_measurement(item, "controls")
        return value


class RequestGuard:
    """Bound actual streamed bytes, authenticate and bind an isolated request identifier."""

    def __init__(self, app: ASGIApp, config: AppConfig) -> None:
        self.app, self.config = app, config

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Check one bounded request and preserve request-local logging context."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        supplied = headers.get(b"x-request-id", b"").decode("utf-8", errors="replace")
        request_id = (
            supplied
            if supplied and len(supplied) <= 128 and all(c.isalnum() or c in "-_" for c in supplied)
            else uuid4().hex
        )
        token: Token[str] = bind_run_id(request_id)

        async def respond(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode("utf-8"))
                )
            await send(message)

        try:
            key = os.environ.get(self.config.api.api_key_env)
            if key and not secrets.compare_digest(headers.get(b"x-api-key", b""), key.encode()):
                await JSONResponse(
                    {
                        "detail": "invalid API key",
                        "mode": self.config.pipeline.default_mode.upper(),
                    },
                    status_code=401,
                )(scope, receive, respond)
                return
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(body) + len(chunk) > self.config.api.max_payload_bytes:
                    await JSONResponse(
                        {
                            "detail": "payload exceeds configured byte limit",
                            "mode": self.config.pipeline.default_mode.upper(),
                        },
                        status_code=413,
                    )(scope, receive, respond)
                    return
                body.extend(chunk)
                if not message.get("more_body", False):
                    break
            delivered = False

            async def replay() -> Message:
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            await self.app(scope, replay, respond)
        finally:
            reset_run_id(token)


def create_app(
    engine: PrescriptXAI | PrescriptXAIEngine | None = None,
    config: AppConfig | None = None,
    *,
    registry: MachineRegistry | None = None,
    machine_artifacts: Path = Path("artifacts/machines"),
) -> FastAPI:
    """Create a loaded service or an explicit unavailable service (503, never fake output)."""
    pipeline = (
        engine
        if isinstance(engine, PrescriptXAI)
        else PrescriptXAI(engine)
        if engine is not None
        else None
    )
    settings = config or (
        pipeline.config if pipeline else load_config(Path("configs/default.yaml"))
    )
    app = FastAPI(
        title="PrescriptXAI",
        version="2.0.0",
        description=(
            "Proxy maintenance decision support. "
            "Model validity is separate from plausibility; no RUL extension is established."
        ),
    )
    app.add_middleware(RequestGuard, config=settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_methods=settings.api.cors_methods,
        allow_headers=settings.api.cors_headers,
    )

    def loaded() -> PrescriptXAI:
        if pipeline is None:
            raise HTTPException(503, "no model is loaded")
        return pipeline

    async def response_mode(request: Request) -> str:
        try:
            body = await request.json()
            mode = body.get("mode") if isinstance(body, dict) else None
            return (
                mode.upper()
                if isinstance(mode, str) and mode in {"fast", "thorough"}
                else settings.pipeline.default_mode.upper()
            )
        except (ValueError, RuntimeError):
            return settings.pipeline.default_mode.upper()

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, error: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            {"detail": error.detail, "mode": await response_mode(request)},
            status_code=error.status_code,
        )

    @app.exception_handler(InputError)
    async def input_error_handler(_request: Request, error: InputError) -> JSONResponse:
        return JSONResponse(
            {
                "detail": str(error),
                "error_type": type(error).__name__,
                "mode": await response_mode(_request),
            },
            status_code=422,
        )

    @app.exception_handler(ArtifactError)
    async def artifact_error_handler(request: Request, error: ArtifactError) -> JSONResponse:
        return JSONResponse(
            {
                "detail": str(error),
                "error_type": type(error).__name__,
                "mode": await response_mode(request),
            },
            status_code=503,
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_request: Request, error: ValidationError) -> JSONResponse:
        return JSONResponse(
            {**_validation_details(error), "mode": await response_mode(_request)}, status_code=422
        )

    @app.exception_handler(RequestValidationError)
    async def request_error_handler(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            {**_validation_details(error), "mode": await response_mode(_request)}, status_code=422
        )

    @app.get("/health")
    def health() -> dict[str, object]:
        service = loaded()
        return {
            "status": "ready",
            "model": service.engine.model.model_type,
            "dataset": service.engine.taxonomy.dataset,
            "mode": settings.pipeline.default_mode.upper(),
            "schema_version": "2.0.0",
        }

    @app.get("/config")
    def configuration() -> dict[str, object]:
        return {
            **loaded().info(),
            "mode": settings.pipeline.default_mode.upper(),
            "authentication_enabled": bool(os.environ.get(settings.api.api_key_env)),
        }

    @app.get("/version")
    def version() -> dict[str, str]:
        return {
            "service_version": __version__,
            "schema_version": "2.0.0",
            "mode": settings.pipeline.default_mode.upper(),
        }

    @app.post("/assess", response_model=Assessment)
    def assess(request: RecourseRequest) -> Assessment:
        mode = (
            request.mode if "mode" in request.model_fields_set else settings.pipeline.default_mode
        )
        return loaded().assess(request.state, request.context, mode)

    @app.post("/recommend", response_model=RecourseResult)
    def recommend(request: RecourseRequest) -> RecourseResult:
        mode = (
            request.mode if "mode" in request.model_fields_set else settings.pipeline.default_mode
        )
        return loaded().recommend(request.state, request.context, mode)

    @app.post("/recommend/batch", response_model=list[RecourseResult])
    def batch(request: BatchRequest) -> list[RecourseResult]:
        service = loaded()
        mode = (
            request.mode if "mode" in request.model_fields_set else settings.pipeline.default_mode
        )
        return service.recommend_batch(
            pd.DataFrame(request.states), mode, contexts=request.contexts
        )

    @app.post("/validate-controls", response_model=RecourseResult)
    def validate_controls(request: ControlPreviewRequest) -> RecourseResult:
        """Preview controls through the exact same library path used by the dashboard."""
        mode = (
            request.mode if "mode" in request.model_fields_set else settings.pipeline.default_mode
        )
        return loaded().validate_controls(request.state, request.controls, request.context, mode)

    app.include_router(
        machine_router(
            registry or MachineRegistry(),
            pipeline,
            machine_artifacts,
            settings.pipeline.max_batch_rows,
        )
    )
    return app
