"""Preserve native metadata pins and every attempted SGEMM control observation."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path


def verify_native_metadata(path, design, side):
    from scripts.diagnostics.phase18_sgemm_build import file_hash

    if file_hash(path) != design["baseline_metadata_native_sha256"][side]:
        raise ValueError("Original native metadata raw bytes changed")
    metadata = json.loads(path.read_text())
    canonical = hashlib.sha256(
        json.dumps(metadata, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    if canonical != design["baseline_metadata_canonical_sha256"]:
        raise ValueError("Original full parsed metadata changed")
    return metadata


def evaluate(args, root, evidence, output, design):
    import numpy as np
    from scripts.diagnostics.phase18_sgemm_build import file_hash, gemm_pair

    if platform.system() != "Linux" or "torch" in sys.modules:
        raise ValueError("Isolated Linux matrix arm must not import torch")
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
    expected_environment = {
        "MKL_CBWR": None,
        "MKL_VERBOSE": "1",
        "MKL_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_THREADING_LAYER": "GNU",
        "MKL_INTERFACE_LAYER": "LP64",
        "LD_PRELOAD": None,
    }
    if environment != expected_environment:
        raise ValueError("Unregistered or interposed numerical environment")
    operands_path = evidence / design["operand_export"] / "operands.json"
    export = json.loads(operands_path.with_name("complete.json").read_text())
    if export["config_sha256"] != file_hash(args.config) or export["operands_sha256"] != file_hash(
        operands_path
    ):
        raise ValueError("Export is not bound to this registration")
    library = args.library.resolve()
    if file_hash(library) != design["libraries"][args.arm]["sha256"]:
        raise ValueError("Registered native library changed")
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
    operands = json.loads(operands_path.read_text())
    if len(operands) != design["expected_operations"]:
        raise ValueError("Fixed operand count changed")
    count, linux_exact, windows_exact = 0, 0, 0
    started = time.perf_counter()
    with (output / "sgemm.jsonl").open("x", encoding="utf-8") as stream:
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
                raise ValueError("Decoded parameter bytes changed")
            result = gemm_pair(sgemm, weight, bias, values)
            repeated = gemm_pair(sgemm, weight, bias, values)
            finite = all(
                np.isfinite(np.asarray(v)).all() for v in [*result.values(), *repeated.values()]
            )
            repeat_exact = result == repeated
            old_exact, win_exact = (
                result == row["expected_linux"],
                result == row["expected_windows"],
            )
            record = {
                "case_id": row["case_id"],
                "group": row["group"],
                "vertex": row["vertex"],
                "stage": row["stage"],
                "parameter_sha256": row["parameter_sha256"],
                "exact_original_linux": old_exact,
                "exact_original_windows": win_exact,
                "finite": bool(finite),
                "repeat_exact": repeat_exact,
                **result,
            }
            if not repeat_exact:
                record["repeated_result"] = repeated
            # Raw failure diagnostics may retain NaN/Infinity tokens; never publish them as success.
            stream.write(json.dumps(record, allow_nan=True) + "\n")
            stream.flush()
            count += 1
            linux_exact += old_exact
            windows_exact += win_exact
            if not finite or not repeat_exact or (args.arm == "embedded" and not old_exact):
                failure = {
                    "success": False,
                    "arm": args.arm,
                    "attempted_operations": count,
                    "failed_record": record,
                    "library_version": version.value.decode(),
                    "config_sha256": file_hash(args.config),
                    "environment": environment,
                    "elapsed_seconds": time.perf_counter() - started,
                    "error": "Native control/repeat/finiteness failed; aligned arm must not advance",
                }
                (output / "failure.json").write_text(
                    json.dumps(failure, indent=2, allow_nan=True) + "\n"
                )
                raise ValueError(failure["error"])
    if "torch" in sys.modules:
        raise ValueError("Matrix process unexpectedly imported torch")
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
        "scope": "Isolated SGEMM diagnostic; no pipeline/search/regression approval",
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
    if count != design["expected_operations"]:
        raise ValueError("Registered operation count incomplete")


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
    from scripts.diagnostics.phase18_sgemm_build import export_operands, verify_inputs

    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if (
        design["schema_version"] != 2
        or design["expected_operations"] != 27
        or not design["no_solves_or_fits"]
        or design["script_canonical_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    ):
        raise ValueError("Registered implementation/counts changed")
    helper = evidence / "scripts/diagnostics/phase18_sgemm_build.py"
    if (
        hashlib.sha256(helper.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        != design["helper_canonical_sha256"]
    ):
        raise ValueError("Immutable v1 helper changed")
    side = platform.system().lower()
    verify_native_metadata(root / "tests/regression/cmapss_baseline.json", design, side)
    native_design = {
        **design,
        "baseline_metadata_sha256": design["baseline_metadata_native_sha256"][side],
    }
    controls = verify_inputs(root, evidence, native_design)
    if args.mode == "export":
        export_operands(root, output, args.config, design, controls)
    else:
        if args.arm is None or args.library is None:
            raise ValueError("Matrix arm needs a registered library")
        evaluate(args, root, evidence, output, design)


if __name__ == "__main__":
    main()
