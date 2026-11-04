"""Freeze and replay the entire registered C-MAPSS headline, without fitting or sampling."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import logging
import math
import os
import sqlite3
import subprocess
from collections import Counter
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yaml
from filelock import FileLock

import prescriptxai
from prescriptxai.evaluation.experiments import (
    ExperimentObservation,
    ExperimentStore,
    QueryCase,
    content_hash,
    file_hash,
    runtime_manifest,
    source_revision,
)
from prescriptxai.evaluation.runner import execute_experiment_cases

SCIENTIFIC_FIELDS = (
    "group", "dataset", "model", "population", "protocol", "variant", "mode", "seed",
    "engine_id", "cycle", "risk_before", "risk_after", "surrogate_after", "original",
    "candidate", "changed_features", "sparsity", "proxy_sparsity", "raw_l1", "scaled_l1",
    "returned", "action_feasible", "tier2", "tier3", "tier4", "joint", "status", "reason",
    "evidence_level", "mahalanobis_before", "mahalanobis_after", "tier4_margin",
    "immutable_violations", "bound_violations", "rate_violations", "rul", "life_fraction",
    "first_alert", "k_max", "K", "D_max", "solver_tau_safe", "solver_tau_danger",
)


@contextmanager
def idle_sleep_guard():
    """Keep this runner awake on Windows and release its own request when it exits."""
    if os.name != "nt":
        yield
        return
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.SetThreadExecutionState.argtypes = [ctypes.c_uint32]
    kernel.SetThreadExecutionState.restype = ctypes.c_uint32
    if not kernel.SetThreadExecutionState(0x80000001):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if kernel.SetThreadExecutionState(0x80000001) != 0x80000001:
            raise RuntimeError("Runner idle-sleep request was not registered")
        yield
    finally:
        kernel.SetThreadExecutionState(0x80000000)


def atomic_json(path: Path, value: object) -> None:
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def portable(value: object) -> object:
    """Map historical Windows separators only; preserve every numerical setting."""
    if isinstance(value, dict):
        return {key: portable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item) for item in value]
    return value.replace("\\", "/") if isinstance(value, str) else value


def differences(expected: object, actual: object, *, path: str = "", atol: float = 1e-6) -> list[str]:
    """Require exact discrete values and finite numerical absolute error at most atol."""
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        return [] if type(actual) is type(expected) and actual == expected else [path]
    if isinstance(expected, (int, float)):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            return [path]
        if not math.isfinite(expected) or not math.isfinite(actual):
            return [path]
        if isinstance(expected, int):
            return [] if isinstance(actual, int) and actual == expected else [path]
        return [] if abs(expected - actual) <= atol else [path]
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            return [path]
        return [item for key in expected for item in differences(
            expected[key], actual[key], path=f"{path}/{key}", atol=atol
        )]
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return [path]
        return [item for index, pair in enumerate(zip(expected, actual, strict=True))
                for item in differences(*pair, path=f"{path}/{index}", atol=atol)]
    raise TypeError(f"Unsupported comparison value at {path}: {type(expected).__name__}")


def scientific(record: dict) -> dict:
    selected = {key: record[key] for key in SCIENTIFIC_FIELDS}
    selected["tier1"] = record["validation"]["tier1_model_safety"]["passed"]
    return selected


def read_design(path: Path) -> dict:
    design = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {
        "solver_seed": 1729, "mode": "FAST", "variant": "full",
        "expected_queries": 32116, "expected_groups": 24, "workers": 4,
        "cpu_threads": 1, "absolute_tolerance": 0.000001, "relative_tolerance": 0,
        "historical_run": "phase7-20261020T102540Z",
        "historical_source": "63c2ed445fba16c73a2771e184f635abf76b4405",
        "source_study": "configs/experiments/phase7-study.yaml",
    }
    if any(design.get(name) != value for name, value in required.items()):
        raise ValueError("Baseline design differs from the complete preregistered headline")
    if design.get("populations") != ["internal_heldout_all_alerts", "grouped_oof_all_alerts", "official_test_all_alerts"]:
        raise ValueError("The exact three reported populations are required")
    return design


def historical_rows(design: dict) -> list[tuple[str, str, str]]:
    database = Path(design["historical_database"])
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        rows = connection.execute(
            "SELECT r.case_id,c.payload,r.payload FROM records r JOIN cases c USING(case_id) "
            "WHERE json_extract(r.payload,'$.seed')=? "
            "AND json_extract(r.payload,'$.mode')=? "
            "AND json_extract(r.payload,'$.variant')=? "
            "AND json_extract(r.payload,'$.population') IN (?,?,?) "
            "ORDER BY json_extract(r.payload,'$.group'),json_extract(r.payload,'$.config_hash'),"
            "json_extract(r.payload,'$.engine_id'),json_extract(r.payload,'$.cycle'),r.case_id",
            (design["solver_seed"], design["mode"], design["variant"], *design["populations"]),
        ).fetchall()
    counts = Counter(json.loads(row[2])["group"] for row in rows)
    if len(rows) != design["expected_queries"] or dict(counts) != design["group_counts"]:
        raise ValueError("Historical headline population/counts differ from registration")
    if len(counts) != design["expected_groups"] or len({row[0] for row in rows}) != len(rows):
        raise ValueError("Historical headline identities are duplicated or incomplete")
    engines: dict[str, set[int]] = {}
    for _, _, encoded in rows:
        record = json.loads(encoded)
        engines.setdefault(record["group"], set()).add(record["engine_id"])
    if {name: len(values) for name, values in engines.items()} != design["group_engine_counts"]:
        raise ValueError("Historical engine counts differ from registration")
    return rows


def identity(design_path: Path, design: dict, rows: list[tuple[str, str, str]], *, run_id: str, preflight: bool = False) -> dict:
    original = json.loads(Path(design["historical_manifest"]).read_text(encoding="utf-8"))
    if original["git_hash"] != design["historical_source"]:
        raise ValueError("Original run source differs from registration")
    known_hashes = {
        str(portable(path)): entry["hashes"][name]
        for entry in original["assets"]["models"].values()
        for name, path in entry["paths"].items()
    }
    known_hashes["configs/features.yaml"] = original["taxonomy_sha256"]
    required_inputs: dict[str, str] = {}
    digest = hashlib.sha256()
    for case_id, case_json, old_json in rows:
        case, old = json.loads(case_json), json.loads(old_json)
        if case["case_id"] != case_id or old["case_id"] != case_id:
            raise ValueError("Historical joined case identity mismatch")
        if content_hash(case["config"]) != old["config_hash"]:
            raise ValueError("Historical record has a different effective configuration")
        mapped = portable(case)
        parsed = QueryCase.model_validate(mapped)
        if (parsed.group != old["group"] or parsed.config.seed != design["solver_seed"]
            or parsed.mode != "fast" or parsed.variant != "full" or parsed.policy is not None
            or parsed.population not in design["populations"]):
            raise ValueError("Historical case labels/seed changed")
        for asset in (parsed.config.artifacts.model, parsed.config.artifacts.coupling,
                      parsed.config.artifacts.mahalanobis, parsed.config.pipeline.taxonomy_path):
            if asset is None:
                raise ValueError("Required frozen fitted input is missing")
            name = str(portable(str(asset)))
            if name not in known_hashes:
                raise ValueError(f"Input has no historical fingerprint: {name}")
            required_inputs[name] = known_hashes[name]
        digest.update(content_hash([case_id, case, old]).encode("ascii"))
    for path, expected in required_inputs.items():
        if file_hash(Path(path)) != expected:
            raise ValueError(f"Frozen input changed: {path}")
    manifest_hash = file_hash(Path(design["historical_manifest"]))
    records_hash = digest.hexdigest()
    for name, actual in (("historical_manifest_sha256", manifest_hash),
                         ("historical_cases_and_records_sha256", records_hash)):
        if design.get(name) != actual and not (preflight and name not in design):
            raise ValueError(f"Historical input fingerprint changed: {name}")
    return {
        "schema_version": 1, "run_id": run_id, "source": source_revision(require_clean=not preflight),
        "design": design, "design_path": design_path.as_posix(),
        "design_sha256": file_hash(design_path), "historical_cases_and_records_sha256": records_hash,
        "historical_manifest_sha256": manifest_hash,
        "historical_database_sha256": file_hash(Path(design["historical_database"])),
        "input_hashes": required_inputs, "runtime": runtime_manifest(),
        "code_hashes": {
            path.as_posix(): file_hash(path)
            for path in [*sorted(Path("src/prescriptxai").rglob("*.py")), Path(__file__).resolve().relative_to(Path.cwd())]
        },
        "comparison_fields": [*SCIENTIFIC_FIELDS, "tier1"],
        "historical_timings_retained": True, "new_timings_are_quality_not_serial_latency": True,
    }


def verify_unchanged(manifest: dict) -> None:
    """Recheck the actual on-disk provenance after work, before any completed export."""
    if source_revision(require_clean=True) != manifest["source"]:
        raise ValueError("Source changed during the run")
    paths = {
        manifest["design_path"]: manifest["design_sha256"],
        manifest["design"]["historical_manifest"]: manifest["historical_manifest_sha256"],
        manifest["design"]["historical_database"]: manifest["historical_database_sha256"],
        **manifest["input_hashes"], **manifest["code_hashes"],
    }
    for path, expected in paths.items():
        if file_hash(Path(path)) != expected:
            raise ValueError(f"Run input changed: {path}")
    if runtime_manifest() != manifest["runtime"]:
        raise ValueError("Runtime changed during the run")


def validate_record(case: QueryCase, key: str, value: str) -> ExperimentObservation:
    """Bind every restored/new result to its input and check the effective execution policy."""
    parsed = ExperimentObservation.model_validate_json(value)
    config = case.config
    if (parsed.case_id != key or parsed.group != case.group
        or parsed.config_hash != content_hash(config.model_dump(mode="json"))
        or parsed.mode.lower() != case.mode or parsed.seed != config.seed
        or parsed.original != case.state or parsed.dataset != case.dataset
        or parsed.model != case.model or parsed.population != case.population
        or parsed.protocol != case.protocol or parsed.variant != case.variant
        or portable(parsed.config_path) != portable(str(case.config_path))
        or parsed.engine_id != case.state["engine_id"] or parsed.cycle != case.state["cycle"]
        or parsed.solver_tau_safe != config.tau_safe or parsed.solver_tau_danger != config.tau_danger
        or parsed.k_max != config.recourse.k_max or config.recourse.rate_horizon_steps != parsed.K):
        raise ValueError(f"Checkpoint record identity/configuration changed: {key}")
    report = parsed.validation
    flags = {
        "tier1_model_safety": parsed.risk_after <= config.tau_safe,
        "tier2_distributional": parsed.tier2,
        "tier3_engineering": parsed.tier3,
        "tier4_sensor_coupling": parsed.tier4,
    }
    if any(report[name]["passed"] is not flag for name, flag in flags.items()):
        raise ValueError(f"Record has inconsistent nested/flat tier verdicts: {key}")
    settings = parsed.solver_settings
    if "search_mode" not in settings:
        if parsed.reason not in {"infeasible_actuator_interval", "mandatory_changes_exceed_sparsity"}:
            raise ValueError(f"Missing effective search settings lack an early-exit reason: {key}")
        if parsed.action_feasible or parsed.joint:
            raise ValueError(f"Infeasible early exit cannot be accepted: {key}")
        return parsed
    expected = {
        "max_iter": config.recourse.max_iterations, "restarts": config.recourse.restarts,
        "alpha_steps": config.recourse.alpha_steps, "support_search_limit": config.recourse.support_search_limit,
        "feedback_max_refinements": config.validation.feedback_max_refinements,
        "search_mode": case.mode, "k_max": config.recourse.k_max,
        "max_scaled_distance": config.recourse.max_scaled_distance,
        "true_model_grid_points": config.recourse.true_model_grid_points,
        "grid_support_cap": None, "validate_plausibility": True, "check_distribution": True,
        "check_coupling": True, "propagate_dependents": True,
        "effective_distribution_filter": True, "effective_coupling_filter": True,
    }
    if any(settings.get(name) != expected_value or type(settings.get(name)) is not type(expected_value)
           for name, expected_value in expected.items()):
        raise ValueError(f"Effective solver settings differ from the frozen case: {key}")
    return parsed


def run_cases(cases: list[QueryCase] | dict[str, str], manifest: dict, output: Path, *, resume: bool) -> list[dict]:
    if output.exists() and not resume:
        raise ValueError("Output already exists; inspect it and explicitly resume compatible work")
    if resume and not (output / "manifest.json").is_file():
        raise ValueError("Resume requires an existing manifest and checkpoint database")
    if resume and not (output / "records.sqlite3").is_file():
        raise ValueError("Resume checkpoint database is absent")
    if (output / "complete.json").exists():
        raise ValueError("Completed runs are immutable; use a new directory")
    store = ExperimentStore(output, manifest)
    baseline = dict(store.connection.execute("SELECT case_id,payload FROM records"))
    # Keep raw serialized cases, not 32,116 expanded configuration/model objects.
    # Only the bounded in-flight worker population is parsed into QueryCase instances.
    case_payloads = {case.case_id: case.model_dump_json() for case in cases} if isinstance(cases, list) else cases
    valid_ids = set(case_payloads)
    if len(valid_ids) != len(cases):
        store.close()
        raise ValueError("Input contains duplicate case IDs")

    def load_case(key: str) -> QueryCase:
        case = QueryCase.model_validate(portable(json.loads(case_payloads[key])))
        if case.case_id != key:
            raise ValueError(f"Input case identity changed: {key}")
        return case

    try:
        if not set(baseline) <= valid_ids:
            raise ValueError("Checkpoint contains foreign case IDs")
        registered = dict(store.connection.execute("SELECT case_id,payload FROM cases"))
        if not set(registered) <= valid_ids or not set(baseline) <= set(registered):
            raise ValueError("Checkpoint contains foreign or unregistered cases")
        for key, value in registered.items():
            if json.loads(value) != load_case(key).model_dump(mode="json"):
                raise ValueError(f"Registered case changed: {key}")
        for key, value in baseline.items():
            validate_record(load_case(key), key, value)
    except BaseException:
        store.close()
        raise
    segment_path = output / "segments.json"
    segments = json.loads(segment_path.read_text(encoding="utf-8")) if segment_path.exists() else []
    segment = {
        "pid": os.getpid(), "started_utc": datetime.now(UTC).isoformat(),
        "completed_before": len(baseline), "preserved_payload_sha256": content_hash(baseline),
        "registered_uncommitted_before": store.connection.execute(
            "SELECT COUNT(*) FROM cases WHERE case_id NOT IN (SELECT case_id FROM records)"
        ).fetchone()[0],
    }
    segments.append(segment)
    atomic_json(segment_path, segments)
    try:
        count = execute_experiment_cases((load_case(key) for key in case_payloads), store, workers=4, cpu_threads=1)
        observed = dict(store.connection.execute("SELECT case_id,payload FROM records"))
        if any(observed.get(key) != value for key, value in baseline.items()):
            raise ValueError("An already completed payload changed during resume")
        if set(observed) != valid_ids:
            raise ValueError("Required cases are missing; this run is incomplete")
        for key, value in observed.items():
            validate_record(load_case(key), key, value)
        segment.update(completed_after=len(observed), new_records=count, actual_success=True)
        return [json.loads(observed[key]) for key in case_payloads]
    except BaseException as error:
        segment.update(actual_success=False, error_type=type(error).__name__, error=str(error))
        raise
    finally:
        segment["ended_utc"] = datetime.now(UTC).isoformat()
        atomic_json(segment_path, segments)
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/phase12-baseline-v1.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if Path(prescriptxai.__file__).resolve() != (Path.cwd() / "src/prescriptxai/__init__.py").resolve():
        raise ValueError("Imports must resolve to this checkout's committed source")
    design = read_design(args.config)
    with FileLock("artifacts/phase12-headline.lock", timeout=0), idle_sleep_guard():
        rows = historical_rows(design)
        manifest = identity(args.config, design, rows, run_id=args.output.name, preflight=args.preflight)
        if args.preflight:
            args.output.mkdir(parents=True, exist_ok=False)
            atomic_json(args.output / "preflight.json", manifest)
            print(json.dumps({"preflight": True, "queries": len(rows), "groups": 24,
                              "inputs": len(manifest["input_hashes"]), "source": manifest["source"]}))
            return
        dirty = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        if dirty:
            raise ValueError("Commit the complete registration, helper and worktree before running")
        cases = {row[0]: row[1] for row in rows}
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
        measured = run_cases(cases, manifest, args.output, resume=args.resume)
        verify_unchanged(manifest)
        mismatches = []
        for row, record in zip(rows, measured, strict=True):
            changed = differences(scientific(json.loads(row[2])), scientific(record))
            if changed:
                mismatches.append({"case_id": row[0], "fields": changed})
        atomic_json(args.output / "historical-comparison.json", {
            "count": len(rows), "absolute_tolerance": design["absolute_tolerance"],
            "relative_tolerance": 0, "mismatches": mismatches,
            "historical_source": design["historical_source"], "current_source": manifest["source"],
        })
        if mismatches:
            raise ValueError(f"Historical regression changed in {len(mismatches)} cases; audit before continuing")
        fixture = args.output / "cmapss_baseline.parquet"
        frame = pd.DataFrame([
            {"case_id": row[0], "group": record["group"], "config_hash": record["config_hash"],
             "run_id": manifest["run_id"], "design_path": manifest["design_path"],
             "design_sha256": manifest["design_sha256"],
             "source": manifest["source"], "historical_source": design["historical_source"],
             "case_json": QueryCase.model_validate(portable(json.loads(row[1]))).model_dump_json(),
             "historical_case_json": row[1],
             "observation_json": json.dumps(record, sort_keys=True, allow_nan=False),
             "historical_observation_json": row[2]}
            for row, record in zip(rows, measured, strict=True)
        ])
        frame.to_parquet(fixture, index=False, compression="zstd")
        atomic_json(args.output / "cmapss_baseline.json", manifest)
        counts = dict(Counter(record["group"] for record in measured))
        atomic_json(args.output / "complete.json", {
            "actual_success": True, "run_id": manifest["run_id"], "queries": len(measured), "groups": counts,
            "design_path": manifest["design_path"], "design_sha256": manifest["design_sha256"],
            "historical_mismatches": 0, "source": manifest["source"],
            "fixture_sha256": file_hash(fixture), "input_hashes": manifest["input_hashes"],
            "completed_utc": datetime.now(UTC).isoformat(),
        })
        print(json.dumps({"actual_success": True, "queries": len(measured), "fixture": str(fixture)}))


if __name__ == "__main__":
    main()
