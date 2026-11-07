"""Explicitly segmented continuation of the interrupted arithmetic diagnostic."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sqlite3
import sys
import types
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import torch
import yaml
from filelock import FileLock
from threadpoolctl import threadpool_limits

from prescriptxai.data.preprocess import FittedFeatureScaler
from prescriptxai.evaluation.experiments import (
    QueryCase,
    file_hash,
    runtime_manifest,
    source_revision,
)
from prescriptxai.evaluation.runner import run_experiment_case
from prescriptxai.recourse.optimizer import RecourseOptimizer


def payload_hash(payload):
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_retained(rows, preserved, cases, baseline):
    actual = {arm + "/" + key: payload_hash(payload) for arm, key, payload in rows}
    if len(rows) != len(actual) or actual != preserved["payload_sha256"]:
        raise ValueError("Retained payload or timing changed")
    for arm, key, payload in rows:
        if arm not in {"current", "historical_graph", "historical_scaler", "historical_both"} or key not in cases:
            raise ValueError("Unknown retained case or arm")
        baseline.validate_record(cases[key], key, payload)
    return actual


def load_helper():
    spec = importlib.util.spec_from_file_location("arithmetic_resume_base", Path(__file__).with_name("phase12_arithmetic.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/phase12-arithmetic-resume-v1.yaml"))
    args = parser.parse_args()
    registration = yaml.safe_load(args.config.read_text())
    helper = load_helper()
    closure = helper.closure_module()
    baseline = closure.baseline_module()
    source = source_revision(require_clean=True)
    root = Path(registration["original_output"])
    output = Path(registration["segment_output"])
    original = json.loads((root / "manifest.json").read_text())
    preservation_path = Path(registration["preservation"])
    if file_hash(preservation_path) != registration["preservation_sha256"]:
        raise ValueError("Preservation receipt changed")
    preserved = json.loads(preservation_path.read_text())
    if preserved["preserved_records"] != 759 or preserved["counts"] != {"current": 712, "historical_graph": 47}:
        raise ValueError("Unexpected interrupted population")
    design = original["design"]
    helper.validate_design(design)
    frozen = {**original["input_hashes"], **original["code_hashes"], **original["config_hashes"],
              **{str(root / name): digest for name, digest in original["snapshot_hashes"].items()},
              str(args.config): file_hash(args.config), str(Path(__file__)): file_hash(Path(__file__)),
              str(preservation_path): registration["preservation_sha256"]}
    frozen.update({path: digest for path, digest in preserved["files"].items()
                   if Path(path).resolve() != (root / "records.sqlite3").resolve()})
    with FileLock("artifacts/phase12-headline.lock", timeout=0), baseline.idle_sleep_guard(), threadpool_limits(limits=1):
        torch.set_num_threads(1)
        helper.verify_inputs(frozen)
        if runtime_manifest() != original["runtime"]:
            raise ValueError("Numerical runtime differs from original segment")
        if output.exists() or (root / "complete.json").exists():
            raise ValueError("Segment output exists or experiment already complete")
        corpus = closure.rows(yaml.safe_load(Path(design["prior_design"]).read_text()))
        cases = {key: QueryCase.model_validate(baseline.portable(case)) for key, case, _, _ in corpus}
        with sqlite3.connect((root / "records.sqlite3").resolve().as_uri() + "?mode=ro", uri=True) as db:
            if db.execute("pragma integrity_check").fetchone()[0] != "ok":
                raise ValueError("Interrupted database integrity failure")
            retained = list(db.execute("SELECT arm,case_id,payload FROM records"))
        verify_retained(retained, preserved, cases, baseline)
        for path, digest in preserved["files"].items():
            if file_hash(Path(path)) != digest:
                raise ValueError("Original evidence changed before resume")
        with (root / "saved-surrogate-scoring.csv").open(newline="", encoding="utf-8") as stream:
            scores = list(csv.DictReader(stream))
        if len(scores) != 5696:
            raise ValueError("Incomplete saved scoring component")
        output.mkdir(parents=True)
        runtime = runtime_manifest()
        baseline.atomic_json(output / "manifest.json", {"source": source, "registration": registration,
            "started_utc": datetime.now(UTC).isoformat(), "retained_payload_hashes": preserved["payload_sha256"],
            "frozen_hashes": frozen, "runtime": runtime, "effective": helper.effective_runtime(),
            "segments": [{"segment": 1, "source": original["source"], "saved": 759,
                "termination": "unverified process disappearance; no native exit receipt"},
                {"segment": 2, "source": source, "fresh_controls_required": 712, "retained_arm_rechecks_required": 47}],
            "not_an_unbroken_process": True})
        # Repeat every control in this fresh process before appending any intervention result.
        with sqlite3.connect(output / "controls.sqlite3") as controls:
            controls.execute("CREATE TABLE controls(case_id TEXT PRIMARY KEY,payload TEXT)")
            for i, (key, _, _, repaired) in enumerate(corpus):
                record = run_experiment_case(cases[key]).model_dump(mode="json")
                encoded = json.dumps(record, allow_nan=False)
                baseline.validate_record(cases[key], key, encoded)
                with controls:
                    controls.execute("INSERT INTO controls VALUES(?,?)", (key, encoded))
                helper.verify_control(baseline.scientific(repaired), baseline.scientific(record))
                print(json.dumps({"stage": "fresh_control", "case": i + 1, "case_id": key}), flush=True)
            if controls.execute("SELECT count(*) FROM controls").fetchone()[0] != 712:
                raise ValueError("Incomplete fresh control")
        baseline.atomic_json(output / "controls-complete.json", {"exact_matches": 712, "effective": helper.effective_runtime()})
        snapshot = types.ModuleType("prescriptxai.recourse._phase12_arithmetic_segment2")
        snapshot.__file__ = str(root / "historical_optimizer.py")
        sys.modules[snapshot.__name__] = snapshot
        exec(compile((root / "historical_optimizer.py").read_text(), snapshot.__file__, "exec"), snapshot.__dict__)
        old_scaler, _ = helper.historical_method(helper.source_blob(design["historical_source"],
            "src/prescriptxai/data/preprocess.py"), "FittedFeatureScaler", "transform", {"np": np, "pd": pd, "cast": cast})
        current_solve, current_scaler = RecourseOptimizer.solve, FittedFeatureScaler.transform
        # Reconstruct the interrupted arm's warmup and check its path in this process.
        RecourseOptimizer.solve = snapshot.RecourseOptimizer.solve
        try:
            saved_graph = {key: payload for arm, key, payload in retained if arm == "historical_graph"}
            with sqlite3.connect(output / "controls.sqlite3") as rechecks:
                rechecks.execute("CREATE TABLE arm_rechecks(case_id TEXT PRIMARY KEY,payload TEXT)")
                for key, _, _, _ in corpus:
                    if key not in saved_graph:
                        continue
                    record = run_experiment_case(cases[key]).model_dump(mode="json")
                    encoded = json.dumps(record, allow_nan=False)
                    baseline.validate_record(cases[key], key, encoded)
                    with rechecks:
                        rechecks.execute("INSERT INTO arm_rechecks VALUES(?,?)", (key, encoded))
                    helper.verify_control(baseline.scientific(json.loads(saved_graph[key])), baseline.scientific(record))
                    print(json.dumps({"stage": "retained_arm_recheck", "case_id": key}), flush=True)
                if rechecks.execute("SELECT count(*) FROM arm_rechecks").fetchone()[0] != 47:
                    raise ValueError("Incomplete retained arm recheck")
            baseline.atomic_json(output / "arm-recheck-complete.json", {"exact_matches": 47, "effective": helper.effective_runtime()})
        finally:
            RecourseOptimizer.solve = current_solve
        new_records = []
        try:
            with sqlite3.connect(root / "records.sqlite3") as db:
                for arm, settings in helper.ARMS.items():
                    RecourseOptimizer.solve = snapshot.RecourseOptimizer.solve if settings["graph"] == "separate" else current_solve
                    FittedFeatureScaler.transform = old_scaler if settings["scaler"] == "historical_StandardScaler" else current_scaler
                    for key, _, _, _ in corpus:
                        if db.execute("SELECT 1 FROM records WHERE arm=? AND case_id=?", (arm, key)).fetchone():
                            continue
                        record = run_experiment_case(cases[key]).model_dump(mode="json")
                        encoded = json.dumps(record, allow_nan=False)
                        baseline.validate_record(cases[key], key, encoded)
                        with db:
                            db.execute("INSERT INTO records VALUES(?,?,?)", (arm, key, encoded))
                        new_records.append({"arm": arm, "case_id": key, "sha256": payload_hash(encoded)})
                        print(json.dumps({"stage": "remaining_factorial", **new_records[-1], "new_records": len(new_records)}), flush=True)
                all_rows = list(db.execute("SELECT arm,case_id,payload FROM records"))
                counts = dict(db.execute("SELECT arm,count(*) FROM records GROUP BY arm"))
        finally:
            RecourseOptimizer.solve, FittedFeatureScaler.transform = current_solve, current_scaler
        if counts != {arm: 712 for arm in helper.ARMS} or len(new_records) != 2089:
            raise ValueError("Incomplete continued factorial")
        old_rows = [row for row in all_rows if row[0] + "/" + row[1] in preserved["payload_sha256"]]
        verify_retained(old_rows, preserved, cases, baseline)
        comparisons = []
        references = {key: (historical, repaired) for key, _, historical, repaired in corpus}
        for arm, key, payload in all_rows:
            historical, repaired = references[key]
            actual = baseline.scientific(json.loads(payload))
            comparisons.append({"arm": arm, "case_id": key, "vs_historical": baseline.differences(baseline.scientific(historical), actual),
                "vs_repaired": baseline.differences(baseline.scientific(repaired), actual)})
        helper.verify_inputs(frozen)
        if runtime_manifest() != runtime or source_revision(require_clean=True) != source:
            raise ValueError("Runtime or registered source changed")
        baseline.atomic_json(output / "comparison.json", comparisons)
        baseline.atomic_json(output / "summary.json", {"search": {arm: {name: sum(bool(r[name]) for r in comparisons if r["arm"] == arm)
            for name in ["vs_historical", "vs_repaired"]} for arm in helper.ARMS},
            "scoring_mismatches": dict(Counter('/'.join(r[k] for k in ['candidate_source','layout','calibration']) for r in scores if abs(float(r['delta'])) > 1e-6))})
        baseline.atomic_json(output / "new-record-segment.json", new_records)
        baseline.atomic_json(output / "complete.json", {"actual_success": True, "source": source, "retained": 759,
            "new_records": 2089, "fresh_controls": 712, "retained_arm_rechecks": 47, "factorial_total": 2848, "score_rows": 5696,
            "diagnostic_only": True, "effective": helper.effective_runtime()})


if __name__ == "__main__":
    main()
