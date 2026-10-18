"""Structured JSON logging with a context-local identifier for each application run."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

_RUN_ID: ContextVar[str] = ContextVar("prescriptxai_run_id", default="unassigned")


def new_run_id() -> str:
    """Generate and activate a unique identifier in the current execution context."""
    run_id = uuid4().hex
    _RUN_ID.set(run_id)
    return run_id


def current_run_id() -> str:
    """Return the active run identifier for the current execution context."""
    return _RUN_ID.get()


class JsonLogFormatter(logging.Formatter):
    """Format standard logging records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize timestamp, severity, logger, run ID, message, and exception."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "run_id": current_run_id(),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, allow_nan=False)


def configure_logging(level: int = logging.INFO, run_id: str | None = None) -> str:
    """Configure JSON logging and return the current run ID.

    A supplied run ID is useful when a request boundary already assigned one. Otherwise, a fresh
    UUID is generated so log streams from independent CLI/API runs can be correlated.
    """
    active_id = run_id or new_run_id()
    if run_id:
        _RUN_ID.set(run_id)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root = logging.getLogger()
    if not any(isinstance(item.formatter, JsonLogFormatter) for item in root.handlers):
        root.addHandler(handler)
    root.setLevel(level)
    return active_id


def bind_run_id(run_id: str) -> Token[str]:
    """Bind one request ID in its context and return a reset token."""
    return _RUN_ID.set(run_id)


def reset_run_id(token: Token[str]) -> None:
    """Restore the parent request/logging context."""
    _RUN_ID.reset(token)
