"""Isolate calibration arithmetic and shared-graph effects on fixed failure examples only."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import torch
import yaml
from filelock import FileLock
from threadpoolctl import threadpool_limits

from prescriptxai.evaluation.experiments import QueryCase, file_hash, source_revision
from prescriptxai.evaluation.runner import run_experiment_case
from prescriptxai.models.calibration import ProbabilityCalibrator
from prescriptxai.recourse.optimizer import RecourseOptimizer


def historical_blob(revision: str, path: str) -> str:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"]).decode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/experiments/phase12-localization-v1.yaml"))
    args = parser.parse_args()
    source = source_revision(require_clean=True)
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Commit the complete diagnostic registration first")
    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if len(design["case_ids"]) != 5 or len(design["arms"]) != 4 or design["expected_calls"] != 20:
        raise ValueError("The registered complete factorial diagnostic is required")
    spec = importlib.util.spec_from_file_location("phase12_baseline", Path(__file__).with_name("phase12_baseline.py"))
    assert spec is not None and spec.loader is not None
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    with FileLock("artifacts/phase12-headline.lock", timeout=0), baseline.idle_sleep_guard(), threadpool_limits(limits=1):
        torch.set_num_threads(1)
        args.output.mkdir(parents=True, exist_ok=False)
        failed_root = Path(design["failed_directory"])
        frozen = json.loads((failed_root / "manifest.json").read_text(encoding="utf-8"))
        if frozen["source"] != design["failed_source"]:
            raise ValueError("Failure reference source changed")
        for path, expected in frozen["input_hashes"].items():
            if file_hash(Path(path)) != expected:
                raise ValueError(f"Frozen input changed: {path}")
        calibration_source = historical_blob(design["historical_source"], "src/prescriptxai/models/calibration.py")
        tree = ast.parse(calibration_source)
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ProbabilityCalibrator")
        function = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "transform_tensor")
        function_source = textwrap.dedent(ast.get_source_segment(calibration_source, function))
        namespace = {"torch": torch}
        exec(compile(function_source, "historical_calibration_transform_tensor", "exec"), namespace)
        old_transform = namespace["transform_tensor"]
        optimizer_source = historical_blob(design["old_optimizer_source"], "src/prescriptxai/recourse/optimizer.py")
        snapshot = types.ModuleType("prescriptxai.recourse._phase12_localization_snapshot")
        snapshot.__file__ = str(args.output / "historical_optimizer.py")
        sys.modules[snapshot.__name__] = snapshot
        exec(compile(optimizer_source, snapshot.__file__, "exec"), snapshot.__dict__)
        (args.output / "historical_optimizer.py").write_text(optimizer_source, encoding="utf-8")
        (args.output / "historical_calibration_method.py").write_text(function_source, encoding="utf-8")
        rows = []
        with sqlite3.connect(Path(design["historical_database"]).resolve().as_uri() + "?mode=ro", uri=True) as db:
            for case_id in design["case_ids"]:
                case, expected = db.execute(
                    "SELECT c.payload,r.payload FROM cases c JOIN records r USING(case_id) WHERE c.case_id=?",
                    (case_id,),
                ).fetchone()
                rows.append((QueryCase.model_validate(baseline.portable(json.loads(case))), json.loads(expected)))
        manifest = {
            "run_id": args.output.name, "source": source, "design_path": args.config.as_posix(),
            "design_sha256": file_hash(args.config), "design": design,
            "input_hashes": frozen["input_hashes"],
            "calibration_snapshot_sha256": hashlib.sha256(function_source.encode()).hexdigest(),
            "optimizer_snapshot_sha256": hashlib.sha256(optimizer_source.encode()).hexdigest(),
            "helper_sha256": file_hash(Path(__file__)),
            "cases": [case.model_dump(mode="json") for case, _ in rows],
            "scientific_settings_unchanged": True, "scope": "failure localization only; no target or full-regression verdict",
        }
        baseline.atomic_json(args.output / "manifest.json", manifest)
        current_transform, current_solve = ProbabilityCalibrator.transform_tensor, RecourseOptimizer.solve
        records = []
        try:
            with sqlite3.connect(args.output / "records.sqlite3") as checkpoint:
                checkpoint.execute("CREATE TABLE records (arm TEXT, case_id TEXT, payload TEXT, PRIMARY KEY(arm,case_id))")
                for arm, settings in design["arms"].items():
                    ProbabilityCalibrator.transform_tensor = old_transform if settings["calibration"] == "historical" else current_transform
                    RecourseOptimizer.solve = snapshot.RecourseOptimizer.solve if settings["lift"] == "separate" else current_solve
                    for case, expected in rows:
                        actual = run_experiment_case(case).model_dump(mode="json")
                        with checkpoint:
                            checkpoint.execute("INSERT INTO records VALUES (?,?,?)", (arm, case.case_id, json.dumps(actual, allow_nan=False)))
                        differences = baseline.differences(baseline.scientific(expected), baseline.scientific(actual))
                        records.append({"arm": arm, "case_id": case.case_id, "group": case.group,
                                        "mismatch_fields": differences, "risk_after": actual["risk_after"],
                                        "status": actual["status"], "tier2": actual["tier2"]})
                        print(json.dumps(records[-1]), flush=True)
        finally:
            ProbabilityCalibrator.transform_tensor, RecourseOptimizer.solve = current_transform, current_solve
        if len(records) != design["expected_calls"] or source_revision(require_clean=True) != source:
            raise ValueError("Incomplete diagnostic or changed source")
        for path, expected in manifest["input_hashes"].items():
            if file_hash(Path(path)) != expected:
                raise ValueError(f"Input changed during diagnostic: {path}")
        baseline.atomic_json(args.output / "comparison.json", records)
        baseline.atomic_json(args.output / "complete.json", {"calls": len(records), "diagnostic_only": True, "source": source})


if __name__ == "__main__":
    main()
