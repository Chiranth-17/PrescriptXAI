"""Preregistered serial fixture profiling, before/after latency, and 10000-call memory study."""

import argparse
import cProfile
import gc
import hashlib
import json
import os
import pstats
import subprocess
import sys
import tracemalloc
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from time import perf_counter_ns

import numpy as np
import pandas as pd
import psutil
import torch
import yaml
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path("tests").resolve()))
from fixtures.golden_operator import (  # noqa: E402
    actual_snapshot,
    assert_snapshot,
    canonical_result,
)
from fixtures.operator_artifacts import write_operator_fixture  # noqa: E402
from prescriptxai.evaluation.experiments import runtime_manifest, source_revision  # noqa: E402
from prescriptxai.evaluation.metrics import engine_bootstrap_interval  # noqa: E402
from prescriptxai.pipeline import PrescriptXAI  # noqa: E402


def write_json(path, value):
    """Create a new result, never overwrite a completed execution segment."""
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def identities(directory):
    """Hash every fixed input and fitted object used by both timing segments."""
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((directory / "fixture").iterdir())
        if path.is_file()
    }


def manifest(config_path, directory):
    """Capture real source, input, configuration, process and environment provenance."""
    frozen_paths = [
        Path("tests/fixtures/operator_artifacts.py"),
        Path("tests/fixtures/recourse_models.py"),
        Path("tests/fixtures/golden_operator.py"),
        Path("tests/golden/operator-v1.json"),
        Path("pyproject.toml"),
        Path("uv.lock"),
        Path(__file__).resolve(),
    ]
    return {
        "source": source_revision(require_clean=True),
        "configuration": str(config_path),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "input_sha256": identities(directory),
        "frozen_helper_sha256": {
            path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in frozen_paths
        },
        "runtime": runtime_manifest(),
        "process_id": os.getpid(),
        "started_utc": datetime.now(UTC).isoformat(),
    }


def cases(directory):
    """Return the six actual saved rows in their fixed engine/cycle order."""
    frame = pd.read_csv(directory / "fixture" / "observed.csv")
    return [
        (
            int(row.engine_id),
            int(row.cycle),
            {"actuator": float(row.actuator), "sensor": float(row.sensor)},
        )
        for row in frame.itertuples(index=False)
    ]


def verify_frozen(reference, actual, *, within_segment=False):
    """Check every frozen byte identity, allowing only an explicitly different code segment."""
    keys = ["input_sha256", "config_sha256", "frozen_helper_sha256"]
    if within_segment:
        keys.append("source")
    if any(reference[key] != actual[key] for key in keys):
        raise ValueError("frozen inputs, helpers, golden, lock or configuration changed")


