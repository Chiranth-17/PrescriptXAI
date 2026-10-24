"""Explicitly trust only this test's managed temporary artifact directory."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def trusted_test_artifact_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Temporary fitted artifacts are local test outputs, never downloaded/uploaded objects."""
    existing = os.environ.get("PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS", "")
    roots = os.pathsep.join(value for value in (existing, str(tmp_path)) if value)
    monkeypatch.setenv("PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS", roots)
