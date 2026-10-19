"""Measure the preregistered public pipeline on real, engine-disjoint FD001 populations."""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from prescriptxai.api import create_app
from prescriptxai.data.cmapss import load_cmapss_archive, to_model_frame
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.evaluation.latency import benchmark_pipeline
from prescriptxai.evaluation.metrics import engine_bootstrap_interval
from prescriptxai.logging_utils import configure_logging
from prescriptxai.pipeline import PrescriptXAI

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts/phase6"
LOGGER = logging.getLogger("prescriptxai.phase6")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def save_document(document: dict[str, Any]) -> None:
    """Preserve run-specific evidence and update the convenience latest pointer."""
    write_json(OUTPUT / document["run_id"] / "pipeline.json", document)
    write_json(OUTPUT / "pipeline.json", document)


def raw_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[
        [
            n
            for n in frame
            if n in {"engine_id", "cycle"} or n.startswith(("sensor_", "op_setting_"))
        ]
    ].copy()


def first_alerts(pipeline: PrescriptXAI, frame: pd.DataFrame) -> pd.DataFrame:
    risk = pipeline.engine.model.predict_risk(frame[list(pipeline.engine.model.feature_names)])
    return raw_frame(
        frame.loc[risk >= pipeline.config.tau_danger]
        .sort_values(["engine_id", "cycle"])
        .groupby("engine_id", as_index=False)
        .head(1)
    )


def summary(records: list[dict[str, Any]], config: Any) -> dict[str, Any]:
    ids = np.asarray([int(r["original_state"]["engine_id"]) for r in records])
    metrics = {}
    bits = {
        "validity": [r["validation_report"]["model_valid"] for r in records],
        "plausibility_all_queries": [r["plausible"] for r in records],
        "tier3": [r["validation_report"]["tier3_engineering"]["passed"] for r in records],
        "tier4": [r["validation_report"]["tier4_sensor_coupling"]["passed"] for r in records],
        "joint": [r["joint"] for r in records],
        "RECOVERABLE": [r["status"] == "RECOVERABLE" for r in records],
        "PARTIAL": [r["status"] == "PARTIAL" for r in records],
        "ESCALATE": [r["status"] == "ESCALATE" for r in records],
    }
    for name, values in bits.items():
        metrics[name] = {
            "numerator": sum(values),
            "denominator": len(values),
            "engine_count": len(set(ids.tolist())),
            "interval": asdict(
                engine_bootstrap_interval(
                    ids, values, seed=config.seed, replicates=config.evaluation.bootstrap_replicates
                )
            ),
        }
    returned = [r for r in records if r["action_feasible"] and r["delta_per_feature"]]
    metrics["plausibility_returned_counterfactuals"] = {
        "numerator": sum(r["plausible"] for r in returned),
        "denominator": len(returned),
        "engine_count": len({int(r["original_state"]["engine_id"]) for r in returned}),
        "interval": asdict(
            engine_bootstrap_interval(
                [int(r["original_state"]["engine_id"]) for r in returned],
                [r["plausible"] for r in returned],
                seed=config.seed,
                replicates=config.evaluation.bootstrap_replicates,
            )
        )
        if returned
        else None,
        "definition": "nonzero sparse feasible returned diagnostic/CF candidate, regardless of tier outcomes; includes failed candidates",
    }
    distances = [r["validation_report"]["tier2_distributional"]["measurement"] for r in records]
    return {
        "metrics": metrics,
        "distance_quantiles": dict(
            zip(
                ["p50", "p95", "p99"],
                np.quantile(distances, [0.5, 0.95, 0.99]).tolist(),
                strict=True,
            )
        ),
        "evidence_counts": {
            level: sum(r["evidence_level"] == level for r in records)
            for level in ("none", "E1", "E2", "E3", "E4", "E5")
        },
    }


def pooled_latency(records: list[dict[str, Any]], config: Any) -> dict[str, Any]:
    """Pool actual OOF call samples, never fold percentiles."""
    result = {}
    budgets = {
        "ingestion_ms": config.latency_budget.ingestion_max_ms,
        "inference_ms": config.latency_budget.inference_max_ms,
        "optimization_ms": config.latency_budget.optimization_max_ms,
        "validation_ms": config.latency_budget.validation_max_ms,
        "pipeline_ms": config.latency_budget.pipeline_max_ms,
    }
    for stage, budget in budgets.items():
        samples = [r["timings"][stage] for r in records]
        ids = [int(r["original_state"]["engine_id"]) for r in records]
        q = np.quantile(samples, [0.5, 0.95, 0.99]).tolist()
        result[stage] = {
            "p50_ms": q[0],
            "p95_ms": q[1],
            "p99_ms": q[2],
            "upper_budget_ms": budget,
            "passed": q[1] <= budget,
            "engine_count": len(set(ids)),
            "count": len(samples),
            "p95_engine_ci": asdict(
                engine_bootstrap_interval(
                    ids,
                    samples,
                    seed=config.seed,
                    replicates=config.evaluation.bootstrap_replicates,
                    statistic=lambda values: float(np.quantile(values, 0.95)),
                )
            ),
        }
    return result


