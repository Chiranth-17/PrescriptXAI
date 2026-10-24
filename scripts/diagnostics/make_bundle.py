#!/usr/bin/env python3
"""Package saved experiment evidence without inventing or recomputing any result.

The retired Phase4 template mixed signs/magnitudes and contained unsupported defaults.
Historical reports remain immutable; this command copies actual saved files with hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

REQUIRED = ("manifest.json", "summary.json", "stages.json", "report.md", "metrics.csv")
OPTIONAL = (
    "report.html",
    "closure_summary.html",
    "latency.json",
    "reference.json",
    "model_metadata.json",
)


def create_review_bundle(source: Path, destination: Path) -> dict:
    """Copy complete saved reports into a new directory; never overwrite historical evidence."""
    source, destination = source.resolve(), destination.resolve()
    if destination == source or destination.is_relative_to(source):
        raise ValueError("review output must be outside the measured run directory")
    missing = [name for name in REQUIRED if not (source / name).is_file()]
    if missing:
        raise ValueError(f"missing saved experiment evidence: {missing}")
    snapshots = {
        name: (source / name).read_bytes()
        for name in (*REQUIRED, *OPTIONAL)
        if (source / name).is_file()
    }
    manifest = json.loads(snapshots["manifest.json"])
    summary = json.loads(snapshots["summary.json"])
    stages = json.loads(snapshots["stages.json"])
    if not all(isinstance(value, dict) for value in (manifest, summary, stages)):
        raise ValueError("saved experiment metadata must be mappings")
    if not summary.get("complete") or not manifest.get("run_id") or not manifest.get("git_hash"):
        raise ValueError("saved experiment is incomplete or lacks run/source provenance")
    if summary.get("manifest") != manifest:
        raise ValueError("saved summary manifest differs from the measured run manifest")
    required_stages = {"diagnostics", "quality", "reference", "latency"}
    if not required_stages.issubset(stages) or any(
        not isinstance(record, dict)
        or not record.get("complete")
        or record.get("source") != manifest["git_hash"]
        for record in stages.values()
    ):
        raise ValueError("saved stage completion evidence is incomplete")
    destination.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, contents in snapshots.items():
        target = destination / name
        target.write_bytes(contents)
        files[name] = {"sha256": hashlib.sha256(contents).hexdigest(), "bytes": len(contents)}
    result = {
        "run_id": manifest["run_id"],
        "measurement_source": manifest["git_hash"],
        "source_directory": str(source),
        "files": files,
        "created_utc": datetime.now(UTC).isoformat(),
        "scope": "Exact saved reports; no fitting, optimization or recomputed metrics",
        "raw_record_location": str(source / "records.sqlite3"),
        "raw_records_copied": False,
        "limitations": "Raw multi-gigabyte query records remain at their original path. "
        "Model validity, statistical plausibility and proxy constraints remain distinct. "
        "This bundle establishes no physical safety or RUL extension.",
    }
    (destination / "bundle_manifest.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    destination = args.output or Path("artifacts/review-bundles") / datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    try:
        result = create_review_bundle(args.run_directory, destination)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
