"""Portable installed-package entrypoints and explicit local workspace initialization."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from importlib.resources import files
from pathlib import Path


def initialize_workspace(destination: Path) -> list[Path]:
    """Create versioned configuration templates without replacing an existing workspace.

    Paths in these templates are relative to the working directory. Change into
    ``destination`` before running the other CLI commands. No fitted data is bundled.
    """
    target = destination.resolve()
    names = ("default.yaml", "features.yaml", "dashboard.yaml")
    paths = [target / "configs" / name for name in names]
    existing = [path for path in paths if path.exists()]
    if existing:
        raise ValueError(f"refusing to replace existing configuration: {existing[0]}")
    templates = files("prescriptxai").joinpath("resources")
    contents = [templates.joinpath(name).read_bytes() for name in names]
    for directory in (target / "configs", target / "data" / "raw", target / "artifacts"):
        directory.mkdir(parents=True, exist_ok=True)
    for path, content in zip(paths, contents, strict=True):
        with path.open("xb") as output:
            output.write(content)
    return paths


def launch_dashboard(settings: Path, host: str, port: int) -> int:
    """Run the installed Streamlit application in the selected operator workspace."""
    if not settings.is_file():
        raise ValueError(f"dashboard settings are missing: {settings}; run prescriptxai init first")
    if importlib.util.find_spec("streamlit") is None:
        raise ValueError("install prescriptxai[dashboard] before running dashboard")
    if not 1 <= port <= 65535:
        raise ValueError("dashboard port must be between 1 and 65535")
    entrypoint = files("prescriptxai").joinpath("dashboard", "simulator_app.py")
    environment = os.environ.copy()
    environment["PRESCRIPTXAI_DASHBOARD_CONFIG"] = str(settings.resolve())
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(entrypoint),
            "--server.address",
            host,
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        env=environment,
        check=False,
    ).returncode
