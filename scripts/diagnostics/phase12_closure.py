"""Immutable 712-case classification, independent rescoring and repeatability experiments."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from filelock import FileLock
from threadpoolctl import threadpool_info, threadpool_limits

from prescriptxai.evaluation.experiments import (
    QueryCase,
    file_hash,
    runtime_manifest,
    source_revision,
)
from prescriptxai.evaluation.runner import run_experiment_case
from prescriptxai.pipeline import PrescriptXAI


def baseline_module():
    spec = importlib.util.spec_from_file_location("closure_baseline", Path(__file__).with_name("phase12_baseline.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flat(value, prefix=""):
    if isinstance(value, dict):
        return {k: v for name, item in value.items() for k, v in flat(item, f"{prefix}/{name}").items()}
    return {prefix: value}


def validate_design(design):
    expected = {"expected_cases": 712, "expected_search_calls": 5696, "repeats": 2,
                "absolute_tolerance": 1e-6, "relative_tolerance": 0,
                "borderline_absolute_margin": 1e-6,
                "process_scopes": ["shared_same_process_for_both_passes", "fresh_independent_process_per_pass"],
                "thread_modes": ["one", "operator_environment_default"], "order": "lexicographic_case_id"}
    if any(type(design.get(k)) is not type(v) or design.get(k) != v for k, v in expected.items()):
        raise ValueError("Diagnostic design differs from the preregistered complete matrix")


def rows(design):
    ids = [r["case_id"] for r in json.loads(Path(design["mismatches"]).read_text())["mismatches"]]
    if len(ids) != 712 or len(set(ids)) != 712:
        raise ValueError("The exact complete 712-case population is required")
    found = {}
    for side in ["historical", "repaired"]:
        with sqlite3.connect(Path(design[f"{side}_database"]).resolve().as_uri() + "?mode=ro", uri=True) as db:
            found[side] = {key: (json.loads(case), json.loads(record)) for key, case, record in db.execute(
                "SELECT c.case_id,c.payload,r.payload FROM cases c JOIN records r USING(case_id) WHERE c.case_id IN (" + ",".join("?" for _ in ids) + ")", ids)}
    if any(set(v) != set(ids) for v in found.values()):
        raise ValueError("Missing required cases")
    return [(key, found["repaired"][key][0], found["historical"][key][1], found["repaired"][key][1]) for key in sorted(ids)]


def margins(record, case):
    result = {name: {k: check.get(k) for k in ["passed", "measurement", "limit", "margin", "checks"]}
              for name, check in record["validation"].items() if isinstance(check, dict) and "passed" in check}
    result["triage"] = {"alert": record["risk_before"] - record["solver_tau_danger"],
                        "safe": record["solver_tau_safe"] - record["risk_after"],
                        "improvement": record["risk_before"] - record["risk_after"] - case["config"]["pipeline"]["delta_min"],
                        "sparsity": record["k_max"] - record["sparsity"], "action_feasible": record["action_feasible"]}
    return result


def audit_risk(bundle, candidate):
    """Independent scaler/class-selection/calibration arithmetic; no search or production map."""
    raw = np.array([[candidate[n] for n in bundle.feature_names]], dtype=np.float64)
    scaled = (raw - bundle.scaler.scaler.mean_) / bundle.scaler.scaler.scale_
    estimator = bundle.estimator.estimator
    probabilities = np.asarray(estimator.predict_proba(scaled), dtype=np.float64)
    positive = probabilities[:, list(estimator.classes_).index(1)]
    calibrator = bundle.calibrator
    if calibrator.method == "isotonic":
        calibrated = np.interp(positive, calibrator.model.X_thresholds_, calibrator.model.y_thresholds_)
    else:
        logits = np.log(np.clip(positive, 1e-12, 1 - 1e-12) / np.clip(1 - positive, 1e-12, 1))
        z = logits / calibrator.temperature if calibrator.method == "temperature" else calibrator.slope * logits + calibrator.intercept
        calibrated = 1 / (1 + np.exp(-np.clip(z, -700, 700)))
    return float(calibrated[0])


def write_csv(path, data):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader()
        for row in data:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def classify(design, output, baseline):
    classification, fields, scores = [], [], []
    with threadpool_limits(limits=1):
        torch.set_num_threads(1)
        for key, case, old, new in rows(design):
            controls = new["solver_settings"]["direct_inputs"]
            old_support = sorted(set(old["changed_features"]) & set(controls))
            new_support = sorted(set(new["changed_features"]) & set(controls))
            all_diff = {n: new["candidate"][n] - v for n, v in old["candidate"].items() if new["candidate"][n] != v}
            control_diff = {n: new["candidate"][n] - old["candidate"][n] for n in controls if new["candidate"][n] != old["candidate"][n]}
            kind = ("different_control_support" if old_support != new_support else
                    "same_support_different_control_values" if control_diff else
                    "same_controls_different_propagation" if all_diff else "identical_candidate")
            flips = [name for name in ["tier2", "tier3", "tier4", "joint", "status"] if old[name] != new[name]]
            if old["validation"]["tier1_model_safety"]["passed"] != new["validation"]["tier1_model_safety"]["passed"]:
                flips.append("tier1")
            before_margins, after_margins = margins(old, case), margins(new, case)
            borderline = {side: [name for name, check in ms.items() if isinstance(check.get("margin"), (int, float)) and abs(check["margin"]) <= design["borderline_absolute_margin"]]
                          for side, ms in [("historical", before_margins), ("repaired", after_margins)]}
            for side, ms in [("historical", before_margins), ("repaired", after_margins)]:
                borderline[side].extend("triage/" + name for name, value in ms["triage"].items()
                                        if type(value) in (int, float) and abs(value) <= design["borderline_absolute_margin"])
            classification.append({"case_id": key, "group": new["group"], "mode": new["mode"], "population": new["population"],
                "seed": new["seed"], "unit": new["engine_id"], "cycle": new["cycle"], "protocol": new["protocol"],
                "candidate_category": kind, "old_direct_support": old_support, "new_direct_support": new_support,
                "candidate_deltas": all_diff, "direct_control_deltas": control_diff, "risk_delta": new["risk_after"] - old["risk_after"],
                "flips": flips, "historical_margins": before_margins, "repaired_margins": after_margins, "borderline": borderline,
                "scientific_difference_paths": baseline.differences(baseline.scientific(old), baseline.scientific(new))})
            left, right = flat({**baseline.scientific(old), "timings": old["timings"]}), flat({**baseline.scientific(new), "timings": new["timings"]})
            for name in sorted(set(left) | set(right)):
                a, b = left.get(name), right.get(name)
                if a != b:
                    numeric = type(a) in (int, float) and type(b) in (int, float)
                    fields.append({"case_id": key, "group": new["group"], "mode": new["mode"], "population": new["population"], "seed": new["seed"], "unit": new["engine_id"], "field": name,
                                   "old": a, "new": b, "absolute_difference": abs(b - a) if numeric else None,
                                   "timing_only_observation": name.startswith("/timings/"), "within_float_tolerance": abs(b-a) <= 1e-6 if numeric else None})
            parsed = QueryCase.model_validate(baseline.portable(case))
            pipeline = PrescriptXAI.from_config(parsed.config)
            for side, record in [("historical", old), ("repaired", new)]:
                candidate = record["candidate"]
                production = float(pipeline.engine.model.predict_risk(pd.DataFrame([candidate]))[0])
                independent = audit_risk(pipeline.engine.model, candidate)
                scores.append({"case_id": key, "candidate_source": side, "production": production, "audit": independent,
                               "saved": record["risk_after"], "production_audit_delta": production - independent,
                               "production_saved_delta": production - record["risk_after"]})
            if len(classification) % 50 == 0:
                print(json.dumps({"classified": len(classification)}), flush=True)
    write_csv(output / "classification.csv", classification)
    write_csv(output / "field_differences.csv", fields)
    write_csv(output / "same_candidate_scores.csv", scores)
    baseline.atomic_json(output / "classification.json", classification)
    baseline.atomic_json(output / "classification-summary.json", {"cases": len(classification), "categories": dict(Counter(r["candidate_category"] for r in classification)),
        "same_candidate_scoring_disagreements": sum(abs(r["production_audit_delta"]) > 1e-6 for r in scores),
        "saved_score_disagreements": sum(abs(r["production_saved_delta"]) > 1e-6 for r in scores),
        "maximum_scoring_disagreement": max(abs(r["production_audit_delta"]) for r in scores),
        "timing_policy": "retained reporting observations, excluded from scientific equality"})


def worker(design, output, args, baseline):
    if args.threads == "one":
        torch.set_num_threads(1)
        threadpool_limits(limits=1)
    baseline.atomic_json(output / f"runtime-{args.scope}-{args.threads}-{args.rep}.json", {
        "pid": os.getpid(), "torch_threads": torch.get_num_threads(), "torch_interop_threads": torch.get_num_interop_threads(),
        "native_pools": threadpool_info(), "environment": {n: os.environ.get(n) for n in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"]},
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(), "runtime": runtime_manifest()})
    corpus = rows(design)
    repetitions = [1, 2] if args.scope == "shared" else [args.rep]
    with sqlite3.connect(output / "repeat-records.sqlite3") as db:
        db.execute("CREATE TABLE IF NOT EXISTS records(scope TEXT,threads TEXT,rep INTEGER,case_id TEXT,payload TEXT,pid INTEGER,PRIMARY KEY(scope,threads,rep,case_id))")
        for rep in repetitions:
            for index, (key, case, _, _) in enumerate(corpus):
                if db.execute("SELECT 1 FROM records WHERE scope=? AND threads=? AND rep=? AND case_id=?", (args.scope, args.threads, rep, key)).fetchone():
                    raise ValueError("Existing diagnostic result: do not silently replace or resume a shared-process experiment")
                parsed = QueryCase.model_validate(baseline.portable(case))
                record = run_experiment_case(parsed).model_dump(mode="json")
                baseline.validate_record(parsed, key, json.dumps(record, allow_nan=False))
                if index == 0:
                    baseline.atomic_json(output / f"effective-{args.scope}-{args.threads}-{rep}.json", {
                        "pid": os.getpid(), "torch_threads": torch.get_num_threads(),
                        "torch_interop_threads": torch.get_num_interop_threads(), "native_pools": threadpool_info(),
                        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()})
                with db:
                    db.execute("INSERT INTO records VALUES (?,?,?,?,?,?)", (args.scope, args.threads, rep, key, json.dumps(record, allow_nan=False), os.getpid()))
                print(json.dumps({"scope": args.scope, "threads": args.threads, "rep": rep, "case": index + 1, "case_id": key}), flush=True)
    baseline.atomic_json(output / f"complete-{args.scope}-{args.threads}-{args.rep}.json", {
        "actual_success": True, "repetitions": repetitions, "queries_each": 712,
        "pid": os.getpid(), "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(), "native_pools": threadpool_info()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/phase12-closure-712-v1.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--scope", choices=["shared", "fresh"])
    parser.add_argument("--threads", choices=["one", "default"])
    parser.add_argument("--rep", type=int, default=1)
    args = parser.parse_args()
    baseline = baseline_module()
    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    validate_design(design)
    source = source_revision(require_clean=True)
    if args.worker:
        worker(design, args.output, args, baseline)
        return
    with FileLock("artifacts/phase12-headline.lock", timeout=0), baseline.idle_sleep_guard():
        if args.output.exists():
            raise ValueError("Output already exists; inspect instead of replacing results")
        for path, expected in design["immutable_files"].items():
            if file_hash(Path(path)) != expected:
                raise ValueError(f"Input changed: {path}")
        args.output.mkdir(parents=True)
        manifest = {"source": source, "config_path": args.config.as_posix(), "config_sha256": file_hash(args.config),
                    "design": design, "started_utc": datetime.now(UTC).isoformat(), "runtime": runtime_manifest(),
                    "helper_sha256": file_hash(Path(__file__)), "code_hashes": {str(p): file_hash(p) for p in Path("src/prescriptxai").rglob("*.py")}}
        baseline.atomic_json(args.output / "manifest.json", manifest)
        classify(design, args.output, baseline)
        for threads in ["one", "default"]:
            for scope in ["shared", "fresh"]:
                for rep in ([1] if scope == "shared" else [1, 2]):
                    env = os.environ.copy()
                    if threads == "one":
                        env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
                    command = [sys.executable, __file__, "--worker", "--config", str(args.config), "--output", str(args.output), "--scope", scope, "--threads", threads, "--rep", str(rep)]
                    log = args.output / f"{scope}-{threads}-{rep}.log"
                    with log.open("w", encoding="utf-8") as stream:
                        result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, check=False)
                    baseline.atomic_json(args.output / f"exit-{scope}-{threads}-{rep}.json", {"native_exit": result.returncode})
                    if result.returncode:
                        raise RuntimeError(f"Diagnostic worker failed; inspect {log}")
        with sqlite3.connect(args.output / "repeat-records.sqlite3") as db:
            results = {(scope, threads, rep, key): json.loads(payload) for scope, threads, rep, key, payload in db.execute("SELECT scope,threads,rep,case_id,payload FROM records")}
        counts = Counter(key[:3] for key in results)
        if len(results) != 5696 or len(counts) != 8 or any(n != 712 for n in counts.values()):
            raise ValueError("Incomplete repeatability population")
        comparisons = []
        for key, _, historical, saved in rows(design):
            reference = results[("shared", "one", 1, key)]
            comparisons.append({"case_id": key, "conditions": {
                f"{scope}/{threads}/{rep}": {"vs_shared_one_first": baseline.differences(baseline.scientific(reference), baseline.scientific(record)),
                    "vs_historical": baseline.differences(baseline.scientific(historical), baseline.scientific(record)),
                    "vs_repaired": baseline.differences(baseline.scientific(saved), baseline.scientific(record))}
                for (scope, threads, rep, identity), record in results.items() if identity == key}})
        baseline.atomic_json(args.output / "repeat-comparison.json", comparisons)
        checked = {**design["immutable_files"], **manifest["code_hashes"], str(args.config): manifest["config_sha256"], __file__: manifest["helper_sha256"]}
        for path, expected in checked.items():
            if file_hash(Path(path)) != expected:
                raise ValueError(f"Input/source changed during diagnostic: {path}")
        if source_revision(require_clean=True) != source:
            raise ValueError("Source changed during diagnostic")
        if runtime_manifest() != manifest["runtime"]:
            raise ValueError("Runtime changed during diagnostic")
        baseline.atomic_json(args.output / "complete.json", {"actual_success": True, "expected_calls": 5696, "source": source, "diagnostic_only": True})


if __name__ == "__main__":
    main()
