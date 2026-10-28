"""One-command reconstruction using the existing scientific pipeline and honest provenance."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd

from prescriptxai import __version__
from prescriptxai.config import load_config
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.data.cmapss import load_cmapss_archive
from prescriptxai.data.download import download_archive, verify_archive
from prescriptxai.data.prepare import prepare_cmapss
from prescriptxai.evaluation.metrics import EvaluationRecord
from prescriptxai.evaluation.report import (
    build_evaluation_provenance,
    evaluation_metric_intervals,
    write_evaluation_report,
)
from prescriptxai.evaluation.runner import EvaluationRun, evaluate_states
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.models.train import train_risk_model
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.provenance import source_identity
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, save_mahalanobis_validator
from prescriptxai.validation.tier4_coupling import calibrate_coupling_thresholds


def _hash(path: Path) -> str:
    """Hash a file without loading large input artifacts into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def reproduction_metrics(
    run: EvaluationRun, service: PrescriptXAI, original: pd.DataFrame
) -> dict[str, Any]:
    """Use the shared audited report definitions for reproduction metrics."""
    return evaluation_metric_intervals(run, service.engine, original)


def reproduce(config_path: Path, progress: Callable[[str], None] = print) -> Path:
    """Prepare, fit, calibrate, validate, evaluate and report into a new output directory.

    The configured model's parent directory owns this run. All generated outputs must
    be within it. Existing directories, including failed runs, are never overwritten.
    A completed workflow is a reproducibility demonstration, not a new efficacy claim.
    """
    config = load_config(config_path)
    if config.model_choice != "xgboost":
        raise ValueError("reproduce currently supports the registered XGBoost workflow only")
    root = config.artifacts.model.resolve().parent
    coupling_path = config.artifacts.coupling
    if coupling_path is None:
        raise ValueError("reproduce requires an explicit coupling artifact path")
    outputs = (
        config.artifacts.model,
        config.artifacts.mahalanobis,
        coupling_path,
        config.artifacts.evaluation_report,
        config.data.processed_root,
    )
    if any(not path.resolve().is_relative_to(root) for path in outputs):
        raise ValueError("all reproduction outputs must be within the model artifact directory")
    if root.exists():
        raise ValueError(f"refusing to replace existing reproduction directory: {root}")
    taxonomy_path = config.pipeline.taxonomy_path
    taxonomy = load_taxonomy(taxonomy_path)
    config_digest = _hash(config_path)
    taxonomy_digest = _hash(taxonomy_path)
    root.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "manifest.json"
    started = perf_counter()
    manifest: dict[str, Any] = {
        "run_id": "reproduce-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"),
        "status": "running",
        "started_utc": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "source": source_identity(),
        "configuration_path": str(config_path),
        "configuration_sha256": config_digest,
        "taxonomy_sha256": taxonomy_digest,
        "effective_configuration": config.model_dump(mode="json"),
        "population": (
            f"reused internal held-out {config.data.dataset} engines; seeded feasible-alert sample"
        ),
        "protocol": "v1" if config.validation.mahalanobis_max == 5.0 else "custom",
        "evidence_limit": "E3 proxy assumptions; no physical proof or RUL extension",
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
            "python": platform.python_version(),
        },
        "dependencies": {
            item.metadata["Name"]: item.version for item in importlib.metadata.distributions()
        },
        "stages": [],
    }

    def persist() -> None:
        temporary = manifest_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        temporary.replace(manifest_path)

    @contextmanager
    def stage(name: str) -> Iterator[None]:
        entry: dict[str, Any] = {"name": name, "status": "running"}
        manifest["stages"].append(entry)
        persist()
        progress(f"Starting {name}")
        clock = perf_counter()
        try:
            yield
        except Exception as error:
            entry.update(status="failed", error_type=type(error).__name__)
            manifest.update(status="failed", failed_stage=name)
            raise RuntimeError(
                f"reproduction stage {name} failed: {error}; see {manifest_path}"
            ) from error
        else:
            entry["status"] = "complete"
        finally:
            entry["elapsed_seconds"] = perf_counter() - clock
            manifest["elapsed_seconds"] = perf_counter() - started
            persist()
        progress(f"Completed {name} ({entry['elapsed_seconds']:.2f}s)")

    with stage("data_prepare"):
        archive = config.data.root / config.data.archive_name
        if not archive.exists():
            download_archive(
                config.data.dataset_url,
                archive,
                config.data.download_timeout_seconds,
                config.data.dataset_sha256,
            )
        manifest["input_archive_sha256"] = verify_archive(archive, config.data.dataset_sha256)
        expected = config.data.expected_row_counts.get(config.data.dataset)
        prepared = prepare_cmapss(
            archive,
            config.data.dataset,
            config.data.processed_root,
            root / "preparation",
            config.seed,
            config.horizon_H,
            config.data.rul_cap,
            config.data.variance_threshold,
            config.data.regime_k,
            config.data.lifetime_buckets,
            config.data.train_fraction,
            config.data.validation_fraction,
            config.data.test_fraction,
            config.data.rolling_features,
            config.data.rolling_window,
            config.data.dataset_sha256,
            expected.model_dump() if expected else None,
        )
        manifest["data_quality_report"] = str(prepared.report_path)
    with stage("train_and_calibrate"):
        dataset = load_cmapss_archive(archive, config.data.dataset)
        trained = train_risk_model(dataset.train, config, taxonomy, "xgb")
        manifest["engine_partitions"] = {
            "train": list(trained.splits.train_engine_ids),
            "validation": list(trained.splits.validation_engine_ids),
            "test": list(trained.splits.test_engine_ids),
        }
        save_model_bundle(trained.bundle, config.artifacts.model)
        (root / "predictor_metrics.json").write_text(
            json.dumps(trained.metrics, indent=2, allow_nan=False), encoding="utf-8"
        )
    with stage("fit_validators"):
        coupling = SensorCouplingModel.fit(
            trained.splits.train,
            taxonomy,
            training_engine_ids=trained.splits.train_engine_ids,
            failure_horizon=config.horizon_H,
            seed=config.seed,
        )
        coupling = calibrate_coupling_thresholds(
            coupling,
            trained.splits.validation,
            trained.splits.validation_engine_ids,
            reference_distribution=config.validation.coupling_calibration_reference,
            min_rul=config.validation.healthy_min_rul,
            evaluation_engine_ids=trained.splits.test_engine_ids,
        )
        coupling.save(coupling_path)
        coupling.write_diagnostic_report(root / "coupling", trained.splits.train)
        validator = fit_mahalanobis_validator(
            trained.splits.train,
            trained.bundle,
            trained.splits.train_engine_ids,
            config,
        )
        save_mahalanobis_validator(validator, config.artifacts.mahalanobis)
    with stage("evaluate"):
        if _hash(config_path) != config_digest or _hash(taxonomy_path) != taxonomy_digest:
            raise ValueError("configuration or taxonomy changed during reproduction")
        service = PrescriptXAI.from_config(config_path)

        def save_selection(rows: pd.DataFrame, counts: dict[str, int]) -> None:
            rows.to_csv(root / "selected_queries.csv", index=False, float_format="%.17g")
            manifest["evaluation_counts"] = {
                **counts,
                "selected_queries": len(rows),
                "completed_queries": 0,
            }
            persist()

        def save_record(record: EvaluationRecord) -> None:
            with (root / "query_results.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(asdict(record), allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            manifest["evaluation_counts"]["completed_queries"] += 1
            persist()

        run = evaluate_states(
            service.engine, trained.splits.test, on_selection=save_selection, on_record=save_record
        )
        source_paths = {
            "configuration": config_path,
            "taxonomy": taxonomy_path,
            "archive": archive,
            "model": config.artifacts.model,
            "mahalanobis": config.artifacts.mahalanobis,
            "coupling": coupling_path,
        }
        provenance = build_evaluation_provenance(service.engine, trained.splits.test, source_paths)
        provenance["reproduction_run_id"] = manifest["run_id"]
        provenance["population_label"] = manifest["population"]
        manifest["evaluation_counts"] = {
            "eligible_alerts": run.summary.eligible_high_risk_states,
            "interval_prescreen_exclusions": run.infeasible_high_risk_states,
            "sampled_queries": len(run.records),
            "sampled_engines": len({record.engine_id for record in run.records}),
            "completed_queries": len(run.records),
        }
    with stage("report"):
        intervals = reproduction_metrics(run, service, trained.splits.test)
        write_evaluation_report(
            run,
            config.artifacts.evaluation_report,
            config.artifacts.evaluation_report.with_suffix(".md"),
            config.recourse.model_dump(mode="json"),
            provenance=provenance,
            metric_intervals=intervals,
        )
        measured = {
            "run_id": manifest["run_id"],
            "source": manifest["source"],
            "config_path": str(config_path),
            "config_sha256": config_digest,
            "protocol": manifest["protocol"],
            "population": manifest["population"],
            "mode": config.recourse.search_mode,
            "K": config.recourse.rate_horizon_steps,
            "k_max": config.recourse.k_max,
            "D_max": service.engine.mahalanobis.max_distance,
            "counts": manifest["evaluation_counts"],
            "metrics": intervals,
            "evidence_limit": manifest["evidence_limit"],
            "returned_definition": (
                "nonzero model-feature change with feasible bounded sparse action"
            ),
        }
        (root / "measured_metrics.json").write_text(
            json.dumps(measured, indent=2, allow_nan=False), encoding="utf-8"
        )
        with config.artifacts.evaluation_report.with_suffix(".md").open(
            "a", encoding="utf-8"
        ) as report:
            report.write("\n\n## Reproduction labels and whole-engine intervals\n\n```json\n")
            report.write(json.dumps(measured, indent=2, allow_nan=False) + "\n```\n")
        manifest["output_sha256"] = {
            path.relative_to(root).as_posix(): _hash(path)
            for path in sorted(root.rglob("*"))
            if path.is_file() and path != manifest_path
        }
    manifest.update(
        status="complete",
        completed_utc=datetime.now(UTC).isoformat(),
        elapsed_seconds=perf_counter() - started,
    )
    persist()
    return manifest_path