def timing(stage, config, config_path, directory):
    """Retain every complete public-call duration and canonical decision in serial order."""
    output = directory / f"{stage}.json"
    if output.exists():
        raise FileExistsError(output)
    evidence = manifest(config_path, directory)
    write_json(directory / f"{stage}-manifest.json", evidence)
    verify_frozen(json.loads((directory / "preparation.json").read_text()), evidence)
    previous = json.loads((directory / "before.json").read_text()) if stage == "after" else None
    if previous and (
        previous["manifest"]["input_sha256"] != evidence["input_sha256"]
        or previous["manifest"]["config_sha256"] != evidence["config_sha256"]
        or previous["manifest"]["frozen_helper_sha256"] != evidence["frozen_helper_sha256"]
    ):
        raise ValueError("before/after artifact/configuration provenance differs")
    service = PrescriptXAI.from_config(directory / "fixture" / "pipeline.yaml")
    assert service.config.seed == config["seeds"]["covariance_fit_and_solver_configuration"]
    assert service.config.recourse.k_max == config["k_max"]
    assert service.config.recourse.rate_horizon_steps == config["K"]
    assert service.config.validation.mahalanobis_max == config["D_max"]
    rows = cases(directory)
    for index in range(config["measurement"]["warmup_calls"]):
        service.recommend(rows[index % len(rows)][2], mode=config["mode"])
    profile = cProfile.Profile()
    profile.enable()
    for index in range(config["measurement"]["profile_calls"]):
        service.recommend(rows[index % len(rows)][2], mode=config["mode"])
    profile.disable()
    profile.dump_stats(str(directory / f"{stage}.pstats"))
    profile_text = StringIO()
    pstats.Stats(profile, stream=profile_text).sort_stats("cumulative").print_stats(35)
    (directory / f"{stage}-profile.txt").write_text(profile_text.getvalue(), encoding="utf-8")
    assert len(rows) == 6 and sorted({row[0] for row in rows}) == config["evaluation_engines"]
    records = []
    with (directory / f"{stage}-calls.jsonl").open("x", encoding="utf-8") as stream:
        for repeat in range(config["measurement"]["repeats_per_observation"]):
            for engine, cycle, state in rows:
                attempt = {
                    "event": "attempt",
                    "engine_id": engine,
                    "cycle": cycle,
                    "repeat": repeat,
                    "started_utc": datetime.now(UTC).isoformat(),
                }
                stream.write(json.dumps(attempt) + "\n")
                stream.flush()
                start = perf_counter_ns()
                try:
                    result = service.recommend(state, mode=config["mode"])
                except BaseException as error:
                    stream.write(
                        json.dumps(
                            {
                                **attempt,
                                "event": "error",
                                "elapsed_ms": (perf_counter_ns() - start) / 1e6,
                                "error_type": type(error).__name__,
                            }
                        )
                        + "\n"
                    )
                    stream.flush()
                    raise
                elapsed = (perf_counter_ns() - start) / 1e6
                decision = canonical_result(result)
                record = {
                    "event": "result",
                    "engine_id": engine,
                    "cycle": cycle,
                    "repeat": repeat,
                    "elapsed_ms": elapsed,
                    "decision": decision,
                }
                # Save before checking equality, so a parity failure never loses its timing.
                stream.write(json.dumps(record, allow_nan=False) + "\n")
                stream.flush()
                if previous:
                    assert_snapshot(decision, previous["records"][len(records)]["decision"])
                records.append(record)
    assert len(records) == config["measurement"]["total_timed_calls_per_segment"]
    snapshot = actual_snapshot(directory / "fixture")
    assert_snapshot(snapshot, json.loads(Path("tests/golden/operator-v1.json").read_text()))
    samples = np.asarray([row["elapsed_ms"] for row in records])
    engines = np.asarray([row["engine_id"] for row in records])
    ci = engine_bootstrap_interval(
        engines,
        samples,
        statistic=lambda values: float(np.percentile(values, 95)),
        replicates=config["measurement"]["bootstrap_replicates"],
        seed=config["seed"],
        confidence=config["measurement"]["confidence"],
    )
    summary = {
        "calls": len(records),
        "engines": len(set(engines.tolist())),
        "p50_ms": float(np.percentile(samples, 50)),
        "p95_ms": float(np.percentile(samples, 95)),
        "p99_ms": float(np.percentile(samples, 99)),
        "p95_engine_ci": ci.__dict__,
    }
    evidence["ended_utc"] = datetime.now(UTC).isoformat()
    verify_frozen(evidence, manifest(config_path, directory), within_segment=True)
    write_json(
        output,
        {
            "stage": stage,
            "manifest": evidence,
            "summary": summary,
            "records": records,
            "golden_passed": True,
        },
    )
    print(json.dumps(summary), flush=True)


