"""Prevent resumed diagnosis from replacing retained payloads or their timings."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


def load_helper() -> ModuleType:
    """Load without running the continuation."""
    spec = importlib.util.spec_from_file_location(
        "resume_helpers", Path("scripts/diagnostics/phase12_arithmetic_resume.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "corruption", ["none", "timing", "payload", "missing", "extra", "unknown_arm"]
)
def test_retained_payload_and_identity_guard(corruption: str) -> None:
    """Reject replaced, absent, extra or unidentified observations before continuing."""
    module = load_helper()
    rows = [("current", "case1", '{"timing": 4.5, "risk": 0.2}')]
    preserved = {"payload_sha256": {"current/case1": module.payload_hash(rows[0][2])}}
    if corruption == "timing":
        rows = [("current", "case1", '{"timing": 4.6, "risk": 0.2}')]
    elif corruption == "payload":
        rows = [("current", "case1", '{"timing": 4.5, "risk": 0.3}')]
    elif corruption == "missing":
        rows = []
    elif corruption == "extra":
        rows = rows + [("current", "case2", "{}")]
    elif corruption == "unknown_arm":
        rows = [("unknown", "case1", "{}")]
        preserved = {"payload_sha256": {"unknown/case1": module.payload_hash("{}")}}
    baseline = SimpleNamespace(validate_record=lambda case, key, payload: None)
    if corruption == "none":
        assert module.verify_retained(rows, preserved, {"case1": object()}, baseline)
    else:
        with pytest.raises(ValueError):
            module.verify_retained(rows, preserved, {"case1": object()}, baseline)
