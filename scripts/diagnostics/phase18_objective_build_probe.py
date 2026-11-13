"""Evaluate a build-aligned child on the registered broader fixed production objectives."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import traceback
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch


@contextmanager
def solver_phase_bridge(pipeline_class, solver_class, enter_bridge):
    """Keep native teacher checks before each case's temporary surrogate bridge."""
    factory = pipeline_class.from_config
    initializer = solver_class.__init__
    with ExitStack() as active:

        def create(*args, **kwargs):
            active.close()
            return factory(*args, **kwargs)

        def initialize(solver, bundle, *args, **kwargs):
            initializer(solver, bundle, *args, **kwargs)
            active.enter_context(enter_bridge(bundle.surrogate.network_))

        with (
            patch.object(pipeline_class, "from_config", side_effect=create),
            patch.object(solver_class, "__init__", initialize),
        ):
            yield


def compare_rows(actual_path, reference_path, output):
    """Retain all exact field differences, including values beyond existing envelopes."""
    from scripts.diagnostics.phase12_baseline import differences

    def load(path):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        index = {(row["case_id"], row["vertex"]): row for row in rows}
        if len(rows) != 159 or len(index) != 159:
            raise ValueError("Expected all 159 unique fixed observations")
        return index

    actual, reference = load(actual_path), load(reference_path)
    if actual.keys() != reference.keys():
        raise ValueError("Fixed row identities changed")
    exact, beyond, details = 0, 0, []
    for key in sorted(actual):
        diff = differences(reference[key], actual[key], atol=0)
        envelope = differences(reference[key], actual[key], atol=1e-6)
        exact += not diff
        beyond += bool(envelope)
        if diff:
            details.append(
                {
                    "case_id": key[0],
                    "vertex": key[1],
                    "exact_differences": diff,
                    "outside_existing_envelope": envelope,
                }
            )
    record = {
        "rows": len(actual),
        "exact_rows": exact,
        "different_rows": 159 - exact,
        "outside_existing_envelope_rows": beyond,
        "details": details,
        "policy": "Diagnostic comparison only; no accepted differences or tolerance changes",
    }
    output.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    return record