def memory(config, config_path, directory):
    """Check retained Python and process allocations over exactly 10000 full safe calls."""
    if (directory / "memory.json").exists():
        raise FileExistsError(directory / "memory.json")
    evidence = manifest(config_path, directory)
    write_json(directory / "memory-manifest.json", evidence)
    fixed = json.loads((directory / "before.json").read_text())["manifest"]
    verify_frozen(fixed, evidence)
    service = PrescriptXAI.from_config(directory / "fixture" / "pipeline.yaml")
    selected_cases = {(row["engine_id"], row["cycle"]) for row in config["memory"]["cases"]}
    safe = [row for row in cases(directory) if (row[0], row[1]) in selected_cases]
    assert len(safe) == 2
    assert all(not service.assess(row[2]).alert for row in safe)
    expected = [canonical_result(service.recommend(row[2])) for row in safe]
    for index in range(config["memory"]["warmup_calls"]):
        service.recommend(safe[index % len(safe)][2])
    gc.collect()
    tracemalloc.start()
    process = psutil.Process()

    def checkpoint(completed):
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        return {
            "calls": completed,
            "python_live_bytes": current,
            "python_peak_bytes": peak,
            "rss_bytes": process.memory_info().rss,
        }

    checkpoints = [checkpoint(0)]
    with (
        (directory / "memory-calls.jsonl").open("x", encoding="utf-8") as stream,
        (directory / "memory-checkpoints.jsonl").open("x", encoding="utf-8") as checkpoint_stream,
    ):
        checkpoint_stream.write(json.dumps(checkpoints[0]) + "\n")
        checkpoint_stream.flush()
        for index in range(config["memory"]["calls"]):
            selected = index % len(safe)
            stream.write(
                json.dumps({"event": "attempt", "call": index + 1, "engine_id": safe[selected][0]})
                + "\n"
            )
            stream.flush()
            try:
                result = service.recommend(safe[selected][2])
            except BaseException as error:
                stream.write(
                    json.dumps(
                        {"event": "error", "call": index + 1, "error_type": type(error).__name__}
                    )
                    + "\n"
                )
                stream.flush()
                raise
            stream.write(
                json.dumps(
                    {
                        "event": "result",
                        "call": index + 1,
                        "engine_id": safe[selected][0],
                        "status": result.status,
                        "risk": result.risk_after,
                    }
                )
                + "\n"
            )
            stream.flush()
            assert_snapshot(canonical_result(result), expected[selected])
            del result
            if (index + 1) % config["memory"]["checkpoint_every"] == 0:
                stream.flush()
                checkpoints.append(checkpoint(index + 1))
                checkpoint_stream.write(json.dumps(checkpoints[-1]) + "\n")
                checkpoint_stream.flush()
                print(json.dumps(checkpoints[-1]), flush=True)
    tracemalloc.stop()
    python_growth = checkpoints[-1]["python_live_bytes"] - checkpoints[0]["python_live_bytes"]
    rss_growth = checkpoints[-1]["rss_bytes"] - checkpoints[0]["rss_bytes"]
    passed = (
        python_growth <= config["memory"]["maximum_final_python_growth_bytes"]
        and rss_growth <= config["memory"]["maximum_final_rss_growth_bytes"]
    )
    evidence["ended_utc"] = datetime.now(UTC).isoformat()
    verify_frozen(evidence, manifest(config_path, directory), within_segment=True)
    write_json(
        directory / "memory.json",
        {
            "manifest": evidence,
            "checkpoints": checkpoints,
            "calls": config["memory"]["calls"],
            "python_growth_bytes": python_growth,
            "rss_growth_bytes": rss_growth,
            "passed": passed,
        },
    )
    if not passed:
        raise RuntimeError(
            "predeclared memory regression budget missed; inspect retained checkpoints"
        )


def main():
    """Run one explicitly requested stage, refusing duplicates and completed-stage replacement."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["prepare", "before", "after", "memory"], required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/experiments/phase9-performance.yaml")
    )
    parser.add_argument("--directory", type=Path, default=Path("artifacts/phase9/performance-v1"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    args.directory.mkdir(parents=True, exist_ok=True)
    lock = args.directory / "active-stage.json"
    write_json(
        lock,
        {
            "process_id": os.getpid(),
            "stage": args.stage,
            "started_utc": datetime.now(UTC).isoformat(),
        },
    )
    try:
        source_revision(require_clean=True)
        if subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"], text=True
        ).strip():
            raise ValueError(
                "commit the complete source, fixtures, goldens and lock before measuring"
            )
        torch.set_num_threads(config["measurement"]["cpu_native_threads"])
        torch.set_num_interop_threads(config["measurement"]["cpu_native_threads"])
        with threadpool_limits(config["measurement"]["cpu_native_threads"]):
            if args.stage == "prepare":
                fixture = (args.directory / "fixture").resolve()
                fixture.mkdir(exist_ok=False)
                write_operator_fixture(fixture)
                write_json(
                    args.directory / "preparation.json", manifest(args.config, args.directory)
                )
            elif args.stage == "memory":
                memory(config, args.config, args.directory)
            else:
                timing(args.stage, config, args.config, args.directory)
    finally:
        lock.unlink()


if __name__ == "__main__":
    main()
