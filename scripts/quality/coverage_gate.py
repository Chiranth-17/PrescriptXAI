"""Enforce scoped line coverage plus full-package line and branch-inclusive ratchets."""

import argparse
import json
from pathlib import Path

import yaml


def check_coverage(document: dict, config: dict) -> dict:
    """Compute disclosed numerators/denominators from every source-file entry."""
    files = document.get("files", {})
    if not files:
        raise ValueError("coverage JSON has no source files")
    excluded = {name.replace("\\", "/") for name in config["rendering_exclusions"]}
    counts = {"full": [0, 0, 0, 0], "scoped": [0, 0, 0, 0]}
    seen = set()
    excluded_actual = []
    for raw_name, entry in files.items():
        name = raw_name.replace("\\", "/")
        if name in seen or not name.startswith("src/prescriptxai/"):
            raise ValueError(f"unexpected/duplicate coverage source: {name}")
        seen.add(name)
        summary = entry["summary"]
        values = [
            summary[key]
            for key in (
                "covered_lines",
                "num_statements",
                "covered_branches",
                "num_branches",
            )
        ]
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values
        ):
            raise ValueError(f"invalid coverage counts: {name}")
        if values[0] > values[1] or values[2] > values[3]:
            raise ValueError(f"coverage numerator exceeds denominator: {name}")
        for scope in ("full", "scoped"):
            if scope == "scoped" and name in excluded:
                excluded_actual.append(name)
                continue
            counts[scope] = [
                left + right for left, right in zip(counts[scope], values, strict=True)
            ]
    if excluded != set(excluded_actual):
        raise ValueError("declared rendering exclusions must appear in the full coverage report")
    full, scoped = counts["full"], counts["scoped"]
    if not full[1] or not scoped[1]:
        raise ValueError("coverage requires nonempty full and scoped statement populations")
    result = {
        "full": {
            "covered_lines": full[0],
            "statements": full[1],
            "covered_branches": full[2],
            "branches": full[3],
            "line_percent": 100 * full[0] / full[1],
            "combined_percent": 100 * (full[0] + full[2]) / (full[1] + full[3]),
        },
        "scoped": {
            "covered_lines": scoped[0],
            "statements": scoped[1],
            "line_percent": 100 * scoped[0] / scoped[1],
        },
        "rendering_exclusions": sorted(excluded_actual),
        "source_files": len(seen),
        "thresholds": config,
    }
    result["passed"] = (
        result["full"]["line_percent"] >= config["full_package_line_floor"]
        and result["full"]["combined_percent"] >= config["full_package_branch_inclusive_floor"]
        and result["scoped"]["line_percent"] >= config["required_scoped_line_percent"]
    )
    return result


def main() -> None:
    """Write an auditable coverage gate and exit nonzero on any unmet threshold."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-json", type=Path, default=Path("coverage.json"))
    parser.add_argument(
        "--config", type=Path, default=Path("configs/experiments/phase9-hardening.yaml")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    coverage = json.loads(args.coverage_json.read_text(encoding="utf-8"))
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))["coverage"]
    # A partial --cov or omitted module must not certify the whole library.
    expected = {path.as_posix() for path in Path("src/prescriptxai").rglob("*.py")}
    measured = {name.replace("\\", "/") for name in coverage["files"]}
    if expected != measured:
        raise ValueError(
            f"coverage source inventory mismatch: missing={sorted(expected - measured)}"
        )
    result = check_coverage(coverage, config)
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
