"""Fixed regression subset retaining all historical diagnostic and native borderline cases."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def test_fixed_cmapss_subset_has_exact_compatible_evidence() -> None:
    """Every fixed ID is verified with explicit reused/recomputed and origin accounting."""
    root = Path(__file__).resolve().parents[2]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = root / "artifacts/regression-tiers" / f"check-{stamp}-{os.getpid()}"
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "scripts.diagnostics.regression_tiers",
        "--tier",
        "subset",
        "--output",
        str(output),
    ]
    if os.environ.get("PSX_QUALITY_REGRESSION_REUSE_ONLY") == "1":
        command.append("--reuse-only")
    with (
        output.with_suffix(".stdout.log").open("x", encoding="utf-8") as stdout,
        output.with_suffix(".stderr.log").open("x", encoding="utf-8") as stderr,
    ):
        completed = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr, check=False)
    output.with_suffix(".exit").write_text(f"{completed.returncode}\n", encoding="utf-8")
    assert completed.returncode == 0, f"Subset evidence failed; inspect {output} and logs"
    ids = json.loads((root / "tests/regression/subset_ids.json").read_text(encoding="utf-8"))
    receipt = json.loads((output / "complete.json").read_text(encoding="utf-8"))
    assert receipt["actual_success"] is True
    assert receipt["requested"] == len(ids)
    assert receipt["reused"] + receipt["recomputed"] == len(ids)
    if receipt_path := os.environ.get("PSX_QUALITY_SUBSET_RECEIPT"):
        with Path(receipt_path).open("x", encoding="utf-8") as stream:
            json.dump({"path": str(output / "complete.json")}, stream)
