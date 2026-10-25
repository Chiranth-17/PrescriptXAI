"""Identify the code being executed independently of the operator's working directory."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def source_identity() -> dict[str, Any]:
    """Return installed build identity or the owning checkout, never an unrelated CWD."""
    package = Path(__file__).resolve().parent
    embedded = package / "_build_info.json"
    if embedded.is_file():
        result: dict[str, Any] = json.loads(embedded.read_text(encoding="utf-8"))
        return result
    root = package.parent.parent
    if package != root / "src" / "prescriptxai" or not (root / ".git").exists():
        return {"git_commit": None, "tracked_source_dirty": None, "origin": "unidentified"}
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return {"git_commit": None, "tracked_source_dirty": None, "origin": "unidentified"}
    return {"git_commit": revision, "tracked_source_dirty": bool(dirty), "origin": "checkout"}
