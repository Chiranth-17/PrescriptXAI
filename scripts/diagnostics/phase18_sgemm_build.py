"""Isolate fixed Linear SGEMM arithmetic in original and aligned native libraries."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def gemm_pair(function, weight, bias, values):
    """Use the production-observed column-major SGEMM layout for forward and ones VJP."""
    import numpy as np

    if weight.dtype != np.float32 or bias.dtype != np.float32 or values.dtype != np.float32:
        raise ValueError("Fixed operands must be original float32 values")
    out_count, in_count = weight.shape
    if bias.shape != (out_count,) or values.shape != (1, in_count):
        raise ValueError("Linear dimensions changed")
    weight, bias, values = (np.ascontiguousarray(a) for a in (weight, bias, values))
    pointer = ctypes.POINTER(ctypes.c_float)

    def call(transpose, m, k, right, right_leading, result, beta):
        a, b = ctypes.c_char(transpose), ctypes.c_char(b"N")
        mm, nn, kk = ctypes.c_int(m), ctypes.c_int(1), ctypes.c_int(k)
        lda, ldb, ldc = ctypes.c_int(in_count), ctypes.c_int(right_leading), ctypes.c_int(m)
        alpha, bet = ctypes.c_float(1), ctypes.c_float(beta)
        function(
            ctypes.byref(a),
            ctypes.byref(b),
            ctypes.byref(mm),
            ctypes.byref(nn),
            ctypes.byref(kk),
            ctypes.byref(alpha),
            weight.ctypes.data_as(pointer),
            ctypes.byref(lda),
            right.ctypes.data_as(pointer),
            ctypes.byref(ldb),
            ctypes.byref(bet),
            result.ctypes.data_as(pointer),
            ctypes.byref(ldc),
        )

    forward = bias.copy()
    call(b"T", out_count, in_count, values, in_count, forward, 1)
    backward = np.zeros(in_count, dtype=np.float32)
    ones = np.ones((1, out_count), dtype=np.float32)
    call(b"N", in_count, out_count, ones, out_count, backward, 0)
    return {"output": forward[None, :].tolist(), "ones_vjp": backward[None, :].tolist()}


def verify_inputs(root, evidence, design):
    metadata_path = root / "tests/regression/cmapss_baseline.json"
    if file_hash(metadata_path) != design["baseline_metadata_sha256"]:
        raise ValueError("Original baseline metadata changed")
    metadata = json.loads(metadata_path.read_text())
    pins = {
        "tests/regression/cmapss_baseline.parquet": metadata["fixture_sha256"],
        "configs/experiments/phase12-baseline-v1.yaml": metadata["design_sha256"],
        **metadata["input_hashes"],
    }
    for name, expected in pins.items():
        if file_hash(root / name.replace("\\", "/")) != expected:
            raise ValueError(f"Original input changed: {name}")
    manifest_path = evidence / design["original_manifest"]
    if file_hash(manifest_path) != design["original_manifest_sha256"]:
        raise ValueError("Original source manifest changed")
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest["context"]["code_hashes"].items():
        actual = hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if actual != expected:
            raise ValueError(f"Original production/helper changed: {name}")
    controls = {}
    for side, info in design["controls"].items():
        path = evidence / info["path"]
        if file_hash(path) != info["sha256"]:
            raise ValueError("Completed operation controls changed")
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        controls[side] = {(r["case_id"], r["vertex"]): r for r in rows}
        if len(rows) != 9 or len(controls[side]) != 9:
            raise ValueError("Incomplete operation controls")
    return controls


def export_operands(root, output, config, design, controls):
    from unittest.mock import patch

    import numpy as np
    import pyarrow.parquet as pq
    import torch
    from scripts.diagnostics.phase12_baseline import portable
    from threadpoolctl import threadpool_limits

    from prescriptxai.evaluation.experiments import QueryCase
    from prescriptxai.models.registry import ModelBundle
    from prescriptxai.pipeline import PrescriptXAI

    if platform.system() != "Windows":
        raise ValueError("Registered operand export uses the original Windows runtime")
    selected = {}
    for batch in pq.ParquetFile(root / "tests/regression/cmapss_baseline.parquet").iter_batches(64):
        for row in batch.to_pylist():
            if row["case_id"] in design["case_ids"]:
                selected[row["case_id"]] = row
    if set(selected) != set(design["case_ids"]):
        raise ValueError("Genuine selected case missing")
    records = []
    with (
        threadpool_limits(1),
        patch.object(
            ModelBundle,
            "predict_risk",
            side_effect=AssertionError("Scoring forbidden during operand export"),
        ),
        patch.object(
            ModelBundle,
            "torch_forward",
            side_effect=AssertionError("Scoring forbidden during operand export"),
        ),
        patch.object(
            torch.nn.Module,
            "_call_impl",
            side_effect=AssertionError("Network forward forbidden during operand export"),
        ),
    ):
        torch.set_num_threads(1)
        for key in design["case_ids"]:
            case = QueryCase.model_validate(portable(json.loads(selected[key]["case_json"])))
            runtime = PrescriptXAI.from_config(case.config)
            _, observed = runtime._normalize(case.state, case.context, complete=True)
            bundle = runtime._bundle(observed)
            network = bundle.surrogate.network_
            for vertex in ("original", "windows_candidate", "linux_candidate"):
                win = controls["windows"][key, vertex]
                lin = controls["linux"][key, vertex]
                for index, layer in network.named_children():
                    if not isinstance(layer, torch.nn.Linear):
                        continue
                    stage_name = f"network/{index}/Linear"
                    wstage = next(s for s in win["stages"] if s["name"] == stage_name)
                    lstage = next(s for s in lin["stages"] if s["name"] == stage_name)
                    weight = layer.weight.detach().cpu().numpy().copy()
                    bias = layer.bias.detach().cpu().numpy().copy()
                    digest = hashlib.sha256(weight.tobytes() + bias.tobytes()).hexdigest()
                    if digest != wstage["parameter_sha256"] or digest != lstage["parameter_sha256"]:
                        raise ValueError(
                            "Exported layer parameters differ from both original runtimes"
                        )
                    values = np.asarray(wstage["native"]["input"], dtype=np.float32)
                    if values.tolist() != lstage["common_windows_operands"]["input"]:
                        raise ValueError("Fixed common operands changed")
                    records.append(
                        {
                            "case_id": key,
                            "group": case.group,
                            "vertex": vertex,
                            "stage": stage_name,
                            "weight_shape": list(weight.shape),
                            "weight_hex": weight.tobytes().hex(),
                            "bias_hex": bias.tobytes().hex(),
                            "input_shape": list(values.shape),
                            "input_hex": values.tobytes().hex(),
                            "parameter_sha256": digest,
                            "expected_windows": {
                                k: wstage["native"][k] for k in ("output", "ones_vjp")
                            },
                            "expected_linux": {
                                k: lstage["common_windows_operands"][k]
                                for k in ("output", "ones_vjp")
                            },
                        }
                    )
    if len(records) != design["expected_operations"]:
        raise ValueError("Registered export count changed")
    path = output / "operands.json"
    path.write_text(json.dumps(records, indent=2, allow_nan=False) + "\n")
    receipt = {
        "export_source": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "config_sha256": file_hash(config),
        "operations": len(records),
        "operands_sha256": file_hash(path),
        "forward_calls": 0,
        "new_solves": 0,
        "new_fits": 0,
        "scope": "Read-only export of original fitted weights and completed fixed operands; not a scoring study",
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


def evaluate(args, root, evidence, output, design):
    import numpy as np

    if platform.system() != "Linux" or "torch" in sys.modules:
        raise ValueError("The isolated SGEMM process must run on Linux without importing torch")
    environment = {
        name: os.environ.get(name)
        for name in (
            "MKL_CBWR",
            "MKL_VERBOSE",
            "MKL_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_THREADING_LAYER",
            "MKL_INTERFACE_LAYER",
            "LD_PRELOAD",
        )
    }
    if environment != {
        "MKL_CBWR": None,
        "MKL_VERBOSE": "1",
        "MKL_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_THREADING_LAYER": "GNU",
        "MKL_INTERFACE_LAYER": "LP64",
        "LD_PRELOAD": None,
    }:
        raise ValueError("Unregistered or interposed numerical environment")
    operands_path = evidence / design["operand_export"] / "operands.json"
    export = json.loads(operands_path.with_name("complete.json").read_text())
    if export["config_sha256"] != file_hash(args.config) or export["operands_sha256"] != file_hash(
        operands_path
    ):
        raise ValueError("Operand export is not bound to this registration")
    library = args.library.resolve()
    expected = design["libraries"][args.arm]["sha256"]
    if file_hash(library) != expected:
        raise ValueError("Native library bytes differ from preregistration")
    handle = ctypes.CDLL(str(library), mode=os.RTLD_LOCAL)
    version = ctypes.create_string_buffer(512)
    version_function = handle.MKL_Get_Version_String
    version_function.argtypes = [ctypes.c_void_p, ctypes.c_int]
    version_function.restype = None
    version_function(version, len(version))
    sgemm = handle.sgemm_
    fp, ip, cp = (
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_char),
    )
    sgemm.argtypes = [cp, cp, ip, ip, ip, fp, fp, ip, fp, ip, fp, fp, ip]
    sgemm.restype = None
    rows = json.loads(operands_path.read_text())
    if len(rows) != design["expected_operations"]:
        raise ValueError("Operand count changed")
    count, linux_exact, windows_exact = 0, 0, 0
    started = time.perf_counter()
    with (output / "sgemm.jsonl").open("x", encoding="utf-8") as stream:
        for row in rows:
            weight = (
                np.frombuffer(bytes.fromhex(row["weight_hex"]), dtype=np.float32)
                .reshape(row["weight_shape"])
                .copy()
            )
            bias = np.frombuffer(bytes.fromhex(row["bias_hex"]), dtype=np.float32).copy()
            values = (
                np.frombuffer(bytes.fromhex(row["input_hex"]), dtype=np.float32)
                .reshape(row["input_shape"])
                .copy()
            )
            if (
                hashlib.sha256(weight.tobytes() + bias.tobytes()).hexdigest()
                != row["parameter_sha256"]
            ):
                raise ValueError("Decoded parameter bytes changed")
            result = gemm_pair(sgemm, weight, bias, values)
            if result != gemm_pair(sgemm, weight, bias, values):
                raise ValueError("Same-library SGEMM repeat changed")
            old_exact = result == row["expected_linux"]
            win_exact = result == row["expected_windows"]
            if args.arm == "embedded" and not old_exact:
                raise ValueError(
                    "Direct SGEMM does not reproduce original Linux operation: stop interpretation"
                )
            linux_exact += old_exact
            windows_exact += win_exact
            stream.write(
                json.dumps(
                    {
                        "case_id": row["case_id"],
                        "group": row["group"],
                        "vertex": row["vertex"],
                        "stage": row["stage"],
                        "parameter_sha256": row["parameter_sha256"],
                        "exact_original_linux": old_exact,
                        "exact_original_windows": win_exact,
                        **result,
                    },
                    allow_nan=False,
                )
                + "\n"
            )
            count += 1
    if "torch" in sys.modules:
        raise ValueError("Isolated operation arm unexpectedly imported torch")
    receipt = {
        "arm": args.arm,
        "config_sha256": file_hash(args.config),
        "library_sha256": file_hash(library),
        "library_version": version.value.decode(),
        "operations": count,
        "exact_original_linux_operations": linux_exact,
        "exact_original_windows_operations": windows_exact,
        "repeat_exact": True,
        "environment": environment,
        "operand_export_sha256": file_hash(operands_path),
        "sgemm_sha256": file_hash(output / "sgemm.jsonl"),
        "new_solves": 0,
        "new_fits": 0,
        "torch_imported": False,
        "elapsed_seconds": time.perf_counter() - started,
        "scope": "Isolated fixed SGEMM arithmetic, not full-pipeline parity or regression approval",
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
    if count != design["expected_operations"]:
        raise ValueError("Registered SGEMM count incomplete")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "evaluate"))
    for name in ("root", "evidence-root", "config", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--arm", choices=("embedded", "aligned"))
    parser.add_argument("--library", type=Path)
    args = parser.parse_args()
    root, evidence = args.root.resolve(), args.evidence_root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(root)
    sys.path.insert(0, str(evidence))
    import yaml

    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if (
        design["schema_version"] != 1
        or design["expected_operations"] != 27
        or not design["no_solves_or_fits"]
        or design["script_canonical_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    ):
        raise ValueError("Registered implementation/counts/scope changed")
    controls = verify_inputs(root, evidence, design)
    if args.mode == "export":
        export_operands(root, output, args.config, design, controls)
    else:
        if args.arm is None or args.library is None:
            raise ValueError("An evaluation arm needs its registered library")
        evaluate(args, root, evidence, output, design)


if __name__ == "__main__":
    main()
