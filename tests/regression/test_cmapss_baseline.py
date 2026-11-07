"""The real complete baseline is mandatory, including its byte-verified external assets."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.mark.slow
def test_complete_cmapss_baseline() -> None:
    """Actually solve all 32,116 registered queries in a fresh child process."""
    root = Path(__file__).resolve().parents[2]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = root / "artifacts" / "phase12" / f"regression-{stamp}-{os.getpid()}"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "scripts.diagnostics.phase12_regression",
        "--output",
        str(output),
    ]
    with (
        output.with_suffix(".stdout.log").open("w", encoding="utf-8") as stdout,
        output.with_suffix(".stderr.log").open("w", encoding="utf-8") as stderr,
    ):
        completed = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr, check=False)
    output.with_suffix(".exit").write_text(f"{completed.returncode}\n", encoding="utf-8")
    assert completed.returncode == 0, f"Actual full regression failed; inspect {output} and logs"
    receipt = json.loads((output / "complete.json").read_text(encoding="utf-8"))
    assert receipt["actual_success"] is True
    assert receipt["queries"] == 32116
    assert len(receipt["groups"]) == 24
    assert sum(receipt["groups"].values()) == 32116