def retain_failed_values(error, path):
    """Retain attempted numerical locals if the unchanged helper rejects a control."""

    def convert(value):
        if hasattr(value, "detach"):
            return value.detach().cpu().tolist()
        if hasattr(value, "tolist"):
            return value.tolist()
        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
            return value
        return None

    keys = (
        "key",
        "label",
        "risk",
        "actual",
        "value",
        "gradient",
        "value_again",
        "gradient_again",
        "decision",
        "raw",
        "scaled",
        "clipped",
        "delta",
    )
    frames = []
    for frame, line in traceback.walk_tb(error.__traceback__):
        if frame.f_code.co_filename.endswith("phase18_gradient_probe.py"):
            frames.append(
                {
                    "function": frame.f_code.co_name,
                    "line": line,
                    "attempted_values": {
                        key: convert(frame.f_locals[key]) for key in keys if key in frame.f_locals
                    },
                }
            )
    path.write_text(
        json.dumps(
            {"error": repr(error), "frames": frames, "traceback": traceback.format_exc()},
            indent=2,
            allow_nan=True,
        )
        + "\n"
    )


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
    os.chdir(root)
    sys.path.insert(0, str(evidence))
    import torch
    import yaml
    from scripts.diagnostics import phase18_gradient_probe as original
    from scripts.diagnostics.phase18_crossscore import file_hash, revision
    from scripts.diagnostics.phase18_sgemm_build import verify_inputs
    from scripts.diagnostics.phase18_sgemm_build_v2 import verify_native_metadata
    from scripts.diagnostics.phase18_torch_build_integration import (
        aligned_layers,
        fixed_control,
        load_function,
    )
    from scripts.diagnostics.regression_tiers import runtime_build
    from threadpoolctl import threadpool_limits

    import prescriptxai
    from prescriptxai.pipeline import PrescriptXAI
    from prescriptxai.recourse.optimizer import RecourseOptimizer

    design = yaml.safe_load(args.config.read_text())
    if (
        platform.system() != "Linux"
        or Path(prescriptxai.__file__).resolve() != root / "src/prescriptxai/__init__.py"
    ):
        raise ValueError("Original Linux package/imports required")
    if (
        design["entrypoint_canonical_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    ):
        raise ValueError("Registered entrypoint changed")
    for name, expected in design["helper_hashes"].items():
        if (
            hashlib.sha256((evidence / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            != expected
        ):
            raise ValueError("Original helper changed")
    for name, expected in design["evidence_hashes"].items():
        if file_hash(evidence / name) != expected:
            raise ValueError("Registered original evidence changed")
    sgemm = yaml.safe_load((evidence / design["sgemm_registration"]).read_text())
    verify_native_metadata(root / "tests/regression/cmapss_baseline.json", sgemm, "linux")
    verify_inputs(
        root,
        evidence,
        {**sgemm, "baseline_metadata_sha256": sgemm["baseline_metadata_native_sha256"]["linux"]},
    )
    if {key: os.environ.get(key) for key in design["environment"]} != design["environment"]:
        raise ValueError("Unregistered numerical environment")
    package_source, analysis_source = revision(root), revision(evidence)
    if package_source != design["origin_source"]:
        raise ValueError("Original package revision changed")
    preflight = output.with_name(output.name + "-preflight")
    preflight.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    torch.manual_seed(design["seed"])
    with threadpool_limits(1):
        build = json.loads(json.dumps(runtime_build()))
    old = json.loads((evidence / design["native_receipt"]).read_text())["runtime_build"]
    for key in (
        "python",
        "packages",
        "native_binaries",
        "torch_build",
        "numpy_build",
        "execution_policy",
    ):
        if build[key] != old[key]:
            raise ValueError(f"Original runtime/build changed: {key}")
    (preflight / "runtime-build.json").write_text(json.dumps(build, indent=2) + "\n")
    function, version = None, None
    if args.arm == "aligned":
        if (
            args.library is None
            or file_hash(args.library) != sgemm["libraries"]["aligned"]["sha256"]
        ):
            raise ValueError("Registered aligned library required")
        _handle, function, version = load_function(args.library.resolve())
        fixed_control(function, evidence / design["operands"], preflight)
    counters = {"forward": 0, "backward": 0}
    saved_argv = sys.argv
    sys.argv = [
        original.__file__,
        "--root",
        str(root),
        "--evidence-root",
        str(evidence),
        "--config",
        str(args.config),
        "--output",
        str(output),
        "--side",
        "linux",
    ]
    try:
        with ExitStack() as stack:
            if function is not None:
                stack.enter_context(
                    solver_phase_bridge(
                        PrescriptXAI,
                        RecourseOptimizer,
                        lambda network: aligned_layers(network, function, counters),
                    )
                )
            original.main()
    except BaseException as error:
        retain_failed_values(error, preflight / "failed-attempt.json")
        raise
    finally:
        sys.argv = saved_argv
    receipt = json.loads((output / "complete.json").read_text())
    if (
        receipt["rows"] != 159
        or receipt["optimizer_iterations"]
        or receipt["new_solver_queries"]
        or receipt["new_fits"]
    ):
        raise ValueError("Registered counts or no-optimization scope changed")
    comparisons = {}
    for side, path in design["gradient_controls"].items():
        comparisons[side] = compare_rows(
            output / "gradients.jsonl", evidence / path, output / f"comparison-{side}.json"
        )
    result = {
        "arm": args.arm,
        "analysis_source": analysis_source,
        "package_source": package_source,
        "config_sha256": file_hash(args.config),
        "rows": 159,
        "cases": 53,
        "comparisons": {
            side: {k: v for k, v in item.items() if k != "details"}
            for side, item in comparisons.items()
        },
        "calls": counters,
        "library_version": version,
        "optimizer_iterations": 0,
        "new_solver_queries": 0,
        "new_fits": 0,
        "intercepted_setup_callbacks": 53,
        "scope": "Selected broader fixed first-objective diagnostic only; no production adoption, search, FD001/corpus parity or latency claim",
    }
    (output / "integration-complete.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if args.arm == "native" and comparisons["linux"]["exact_rows"] != 159:
        raise ValueError("Native full-gradient controls differ; aligned arm must not start")
    if args.arm == "aligned" and (not counters["forward"] or not counters["backward"]):
        raise ValueError("Aligned bridge was not exercised")


if __name__ == "__main__":
    main()
