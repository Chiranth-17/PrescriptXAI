"""Compare preregistered native and compatible MKL policies at fixed operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "evidence-root", "config", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--side", required=True, choices=("windows", "linux"))
    parser.add_argument("--policy", required=True, choices=("native", "compatible"))
    args = parser.parse_args()
    root, evidence = args.root.resolve(), args.evidence_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(root)
    sys.path.insert(0, str(evidence))
    # Environment must be set by the parent BEFORE importing the numerical stack.
    expected = None if args.policy == "native" else "COMPATIBLE"
    if os.environ.get("MKL_CBWR") != expected or os.environ.get("MKL_VERBOSE") != "1":
        raise ValueError("Native numerical libraries were not launched with registered policy")

    import pyarrow.parquet as pq
    import torch
    import yaml
    from scripts.diagnostics.phase12_baseline import portable
    from scripts.diagnostics.phase12_regression import verify_files
    from scripts.diagnostics.phase18_crossscore import file_hash, revision
    from scripts.diagnostics.phase18_operator_probe import trace
    from scripts.diagnostics.regression_tiers import runtime_build
    from threadpoolctl import threadpool_limits

    import prescriptxai
    from prescriptxai.evaluation.experiments import QueryCase
    from prescriptxai.pipeline import PrescriptXAI

    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if (
        design["schema_version"] != 1
        or design["expected_cases"] != 3
        or design["expected_rows_per_arm"] != 9
        or args.policy not in design["policies"]
        or not design["no_solves_or_fits"]
        or design["script_canonical_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        or platform.system().lower() != args.side
        or Path(prescriptxai.__file__).resolve() != root / "src/prescriptxai/__init__.py"
    ):
        raise ValueError("Registered implementation/runtime/counts changed")
    helper = evidence / "scripts/diagnostics/phase18_operator_probe.py"
    if (
        hashlib.sha256(helper.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        != design["operator_helper_canonical_sha256"]
    ):
        raise ValueError("Existing operation-trace implementation changed")
    metadata = json.loads(Path("tests/regression/cmapss_baseline.json").read_text())
    verify_files(
        {
            "tests/regression/cmapss_baseline.parquet": metadata["fixture_sha256"],
            "configs/experiments/phase12-baseline-v1.yaml": metadata["design_sha256"],
            **metadata["input_hashes"],
        }
    )
    manifest_path = evidence / design["original_manifest"]
    if file_hash(manifest_path) != design["original_manifest_sha256"]:
        raise ValueError("Original source/input manifest changed")
    manifest = json.loads(manifest_path.read_text())
    for name, expected_hash in manifest["context"]["code_hashes"].items():
        if (
            hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            != expected_hash
        ):
            raise ValueError(f"Original production/helper source changed: {name}")
    controls = {}
    for side, registered in design["controls"].items():
        path = evidence / registered["path"]
        if file_hash(path) != registered["sha256"]:
            raise ValueError(f"Completed {side} operation controls changed")
        records = [json.loads(line) for line in path.read_text().splitlines()]
        controls[side] = {(r["case_id"], r["vertex"]): r for r in records}
        if len(controls[side]) != 9 or len(records) != 9:
            raise ValueError("Completed operation control set is incomplete")
    selected = {}
    for batch in pq.ParquetFile("tests/regression/cmapss_baseline.parquet").iter_batches(64):
        for row in batch.to_pylist():
            if row["case_id"] in design["case_ids"]:
                selected[row["case_id"]] = row
    if set(selected) != set(design["case_ids"]):
        raise ValueError("Genuine selected cases missing")
    torch.set_num_threads(1)
    torch.manual_seed(design["seed"])
    torch.use_deterministic_algorithms(True)
    started = time.perf_counter()
    rows, native_differences = 0, []
    with threadpool_limits(1), (output / "operations.jsonl").open("x", encoding="utf-8") as stream:
        for key in design["case_ids"]:
            case = QueryCase.model_validate(portable(json.loads(selected[key]["case_json"])))
            runtime = PrescriptXAI.from_config(case.config)
            _, observed = runtime._normalize(case.state, case.context, complete=True)
            with runtime.engine.predictor_lock:
                bundle = runtime._bundle(observed)
                for vertex in ("original", "windows_candidate", "linux_candidate"):
                    common = controls["windows"][key, vertex]
                    native = controls[args.side][key, vertex]
                    values = common["stages"][0]["native"]["input"]
                    result = trace(bundle, values, common["stages"])
                    repeated = trace(bundle, values, common["stages"])
                    if result != repeated:
                        raise ValueError("Same-policy fixed-operation repeat is not exact")
                    expected_result = {k: native[k] for k in result}
                    exact = result == expected_result
                    if not exact:
                        native_differences.append({"case_id": key, "vertex": vertex})
                    if args.policy == "native" and not exact:
                        raise ValueError(
                            "Unchanged native control failed: stop causal interpretation"
                        )
                    for actual, baseline in zip(result["stages"], common["stages"], strict=True):
                        if (
                            actual["name"] != baseline["name"]
                            or actual["parameter_sha256"] != baseline["parameter_sha256"]
                        ):
                            raise ValueError("Architecture or parameter bytes changed")
                        if (
                            actual["common_windows_operands"]["input"]
                            != baseline["native"]["input"]
                        ):
                            raise ValueError("Common Windows operands changed")
                    stream.write(
                        json.dumps(
                            {
                                "case_id": key,
                                "group": case.group,
                                "vertex": vertex,
                                "exact_original_native": exact,
                                **result,
                            },
                            allow_nan=False,
                        )
                        + "\n"
                    )
                    rows += 1
        runtime_info = runtime_build()
    receipt = {
        "schema_version": 1,
        "side": args.side,
        "policy": args.policy,
        "analysis_source": revision(evidence),
        "package_source": revision(root),
        "config_sha256": file_hash(args.config),
        "cases": len(selected),
        "rows": rows,
        "native_control_required": args.policy == "native",
        "exact_original_native_rows": rows - len(native_differences),
        "native_differences": native_differences,
        "same_policy_repeat_exact": True,
        "manual_production_chain_exact": True,
        "new_solves": 0,
        "new_fits": 0,
        "environment": {
            name: os.environ.get(name)
            for name in (
                "MKL_CBWR",
                "MKL_VERBOSE",
                "MKL_DYNAMIC",
                "OMP_DYNAMIC",
                "MKL_NUM_THREADS",
                "OMP_NUM_THREADS",
            )
        },
        "runtime_build": runtime_info,
        "operations_sha256": file_hash(output / "operations.jsonl"),
        "elapsed_seconds": time.perf_counter() - started,
        "scope": "Isolated two-policy fixed-operation study; no production policy or historical acceptance change",
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in (
                    "side",
                    "policy",
                    "cases",
                    "rows",
                    "exact_original_native_rows",
                    "elapsed_seconds",
                )
            }
        )
    )
    if rows != design["expected_rows_per_arm"]:
        raise ValueError("Registered fixed-operation arm incomplete")


if __name__ == "__main__":
    main()
