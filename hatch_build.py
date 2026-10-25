"""Embed the actual build source identity in both distribution formats."""

import hashlib
import json
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Record source ownership without importing the package or its heavy dependencies."""

    def initialize(self, version, build_data):
        """Include a source manifest in the requested distribution."""
        root = Path(self.root)
        package = root / "src" / "prescriptxai"
        embedded = package / "_build_info.json"
        identity = {"git_commit": None, "tracked_source_dirty": None, "origin": "source_archive"}
        if (root / ".git").exists():
            identity = {
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=root, text=True
                ).strip(),
                "tracked_source_dirty": bool(
                    subprocess.check_output(
                        ["git", "status", "--porcelain", "--untracked-files=no"],
                        cwd=root,
                        text=True,
                    ).strip()
                ),
                "origin": "distribution_build",
            }
        elif embedded.is_file():
            identity = json.loads(embedded.read_text(encoding="utf-8"))
        hashes = {
            path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(package.rglob("*"))
            if path.is_file() and path.suffix in {".py", ".yaml"}
        }
        identity["source_file_hashes"] = hashes
        identity["source_tree_sha256"] = hashlib.sha256(
            json.dumps(hashes, sort_keys=True).encode()
        ).hexdigest()
        if embedded.is_file():
            embedded.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
            return
        target = root / "build" / "_build_info.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
        destination = "prescriptxai/_build_info.json"
        if self.target_name == "sdist":
            destination = "src/" + destination
        build_data["force_include"][str(target)] = destination
