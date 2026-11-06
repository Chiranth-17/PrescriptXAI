"""Controlled historical graph/scaler arithmetic factorial on all 712 saved cases."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sqlite3
import subprocess
import sys
import textwrap
import types
from collections import Counter
from functools import partial
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import torch
import yaml
from filelock import FileLock
from threadpoolctl import threadpool_info, threadpool_limits

from prescriptxai.data.preprocess import FittedFeatureScaler
from prescriptxai.evaluation.experiments import (
    QueryCase,
    file_hash,
    runtime_manifest,
    source_revision,
)
from prescriptxai.evaluation.runner import run_experiment_case
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.recourse.optimizer import RecourseOptimizer

ARMS = {
    "current": {"graph": "shared", "scaler": "current_C_copy"},
    "historical_graph": {"graph": "separate", "scaler": "current_C_copy"},
    "historical_scaler": {"graph": "shared", "scaler": "historical_StandardScaler"},
    "historical_both": {"graph": "separate", "scaler": "historical_StandardScaler"},
}


def closure_module():
    spec = importlib.util.spec_from_file_location("arithmetic_closure", Path(__file__).with_name("phase12_closure.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_design(design):
    if (design.get("arms") != ARMS or design.get("historical_source") != "63c2ed445fba16c73a2771e184f635abf76b4405"
            or design.get("expected_cases") != 712
            or design.get("expected_search_calls") != 2848
            or design.get("expected_score_rows") != 5696
            or design.get("absolute_tolerance") != 1e-6 or design.get("relative_tolerance") != 0
            or design.get("threads") != 1):
        raise ValueError("The complete registered arithmetic factorial is required")


def historical_method(source, class_name, method_name, namespace):
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    method = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    code = textwrap.dedent(ast.get_source_segment(source, method))
    exec(compile("from __future__ import annotations\n" + code, "audited_historical_method", "exec"), namespace)
    return namespace[method_name], code


def source_blob(revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"]).decode("utf-8")


def verify_inputs(hashes):
    for path, expected in hashes.items():
        if file_hash(Path(path)) != expected:
            raise ValueError(f"Registered input bytes changed: {path}")


def verify_control(expected_scientific, actual_scientific):
    """Require an exact stable control before interpreting intervention arms."""
    if expected_scientific != actual_scientific:
        raise ValueError("Current control does not exactly reproduce the audited repaired record")


def effective_runtime():
    return {"native_pools": threadpool_info(), "torch_threads": torch.get_num_threads(),
            "torch_interop_threads": torch.get_num_interop_threads(),
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()}


def score_candidates(corpus, old_scaler, old_calibration, output, closure):
    """Vary only scaler layout and calibration implementation on identical saved rows."""
    scores = []
    for key, case, historical, repaired in corpus:
        parsed = QueryCase.model_validate(closure.baseline_module().portable(case))
        bundle = PrescriptXAI.from_config(parsed.config).engine.model
        for side, record in [("historical", historical), ("repaired", repaired)]:
            frame = pd.DataFrame([record["original"], record["candidate"]])[list(bundle.feature_names)]
            current = bundle.scaler.transform(frame)
            legacy = old_scaler(bundle.scaler, frame)
            for layout, scaled in [("current", current), ("historical", legacy)]:
                tensor = torch.as_tensor(scaled, dtype=torch.float32)
                with torch.no_grad():
                    raw = bundle.surrogate.torch_forward(tensor)
                    for calibration, fn in [("production", bundle.calibrator.transform_tensor),
                                            ("historical", partial(old_calibration, bundle.calibrator))]:
                        value = float(fn(raw)[1])
                        scores.append({"case_id": key, "candidate_source": side, "layout": layout,
                            "calibration": calibration, "saved": record["surrogate_after"], "actual": value,
                            "delta": value - record["surrogate_after"], "raw_surrogate": float(raw[1]),
                            "scaled_logical_max_delta": float(np.max(np.abs(current - legacy))),
                            "C_contiguous": bool(scaled.flags.c_contiguous), "F_contiguous": bool(scaled.flags.f_contiguous),
                            "tensor_stride": list(tensor.stride()), "tensor_map_version": bundle.calibrator.tensor_map_version})
    closure.write_csv(output / "saved-surrogate-scoring.csv", scores)
    return scores


def run(design, output, closure, baseline):
    source = source_revision(require_clean=True)
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit diagnostic registration before execution")
    config_hashes = {str(p): file_hash(p) for p in [Path(design["config_path"]), Path(__file__),
        Path(design["prior_design"]), Path(__file__).with_name("phase12_closure.py"),
        Path(__file__).with_name("phase12_baseline.py")]}
    prior = yaml.safe_load(Path(design["prior_design"]).read_text())
    closure.validate_design(prior)
    verify_inputs(prior["immutable_files"])
    if file_hash(Path(design["repeat_database"])) != design["repeat_database_sha256"]:
        raise ValueError("Completed control matrix bytes changed")
    code_hashes = {str(p): file_hash(p) for p in Path("src/prescriptxai").rglob("*.py")}
    runtime = runtime_manifest()
    corpus = closure.rows(prior)
    if len(corpus) != 712:
        raise ValueError("Incomplete case population")
    optimizer_source = source_blob(design["historical_source"], "src/prescriptxai/recourse/optimizer.py")
    snapshot = types.ModuleType("prescriptxai.recourse._phase12_arithmetic_snapshot")
    snapshot.__file__ = str(output / "historical_optimizer.py")
    sys.modules[snapshot.__name__] = snapshot
    exec(compile(optimizer_source, snapshot.__file__, "exec"), snapshot.__dict__)
    old_scaler, scaler_source = historical_method(
        source_blob(design["historical_source"], "src/prescriptxai/data/preprocess.py"),
        "FittedFeatureScaler", "transform", {"np": np, "pd": pd, "cast": cast})
    old_calibration, calibration_source = historical_method(
        source_blob(design["historical_source"], "src/prescriptxai/models/calibration.py"),
        "ProbabilityCalibrator", "transform_tensor", {"torch": torch})
    output.mkdir(parents=True, exist_ok=False)
    for name, text in [("historical_optimizer.py", optimizer_source), ("historical_scaler.py", scaler_source),
                       ("historical_calibration.py", calibration_source)]:
        (output / name).write_text(text, encoding="utf-8")
    baseline.atomic_json(output / "manifest.json", {"source": source, "design": design,
        "design_sha256": file_hash(Path(design["config_path"])), "helper_sha256": file_hash(Path(__file__)),
        "input_hashes": prior["immutable_files"], "code_hashes": code_hashes, "config_hashes": config_hashes, "runtime": runtime,
        "native_pools": threadpool_info(), "torch_threads": torch.get_num_threads(),
        "snapshot_hashes": {p.name: file_hash(p) for p in output.glob("*.py")},
        "scope": "diagnosis only; no production fix, new headline, fixture or closure"})
    scores = score_candidates(corpus, old_scaler, old_calibration, output, closure)
    baseline.atomic_json(output / "effective-after-scoring.json", effective_runtime())
    original_solve, original_scaler = RecourseOptimizer.solve, FittedFeatureScaler.transform
    comparisons = []
    try:
        with sqlite3.connect(output / "records.sqlite3") as db:
            db.execute("CREATE TABLE records(arm TEXT,case_id TEXT,payload TEXT,PRIMARY KEY(arm,case_id))")
            for arm, settings in design["arms"].items():
                RecourseOptimizer.solve = snapshot.RecourseOptimizer.solve if settings["graph"] == "separate" else original_solve
                FittedFeatureScaler.transform = old_scaler if settings["scaler"] == "historical_StandardScaler" else original_scaler
                for index, (key, case, historical, repaired) in enumerate(corpus):
                    parsed = QueryCase.model_validate(baseline.portable(case))
                    record = run_experiment_case(parsed).model_dump(mode="json")
                    encoded = json.dumps(record, allow_nan=False)
                    baseline.validate_record(parsed, key, encoded)
                    with db:
                        db.execute("INSERT INTO records VALUES(?,?,?)", (arm, key, encoded))
                    if arm == "current":
                        verify_control(baseline.scientific(repaired), baseline.scientific(record))
                    if index == 0:
                        baseline.atomic_json(output / f"effective-{arm}.json", effective_runtime())
                    comparisons.append({"arm": arm, "case_id": key,
                        "vs_historical": baseline.differences(baseline.scientific(historical), baseline.scientific(record)),
                        "vs_repaired": baseline.differences(baseline.scientific(repaired), baseline.scientific(record))})
                    print(json.dumps({"arm": arm, "case": index + 1, **comparisons[-1]}), flush=True)
            counts = dict(db.execute("SELECT arm,count(*) FROM records GROUP BY arm"))
            if counts != {arm: 712 for arm in ARMS}:
                raise ValueError("Incomplete arithmetic matrix")
    finally:
        RecourseOptimizer.solve, FittedFeatureScaler.transform = original_solve, original_scaler
    if len(scores) != 5696 or len(comparisons) != 2848 or source_revision(require_clean=True) != source:
        raise ValueError("Incomplete matrix or changed measured source")
    verify_inputs(prior["immutable_files"])
    verify_inputs(code_hashes)
    verify_inputs(config_hashes)
    if runtime_manifest() != runtime:
        raise ValueError("Runtime changed during arithmetic diagnostic")
    if file_hash(Path(design["repeat_database"])) != design["repeat_database_sha256"]:
        raise ValueError("Control matrix changed during execution")
    baseline.atomic_json(output / "comparison.json", comparisons)
    summary = {arm: {name: sum(bool(r[name]) for r in comparisons if r["arm"] == arm)
                    for name in ["vs_historical", "vs_repaired"]} for arm in ARMS}
    baseline.atomic_json(output / "summary.json", {"search": summary,
        "scoring_mismatches": dict(Counter(f"{r['candidate_source']}/{r['layout']}/{r['calibration']}" for r in scores if abs(r["delta"]) > 1e-6))})
    baseline.atomic_json(output / "complete.json", {"actual_success": True, "source": source,
        "search_calls": len(comparisons), "score_rows": len(scores), "diagnostic_only": True,
        "effective_runtime": effective_runtime()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/phase12-arithmetic-v1.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    validate_design(design)
    design["config_path"] = args.config.as_posix()
    closure = closure_module()
    baseline = closure.baseline_module()
    with FileLock("artifacts/phase12-headline.lock", timeout=0), baseline.idle_sleep_guard(), threadpool_limits(limits=1):
        torch.set_num_threads(1)
        run(design, args.output, closure, baseline)


if __name__ == "__main__":
    main()
