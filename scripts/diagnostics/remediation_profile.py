"""Profile real, frozen development queries without training or target redefinition."""

from __future__ import annotations

import argparse
import cProfile
import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter_ns

import numpy as np
import torch
import yaml
from threadpoolctl import threadpool_limits

import prescriptxai
from prescriptxai.config import AppConfig
from prescriptxai.evaluation.experiments import (
    content_hash,
    file_hash,
    runtime_manifest,
    source_revision,
)
from prescriptxai.evaluation.metrics import engine_bootstrap_interval
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import InputContext


def main() -> None:
    """Write a new development measurement directory; never overwrite a completed run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    design = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    fixed = {"modes":["fast","thorough"], "repeats":1, "warmup_calls_per_mode":2,
             "profile_calls_per_mode":1, "native_threads":1,
             "expected_queries_per_mode":60, "expected_engines":14,
             "bootstrap_replicates":2000, "bootstrap_seed":1729, "bootstrap_confidence":.95}
    if any(design.get(name) != value for name,value in fixed.items()):
        raise ValueError("measurement settings differ from this registered development protocol")
    source = source_revision(require_clean=True)
    if Path(prescriptxai.__file__).resolve() != (Path.cwd()/"src/prescriptxai/__init__.py").resolve():
        raise ValueError("measurement imports do not resolve to the committed workspace source")
    args.output.mkdir(parents=True, exist_ok=False)
    database = Path(design["historical_database"])
    historical_manifest = json.loads((database.parent / "manifest.json").read_text(encoding="utf-8"))
    if historical_manifest["git_hash"] != design["historical_source"]:
        raise ValueError("historical measurement source differs from registration")
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        payloads = connection.execute(
            "SELECT c.payload FROM records r JOIN cases c USING(case_id) "
            "WHERE json_extract(r.payload,'$.group')=? AND json_extract(r.payload,'$.seed')=?",
            (design["cohort"], design["solver_seed"]),
        ).fetchall()
    cases = sorted(
        (json.loads(value) for value, in payloads),
        key=lambda item: (item["state"]["engine_id"], item["state"]["cycle"]),
    )
    if len(cases) != design["expected_queries_per_mode"]:
        raise ValueError("the complete registered development population is required")
    if len({case["state"]["engine_id"] for case in cases}) != design["expected_engines"]:
        raise ValueError("development engine count differs from registration")
    config_hashes = {content_hash(case["config"]) for case in cases}
    if len(config_hashes) != 1:
        raise ValueError("saved queries do not share one effective configuration")
    identities = [(int(c["state"]["engine_id"]), int(c["state"]["cycle"])) for c in cases]
    if len(set(identities)) != len(cases):
        raise ValueError("development query identities must be unique")
    with closing(sqlite3.connect(Path(design["historical_latency"]).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        historic = [
            json.loads(value) for value, in connection.execute(
                "SELECT payload FROM samples WHERE mode='fast' ORDER BY idx",
            )
        ]
    historical_ids = {(int(row["engine_id"]), int(row["cycle"])) for row in historic}
    config = AppConfig.model_validate(cases[0]["config"])
    if (config.tau_safe,config.tau_danger,config.recourse.rate_horizon_steps,
        config.recourse.k_max,config.validation.mahalanobis_max) != (.2,.8,1,3,5.):
        raise ValueError("scientific cutoffs, horizon or sparsity changed")
    inputs = {str(path): file_hash(path) for path in (
        config.artifacts.model, config.artifacts.mahalanobis,
        config.artifacts.coupling, config.pipeline.taxonomy_path,
    ) if path is not None}
    historical_asset = historical_manifest["assets"]["models"]["FD001/xgb/base"]
    expected_inputs = {
        str(config.pipeline.taxonomy_path): historical_manifest["taxonomy_sha256"],
        **{str(Path(historical_asset["paths"][key])):historical_asset["hashes"][key]
           for key in ("model","coupling","mahalanobis_v1")},
    }
    if inputs != expected_inputs:
        raise ValueError("fitted inputs differ from the historical source manifest")
    code_hashes = {str(path):file_hash(path) for path in Path("src/prescriptxai").rglob("*.py")}
    code_hashes[str(Path(__file__).resolve().relative_to(Path.cwd().resolve()))] = file_hash(Path(__file__))
    config_digest = file_hash(args.config)
    manifest = {
        "started_utc": datetime.now(UTC).isoformat(), "source": source,
        "measurement_config": str(args.config), "config_sha256": file_hash(args.config),
        "source_config": design["source_config"], "historical_case_config_hash": next(iter(config_hashes)),
        "effective_config": config.model_dump(mode="json"), "effective_config_hash": content_hash(config.model_dump(mode="json")),
        "input_hashes": inputs, "query_identities": identities,
        "case_ids": [case["case_id"] for case in cases], "runtime": runtime_manifest(),
        "historical_serial_identity_overlap": len(set(identities) & historical_ids),
        "population_is_original_full_serial_workload": False,
        "historical_database_sha256": file_hash(database),
        "historical_latency_sha256": file_hash(Path(design["historical_latency"])),
        "source_config_sha256": file_hash(Path(design["source_config"])),
        "code_hashes":code_hashes,
        "interpretation": design["interpretation"], "expected_calls": len(cases) * len(design["modes"]),
        "protocol": "v1", "k_max": config.recourse.k_max, "K": config.recourse.rate_horizon_steps,
        "D_max_version": "v1", "D_max": config.validation.mahalanobis_max,
        "population": design["population"], "native_threads": design["native_threads"],
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    torch.set_num_threads(design["native_threads"])
    records: dict[str, list[dict]] = {}
    with threadpool_limits(limits=design["native_threads"]):
        pipeline = PrescriptXAI.from_config(config)
        if pipeline.config.recourse != config.recourse or pipeline.config.artifacts != config.artifacts:
            raise ValueError("pipeline changed the frozen effective recourse or fitted assets")
        with closing(sqlite3.connect(args.output / "samples.sqlite3")) as checkpoint:
            checkpoint.execute("CREATE TABLE samples (mode TEXT, idx INTEGER, payload TEXT, PRIMARY KEY(mode,idx))")
            for mode in design["modes"]:
                for index in range(design["warmup_calls_per_mode"]):
                    warm = cases[index % len(cases)]
                    pipeline.recommend(warm["state"], mode=mode,
                                       context=InputContext.model_validate(warm["context"]) if warm["context"] else None)
                records[mode.upper()] = []
                for index, case in enumerate(cases * design["repeats"]):
                    started = perf_counter_ns()
                    try:
                        result = pipeline.recommend(case["state"], mode=mode,
                                                   context=InputContext.model_validate(case["context"]) if case["context"] else None)
                        elapsed = (perf_counter_ns() - started) / 1e6
                        payload = {"result":result.model_dump(mode="json"), "status":result.status,
                                   "original_state":case["state"], "timings":result.timings.model_dump(mode="json"),
                                   "observed_public_call_ms":elapsed, "case_id":case["case_id"]}
                    except Exception as error:
                        elapsed = (perf_counter_ns() - started) / 1e6
                        payload = {"status": "ERROR", "error_type": type(error).__name__,
                                   "original_state": case["state"], "timings": {},
                                   "observed_public_call_ms":elapsed, "case_id":case["case_id"]}
                    with checkpoint:
                        checkpoint.execute("INSERT INTO samples VALUES (?,?,?)", (mode,index,json.dumps(payload,allow_nan=False)))
                    records[mode.upper()].append(payload)
        for mode in design["modes"]:
            profile = cProfile.Profile()
            profile.enable()
            for _ in range(design["profile_calls_per_mode"]):
                first = cases[0]
                pipeline.recommend(first["state"], mode=mode,
                                   context=InputContext.model_validate(first["context"]) if first["context"] else None)
            profile.disable()
            profile.dump_stats(args.output / f"{mode}.prof")
    budgets = {"ingestion_ms": config.latency_budget.ingestion_max_ms,
               "inference_ms": config.latency_budget.inference_max_ms,
               "optimization_ms": config.latency_budget.optimization_max_ms,
               "validation_ms": config.latency_budget.validation_max_ms,
               "pipeline_ms": config.latency_budget.pipeline_max_ms,
               "dashboard_ms": config.latency_budget.dashboard_max_ms}
    modes = {}
    for mode, rows in records.items():
        modes[mode] = {}
        for stage, budget in budgets.items():
            pairs = [(int(row["original_state"]["engine_id"]),
                      row["observed_public_call_ms"] if stage == "pipeline_ms" else row["timings"][stage])
                     for row in rows if stage == "pipeline_ms" or row["timings"].get(stage) is not None]
            values = np.array([value for _, value in pairs], dtype=float)
            ids = np.array([unit for unit, _ in pairs], dtype=np.int64)
            interval = engine_bootstrap_interval(
                ids, values, seed=design["bootstrap_seed"],
                replicates=design["bootstrap_replicates"], confidence=design["bootstrap_confidence"],
                statistic=lambda samples: float(np.quantile(samples,.95)),
            ) if pairs else None
            modes[mode][stage] = {"count":len(pairs), "engine_count":len(set(ids)),
                "p95_ms":float(np.quantile(values,.95)) if pairs else None,
                "all_query_count":len(rows), "missing_count":len(rows)-len(pairs),
                "error_count":sum(row["status"] == "ERROR" for row in rows),
                "upper_budget_ms":budget,"p95_engine_ci":asdict(interval) if interval else None,
                "development_profile_only":True}
    errors = sum(row["status"] == "ERROR" for rows in records.values() for row in rows)
    if source_revision(require_clean=True) != source or file_hash(args.config) != config_digest:
        raise ValueError("measurement source/configuration changed during execution")
    if any(file_hash(Path(path)) != digest for path,digest in {**inputs,**code_hashes}.items()):
        raise ValueError("measurement code or frozen fitted inputs changed during execution")
    if sum(map(len,records.values())) != manifest["expected_calls"]:
        raise ValueError("the registered query population is incomplete")
    (args.output / "measurements.json").write_text(json.dumps({"metadata":manifest,"modes":modes,"results":records},indent=2,allow_nan=False),encoding="utf-8")
    final = {"completed_utc": datetime.now(UTC).isoformat(), "complete": True,
             "calls": sum(len(rows) for rows in records.values()), "errors":errors,
             "modes":modes,"passed":errors == 0}
    (args.output / "complete.json").write_text(json.dumps(final, indent=2), encoding="utf-8")
    print(json.dumps(final, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
