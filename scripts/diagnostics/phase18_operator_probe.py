"""Trace fixed surrogate operations with exact native controls and shared operands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path


def operation(function, values):
    import torch

    tensor = torch.tensor(values, dtype=torch.float32, requires_grad=True)
    result = function(tensor)
    gradient = torch.autograd.grad(result.sum(), tensor)[0]
    return {
        "input": tensor.detach().tolist(),
        "output": result.detach().tolist(),
        "ones_vjp": gradient.detach().tolist(),
    }


def trace(bundle, values, common=None):
    import torch

    network = bundle.surrogate.network_
    if not isinstance(network, torch.nn.Sequential):
        raise ValueError("Registered probe requires the existing XGBoost MLP surrogate")
    functions = [
        (f"network/{name}/{type(layer).__name__}", layer)
        for name, layer in network.named_children()
    ]
    functions += [("probability_sigmoid", lambda x: torch.sigmoid(x).reshape(-1))]
    if bundle.calibrator is not None:
        functions += [("calibration", bundle.calibrator.transform_tensor)]
    current = torch.tensor(values, dtype=torch.float32, requires_grad=True)
    stages = []
    for index, (name, function) in enumerate(functions):
        inputs = current.detach().tolist()
        current = function(current)
        if common is not None and common[index]["name"] != name:
            raise ValueError("Native architecture differs from the fixed common trace")
        shared = inputs if common is None else common[index]["native"]["input"]
        parameters = list(function.parameters()) if isinstance(function, torch.nn.Module) else []
        state = hashlib.sha256()
        for parameter in parameters:
            state.update(parameter.detach().cpu().numpy().tobytes())
        stages.append(
            {
                "name": name,
                "parameter_sha256": state.hexdigest(),
                "native": operation(function, inputs),
                "common_windows_operands": operation(function, shared),
            }
        )
    seed = torch.tensor(values, dtype=torch.float32, requires_grad=True)
    direct = bundle.torch_forward(seed)
    direct_gradient = torch.autograd.grad(direct.sum(), seed)[0]
    original = torch.tensor(values, dtype=torch.float32, requires_grad=True)
    manual = original
    for _, function in functions:
        manual = function(manual)
    manual_gradient = torch.autograd.grad(manual.sum(), original)[0]
    if not torch.equal(direct, manual) or not torch.equal(direct_gradient, manual_gradient):
        raise ValueError("Tracing changes the native production forward/backward result")
    return {
        "surrogate": float(direct.detach().reshape(())),
        "surrogate_gradient": direct_gradient.detach().tolist(),
        "stages": stages,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "evidence-root", "config", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--side", required=True, choices=("windows", "linux"))
    args = parser.parse_args()
    root, evidence = args.root.resolve(), args.evidence_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(root)
    sys.path.insert(0, str(evidence))

    import pyarrow.parquet as pq
    import torch
    import yaml
    from scripts.diagnostics.phase12_baseline import portable
    from scripts.diagnostics.phase12_regression import verify_files
    from scripts.diagnostics.phase18_crossscore import file_hash, revision
    from scripts.diagnostics.regression_tiers import runtime_build
    from threadpoolctl import threadpool_limits

    import prescriptxai
    from prescriptxai.evaluation.experiments import QueryCase
    from prescriptxai.pipeline import PrescriptXAI

    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if (
        design["schema_version"] != 1
        or design["expected_cases"] != 3
        or design["expected_rows"] != 9
        or not design["no_solves_or_fits"]
        or design["script_canonical_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        or platform.system().lower() != args.side
        or Path(prescriptxai.__file__).resolve() != root / "src/prescriptxai/__init__.py"
    ):
        raise ValueError("Registered implementation/runtime/scope changed")
    control_path = evidence / design["controls"][args.side]["path"]
    if file_hash(control_path) != design["controls"][args.side]["sha256"]:
        raise ValueError("Original native gradient controls changed")
    controls = {
        (r["case_id"], r["vertex"]): r
        for r in map(json.loads, control_path.read_text().splitlines())
    }
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
    for name, expected in manifest["context"]["code_hashes"].items():
        if (
            hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            != expected
        ):
            raise ValueError(f"Original production/helper code changed: {name}")
    selected = {}
    for batch in pq.ParquetFile("tests/regression/cmapss_baseline.parquet").iter_batches(64):
        for row in batch.to_pylist():
            if row["case_id"] in design["case_ids"]:
                selected[row["case_id"]] = row
    if set(selected) != set(design["case_ids"]):
        raise ValueError("A selected genuine case is missing")
    shared = None
    if args.side == "linux":
        windows_path = evidence / design["windows_trace"]
        windows_receipt = json.loads(windows_path.with_name("complete.json").read_text())
        if (
            windows_receipt["config_sha256"] != file_hash(args.config)
            or windows_receipt["trace_sha256"] != file_hash(windows_path)
            or not windows_receipt["native_controls_exact"]
        ):
            raise ValueError("Common Windows operands lack a matching native receipt")
        shared = {
            (r["case_id"], r["vertex"]): r
            for r in map(json.loads, windows_path.read_text().splitlines())
        }
        if len(shared) != 9:
            raise ValueError("Common Windows operand set is incomplete")
    torch.set_num_threads(1)
    torch.manual_seed(design["seed"])
    torch.use_deterministic_algorithms(True)
    started = time.perf_counter()
    rows = 0
    with threadpool_limits(1), (output / "trace.jsonl").open("x", encoding="utf-8") as stream:
        for key in design["case_ids"]:
            case = QueryCase.model_validate(portable(json.loads(selected[key]["case_json"])))
            runtime = PrescriptXAI.from_config(case.config)
            initial, observed = runtime._normalize(case.state, case.context, complete=True)
            with runtime.engine.predictor_lock:
                bundle = runtime._bundle(observed)
                if list(bundle.feature_names) != controls[key, "original"]["features"]:
                    raise ValueError("Model/input feature order changed")
                for vertex in ("original", "windows_candidate", "linux_candidate"):
                    control = controls[key, vertex]
                    result = trace(
                        bundle,
                        control["scaled_input"],
                        None if shared is None else shared[key, vertex]["stages"],
                    )
                    if (
                        result["surrogate"] != control["surrogate"]
                        or result["surrogate_gradient"] != control["surrogate_gradient"]
                    ):
                        raise ValueError(f"Native forward/backward control changed: {key}/{vertex}")
                    stream.write(
                        json.dumps(
                            {"case_id": key, "group": case.group, "vertex": vertex, **result},
                            allow_nan=False,
                        )
                        + "\n"
                    )
                    rows += 1
        runtime_info = runtime_build()
    receipt = {
        "schema_version": 1,
        "side": args.side,
        "analysis_source": revision(evidence),
        "package_source": revision(root),
        "config_sha256": file_hash(args.config),
        "cases": len(selected),
        "rows": rows,
        "native_controls_exact": True,
        "manual_chain_exact": True,
        "new_solves": 0,
        "new_fits": 0,
        "runtime_build": runtime_info,
        "trace_sha256": file_hash(output / "trace.jsonl"),
        "elapsed_seconds": time.perf_counter() - started,
        "scope": "Fixed-operation diagnostic; common Windows operands do not replace production results",
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in ("side", "cases", "rows", "native_controls_exact", "elapsed_seconds")
            }
        )
    )
    if rows != 9:
        raise ValueError("Registered row count incomplete")


if __name__ == "__main__":
    main()
