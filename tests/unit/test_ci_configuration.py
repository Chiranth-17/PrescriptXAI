"""Basic syntax and target-matrix checks for the CI workflow configuration."""

from pathlib import Path
from typing import Any

import yaml


def test_ci_workflow_is_valid_yaml_and_checks_supported_python_versions() -> None:
    """CI syntax parses and exercises both Python versions in the scaffold requirements."""
    workflow: Any = yaml.safe_load(Path(".github/workflows/ci.yml").read_text(encoding="utf-8"))

    assert "jobs" in workflow
    matrix = workflow["jobs"]["checks"]["strategy"]["matrix"]
    assert matrix["python-version"] == ["3.11", "3.12"]