def run() -> None:
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT
    ).decode()
    if any(
        entry[3:].startswith(("src/", "scripts/", "configs/", "docs/evaluation_protocol"))
        for entry in dirty.splitlines()
    ):
        raise ValueError("commit implementation/configuration/protocol before real measurements")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    run_id = "phase6-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    configure_logging(run_id=run_id)
    source = json.loads((ROOT / "artifacts/phase5/funnel.json").read_text(encoding="utf-8"))
    provenance = source["provenance"]
    pipelines = {
        version: PrescriptXAI.from_config(
            ROOT / f"configs/experiments/phase6-pipeline-{version}.yaml"
        )
        for version in ("v1", "v2")
    }
    base = pipelines["v1"]
    archive_path = base.config.data.root / base.config.data.archive_name
    archive = load_cmapss_archive(archive_path, "FD001")
    labeled = add_training_labels(to_model_frame(archive.train), None, base.config.horizon_H)
    validation_ids = provenance["base/v1"]["validation_engine_ids"]
    test_ids = provenance["base/v1"]["evaluation_engine_ids"]
    if set(validation_ids) & set(test_ids) or set(test_ids) & set(
        base.engine.model.training_engine_ids
    ):
        raise ValueError("engine leakage in declared internal partitions")
    development = first_alerts(base, labeled.loc[labeled.engine_id.isin(validation_ids)])
    holdout = first_alerts(base, labeled.loc[labeled.engine_id.isin(test_ids)])
    official = to_model_frame(archive.test)
    terminals = official.groupby("engine_id").cycle.max()
    rul = dict(zip(archive.test_rul.unit_id, archive.test_rul.rul, strict=True))
    official["rul"] = [
        float(rul[int(unit)] + terminals[int(unit)] - cycle)
        for unit, cycle in zip(official.engine_id, official.cycle, strict=True)
    ]
    official["engine_id"] += 10000
    official_alerts = first_alerts(base, official)
    document: dict[str, Any] = {
        "run_id": run_id,
        "git_hash": commit,
        "preregistration_commit": subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", "docs/evaluation_protocol.md"], cwd=ROOT
        )
        .decode()
        .strip(),
        "input_fingerprints": {
            "phase5_report": digest(ROOT / "artifacts/phase5/funnel.json"),
            "taxonomy": digest(ROOT / "configs/features.yaml"),
        },
        "archive_sha256": digest(archive_path),
        "assumptions": "C-MAPSS proxy limits and K=1; static data; E3 maximum, no RUL extension",
        "reports": [],
        "audit": {},
        "api_cli": [],
    }
    if digest(archive_path) != source["input_fingerprints"]["archive"]:
        raise ValueError("real archive differs from Phase5 provenance")
    document["input_fingerprints"]["artifacts"] = {}

    def record_artifacts(label: str, service: PrescriptXAI) -> None:
        paths = {
            "model": service.config.artifacts.model,
            "validator": service.config.artifacts.mahalanobis,
            "coupling": service.config.artifacts.coupling,
        }
        document["input_fingerprints"]["artifacts"][label] = {
            name: {"path": str(path), "sha256": digest(path)}
            for name, path in paths.items()
            if path is not None
        }

    for version, pipeline in pipelines.items():
        record_artifacts("base/" + version, pipeline)
        config_path = ROOT / f"configs/experiments/phase6-pipeline-{version}.yaml"
        for population, rows in (
            ("development_first_alert", development),
            ("internal_heldout_first_alert", holdout),
            ("official_test_first_alert", official_alerts),
        ):
            LOGGER.info("Measuring %s %s: %s engines", version, population, len(rows))
            metadata = {
                "run_id": run_id,
                "git_hash": commit,
                "protocol_version": version,
                "D_max_version": version,
                "population": population,
                "config_path": str(config_path.relative_to(ROOT)),
                "config_file_sha256": digest(config_path),
            }
            report = benchmark_pipeline(
                pipeline, rows, warmup_frame=development, metadata=metadata
            ).model_dump(mode="json")
            report["quality"] = {
                mode: summary(records, pipeline.config)
                for mode, records in report["results"].items()
            }
            document["reports"].append(report)
            save_document(document)
        # Real CLI/API demonstration: include first chronological nonrecoverable result if present.
        records = next(
            r
            for r in document["reports"]
            if r["metadata"]["protocol_version"] == version
            and r["metadata"]["population"] == "internal_heldout_first_alert"
        )["results"]["FAST"]
        declared = (
            records
            + next(
                r
                for r in document["reports"]
                if r["metadata"]["protocol_version"] == version
                and r["metadata"]["population"] == "development_first_alert"
            )["results"]["FAST"]
        )
        selected = [records[0]]
        for status in ("PARTIAL", "ESCALATE"):
            matches = sorted(
                (r for r in declared if r["status"] == status),
                key=lambda r: (r["original_state"]["engine_id"], r["original_state"]["cycle"]),
            )
            selected.extend(matches[:1])
        for saved in selected:
            state = saved["original_state"]
            response = TestClient(create_app(pipeline)).post(
                "/recommend", json={"state": state, "mode": "fast"}
            )
            cli = subprocess.run(
                [
                    "uv",
                    "run",
                    "prescriptxai",
                    "recommend",
                    "--engine-id",
                    str(int(state["engine_id"])),
                    "--cycle",
                    str(int(state["cycle"])),
                    "--config",
                    str(config_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if response.status_code != 200 or cli.returncode != 0:
                raise ValueError(f"real API/CLI gate failed: {response.text} {cli.stdout}")
            cli_result = json.loads(cli.stdout)
            if cli_result["new_state"] != response.json()["new_state"]:
                raise ValueError("real CLI/API candidate mismatch")
            document["api_cli"].append(
                {
                    "protocol": version,
                    "population": next(
                        r["metadata"]["population"] for r in document["reports"]
                        if r["metadata"]["protocol_version"] == version
                        and any(x["original_state"] == state for x in r["results"]["FAST"])
                    ),
                    "state": state, "api": response.json(), "cli": cli_result,
                }
            )
            save_document(document)
    for version in ("v1", "v2"):
        fold_records: dict[str, list[dict[str, Any]]] = {"FAST": [], "THOROUGH": []}
        fold_reports = []
        for fold in range(1, 6):
            path = ROOT / f"configs/experiments/phase6-fold-{fold}-{version}.yaml"
            pipeline = PrescriptXAI.from_config(path)
            record_artifacts(f"fold-{fold}/{version}", pipeline)
            ids = provenance[f"fold-{fold}/{version}"]["evaluation_engine_ids"]
            if set(ids) & (
                set(pipeline.engine.model.training_engine_ids)
                | set(pipeline.engine.coupling.calibration_engine_ids)
            ):
                raise ValueError("OOF engine leakage")
            heldout_rows = first_alerts(pipeline, labeled.loc[labeled.engine_id.isin(ids)])
            warm = first_alerts(
                pipeline,
                labeled.loc[
                    labeled.engine_id.isin(pipeline.engine.coupling.calibration_engine_ids)
                ],
            )
            LOGGER.info("Measuring %s OOF fold %s: %s engines", version, fold, len(heldout_rows))
            report = benchmark_pipeline(
                pipeline,
                heldout_rows,
                warmup_frame=warm,
                metadata={
                    "run_id": run_id,
                    "git_hash": commit,
                    "protocol_version": version,
                    "D_max_version": version,
                    "population": f"grouped_oof_fold_{fold}_first_alert",
                    "config_path": str(path.relative_to(ROOT)),
                    "config_file_sha256": digest(path),
                },
            ).model_dump(mode="json")
            for mode, records in report["results"].items():
                fold_records[mode].extend(records)
            fold_reports.append(report)
            document["oof_folds_" + version] = fold_reports
            save_document(document)
        # Pooled OOF counts are per-engine, each assessed only by its held-out fold model.
        document["oof_quality_" + version] = {
            mode: summary(records, pipeline.config) for mode, records in fold_records.items()
        }
        document["oof_latency_" + version] = {
            mode: pooled_latency(records, pipeline.config) for mode, records in fold_records.items()
        }
        document["audit"][version] = {
            "oof_engine_count": len(
                {r["original_state"]["engine_id"] for r in fold_records["FAST"]}
            ),
            "fold_config_hashes": [r["metadata"]["config_file_sha256"] for r in fold_reports],
        }
        save_document(document)
    LOGGER.info("Completed %s; evidence written to %s", run_id, OUTPUT / "pipeline.json")


if __name__ == "__main__":
    run()
