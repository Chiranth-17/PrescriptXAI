"""Replay every audited baseline query; absent external assets are a failure, never a skip."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq
from filelock import FileLock
from scripts.diagnostics.phase12_baseline import (
    atomic_json,
    differences,
    idle_sleep_guard,
    portable,
    read_design,
    run_cases,
    validate_record,
)

import prescriptxai
from prescriptxai.evaluation.experiments import (
    QueryCase,
    file_hash,
    runtime_manifest,
    source_revision,
)

FIXTURE = Path("tests/regression/cmapss_baseline.parquet")
MANIFEST = FIXTURE.with_suffix(".json")
DESIGN = Path("configs/experiments/phase12-baseline-v1.yaml")


def clean_source() -> str:
    """Require the complete tracked and untracked worktree to be committed."""
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit the complete regression worktree before replay")
    return source_revision(require_clean=True)


def verify_files(hashes: dict[str, str]) -> None:
    """Check every required byte before unpickling any fitted asset."""
    for name, expected in hashes.items():
        path = Path(name)
        if not path.is_file():
            raise FileNotFoundError(f"Required regression input missing: {name}")
        if file_hash(path) != expected:
            raise ValueError(f"Required regression input SHA256 differs: {name}")


def comparison_record(record: dict) -> dict:
    """Compare full scientific structure, omitting timing and rounded presentation prose."""
    selected = {key: value for key, value in record.items() if key != "timings"}
    selected["config_path"] = portable(selected["config_path"])
    report = dict(selected["validation"])
    for name, tier in report.items():
        if isinstance(tier, dict):
            cleaned = {key: value for key, value in tier.items() if key != "diagnostics"}
            cleaned["checks"] = [
                {key: value for key, value in check.items() if key != "explanation"}
                for check in tier["checks"]
            ]
            report[name] = cleaned
    selected["validation"] = report
    return selected


def native_margins(record: dict, *, delta_min: float):
    """Yield every numeric tier/check and alert/triage margin in native predicate units."""
    for name, tier in record["validation"].items():
        if not isinstance(tier, dict):
            continue
        if tier.get("margin") is not None:
            yield name, tier["margin"], tier["passed"], None
        for index, check in enumerate(tier["checks"]):
            if check.get("margin") is not None:
                yield (
                    f"{name}/checks/{index}/{check['name']}",
                    check["margin"],
                    check["passed"],
                    check.get("feature"),
                )
    yield (
        "alert_gate",
        record["risk_before"] - record["solver_tau_danger"],
        record["risk_before"] >= record["solver_tau_danger"],
        None,
    )
    yield (
        "tier1_safe_gate",
        record["solver_tau_safe"] - record["risk_after"],
        record["risk_after"] <= record["solver_tau_safe"],
        None,
    )
    yield (
        "triage_improvement",
        record["risk_before"] - record["risk_after"] - delta_min,
        record["risk_before"] - record["risk_after"] >= delta_min,
        None,
    )


def read_fixture(fixture: Path, metadata: dict, design: dict) -> tuple[dict, dict]:
    """Bind all 32,116 genuine cases and observations to the audited export."""
    cases, expected = {}, {}
    counts, engines, referenced_inputs = Counter(), {}, set()
    required_columns = {
        "case_id",
        "group",
        "config_hash",
        "run_id",
        "design_path",
        "design_sha256",
        "source",
        "historical_source",
        "case_json",
        "historical_case_json",
        "observation_json",
        "historical_observation_json",
    }
    parquet = pq.ParquetFile(fixture)
    if set(parquet.schema.names) != required_columns:
        raise ValueError("Regression fixture columns changed")
    for batch in parquet.iter_batches(batch_size=64):
        for row in batch.to_pylist():
            key = row["case_id"]
            if key in cases:
                raise ValueError(f"Duplicate regression case: {key}")
            case = QueryCase.model_validate_json(row["case_json"])
            record = validate_record(case, key, row["observation_json"]).model_dump(mode="json")
            if (
                row["source"] != metadata["reference_source"]
                or row["run_id"] != metadata["reference_run_id"]
                or row["design_sha256"] != metadata["design_sha256"]
                or row["design_path"] != DESIGN.as_posix()
                or row["historical_source"] != design["historical_source"]
                or row["config_hash"] != record["config_hash"]
                or row["group"] != record["group"]
            ):
                raise ValueError(f"Regression fixture provenance differs: {key}")
            if (
                case.case_id != key
                or case.mode != "fast"
                or case.variant != "full"
                or case.policy is not None
                or case.config.seed != design["solver_seed"]
                or case.population not in design["populations"]
            ):
                raise ValueError(f"Regression case policy differs: {key}")
            for asset in (
                case.config.artifacts.model,
                case.config.artifacts.coupling,
                case.config.artifacts.mahalanobis,
                case.config.pipeline.taxonomy_path,
            ):
                if asset is None:
                    raise ValueError(f"Regression case lacks a required asset: {key}")
                referenced_inputs.add(str(portable(str(asset))))
            cases[key] = row["case_json"]
            expected[key] = row["observation_json"]
            counts[case.group] += 1
            engines.setdefault(case.group, set()).add(record["engine_id"])
    if (
        len(cases) != design["expected_queries"]
        or dict(counts) != design["group_counts"]
        or {key: len(value) for key, value in engines.items()} != design["group_engine_counts"]
    ):
        raise ValueError("Regression fixture is not the complete registered corpus")
    if referenced_inputs != set(metadata["input_hashes"]):
        raise ValueError("Fixture asset references differ from the required byte manifest")
    return cases, expected


def preflight() -> tuple[dict, dict, dict]:
    """Fail closed on absent fixtures, fitted bytes, changed registration or dirty source."""
    if not MANIFEST.is_file():
        raise FileNotFoundError(f"Required audited regression manifest missing: {MANIFEST}")
    metadata = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (
        metadata["schema_version"] != 1
        or metadata["absolute_tolerance"] != 1e-6
        or metadata["relative_tolerance"] != 0
        or metadata["external_input_count"] != 97
        or len(metadata["input_hashes"]) != 97
        or metadata["independent_audit"]["fixture_promotion_go"] is not True
    ):
        raise ValueError("Regression manifest lacks the complete independently approved corpus")
    verify_files(
        {
            FIXTURE.as_posix(): metadata["fixture_sha256"],
            DESIGN.as_posix(): metadata["design_sha256"],
            **metadata["input_hashes"],
        }
    )
    design = read_design(DESIGN)
    runtime = runtime_manifest()

    def dependencies(versions):
        return {key: value for key, value in versions.items() if key != "prescriptxai"}

    if dependencies(runtime["package_versions"]) != dependencies(
        metadata["reference_runtime"]["package_versions"]
    ):
        raise ValueError("Regression dependencies differ from the audited runtime")
    manifest = {
        "schema_version": 1,
        "source": clean_source(),
        "reference": metadata,
        "runtime": runtime,
        "regression_manifest_sha256": file_hash(MANIFEST),
        "code_hashes": {
            path.as_posix(): file_hash(path)
            for path in (
                *sorted(Path("src/prescriptxai").rglob("*.py")),
                Path("scripts/diagnostics/phase12_baseline.py"),
                Path("scripts/diagnostics/phase12_regression.py"),
            )
        },
        "timing_scope": "parallel quality replay; not serial latency certification",
    }
    cases, expected = read_fixture(FIXTURE, metadata, design)
    return manifest, cases, expected


def verify_unchanged(manifest: dict) -> None:
    """Recheck current source and every frozen input after the actual replay."""
    if clean_source() != manifest["source"]:
        raise ValueError("Regression source changed during replay")
    metadata = manifest["reference"]
    verify_files(
        {
            FIXTURE.as_posix(): metadata["fixture_sha256"],
            MANIFEST.as_posix(): manifest["regression_manifest_sha256"],
            DESIGN.as_posix(): metadata["design_sha256"],
            **metadata["input_hashes"],
            **manifest["code_hashes"],
        }
    )
    if runtime_manifest() != manifest["runtime"]:
        raise ValueError("Regression runtime changed during replay")


def replay(output: Path) -> None:
    """Execute the complete corpus afresh; retain every checkpoint, failure and timing."""
    if output.exists():
        raise FileExistsError("Regression output already exists; preserve and inspect it")
    output.mkdir(parents=True)
    try:
        with FileLock("artifacts/phase12-headline.lock", timeout=0), idle_sleep_guard():
            manifest, cases, expected = preflight()
            manifest["run_id"] = output.name
            atomic_json(output / "manifest.json", manifest)
            measured = run_cases(cases, manifest, output / "replay", resume=False)
            verify_unchanged(manifest)
            mismatches, exact_differences, borderline = [], [], Counter()
            border_path = output / "borderline.csv"
            with border_path.open("w", encoding="utf-8", newline="") as border_stream:
                writer = csv.writer(border_stream)
                writer.writerow(
                    ["case_id", "group", "predicate", "margin", "passed", "feature", "units"]
                )
                for record in measured:
                    key = record["case_id"]
                    previous = comparison_record(json.loads(expected[key]))
                    current = comparison_record(record)
                    changed = differences(previous, current)
                    if changed:
                        mismatches.append({"case_id": key, "fields": changed})
                    if differences(previous, current, atol=0):
                        exact_differences.append(key)
                    delta_min = json.loads(cases[key])["config"]["pipeline"]["delta_min"]
                    for name, margin, passed, feature in native_margins(
                        record, delta_min=delta_min
                    ):
                        if abs(margin) <= 1e-6:
                            borderline[name] += 1
                            writer.writerow(
                                [
                                    key,
                                    record["group"],
                                    name,
                                    margin,
                                    passed,
                                    feature,
                                    "native units of the named predicate",
                                ]
                            )
            comparison = {
                "queries": len(measured),
                "groups": dict(Counter(r["group"] for r in measured)),
                "absolute_tolerance": 1e-6,
                "relative_tolerance": 0,
                "discrete_policy": "exact including supports, verdicts, triage and effective settings",
                "omitted_fields": [
                    "timings",
                    "validation/*/diagnostics",
                    "validation/*/checks/*/explanation",
                ],
                "omission_reason": "Timings vary; rounded prose is presentation. All numeric margins, measurements, limits, checks, statuses and assumptions are compared.",
                "mismatches": mismatches,
                "float_exact_different_cases": exact_differences,
                "borderline_native_predicate_counts": dict(borderline),
                "borderline_file": border_path.name,
                "borderline_sha256": file_hash(border_path),
            }
            atomic_json(output / "comparison.json", comparison)
            if mismatches:
                raise ValueError(f"Full corpus regression differs in {len(mismatches)} cases")
            atomic_json(
                output / "complete.json",
                {
                    "actual_success": True,
                    "queries": len(measured),
                    "groups": comparison["groups"],
                    "source": manifest["source"],
                    "run_id": manifest["run_id"],
                    "comparison_sha256": file_hash(output / "comparison.json"),
                    "completed_utc": datetime.now(UTC).isoformat(),
                },
            )
    except BaseException as error:
        atomic_json(
            output / "failure.json",
            {
                "actual_success": False,
                "error_type": type(error).__name__,
                "error": str(error),
                "failed_utc": datetime.now(UTC).isoformat(),
                "partials_retained": True,
            },
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        Path(prescriptxai.__file__).resolve()
        != (Path.cwd() / "src/prescriptxai/__init__.py").resolve()
    ):
        raise ValueError("Regression imports must resolve to this checkout")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    replay(args.output)


if __name__ == "__main__":
    main()
