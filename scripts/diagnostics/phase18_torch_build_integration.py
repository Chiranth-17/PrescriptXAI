"""Test isolated build-aligned Linear operations inside the original fixed Torch graph."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import sys
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import MethodType
from unittest.mock import patch


def linear_forward(function, weight, bias, values):
    import numpy as np

    if any(a.dtype != np.float32 for a in (weight, bias, values)):
        raise ValueError("Diagnostic requires original float32 operands")
    out_count, in_count = weight.shape
    if values.shape != (1, in_count) or bias.shape != (out_count,):
        raise ValueError("Diagnostic requires one recorded row with matching dimensions")
    result = np.ascontiguousarray(bias).copy()
    _call(function, b"T", weight, values, result, out_count, in_count, in_count, 1)
    return result[None, :]


def linear_vjp(function, weight, upstream):
    import numpy as np

    if weight.dtype != np.float32 or upstream.dtype != np.float32:
        raise ValueError("Diagnostic requires original float32 operands")
    out_count, in_count = weight.shape
    if upstream.shape != (1, out_count):
        raise ValueError("Diagnostic requires one upstream row with matching dimensions")
    result = np.zeros(in_count, dtype=np.float32)
    _call(function, b"N", weight, upstream, result, in_count, out_count, out_count, 0)
    return result[None, :]


def _call(function, transpose, weight, right, result, m, k, right_leading, beta):
    import numpy as np

    weight, right = (np.ascontiguousarray(a) for a in (weight, right))
    a, b = ctypes.c_char(transpose), ctypes.c_char(b"N")
    mm, nn, kk = ctypes.c_int(m), ctypes.c_int(1), ctypes.c_int(k)
    lda, ldb, ldc = ctypes.c_int(weight.shape[1]), ctypes.c_int(right_leading), ctypes.c_int(m)
    alpha, bet = ctypes.c_float(1), ctypes.c_float(beta)
    fp = ctypes.POINTER(ctypes.c_float)
    function(
        ctypes.byref(a),
        ctypes.byref(b),
        ctypes.byref(mm),
        ctypes.byref(nn),
        ctypes.byref(kk),
        ctypes.byref(alpha),
        weight.ctypes.data_as(fp),
        ctypes.byref(lda),
        right.ctypes.data_as(fp),
        ctypes.byref(ldb),
        ctypes.byref(bet),
        result.ctypes.data_as(fp),
        ctypes.byref(ldc),
    )


@contextmanager
def aligned_layers(network, function, counters):
    """Replace only child-local Linear input derivatives; original weights stay unchanged."""
    import torch

    class AlignedLinear(torch.autograd.Function):
        @staticmethod
        def forward(ctx, values, weight, bias):
            if any(
                t.device.type != "cpu" or t.dtype != torch.float32 for t in (values, weight, bias)
            ):
                raise ValueError("Only original CPU float32 inputs are registered")
            ctx.save_for_backward(weight)
            counters["forward"] += 1
            output = linear_forward(
                function, weight.detach().numpy(), bias.detach().numpy(), values.detach().numpy()
            )
            return torch.from_numpy(output)

        @staticmethod
        def backward(ctx, upstream):
            (weight,) = ctx.saved_tensors
            counters["backward"] += 1
            gradient = linear_vjp(function, weight.detach().numpy(), upstream.detach().numpy())
            # Parameters are fixed; this experiment asks only for input gradients, never trains.
            return torch.from_numpy(gradient), None, None

    def forward(layer, values):
        return AlignedLinear.apply(values, layer.weight, layer.bias)

    with ExitStack() as stack:
        count = 0
        for layer in network.children():
            if isinstance(layer, torch.nn.Linear):
                stack.enter_context(patch.object(layer, "forward", MethodType(forward, layer)))
                count += 1
        if count != 3:
            raise ValueError("Original three Linear layers required")
        yield


def load_function(library):
    handle = ctypes.CDLL(str(library), mode=os.RTLD_LOCAL)
    version = ctypes.create_string_buffer(512)
    version_function = handle.MKL_Get_Version_String
    version_function.argtypes = [ctypes.c_void_p, ctypes.c_int]
    version_function.restype = None
    version_function(version, len(version))
    fp, ip, cp = (ctypes.POINTER(t) for t in (ctypes.c_float, ctypes.c_int, ctypes.c_char))
    function = handle.sgemm_
    function.argtypes = [cp, cp, ip, ip, ip, fp, fp, ip, fp, ip, fp, fp, ip]
    function.restype = None
    return handle, function, version.value.decode()


def finite_tree(value):
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, list):
        return all(finite_tree(v) for v in value)
    return not isinstance(value, (int, float)) or math.isfinite(value)


def fixed_control(function, operands_path, output):
    """Recheck 27 operations after Torch loads; retain failures before rejecting them."""
    import numpy as np
    from scripts.diagnostics.phase18_sgemm_build import gemm_pair

    operands = json.loads(operands_path.read_text())
    if len(operands) != 27:
        raise ValueError("Original 27 operands required")
    with (output / "loaded-library-controls.jsonl").open("x") as stream:
        for row in operands:
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
                raise ValueError("Original operand parameter bytes changed")
            result, repeated = (
                gemm_pair(function, weight, bias, values),
                gemm_pair(function, weight, bias, values),
            )
            exact = result == row["expected_windows"]
            record = {
                "case_id": row["case_id"],
                "vertex": row["vertex"],
                "stage": row["stage"],
                "exact_windows": exact,
                "repeat_exact": result == repeated,
                **result,
            }
            stream.write(json.dumps(record, allow_nan=True) + "\n")
            stream.flush()
            if not exact or result != repeated:
                raise ValueError("Torch-loaded aligned SGEMM control failed; no integration calls")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "evidence-root", "config", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--arm", choices=("native", "aligned"), required=True)
    parser.add_argument("--library", type=Path)
    args = parser.parse_args()
    root, evidence, output = (
        args.root.resolve(),
        args.evidence_root.resolve(),
        args.output.resolve(),
    )
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(root)
    sys.path.insert(0, str(evidence))
    import pyarrow.parquet as pq
    import torch
    import yaml
    from scripts.diagnostics.phase12_baseline import portable
    from scripts.diagnostics.phase18_crossscore import file_hash, revision
    from scripts.diagnostics.phase18_operator_probe import trace
    from scripts.diagnostics.phase18_sgemm_build import verify_inputs
    from scripts.diagnostics.phase18_sgemm_build_v2 import verify_native_metadata
    from scripts.diagnostics.regression_tiers import runtime_build
    from threadpoolctl import threadpool_limits

    import prescriptxai
    from prescriptxai.evaluation.experiments import QueryCase
    from prescriptxai.models.registry import ModelBundle
    from prescriptxai.pipeline import PrescriptXAI

    design = yaml.safe_load(args.config.read_text())
    if (
        platform.system() != "Linux"
        or Path(prescriptxai.__file__).resolve() != root / "src/prescriptxai/__init__.py"
    ):
        raise ValueError("Only original Linux package/imports are registered")
    if (
        design["schema_version"] != 1
        or design["expected_rows"] != 9
        or not design["no_search_or_fit"]
    ):
        raise ValueError("Registered scope changed")
    if (
        design["script_canonical_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    ):
        raise ValueError("Registered implementation changed")
    for name, expected in design["helpers"].items():
        if (
            hashlib.sha256((evidence / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            != expected
        ):
            raise ValueError("Immutable helper changed")
    for name, expected in design["evidence_hashes"].items():
        if file_hash(evidence / name) != expected:
            raise ValueError("Original registered evidence changed")
    sgemm = yaml.safe_load((evidence / design["sgemm_registration"]).read_text())
    verify_native_metadata(root / "tests/regression/cmapss_baseline.json", sgemm, "linux")
    verify_inputs(
        root,
        evidence,
        {**sgemm, "baseline_metadata_sha256": sgemm["baseline_metadata_native_sha256"]["linux"]},
    )
    environment = {name: os.environ.get(name) for name in design["environment"]}
    if environment != design["environment"]:
        raise ValueError("Unregistered numerical environment")
    torch.set_num_threads(1)
    torch.manual_seed(design["seed"])
    torch.use_deterministic_algorithms(True)
    with threadpool_limits(1):
        build = json.loads(json.dumps(runtime_build()))
    (output / "runtime-build.json").write_text(json.dumps(build, indent=2) + "\n")
    old_build = json.loads((evidence / design["native_receipt"]).read_text())["runtime_build"]
    for name in (
        "python",
        "packages",
        "native_binaries",
        "torch_build",
        "numpy_build",
        "execution_policy",
    ):
        if build[name] != old_build[name]:
            raise ValueError(f"Original runtime/build changed: {name}")
    controls = {}
    for side, path in design["controls"].items():
        controls[side] = {
            (r["case_id"], r["vertex"]): r
            for r in map(json.loads, (evidence / path).read_text().splitlines())
        }
        if len(controls[side]) != 9:
            raise ValueError("Original trace incomplete")
    selected = {}
    for batch in pq.ParquetFile(root / "tests/regression/cmapss_baseline.parquet").iter_batches(64):
        for row in batch.to_pylist():
            if row["case_id"] in design["case_ids"]:
                selected[row["case_id"]] = row
    if set(selected) != set(design["case_ids"]):
        raise ValueError("Original cases missing")
    counters, function, library_version = {"forward": 0, "backward": 0}, None, None
    started = time.perf_counter()
    if args.arm == "aligned":
        if (
            args.library is None
            or file_hash(args.library) != sgemm["libraries"]["aligned"]["sha256"]
        ):
            raise ValueError("Registered aligned library required")
        _handle, function, library_version = load_function(args.library.resolve())
        fixed_control(function, evidence / design["operands"], output)
    rows, exact_windows, exact_linux = 0, 0, 0
    forbidden = AssertionError(
        "Teacher scoring/search/training forbidden in fixed graph diagnostic"
    )
    with (
        threadpool_limits(1),
        patch.object(PrescriptXAI, "recommend", side_effect=forbidden),
        patch.object(ModelBundle, "predict_risk", side_effect=forbidden),
        (output / "trace.jsonl").open("x") as stream,
    ):
        for key in design["case_ids"]:
            case = QueryCase.model_validate(portable(json.loads(selected[key]["case_json"])))
            runtime = PrescriptXAI.from_config(case.config)
            _, observed = runtime._normalize(case.state, case.context, complete=True)
            bundle = runtime._bundle(observed)
            original_linear = [
                s
                for s in controls["windows"][key, "original"]["stages"]
                if s["name"].endswith("/Linear")
            ]
            layers = [
                layer
                for layer in bundle.surrogate.network_.children()
                if isinstance(layer, torch.nn.Linear)
            ]
            if len(layers) != len(original_linear):
                raise ValueError("Original Linear architecture changed")
            for layer, original in zip(layers, original_linear, strict=True):
                parameter_hash = hashlib.sha256(
                    layer.weight.detach().numpy().tobytes() + layer.bias.detach().numpy().tobytes()
                ).hexdigest()
                if parameter_hash != original["parameter_sha256"]:
                    raise ValueError("Original fitted layer parameters changed")
            with ExitStack() as stack:
                if function is not None:
                    stack.enter_context(
                        aligned_layers(bundle.surrogate.network_, function, counters)
                    )
                for vertex in ("original", "windows_candidate", "linux_candidate"):
                    old, win = controls["linux"][key, vertex], controls["windows"][key, vertex]
                    values = old["stages"][0]["native"]["input"]
                    if values != win["stages"][0]["native"]["input"]:
                        raise ValueError("Original scaled starting values differ")
                    result = trace(bundle, values, win["stages"])
                    repeated = trace(bundle, values, win["stages"])
                    record = {"case_id": key, "group": case.group, "vertex": vertex, **result}
                    lexact, wexact = record == old, record == win
                    stream.write(
                        json.dumps(
                            {
                                **record,
                                "exact_linux": lexact,
                                "exact_windows": wexact,
                                "repeat_exact": result == repeated,
                            },
                            allow_nan=True,
                        )
                        + "\n"
                    )
                    stream.flush()
                    rows += 1
                    exact_linux += lexact
                    exact_windows += wexact
                    if (
                        not finite_tree(result)
                        or result != repeated
                        or (args.arm == "native" and not lexact)
                    ):
                        raise ValueError("Native/repeat controls failed; retain attempted trace")
    if rows != 9:
        raise ValueError("Registered row count incomplete")
    if args.arm == "aligned" and counters != design["expected_aligned_calls"]:
        raise ValueError("Not every registered Linear forward/backward used the bridge")
    receipt = {
        "arm": args.arm,
        "analysis_source": revision(evidence),
        "package_source": revision(root),
        "config_sha256": file_hash(args.config),
        "rows": rows,
        "cases": len(selected),
        "exact_original_linux_traces": exact_linux,
        "exact_original_windows_traces": exact_windows,
        "repeat_exact": True,
        "manual_chain_exact": True,
        "new_solves": 0,
        "new_fits": 0,
        "runtime_build": build,
        "library_version": library_version,
        "library_sha256": file_hash(args.library) if args.arm == "aligned" else None,
        "calls": counters,
        "trace_sha256": file_hash(output / "trace.jsonl"),
        "elapsed_seconds": time.perf_counter() - started,
        "scope": "Selected fixed full-surrogate/input-gradient integration only; no objective/search/production adoption or release",
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in (
                    "arm",
                    "rows",
                    "exact_original_linux_traces",
                    "exact_original_windows_traces",
                    "elapsed_seconds",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
