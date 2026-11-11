"""Portable initialization, source ownership and release metadata regressions."""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from prescriptxai import __version__, provenance, workspace
from prescriptxai.cli import app
from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.dashboard.state import load_settings

ROOT = Path(__file__).resolve().parents[1]


def test_initialized_workspace_contains_loadable_canonical_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty location receives real versioned configs without relying on the checkout."""
    result = CliRunner().invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0, result.output
    monkeypatch.chdir(tmp_path)
    config = load_config(Path("configs/default.yaml"))
    assert config.tau_safe == 0.2 and config.tau_danger == 0.8
    assert config.artifacts.model == Path("artifacts/reproduction/model.joblib")
    assert load_taxonomy(config.pipeline.taxonomy_path).controllable_feature_names()
    settings = load_settings(Path("configs/dashboard.yaml"))
    assert settings.profiles["FD001"]["XGBoost / reproduction v1"] == Path("configs/default.yaml")
    assert (
        Path("configs/default.yaml").read_bytes()
        == (ROOT / "configs/experiments/phase10-reproduce-v1.yaml").read_bytes()
    )
    assert (
        Path("configs/features.yaml").read_bytes() == (ROOT / "configs/features.yaml").read_bytes()
    )
    result = CliRunner().invoke(app, ["init"])
    assert result.exit_code == 2 and "refusing to replace" in result.output


def test_init_refuses_partial_existing_configuration_without_touching_it(tmp_path: Path) -> None:
    """Preflight prevents a partial workspace overwrite."""
    (tmp_path / "configs").mkdir()
    existing = tmp_path / "configs/features.yaml"
    existing.write_text("owned by operator", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing to replace"):
        workspace.initialize_workspace(tmp_path)
    assert existing.read_text() == "owned by operator"
    assert not (tmp_path / "configs/default.yaml").exists()


def test_package_source_is_independent_of_operator_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Running from another repository cannot assign its commit to this package."""
    original = provenance.source_identity()
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    assert provenance.source_identity() == original
    assert original["git_commit"]


def test_installed_provenance_uses_embedded_identity_or_explicit_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An installation without Git never silently adopts an operator checkout."""
    monkeypatch.setattr(provenance, "__file__", str(tmp_path / "provenance.py"))
    assert provenance.source_identity()["origin"] == "unidentified"
    expected = {
        "git_commit": "a" * 40,
        "tracked_source_dirty": False,
        "origin": "distribution_build",
    }
    (tmp_path / "_build_info.json").write_text(json.dumps(expected), encoding="utf-8")
    assert provenance.source_identity() == expected


def test_checkout_provenance_without_git_executable_is_explicit_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing Git does not leak a subprocess exception into training."""

    def unavailable(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git unavailable")

    monkeypatch.setattr(provenance.subprocess, "run", unavailable)
    assert provenance.source_identity()["git_commit"] is None


def test_dashboard_launcher_validates_inputs_and_forwards_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Launch uses the installed app and current interpreter without a shell."""
    settings = tmp_path / "dashboard.yaml"
    with pytest.raises(ValueError, match="settings are missing"):
        workspace.launch_dashboard(settings, "127.0.0.1", 8501)
    settings.write_text("profiles: {}", encoding="utf-8")
    with pytest.raises(ValueError, match="port must"):
        workspace.launch_dashboard(settings, "127.0.0.1", 0)
    captured: dict[str, Any] = {}

    def launch(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured.update(command=command, **kwargs)
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(workspace.subprocess, "run", launch)
    assert workspace.launch_dashboard(settings, "127.0.0.1", 8501, local_demo=True) == 7
    assert Path(captured["command"][4]).is_file()
    assert captured["env"]["PRESCRIPTXAI_DASHBOARD_CONFIG"] == str(settings.resolve())
    monkeypatch.setattr(workspace.importlib.util, "find_spec", lambda _: None)
    with pytest.raises(ValueError, match="install prescriptxai"):
        workspace.launch_dashboard(settings, "127.0.0.1", 8501)


def test_release_versions_and_explicit_runtime_dependencies_match() -> None:
    """Published metadata installs the direct runtime imports and keeps schema separate."""
    document = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    metadata = document["project"]
    assert metadata["dynamic"] == ["version"]
    assert document["tool"]["hatch"]["version"]["path"] == "src/prescriptxai/__init__.py"
    assert importlib.metadata.version("prescriptxai") == __version__
    assert metadata["license"] == "MIT"
    assert {"numpy", "pandas", "torch", "xgboost", "joblib", "plotly"}.issubset(
        {dependency.split("==")[0] for dependency in metadata["dependencies"]}
    )
    assert set(metadata["optional-dependencies"]) == {"api", "dashboard", "baselines", "dev"}
    assert set(metadata["optional-dependencies"]["dev"]) == set(
        document["dependency-groups"]["dev"]
    )
