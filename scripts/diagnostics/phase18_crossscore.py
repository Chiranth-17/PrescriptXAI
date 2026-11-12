"""Revalidate fixed saved candidates without optimization, propagation, or fitting."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def revision(root):
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--side", required=True, choices=("windows", "linux"))
    args = parser.parse_args()
    root = args.root.resolve()
    evidence = args.evidence_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(root)
    sys.path.insert(0, str(root))

    import pyarrow.parquet as pq
    import torch
    import yaml
    from scripts.diagnostics.phase12_baseline import differences, portable
    from scripts.diagnostics.phase12_regression import comparison_record, verify_files
    from scripts.diagnostics.regression_tiers import runtime_build
    from threadpoolctl import threadpool_limits

    import prescriptxai
    from prescriptxai.evaluation.experiments import QueryCase
    from prescriptxai.pipeline import PrescriptXAI
    from prescriptxai.validation.pipeline import validate_candidate

    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if platform.system().lower() != args.side:
        raise ValueError("Runtime label must match the actual operating system")
    if (
        design["schema_version"] != 1
        or design["expected_cases"] != 53
        or design["expected_rows_per_runtime"] != 159
        or not design["no_new_solves"]
        or not design["no_refits"]
        or design["cpu_threads"] != 1
        or design["diagnostic_tolerance"] != 1e-6
    ):
        raise ValueError("Committed diagnostic design changed")
    script_hash = hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if script_hash != design["script_canonical_sha256"]:
        raise ValueError("Diagnostic implementation differs from its committed registration")
    if Path(prescriptxai.__file__).resolve() != root / "src/prescriptxai/__init__.py":
        raise ValueError("Package must resolve to the selected original environment")
    database = evidence / design["linux_database"]
    wal = database.with_name(database.name + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise ValueError("Preserved database must have no pending WAL")
    ids_path = evidence / design["ids_path"]
    if (
        file_hash(database) != design["linux_database_sha256"]
        or file_hash(ids_path) != design["ids_sha256"]
    ):
        raise ValueError("Preserved input database or fixed selection changed")
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    if len(ids) != 53 or ids != sorted(set(ids)):
        raise ValueError("Fixed diagnostic selection differs")
    metadata = json.loads(Path("tests/regression/cmapss_baseline.json").read_text())
    verify_files(
        {
            "tests/regression/cmapss_baseline.parquet": metadata["fixture_sha256"],
            "configs/experiments/phase12-baseline-v1.yaml": metadata["design_sha256"],
            **metadata["input_hashes"],
        }
    )
    origin = json.loads((evidence / design["linux_manifest"]).read_text())
    for name, expected in origin["context"]["code_hashes"].items():
        actual = hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if actual != expected:
            raise ValueError(f"Production code changed: {name}")
    saved = {}
    for batch in pq.ParquetFile("tests/regression/cmapss_baseline.parquet").iter_batches(64):
        for row in batch.to_pylist():
            if row["case_id"] in ids:
                saved[row["case_id"]] = row
    if set(saved) != set(ids):
        raise ValueError("A genuine selected fixture case is missing")
    torch.set_num_threads(1)
    torch.manual_seed(design["seed"])
    receipt = {
        "schema_version": 1,
        "side": args.side,
        "analysis_source": revision(evidence),
        "package_source": revision(root),
        "config_sha256": file_hash(args.config),
        "database_sha256": file_hash(database),
        "new_solves": 0,
        "new_fits": 0,
        "scope": "Fixed-candidate diagnostic, not regression approval or latency certification",
    }
    failures = []
    rows = 0
    started = time.perf_counter()
    with (
        threadpool_limits(1),
        closing(sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)) as db,
        (output / "scores.jsonl").open("x", encoding="utf-8") as stream,
    ):
        for key in ids:
            previous = json.loads(saved[key]["observation_json"])
            current = json.loads(
                db.execute("SELECT payload FROM records WHERE case_id=?", (key,)).fetchone()[0]
            )
            case = QueryCase.model_validate(portable(json.loads(saved[key]["case_json"])))
            runtime = PrescriptXAI.from_config(case.config)
            runtime.config = case.config.model_copy(deep=True)
            initial, observed = runtime._normalize(case.state, case.context, complete=True)
            risk = runtime.assess(initial, case.context, case.mode).risk
            with runtime.engine.predictor_lock:
                bundle = runtime._bundle(observed)
                stream.write(
                    json.dumps(
                        {"case_id": key, "group": case.group, "vertex": "original", "risk": risk},
                        allow_nan=False,
                    )
                    + "\n"
                )
                rows += 1
                control = previous if args.side == "windows" else current
                if risk != control["risk_before"]:
                    failures.append(
                        {
                            "case_id": key,
                            "vertex": "original",
                            "field": "risk_before",
                            "saved": control["risk_before"],
                            "actual": risk,
                        }
                    )
                for label, record in (
                    ("windows_candidate", previous),
                    ("linux_candidate", current),
                ):
                    report = (
                        validate_candidate(
                            initial,
                            record["candidate"],
                            bundle,
                            runtime.engine.taxonomy,
                            runtime.engine.mahalanobis,
                            runtime.config,
                            runtime.engine.coupling,
                        )
                        .to_schema()
                        .model_dump(mode="json")
                    )
                    stream.write(
                        json.dumps(
                            {
                                "case_id": key,
                                "group": case.group,
                                "vertex": label,
                                "candidate": record["candidate"],
                                "validation": report,
                            },
                            allow_nan=False,
                        )
                        + "\n"
                    )
                    rows += 1
                    if label == (
                        "windows_candidate" if args.side == "windows" else "linux_candidate"
                    ):
                        left = comparison_record(
                            {"config_path": "diagnostic", "validation": record["validation"]}
                        )
                        right = comparison_record(
                            {"config_path": "diagnostic", "validation": report}
                        )
                        changed = differences(left, right, atol=0)
                        if changed:
                            failures.append({"case_id": key, "vertex": label, "fields": changed})
        receipt["runtime_build"] = runtime_build()
    receipt.update(
        rows=rows,
        cases=len(ids),
        elapsed_seconds=time.perf_counter() - started,
        native_control_exact=not failures,
        control_failures=failures,
        scores_sha256=file_hash(output / "scores.jsonl"),
    )
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in (
                    "side",
                    "rows",
                    "cases",
                    "native_control_exact",
                    "new_solves",
                    "new_fits",
                    "elapsed_seconds",
                )
            }
        )
    )
    if rows != 159 or failures:
        raise ValueError("Native saved-candidate control did not reproduce; do not infer causes")


if __name__ == "__main__":
    main()
