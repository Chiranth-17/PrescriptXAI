"""Inspect fixed-state gradients and the first production objective without solving."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import platform
import sqlite3
import sys
import time
from contextlib import closing, suppress
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch


class ObjectiveCaptured(Exception):
    """Stop before SciPy is called; retain the production callback and start."""


def capture_first_objective(solver, state, config):
    captured = {}

    def intercept(function, start, **kwargs):
        captured.update(objective=function.__self__, start=start.copy(), options=kwargs)
        raise ObjectiveCaptured

    with (
        patch("prescriptxai.recourse.optimizer.minimize", side_effect=intercept),
        suppress(ObjectiveCaptured),
    ):
        solver.solve(state, config)
    if not captured:
        raise ValueError("Case never reached the registered first dense objective")
    return captured


def derivative(function, decision):
    import torch

    point = torch.tensor(decision, dtype=torch.float64, requires_grad=True)
    value = function(point).reshape(())
    gradient = torch.autograd.grad(value, point)[0]
    return {"value": float(value.detach()), "gradient": gradient.detach().tolist()}


def probe_objective(objective, decision):
    import numpy as np

    value, gradient = objective.value_and_grad(decision)
    again, gradient_again = objective.value_and_grad(decision)
    if value != again or not np.array_equal(gradient, gradient_again):
        raise ValueError("Repeated objective evaluation changed its graph or values")
    delta = objective.decode(decision)
    feature_function = inspect.getclosurevars(objective.risk_function).nonlocals["feature_function"]
    import torch

    tensor = torch.tensor(delta, dtype=torch.float64)
    features = feature_function(tensor)
    return {
        "decision": decision.tolist(),
        "lifted_scaled_features": features.detach().tolist(),
        "objective": value,
        "gradient": gradient.tolist(),
        "terms": asdict(objective.components(decision)),
        "risk_component": derivative(objective.risk_function, delta),
        "feasibility_component": (
            derivative(objective.feasibility_function, delta)
            if objective.feasibility_function is not None
            else None
        ),
        "repeat_exact": True,
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

    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    import torch
    import yaml
    from scripts.diagnostics.phase12_baseline import differences, portable
    from scripts.diagnostics.phase12_regression import verify_files
    from scripts.diagnostics.phase18_crossscore import file_hash, revision
    from scripts.diagnostics.regression_tiers import runtime_build
    from threadpoolctl import threadpool_limits

    import prescriptxai
    from prescriptxai.evaluation.experiments import QueryCase
    from prescriptxai.pipeline import PrescriptXAI
    from prescriptxai.recourse.optimizer import RecourseOptimizer
    from prescriptxai.validation.pipeline import validate_candidate

    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    implementation = hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if (
        design["schema_version"] != 1
        or design["script_canonical_sha256"] != implementation
        or platform.system().lower() != args.side
        or design["expected_cases"] != 53
        or design["expected_rows_per_runtime"] != 159
        or not design["no_optimizer_iterations"]
        or not design["no_refits"]
    ):
        raise ValueError("Registered implementation, counts, runtime or scope changed")
    if Path(prescriptxai.__file__).resolve() != root / "src/prescriptxai/__init__.py":
        raise ValueError("Package does not resolve to the original runtime")
    previous_design_path = evidence / design["crossscore_config"]
    if file_hash(previous_design_path) != design["crossscore_config_sha256"]:
        raise ValueError("Original cross-score design changed")
    previous_design = yaml.safe_load(previous_design_path.read_text(encoding="utf-8"))
    helper = evidence / "scripts/diagnostics/phase18_crossscore.py"
    if hashlib.sha256(helper.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != previous_design["script_canonical_sha256"]:
        raise ValueError("Original control helper implementation changed")
    ids_path = evidence / previous_design["ids_path"]
    database = evidence / previous_design["linux_database"]
    if (
        file_hash(ids_path) != previous_design["ids_sha256"]
        or file_hash(database) != previous_design["linux_database_sha256"]
        or database.with_name(database.name + "-wal").stat().st_size
    ):
        raise ValueError("Original selected inputs changed or database has pending WAL")
    ids = json.loads(ids_path.read_text())
    if len(ids) != 53 or ids != sorted(set(ids)):
        raise ValueError("Fixed case selection changed")
    metadata = json.loads(Path("tests/regression/cmapss_baseline.json").read_text())
    verify_files(
        {
            "tests/regression/cmapss_baseline.parquet": metadata["fixture_sha256"],
            "configs/experiments/phase12-baseline-v1.yaml": metadata["design_sha256"],
            **metadata["input_hashes"],
        }
    )
    origin = json.loads((evidence / previous_design["linux_manifest"]).read_text())
    for name, expected in origin["context"]["code_hashes"].items():
        if (
            hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            != expected
        ):
            raise ValueError(f"Original production helper changed: {name}")
    control_path = evidence / design["controls"][args.side]["path"]
    if file_hash(control_path) != design["controls"][args.side]["sha256"]:
        raise ValueError("Completed native cross-score controls changed")
    controls = {
        (row["case_id"], row["vertex"]): row
        for row in map(json.loads, control_path.read_text().splitlines())
    }
    if len(controls) != 159:
        raise ValueError("Completed native controls are incomplete")
    saved = {}
    for batch in pq.ParquetFile("tests/regression/cmapss_baseline.parquet").iter_batches(64):
        for row in batch.to_pylist():
            if row["case_id"] in ids:
                saved[row["case_id"]] = row
    if set(saved) != set(ids):
        raise ValueError("Genuine fixture case missing")
    torch.set_num_threads(design["cpu_threads"])
    torch.manual_seed(design["seed"])
    started = time.perf_counter()
    rows = 0
    with (
        threadpool_limits(design["cpu_threads"]),
        closing(sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)) as db,
        (output / "gradients.jsonl").open("x", encoding="utf-8") as stream,
    ):
        for key in ids:
            old = json.loads(saved[key]["observation_json"])
            new = json.loads(
                db.execute("SELECT payload FROM records WHERE case_id=?", (key,)).fetchone()[0]
            )
            case = QueryCase.model_validate(portable(json.loads(saved[key]["case_json"])))
            if case.variant != "full" or case.policy is not None:
                raise ValueError("Probe requires the registered full-policy dense objective")
            runtime = PrescriptXAI.from_config(case.config)
            runtime.config = case.config.model_copy(deep=True)
            initial, observed = runtime._normalize(case.state, case.context, complete=True)
            with runtime.engine.predictor_lock:
                bundle = runtime._bundle(observed)
                risk = float(bundle.predict_risk(pd.DataFrame([initial]))[0])
                if risk != controls[key, "original"]["risk"]:
                    raise ValueError(f"Native original-risk control changed: {key}")
                for label, record in (("windows_candidate", old), ("linux_candidate", new)):
                    actual = (
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
                    if differences(controls[key, label]["validation"], actual, atol=0):
                        raise ValueError(f"Native full validation control changed: {key}/{label}")
                config = runtime.config.model_copy(deep=True)
                config.recourse.search_mode = case.mode
                solver = RecourseOptimizer(
                    bundle,
                    runtime.engine.taxonomy,
                    runtime.engine.coupling,
                    runtime.engine.mahalanobis,
                )
                captured = capture_first_objective(solver, initial, config)
                objective = captured["objective"]
                names = runtime.engine.taxonomy.active_controllable_feature_names(
                    bundle.feature_names
                )
                if len(names) != objective.control_count:
                    raise ValueError("Intercepted callback is not the first full dense support")
                scale = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
                for label, record in (
                    ("original", None),
                    ("windows_candidate", old),
                    ("linux_candidate", new),
                ):
                    raw = initial if record is None else record["candidate"]
                    point = pd.DataFrame([raw]).loc[:, list(bundle.feature_names)]
                    scaled = bundle.scaler.transform(point)
                    tensor = torch.tensor(scaled, dtype=torch.float32, requires_grad=True)
                    surrogate = bundle.torch_forward(tensor).reshape(())
                    gradient = torch.autograd.grad(surrogate, tensor)[0]
                    delta = np.asarray(
                        [(raw[name] - initial[name]) / scale[name] for name in names]
                    )
                    clipped = np.clip(delta, objective.lower_change, objective.upper_change)
                    decision = captured["start"] if record is None else objective.encode(clipped)
                    row = {
                        "case_id": key,
                        "group": case.group,
                        "vertex": label,
                        "features": list(bundle.feature_names),
                        "controls": list(names),
                        "scaled_input": scaled.tolist(),
                        "scaled_strides": list(scaled.strides),
                        "surrogate": float(surrogate.detach()),
                        "surrogate_gradient": gradient.detach().tolist(),
                        "saved_surrogate": None if record is None else record["surrogate_after"],
                        "bounds": [list(pair) for pair in captured["options"]["bounds"]],
                        "solver_options": captured["options"]["options"],
                        "fixed_control_delta": delta.tolist(),
                        "clipped_control_delta": clipped.tolist(),
                        "dense_objective": probe_objective(objective, decision),
                    }
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                    rows += 1
        runtime_info = runtime_build()
    receipt = {
        "schema_version": 1,
        "side": args.side,
        "analysis_source": revision(evidence),
        "package_source": revision(root),
        "config_sha256": file_hash(args.config),
        "cases": len(ids),
        "rows": rows,
        "native_controls_exact": True,
        "repeat_objectives_exact": True,
        "optimizer_iterations": 0,
        "new_solver_queries": 0,
        "new_fits": 0,
        "intercepted_first_dense_callbacks": len(ids),
        "runtime_build": runtime_info,
        "elapsed_seconds": time.perf_counter() - started,
        "gradients_sha256": file_hash(output / "gradients.jsonl"),
        "scope": "Fixed-state diagnostic; no SciPy execution, regression pass or latency claim",
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in (
                    "side",
                    "cases",
                    "rows",
                    "native_controls_exact",
                    "optimizer_iterations",
                    "elapsed_seconds",
                )
            }
        )
    )
    if rows != design["expected_rows_per_runtime"]:
        raise ValueError("Registered gradient row count not completed")


if __name__ == "__main__":
    main()
