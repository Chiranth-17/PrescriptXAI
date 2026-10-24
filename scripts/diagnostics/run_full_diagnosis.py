#!/usr/bin/env python3
"""Rebuild the Phase 4 closure evidence from saved FD001 artifacts and fixed protocols.

This diagnostic intentionally distinguishes the model's risk gate from Tier 2–4 checks. It never
uses illustrative synopsis numbers, and it never labels a finite-grid miss as physical proof of
infeasibility.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import pickle
import re
import subprocess
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

from prescriptxai.artifacts import load_trusted_pickle
from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.bounds import allowed_interval
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import FeatureTaxonomy, load_taxonomy
from prescriptxai.data.cmapss import load_cmapss_archive, to_model_frame
from prescriptxai.data.preprocess import (
    add_training_labels,
    fit_feature_scaler,
)
from prescriptxai.data.splits import split_engines
from prescriptxai.evaluation.metrics import EvaluationRecord, engine_bootstrap_interval
from prescriptxai.evaluation.report import build_evaluation_provenance
from prescriptxai.evaluation.runner import (
    _has_feasible_actuator_intervals,
    evaluate_states,
)
from prescriptxai.models.calibration import fit_probability_calibrator
from prescriptxai.models.registry import ModelBundle, save_model_bundle
from prescriptxai.models.train import (
    _build_estimator,
    _configuration_hash,
    _model_feature_names,
)
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.recourse.sparsify import bounded_sparse_delta_grid
from prescriptxai.validation.feasibility import frozen_settings
from prescriptxai.validation.pipeline import (
    fit_mahalanobis_validator,
    save_mahalanobis_validator,
)
from prescriptxai.validation.tier3_engineering import validate_engineering
from prescriptxai.validation.tier4_coupling import validate_sensor_coupling

LOGGER = logging.getLogger("prescriptxai.phase4_closure")
ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/profiles/phase4-grid-final.yaml"
TAXONOMY_PATH = ROOT / "configs/features.yaml"
PROTOCOL_PATH = ROOT / "docs/phase4_protocol_v2.md"
OUTPUT_ROOT = ROOT / "artifacts/phase4-final"
REPORT_PATH = ROOT / "docs/phase4_full_diagnosis_results.json"
FINAL_DOC_PATH = ROOT / "docs/phase4_final.md"
K_CURVE_PATH = ROOT / "docs/phase4_k_curve.svg"
D_MAX_V2 = 8.0
BOOTSTRAP_REPLICATES = 2_000
SENSITIVITY_SAMPLE = 60
ORACLE_GRID_POINTS = 9
CHECKPOINT_VERSION = 1
COMPATIBLE_HOLDOUT_SOURCE_COMMIT = "7860fed5a99b6c94eefc2ffd2c8327052ea56b24"


def _commit() -> str:
    """Return the source revision that produced the measurements."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True, cwd=ROOT
    )
    return result.stdout.strip()


def _sha256_file(path: Path) -> str:
    """Hash a frozen protocol or input artifact."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_checkpoint(name: str, context_hash: str, run_id: str, payload: Any) -> None:
    """Atomically persist an ignored, versioned stage result for diagnostic resumption."""
    directory = OUTPUT_ROOT / "checkpoints"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{name}.pickle"
    temporary = target.with_suffix(".pickle.tmp")
    with temporary.open("wb") as stream:
        pickle.dump(
            {
                "version": CHECKPOINT_VERSION,
                "context_hash": context_hash,
                "run_id": run_id,
                "source_commit": _commit(),
                "payload": payload,
            },
            stream,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    temporary.replace(target)


def _read_checkpoint(
    name: str,
    context_hash: str,
    *,
    compatible_context_hashes: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Load a compatible stage checkpoint; discard results from different inputs or code."""
    path = OUTPUT_ROOT / "checkpoints" / f"{name}.pickle"
    if not path.is_file():
        return None
    try:
        checkpoint = load_trusted_pickle(path)
    except (OSError, ValueError, pickle.PickleError, EOFError, AttributeError, ImportError):
        LOGGER.warning("Ignoring unreadable diagnostic checkpoint %s", path)
        return None
    if not isinstance(checkpoint, dict) or checkpoint.get("version") != CHECKPOINT_VERSION:
        LOGGER.info("Ignoring stale diagnostic checkpoint %s", path)
        return None
    if checkpoint.get("context_hash") != context_hash:
        compatible = compatible_context_hashes or {}
        matched_commit = next(
            (
                commit
                for commit, compatible_hash in compatible.items()
                if checkpoint.get("context_hash") == compatible_hash
            ),
            None,
        )
        if name not in {"holdout", "sensitivity"} or matched_commit is None:
            LOGGER.info("Ignoring stale diagnostic checkpoint %s", path)
            return None
        checkpoint["source_commit"] = matched_commit
    return checkpoint


def _config_hash(config: AppConfig) -> str:
    """Hash the complete effective typed configuration, including runtime overrides."""
    serialized = json.dumps(
        config.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    """Convert numpy and dataclass values to JSON-compatible builtins."""
    if hasattr(value, "__dataclass_fields__"):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def _write_json(path: Path, document: Any) -> None:
    """Write a deterministic, finite JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(document), indent=2, allow_nan=False), encoding="utf-8"
    )


def _engine_with_settings(
    engine: PrescriptXAIEngine,
    *,
    recourse_updates: dict[str, Any] | None = None,
    mahalanobis_max: float | None = None,
    max_queries: int | None = None,
) -> PrescriptXAIEngine:
    """Clone an engine with explicitly recorded one-factor settings."""
    recourse = engine.config.recourse
    if recourse_updates:
        recourse = recourse.model_copy(update=recourse_updates)
    evaluation = engine.config.evaluation
    if max_queries is not None:
        evaluation = evaluation.model_copy(update={"max_queries": max_queries})
    validation = engine.config.validation
    mahalanobis = engine.mahalanobis
    if mahalanobis_max is not None:
        validation = validation.model_copy(update={"mahalanobis_max": mahalanobis_max})
        mahalanobis = replace(mahalanobis, max_distance=mahalanobis_max)
    config = engine.config.model_copy(
        update={"recourse": recourse, "evaluation": evaluation, "validation": validation}
    )
    return PrescriptXAIEngine(
        config, engine.taxonomy, engine.model, mahalanobis, engine.coupling
    )


def _alert_rows(engine: PrescriptXAIEngine, frame: pd.DataFrame) -> pd.DataFrame:
    """Select every row whose calibrated true-model risk meets the alert threshold."""
    risks = engine.model.predict_risk(frame[list(engine.model.feature_names)])
    return frame.iloc[np.flatnonzero(risks >= engine.config.model.danger_threshold)].copy()


def _effective_solver_settings(records: tuple[EvaluationRecord, ...]) -> dict[str, Any]:
    """Summarize observed runtime settings and grid-path enforcement without treating missing data as pass."""
    settings = [dict(record.effective_solver_settings) for record in records]
    grid_runs = [item for item in settings if item.get("grid_ran") is True]

    def enforcement_count(key: str) -> dict[str, int]:
        values = [item.get(key) for item in grid_runs]
        return {
            "true": sum(value is True for value in values),
            "false": sum(value is False for value in values),
            "unreported": sum(value is None for value in values),
        }

    k_enforcement = enforcement_count("grid_k_limit_honored")
    distance_enforcement = enforcement_count("grid_scaled_distance_honored")
    return {
        "record_count": len(settings),
        "grid_run_count": len(grid_runs),
        "k_max_enforcement": k_enforcement,
        "max_scaled_distance_enforcement": distance_enforcement,
        "all_grid_runs_honored_k_max": (
            k_enforcement["true"] == len(grid_runs) and bool(grid_runs)
        ),
        "all_grid_runs_honored_max_scaled_distance": (
            distance_enforcement["true"] == len(grid_runs) and bool(grid_runs)
        ),
        "runtime_settings_observed": Counter(
            json.dumps(item, sort_keys=True) for item in settings
        ),
    }


def _saved_run_counts(path: Path) -> dict[str, Any] | None:
    """Read outcome counts and runtime configuration from an existing local JSON artifact."""
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    records = document.get("records", [])
    count = len(records)
    model_valid = sum(bool(item.get("model_valid")) for item in records)
    tier2 = sum(bool(item.get("tier2_plausible")) for item in records)
    joint = sum(
        bool(item.get("model_valid"))
        and bool(item.get("recourse_feasible"))
        and bool(item.get("tier2_plausible"))
        and bool(item.get("tier3_engineering_valid"))
        and bool(item.get("tier4_coupling_valid"))
        for item in records
    )
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": _sha256_file(path),
        "query_count": count,
        "model_valid_count": model_valid,
        "tier2_count": tier2,
        "joint_count": joint,
        "recourse_search_configuration": document.get("recourse_search_configuration"),
        "provenance": document.get("provenance"),
    }


def _parse_legacy_d1_counts(report_text: str) -> dict[str, list[list[int]]]:
    """Extract reported numerator/denominator pairs from the superseded D1 table."""
    patterns = {
        "tier1": r"Recourse Validity[^|]*\|\s*(\d+)\s*\|\s*(\d+)",
        "tier2": r"Distributional Plausibility[^|]*\|\s*(\d+)\s*\|\s*(\d+)",
        "joint": r"Joint success[^|]*\|\s*(\d+)\s*\|\s*(\d+)",
    }
    return {
        label: [[int(value) for value in pair] for pair in re.findall(pattern, report_text)]
        for label, pattern in patterns.items()
    }


def _historical_count_audit() -> dict[str, Any]:
    """Audit the reported dirty-run count collision against the saved local evidence."""
    legacy_doc_path = ROOT / "docs/phase4_diagnosis.md"
    legacy_text = legacy_doc_path.read_text(encoding="utf-8") if legacy_doc_path.is_file() else ""
    d1_rows = _parse_legacy_d1_counts(legacy_text)
    k3 = _saved_run_counts(ROOT / "artifacts/FD001-evaluation-grid-200.json")
    k5 = _saved_run_counts(ROOT / "artifacts/FD001-evaluation-grid-final.json")
    same_artifact_outcomes = bool(
        k3
        and k5
        and tuple(k3[key] for key in ("model_valid_count", "tier2_count", "joint_count"))
        == tuple(k5[key] for key in ("model_valid_count", "tier2_count", "joint_count"))
    )
    return {
        "legacy_diagnosis_document": (
            {
                "path": str(legacy_doc_path.relative_to(ROOT)),
                "sha256": _sha256_file(legacy_doc_path),
                "reported_counts_and_denominators": d1_rows,
                "config_warning": (
                    "The archived diagnosis says it used expanded k_max=5, max_scaled_distance=6, "
                    "restarts=3, max_iter=100, grid_points=10 on observed test states."
                ),
            }
            if legacy_text
            else None
        ),
        "saved_k3_run": k3,
        "saved_k5_run": k5,
        "saved_k3_and_k5_outcome_counts_equal": same_artifact_outcomes,
        "interpretation": (
            "The two saved JSON runs have the same outcome counts."
            if same_artifact_outcomes
            else "The saved k3 and k5 JSON artifacts do not support the claimed identical counts. "
            "The archived diagnosis table is not backed by a matching saved per-query run artifact, "
            "so the historical cause cannot be established. Current closure counts are freshly "
            "recomputed from the committed runtime settings."
        ),
    }


def _key(row: Any) -> tuple[int, int]:
    """Return the stable engine-cycle key for a held-out state."""
    return int(row.engine_id), int(row.cycle)


def _records_by_key(records: tuple[EvaluationRecord, ...]) -> dict[tuple[int, int], EvaluationRecord]:
    """Index one population's counterfactual records by engine and cycle."""
    return {(record.engine_id, record.cycle): record for record in records}


def _sample_headline_rows(
    engine: PrescriptXAIEngine,
    alert_rows: pd.DataFrame,
    *,
    sample_size: int,
    seed: int,
) -> pd.DataFrame:
    """Draw the protocol-defined seeded uniform sample from actionable alerts."""
    actionable_positions = [
        index
        for index, (_, row) in enumerate(alert_rows.iterrows())
        if _has_feasible_actuator_intervals(engine, row)
    ]
    count = min(sample_size, len(actionable_positions))
    if count == 0:
        return alert_rows.iloc[:0].copy()
    rng = np.random.default_rng(seed)
    selected = np.sort(rng.choice(actionable_positions, size=count, replace=False))
    return alert_rows.iloc[selected].copy()


def _first_alert_rows(alert_rows: pd.DataFrame) -> pd.DataFrame:
    """Select the earliest-cycle high-risk row per engine."""
    if alert_rows.empty:
        return alert_rows.copy()
    return (
        alert_rows.sort_values(["engine_id", "cycle"])
        .groupby("engine_id", sort=True, as_index=False)
        .head(1)
        .reset_index(drop=True)
    )


def _distance_rows(engine: PrescriptXAIEngine, frame: pd.DataFrame) -> np.ndarray:
    """Vectorized Mahalanobis distance using the fitted training-only validator."""
    scaled = engine.model.scaler.transform(frame[list(engine.model.feature_names)])
    return engine.mahalanobis.distance_batch(scaled)


def _bootstrap(
    frame: pd.DataFrame,
    values: list[float | bool],
    *,
    seed: int,
    statistic: Callable[[np.ndarray], float] = np.mean,
) -> dict[str, Any]:
    """Return an engine-cluster percentile interval with its denominators."""
    if not values:
        return {"estimate": None, "lower": None, "upper": None, "engine_count": 0, "n": 0}
    interval = engine_bootstrap_interval(
        frame["engine_id"].to_numpy(dtype=np.int64),
        values,
        seed=seed,
        replicates=BOOTSTRAP_REPLICATES,
        statistic=statistic,
    )
    return {
        "estimate": interval.estimate,
        "lower": interval.lower,
        "upper": interval.upper,
        "engine_count": interval.engine_count,
        "n": interval.observation_count,
        "replicates": interval.replicate_count,
        "seed": interval.seed,
        "method": "percentile bootstrap resampling engine clusters",
    }


def _population_outcomes(
    engine: PrescriptXAIEngine,
    rows: pd.DataFrame,
    records: tuple[EvaluationRecord, ...],
    *,
    seed: int,
    include_frame: bool = False,
) -> dict[str, Any]:
    """Compute query-denominator and returned-counterfactual metrics with cluster CIs."""
    indexed = _records_by_key(records)
    record_values = [indexed.get(_key(row)) for row in rows.itertuples()]
    if "_risk_before" in rows:
        risk_before = rows["_risk_before"].to_numpy(dtype=np.float64)
    else:
        risk_before = engine.model.predict_risk(rows[list(engine.model.feature_names)])
    row_copy = rows.reset_index(drop=True).copy()
    row_copy["_risk_before"] = risk_before
    n = len(row_copy)
    data: list[dict[str, Any]] = []
    for position, (_, row) in enumerate(row_copy.iterrows()):
        record = record_values[position]
        initial_risk = float(row["_risk_before"])
        final_risk = record.final_risk if record is not None else initial_risk
        risk_drop = initial_risk - final_risk
        physical_tiers = bool(
            record
            and record.tier2_plausible
            and record.tier3_engineering_valid
            and record.tier4_coupling_valid
        )
        recoverable = bool(record and record.model_valid and record.recourse_feasible and physical_tiers)
        partial = bool(
            record
            and physical_tiers
            and risk_drop >= 0.30
            and final_risk > engine.config.model.safe_threshold
        )
        triage = "RECOVERABLE" if recoverable else "PARTIAL" if partial else "ESCALATE"
        data.append(
            {
                "engine_id": int(row["engine_id"]),
                "cycle": int(row["cycle"]),
                "rul": float(row.get("rul", np.nan)),
                "initial_risk": initial_risk,
                "final_risk": final_risk,
                "risk_drop": risk_drop,
                "record": record,
                "model_valid": bool(record and record.model_valid),
                "tier2": bool(record and record.tier2_plausible),
                "tier3": bool(record and record.tier3_engineering_valid),
                "tier4": bool(record and record.tier4_coupling_valid),
                "joint": recoverable,
                "returned": bool(record and record.recourse_feasible),
                "fallback": bool(record and record.engineering_only_fallback),
                "changed_features": record.changed_features if record else 0,
                "optimization_ms": record.optimization_ms if record else None,
                "triage": triage,
            }
        )
    outcomes = pd.DataFrame(
        data,
        columns=(
            "engine_id",
            "cycle",
            "rul",
            "initial_risk",
            "final_risk",
            "risk_drop",
            "record",
            "model_valid",
            "tier2",
            "tier3",
            "tier4",
            "joint",
            "returned",
            "fallback",
            "changed_features",
            "optimization_ms",
            "triage",
        ),
    )
    cluster_frame = outcomes[["engine_id"]]

    def ci(
        name: str,
        values: list[float | bool],
        offset: int = 0,
        frame: pd.DataFrame = cluster_frame,
    ) -> dict[str, Any]:
        del name
        return _bootstrap(frame, values, seed=seed + offset)

    all_records = [item for item in record_values if item is not None]
    returned = [item for item in data if item["returned"]]
    joint_successes = [item for item in data if item["joint"]]
    latency_frame = pd.DataFrame(
        [{"engine_id": int(item.engine_id), "value": float(item.optimization_ms)} for item in all_records]
    )
    lat_ci = (
        engine_bootstrap_interval(
            latency_frame.engine_id.to_numpy(dtype=np.int64),
            latency_frame.value.to_numpy(dtype=np.float64),
            seed=seed + 20,
            replicates=BOOTSTRAP_REPLICATES,
            statistic=lambda values: float(np.quantile(values, 0.95)),
        )
        if len(latency_frame)
        else None
    )
    triage = {
        group: {
            "count": int((outcomes["triage"] == group).sum()),
            "rate": float((outcomes["triage"] == group).mean()) if n else None,
            "ci": ci(group, (outcomes["triage"] == group).to_list(), offset=30 + index),
        }
        for index, group in enumerate(("RECOVERABLE", "PARTIAL", "ESCALATE"))
    }
    risk_bins = [
        ("negative", -float("inf"), 0.0),
        ("0_to_0.10", 0.0, 0.10),
        ("0.10_to_0.30", 0.10, 0.30),
        ("0.30_to_0.60", 0.30, 0.60),
        ("0.60_to_1.00", 0.60, float("inf")),
    ]
    histogram = {
        name: {
            "count": int(((outcomes.risk_drop >= low) & (outcomes.risk_drop < high)).sum()),
            "rate": float(((outcomes.risk_drop >= low) & (outcomes.risk_drop < high)).mean())
            if n
            else None,
            "engine_bootstrap_ci": ci(
                f"risk_drop_bin_{name}",
                ((outcomes.risk_drop >= low) & (outcomes.risk_drop < high)).to_list(),
                offset=50 + index,
            ),
        }
        for index, (name, low, high) in enumerate(risk_bins)
    }
    end_life = outcomes[outcomes.rul <= 10]
    beyond_end_life = outcomes[outcomes.rul > 10]
    end_life_triage = {
        label: {
            "n": len(group),
            "engine_count": int(group.engine_id.nunique()) if len(group) else 0,
            "recoverable_rate": _bootstrap(
                group[["engine_id"]], (group.triage == "RECOVERABLE").to_list(), seed=seed + 70
            ) if len(group) else None,
            "partial_rate": _bootstrap(
                group[["engine_id"]], (group.triage == "PARTIAL").to_list(), seed=seed + 71
            ) if len(group) else None,
            "escalate_rate": _bootstrap(
                group[["engine_id"]], (group.triage == "ESCALATE").to_list(), seed=seed + 72
            ) if len(group) else None,
        }
        for label, group in (("RUL<=10", end_life), ("RUL>10", beyond_end_life))
    }
    successful_features = [float(item["changed_features"]) for item in joint_successes]
    successful_engines = [int(item["engine_id"]) for item in joint_successes]
    successful_sparsity = (
        engine_bootstrap_interval(
            successful_engines,
            successful_features,
            seed=seed + 21,
            replicates=BOOTSTRAP_REPLICATES,
        )
        if successful_features
        else None
    )
    returned_sparsity = (
        _bootstrap(
            outcomes.loc[outcomes.returned, ["engine_id"]],
            outcomes.loc[outcomes.returned, "changed_features"].astype(float).to_list(),
            seed=seed + 22,
        )
        if returned
        else {"estimate": None, "lower": None, "upper": None, "engine_count": 0, "n": 0}
    )
    latency_summary = (
        {
            "p95_ms": float(latency_frame.value.quantile(0.95)),
            "engine_bootstrap_ci": {
                "lower": lat_ci.lower,
                "upper": lat_ci.upper,
                "engine_count": lat_ci.engine_count,
                "n": lat_ci.observation_count,
                "replicates": lat_ci.replicate_count,
                "seed": lat_ci.seed,
                "method": "percentile bootstrap resampling engine clusters; statistic p95",
            },
            "estimate": lat_ci.estimate,
            "lower": lat_ci.lower,
            "upper": lat_ci.upper,
            "engine_count": lat_ci.engine_count,
            "n": lat_ci.observation_count,
        }
        if lat_ci is not None
        else {
            "p95_ms": None,
            "engine_bootstrap_ci": None,
            "estimate": None,
            "lower": None,
            "upper": None,
            "engine_count": 0,
            "n": 0,
        }
    )
    return {
        "query_count": n,
        "engine_count": int(outcomes.engine_id.nunique()) if n else 0,
        "actionable_or_attempted_count": len(all_records),
        "no_candidate_count": n - len(all_records),
        "returned_counterfactual_count": len(returned),
        "engineering_only_fallback_count": int(outcomes.fallback.sum()),
        "metrics": {
            "model_valid_all_queries": ci("model_valid_all", outcomes.model_valid.to_list(), 1),
            "tier2_plausible_all_queries": ci("tier2_all", outcomes.tier2.to_list(), 2),
            "tiers2_to4_joint_all_queries": ci("joint_all", outcomes.joint.to_list(), 3),
            "tier2_plausible_returned_counterfactuals": ci(
                "tier2_returned",
                [bool(item["record"].tier2_plausible) for item in returned],
                4,
                outcomes.loc[outcomes.returned, ["engine_id"]],
            ),
            "tiers2_to4_joint_returned_counterfactuals": ci(
                "joint_returned",
                [bool(item["joint"]) for item in returned],
                5,
                outcomes.loc[outcomes.returned, ["engine_id"]],
            ),
            "mean_sparsity_returned_counterfactuals": ci(
                "sparsity_returned",
                [float(item["changed_features"]) for item in returned],
                6,
                outcomes.loc[outcomes.returned, ["engine_id"]],
            ),
            "mean_sparsity_joint_successes": (
                _bootstrap(
                    outcomes.loc[outcomes.joint, ["engine_id"]],
                    outcomes.loc[outcomes.joint, "changed_features"].astype(float).to_list(),
                    seed=seed + 21,
                )
            ),
            "mean_risk_drop_all_queries": ci("risk_drop", outcomes.risk_drop.to_list(), 6),
            "fallback_rate_all_queries": ci("fallback", outcomes.fallback.to_list(), 7),
        },
        "mean_sparsity_on_joint_successes": asdict(successful_sparsity)
        if successful_sparsity is not None
        else None,
        "mean_sparsity_on_returned_counterfactuals": returned_sparsity,
        "optimization_latency": latency_summary,
        "triage": triage,
        "risk_reduction_histogram": {
            "bins": histogram,
            "population_count": n,
            "bin_definition": "risk_before - risk_after; no-candidate states have zero reduction",
        },
        "end_of_life_concentration": end_life_triage,
        "records": outcomes.drop(columns=["record"]).to_dict(orient="records"),
        **({"_raw_outcomes": outcomes} if include_frame else {}),
    }


def _metric_row(
    label: str,
    metric: dict[str, Any],
    *,
    target: float | None,
    direction: str,
) -> dict[str, Any]:
    """Attach an unchanged design target and signed distance from that target."""
    value = metric["estimate"]
    if value is None or target is None:
        gap = None
    else:
        gap = float(value - target) if direction == ">=" else float(target - value)
    target_label = "reported separately" if target is None else f"{direction} {target:g}"
    return {"metric": label, **metric, "target": target_label, "gap_to_target": gap}


def _population_target_rows(population: dict[str, Any]) -> list[dict[str, Any]]:
    """Build final target rows from measured values and engine-bootstrap intervals."""
    metrics = population["metrics"]
    return [
        _metric_row("True calibrated model validity", metrics["model_valid_all_queries"], target=0.95, direction=">="),
        _metric_row("Tier 2 plausibility, all queries", metrics["tier2_plausible_all_queries"], target=0.90, direction=">="),
        _metric_row(
            "Tier 2 plausibility among returned counterfactuals",
            metrics["tier2_plausible_returned_counterfactuals"],
            target=0.90,
            direction=">=",
        ),
        _metric_row("Joint Tiers 2–4 plausibility, all queries", metrics["tiers2_to4_joint_all_queries"], target=0.90, direction=">="),
        _metric_row(
            "Joint Tiers 2–4 among returned counterfactuals",
            metrics["tiers2_to4_joint_returned_counterfactuals"],
            target=None,
            direction=">=",
        ),
        _metric_row("Mean risk reduction, all queries", metrics["mean_risk_drop_all_queries"], target=0.60, direction=">="),
        _metric_row(
            "Mean changed features among joint successes",
            metrics["mean_sparsity_joint_successes"],
            target=3.0,
            direction="<=",
        ),
        _metric_row(
            "Optimization p95 ms (attempted queries)",
            population["optimization_latency"],
            target=1_800.0,
            direction="<=",
        ),
    ]


def _fold_engine_ids(frame: pd.DataFrame, folds: int, seed: int) -> list[tuple[int, ...]]:
    """Create deterministic lifetime-stratified engine-grouped out-of-fold assignments."""
    lifetimes = frame.groupby("engine_id").cycle.max().sort_index()
    ranks = lifetimes.rank(method="first")
    buckets = pd.qcut(ranks, q=min(6, len(lifetimes) // folds), labels=False, duplicates="drop")
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    ids = lifetimes.index.to_numpy(dtype=np.int64)
    assignments: list[tuple[int, ...]] = []
    for _, test_positions in splitter.split(ids, buckets.to_numpy()):
        assignments.append(tuple(sorted(int(value) for value in ids[test_positions])))
    flattened = [value for assignment in assignments for value in assignment]
    if len(flattened) != len(set(flattened)) or set(flattened) != set(int(value) for value in ids):
        raise ValueError("grouped out-of-fold assignments overlap or omit an engine")
    return assignments


def _fit_oof_engine(
    labeled: pd.DataFrame,
    base_config: AppConfig,
    taxonomy: FeatureTaxonomy,
    held_out_engine_ids: tuple[int, ...],
    *,
    fold: int,
) -> PrescriptXAIEngine:
    """Fit one fully engine-disjoint XGBoost, calibration, coupling, and Tier 2 fold."""
    outer_train_ids = tuple(
        sorted(set(int(value) for value in labeled.engine_id.unique()) - set(held_out_engine_ids))
    )
    lifetime = labeled.groupby("engine_id").cycle.max()
    ranks = lifetime.loc[list(outer_train_ids)].rank(method="first")
    strata = pd.qcut(ranks, q=min(6, len(outer_train_ids) // 5), labels=False, duplicates="drop")
    train_ids, validation_ids = train_test_split(
        np.asarray(outer_train_ids, dtype=np.int64),
        test_size=0.15,
        random_state=base_config.seed + fold,
        stratify=strata.to_numpy(),
    )
    train_engine_ids = tuple(sorted(int(value) for value in train_ids))
    validation_engine_ids = tuple(sorted(int(value) for value in validation_ids))
    training = labeled[labeled.engine_id.isin(train_engine_ids)].copy()
    validation = labeled[labeled.engine_id.isin(validation_engine_ids)].copy()
    feature_names = _model_feature_names(
        taxonomy, labeled, training, base_config.data.variance_threshold
    )
    taxonomy.validate_model_feature_coverage(feature_names)
    fold_taxonomy = taxonomy.fit_training_bounds(training, columns=feature_names)
    fold_taxonomy.validate_bounds_against_observed(training, columns=feature_names)
    scaler = fit_feature_scaler(training, feature_names)
    x_train = scaler.transform(training[list(feature_names)])
    y_train = training.failure_label.to_numpy(dtype=np.int64)
    x_validation = scaler.transform(validation[list(feature_names)])
    y_validation = validation.failure_label.to_numpy(dtype=np.int64)
    fold_seed = base_config.seed + fold
    fold_config = base_config.model_copy(
        update={
            "seed": fold_seed,
            "evaluation": base_config.evaluation.model_copy(
                update={"random_seed": fold_seed}
            ),
        }
    )
    estimator = _build_estimator(fold_config, "xgb")
    estimator.fit(x_train, y_train, validation_data=(x_validation, y_validation))
    validation_before = estimator.predict_proba(x_validation)
    calibrator = fit_probability_calibrator(
        validation_before,
        y_validation,
        fold_config.model.calibration_method,
    )
    surrogate = _build_estimator(fold_config, "mlp")
    train_teacher = estimator.predict_proba(x_train)
    validation_teacher = validation_before
    surrogate.fit_distillation(
        x_train, train_teacher, (x_validation, validation_teacher)
    )
    resolved_bounds = {
        name: (
            float(fold_taxonomy.feature_by_name()[name].bounds.minimum),
            float(fold_taxonomy.feature_by_name()[name].bounds.maximum),
        )
        for name in feature_names
    }
    resolved_rates = {
        name: float(item.max_change_per_step)
        for name, item in fold_taxonomy.actuator_constraints.items()
    }
    split_metrics: dict[str, Any] = {
        "dataset": fold_config.data.dataset,
        "horizon_H": fold_config.horizon_H,
        "split_engines": {
            "train": list(train_engine_ids),
            "validation": list(validation_engine_ids),
        },
        "calibration": {"fit_engine_ids": list(validation_engine_ids)},
    }
    bundle = ModelBundle(
        estimator=estimator,
        scaler=scaler,
        feature_names=feature_names,
        training_engine_ids=train_engine_ids,
        model_type="xgb",
        seed=fold_seed,
        calibrator=calibrator,
        surrogate=surrogate,
        config_hash=_configuration_hash(fold_config, "xgb"),
        git_commit=_commit(),
        metrics=split_metrics,
        resolved_bounds=resolved_bounds,
        resolved_rate_limits=resolved_rates,
    )
    fold_taxonomy = fold_taxonomy.with_resolved_bounds(resolved_bounds, resolved_rates)
    coupling = SensorCouplingModel.fit(
        labeled,
        fold_taxonomy,
        training_engine_ids=train_engine_ids,
        failure_horizon=fold_config.horizon_H,
        seed=fold_seed,
    )
    mahalanobis = fit_mahalanobis_validator(
        training, bundle, train_engine_ids, fold_config
    )
    held_out = set(held_out_engine_ids)
    calibration_ids = set(
        int(value) for value in split_metrics["calibration"]["fit_engine_ids"]
    )
    fitted_ids = {
        "model": set(bundle.training_engine_ids),
        "scaler": set(scaler.training_engine_ids),
        "coupling": set(coupling.training_engine_ids),
        "mahalanobis": set(mahalanobis.training_engine_ids),
        "calibrator": calibration_ids,
    }
    contaminated = {
        source: sorted(held_out & engine_ids)
        for source, engine_ids in fitted_ids.items()
        if held_out & engine_ids
    }
    if contaminated:
        raise ValueError(
            f"grouped CV fold {fold} has held-out engine leakage: {contaminated}"
        )
    if any(fitted_ids[name] != set(train_engine_ids) for name in ("model", "scaler", "coupling", "mahalanobis")):
        raise ValueError(f"grouped CV fold {fold} fit artifacts disagree on training engines")
    if calibration_ids != set(validation_engine_ids):
        raise ValueError(f"grouped CV fold {fold} calibrator did not use validation engines only")
    artifact_dir = OUTPUT_ROOT / "grouped-cv" / f"fold-{fold}"
    save_model_bundle(bundle, artifact_dir / "model.joblib")
    save_mahalanobis_validator(mahalanobis, artifact_dir / "mahalanobis.joblib")
    coupling.save(artifact_dir / "coupling.joblib")
    return PrescriptXAIEngine(fold_config, fold_taxonomy, bundle, mahalanobis, coupling)


def _run_grouped_cv(
    base_engine: PrescriptXAIEngine,
    labeled: pd.DataFrame,
    taxonomy: FeatureTaxonomy,
    *,
    sample_size: int,
    seed: int,
) -> dict[str, Any]:
    """Fit five grouped folds, then evaluate a deterministic pooled OOF alert sample."""
    assignments = _fold_engine_ids(labeled, folds=5, seed=seed)
    folds: list[dict[str, Any]] = []
    oof_alerts: list[pd.DataFrame] = []
    fold_engines: dict[int, PrescriptXAIEngine] = {}
    for fold_number, held_out_ids in enumerate(assignments, start=1):
        fold_engine = _fit_oof_engine(
            labeled,
            base_engine.config,
            taxonomy,
            held_out_ids,
            fold=fold_number,
        )
        fold_engines[fold_number] = fold_engine
        held_out = labeled[labeled.engine_id.isin(held_out_ids)].copy()
        held_out["_risk_before"] = fold_engine.model.predict_risk(
            held_out[list(fold_engine.model.feature_names)]
        )
        alerts = _alert_rows(fold_engine, held_out)
        alerts["_outer_fold"] = fold_number
        oof_alerts.append(alerts)
        folds.append(
            {
                "fold": fold_number,
                "held_out_engine_ids": list(held_out_ids),
                "alert_rows": len(alerts),
                "training_engine_ids": list(fold_engine.model.training_engine_ids),
                "calibration_engine_ids": list(
                    fold_engine.model.metrics.get("calibration", {}).get("fit_engine_ids", [])
                    if fold_engine.model.metrics
                    else []
                ),
                "held_out_overlap_check": False,
            }
        )
    all_alerts = pd.concat(oof_alerts, ignore_index=True) if oof_alerts else labeled.iloc[:0]
    take = min(sample_size, len(all_alerts))
    rng = np.random.default_rng(seed)
    positions = np.sort(rng.choice(len(all_alerts), size=take, replace=False)) if take else []
    sampled = all_alerts.iloc[positions].copy()
    results_by_protocol: dict[str, Any] = {}
    for protocol, d_max in (("v1", 5.0), ("v2", D_MAX_V2)):
        records: list[EvaluationRecord] = []
        for fold_number, group in sampled.groupby("_outer_fold", sort=True):
            fold_engine = _engine_with_settings(
                fold_engines[int(fold_number)], mahalanobis_max=d_max, max_queries=len(group) + 1
            )
            records.extend(evaluate_states(fold_engine, group.drop(columns=["_outer_fold"])).records)
        results_by_protocol[protocol] = {
            "population": "seeded sample of grouped out-of-fold alert states",
            "sampled_query_count": len(sampled),
            "sampled_engine_count": int(sampled.engine_id.nunique()) if len(sampled) else 0,
            "protocol_version": protocol,
            "D_max": d_max,
            "k_max": base_engine.config.recourse.max_changed_features,
            "K": base_engine.config.recourse.rate_horizon_steps,
            "effective_configuration_sha256": _config_hash(
                _engine_with_settings(base_engine, mahalanobis_max=d_max).config
            ),
            "per_fold_effective_configuration_sha256": {
                str(fold): _config_hash(fold_engine.config)
                for fold, fold_engine in fold_engines.items()
            },
            "effective_solver_settings": _effective_solver_settings(tuple(records)),
            "records": records,
            "outcomes": _population_outcomes(
                _engine_with_settings(base_engine, mahalanobis_max=d_max),
                sampled.drop(columns=["_outer_fold"]),
                tuple(records),
                seed=seed + (0 if protocol == "v1" else 10),
            ),
        }
    return {
        "folds": folds,
        "all_oof_alert_rows": len(all_alerts),
        "all_oof_engine_count": int(all_alerts.engine_id.nunique()) if len(all_alerts) else 0,
        "sampled_oof_rows": sampled.drop(columns=["_outer_fold"]).to_dict(orient="records"),
        "by_protocol": results_by_protocol,
    }


def _official_test_frame(engine: PrescriptXAIEngine, archive: Any) -> pd.DataFrame:
    """Build official-test RUL labels and namespace IDs to keep train/test identities distinct."""
    official = to_model_frame(archive.test)
    last_cycles = archive.test.groupby("unit_id").cycle.max()
    rul_by_unit = dict(zip(archive.test_rul.unit_id, archive.test_rul.rul, strict=True))
    official["rul"] = [
        float(rul_by_unit[int(unit)] + last_cycles[int(unit)] - cycle)
        for unit, cycle in zip(official.engine_id, official.cycle, strict=True)
    ]
    official["failure_label"] = (official.rul <= engine.config.horizon_H).astype("int8")
    # C-MAPSS train and official test unit IDs are separate source namespaces.
    official["engine_id"] = official.engine_id.astype(np.int64) + 10_000
    return official


def _coupling_candidate_diagnostics(records: tuple[EvaluationRecord, ...]) -> dict[str, Any]:
    """Summarize dependent residual-threshold exceedances from actual returned candidates."""
    measured = [
        record
        for record in records
        if record.dependent_sensor_count is not None
        and record.dependent_residual_violation_count is not None
    ]

    def summarize(candidates: list[EvaluationRecord], *, seed: int) -> dict[str, Any]:
        denominator = sum(int(record.dependent_sensor_count or 0) for record in candidates)
        violations = sum(
            int(record.dependent_residual_violation_count or 0) for record in candidates
        )
        candidate_violations = sum(
            int((record.dependent_residual_violation_count or 0) > 0)
            for record in candidates
        )
        return {
            "candidate_count": len(candidates),
            "any_dependent_over_tier4_threshold": {
                "count": candidate_violations,
                "rate": candidate_violations / len(candidates) if candidates else None,
                "engine_bootstrap_ci": (
                    _bootstrap(
                        pd.DataFrame({"engine_id": [item.engine_id for item in candidates]}),
                        [bool(item.dependent_residual_violation_count) for item in candidates],
                        seed=seed,
                    )
                    if candidates
                    else None
                ),
            },
            "dependent_sensor_checks_over_threshold": {
                "count": violations,
                "denominator": denominator,
                "rate": violations / denominator if denominator else None,
            },
        }

    returned = [record for record in measured if record.recourse_feasible]
    return {
        "attempted_optimizer_candidates": summarize(measured, seed=4_129),
        "returned_counterfactuals": summarize(returned, seed=4_130),
    }


def _strata_table(
    engine: PrescriptXAIEngine,
    rows: pd.DataFrame,
    records: tuple[EvaluationRecord, ...],
    *,
    seed: int,
) -> dict[str, Any]:
    """Recompute risk, RUL, and life-fraction strata for a named population."""
    outcomes = _population_outcomes(
        engine, rows, records, seed=seed, include_frame=True
    )["_raw_outcomes"]
    groups: dict[str, dict[str, pd.Index]] = {
        "risk_band": {
            "0.80-0.85": outcomes.index[(outcomes.initial_risk >= 0.80) & (outcomes.initial_risk < 0.85)],
            "0.85-0.90": outcomes.index[(outcomes.initial_risk >= 0.85) & (outcomes.initial_risk < 0.90)],
            "0.90-0.95": outcomes.index[(outcomes.initial_risk >= 0.90) & (outcomes.initial_risk < 0.95)],
            "0.95-1.00": outcomes.index[(outcomes.initial_risk >= 0.95) & (outcomes.initial_risk <= 1.0)],
        },
        "rul_bucket": {
            "0-10": outcomes.index[outcomes.rul <= 10],
            "11-20": outcomes.index[(outcomes.rul > 10) & (outcomes.rul <= 20)],
            "21-30": outcomes.index[(outcomes.rul > 20) & (outcomes.rul <= 30)],
            ">30": outcomes.index[outcomes.rul > 30],
        },
    }
    life_fraction = outcomes.cycle.to_numpy(dtype=float) / np.maximum(
        outcomes.cycle.to_numpy(dtype=float) + outcomes.rul.to_numpy(dtype=float), 1.0
    )
    groups["life_fraction"] = {
        "<0.70": outcomes.index[life_fraction < 0.70],
        "0.70-0.80": outcomes.index[(life_fraction >= 0.70) & (life_fraction < 0.80)],
        "0.80-0.90": outcomes.index[(life_fraction >= 0.80) & (life_fraction < 0.90)],
        "0.90-1.00": outcomes.index[life_fraction >= 0.90],
    }
    strata_results: dict[str, Any] = {}
    for family, entries in groups.items():
        strata_results[family] = {}
        for label, indexes in entries.items():
            group = outcomes.loc[indexes]
            if group.empty:
                strata_results[family][label] = {"n": 0, "engine_count": 0}
                continue
            strata_results[family][label] = {
                "n": len(group),
                "engine_count": int(group.engine_id.nunique()),
                "model_valid": _bootstrap(
                    group[["engine_id"]], group.model_valid.to_list(), seed=seed + len(strata_results[family]) + 1
                ),
                "tier2_all_queries": _bootstrap(
                    group[["engine_id"]], group.tier2.to_list(), seed=seed + len(strata_results[family]) + 2
                ),
                "joint_success": _bootstrap(
                    group[["engine_id"]], group.joint.to_list(), seed=seed + len(strata_results[family]) + 3
                ),
            }
    return strata_results


def _oracle_for_failed_state(
    engine: PrescriptXAIEngine,
    original: dict[str, float],
    production: EvaluationRecord,
    *,
    grid_points: int,
) -> dict[str, Any]:
    """Compare a failed result to the union of fine/coarse grids and traced solver outputs."""
    controls = engine.taxonomy.active_controllable_feature_names(engine.model.feature_names)
    feature_names = engine.model.feature_names
    scales = dict(zip(feature_names, engine.model.scaler.scaler.scale_, strict=True))
    lower: list[float] = []
    upper: list[float] = []
    current: list[float] = []
    control_scales: list[float] = []
    for name in controls:
        value = float(original[name])
        scale = float(scales[name])
        raw_lower, raw_upper = allowed_interval(
            value,
            engine.taxonomy.actuator_constraints[name],
            horizon_steps=engine.config.recourse.rate_horizon_steps,
        )
        scaled_lower = max(
            (raw_lower - value) / scale, -engine.config.recourse.max_scaled_distance
        )
        scaled_upper = min(
            (raw_upper - value) / scale, engine.config.recourse.max_scaled_distance
        )
        lower.append(scaled_lower)
        upper.append(scaled_upper)
        current.append(value)
        control_scales.append(scale)
    lower_array = np.asarray(lower, dtype=np.float64)
    upper_array = np.asarray(upper, dtype=np.float64)
    max_k = engine.config.recourse.max_changed_features
    coarse = bounded_sparse_delta_grid(
        lower_array,
        upper_array,
        max_changed_features=max_k,
        grid_points=engine.config.recourse.true_model_grid_points,
        change_tolerance=engine.config.recourse.change_tolerance,
    )
    fine = bounded_sparse_delta_grid(
        lower_array,
        upper_array,
        max_changed_features=max_k,
        grid_points=grid_points,
        change_tolerance=engine.config.recourse.change_tolerance,
    )
    vectors: dict[tuple[float, ...], np.ndarray] = {}
    for delta in np.vstack([coarse, fine]):
        vectors[tuple(np.round(delta, 12))] = delta
    # Explicitly include every terminal optimizer candidate and final returned state.
    trace_engine = _engine_with_settings(
        engine,
        recourse_updates={"record_candidate_trace": True, "search_mode": "thorough"},
        max_queries=1,
    )
    trace_result = trace_engine.recommend(original)
    replay_matches_production = (
        trace_result.optimization.state == dict(production.candidate_state)
        and trace_result.optimization.final_risk == production.final_risk
    )
    traced_states = list(trace_result.optimization.search_candidate_states)
    traced_states.append(dict(production.candidate_state))
    trace_rows = [
        np.asarray([state[name] for name in feature_names], dtype=np.float64)
        for state in traced_states
    ]
    raw_rows: list[np.ndarray] = []
    raw_initial = np.asarray([original[name] for name in feature_names], dtype=np.float64)
    control_positions = np.asarray([feature_names.index(name) for name in controls], dtype=np.int64)
    ordered_vectors = list(vectors.values())
    for start in range(0, len(ordered_vectors), 4_000):
        delta_batch = np.asarray(ordered_vectors[start : start + 4_000], dtype=np.float64)
        batch = np.repeat(raw_initial[None, :], len(delta_batch), axis=0)
        batch[:, control_positions] = np.asarray(current)[None, :] + delta_batch * np.asarray(control_scales)[None, :]
        if engine.coupling is not None:
            batch = engine.coupling.propagate_batch(
                batch, feature_names, reference_state=raw_initial
            )
        raw_rows.extend(batch)
    raw_rows.extend(trace_rows)
    if not raw_rows:
        return {
            "candidate_count": 0,
            "verified_candidate_set_superset": False,
            "classification": "no_candidates",
            "global_infeasibility_certified": False,
        }
    candidate_matrix = np.asarray(raw_rows, dtype=np.float64)
    unique_rows = np.unique(np.round(candidate_matrix, decimals=12), axis=0)
    risks = engine.model.predict_risk(pd.DataFrame(unique_rows, columns=feature_names))
    scaled = engine.model.scaler.transform(pd.DataFrame(unique_rows, columns=feature_names))
    dm = engine.mahalanobis.distance_batch(
        scaled, frozen_operating_settings=frozen_settings(engine.mahalanobis, original)
    )
    safe_idx = np.flatnonzero(risks <= engine.config.model.safe_threshold)
    plausible_idx = safe_idx[dm[safe_idx] <= engine.mahalanobis.max_distance]
    any_joint = False
    for index in plausible_idx:
        candidate_delta = {
            name: float(unique_rows[index, position] - raw_initial[position])
            for position, name in enumerate(feature_names)
        }
        changed_control_count = sum(
            abs(candidate_delta[name] / scales[name])
            > engine.config.recourse.change_tolerance
            for name in controls
        )
        scaled_control_distance = max(
            (
                abs(candidate_delta[name]) / scales[name]
                for name in controls
            ),
            default=0.0,
        )
        if (
            changed_control_count > engine.config.recourse.max_changed_features
            or scaled_control_distance > engine.config.recourse.max_scaled_distance + 1e-12
            or any(
                abs(candidate_delta[name]) > engine.config.recourse.change_tolerance
                for name in feature_names
                if name not in controls and name not in engine.coupling.dependent_features
            )
        ):
            continue
        candidate = dict(original)
        candidate.update(
            {name: float(unique_rows[index, position]) for position, name in enumerate(feature_names)}
        )
        if not validate_engineering(
            original,
            candidate,
            engine.taxonomy,
            horizon_steps=engine.config.recourse.rate_horizon_steps,
        ).valid:
            continue
        if validate_sensor_coupling(candidate, engine.taxonomy, engine.coupling).valid:
            any_joint = True
            break
    production_joint = bool(
        production.model_valid
        and production.recourse_feasible
        and production.tier2_plausible
        and production.tier3_engineering_valid
        and production.tier4_coupling_valid
    )
    if not replay_matches_production:
        classification = "superset_verification_failed"
    elif any_joint and not production_joint:
        classification = "search_failure_candidate_found"
    else:
        classification = "no_candidate_found_within_verified_search_superset"
    return {
        "candidate_count": len(unique_rows),
        "coarse_production_grid_count": len(coarse),
        "fine_grid_count": len(fine),
        "traced_terminal_solver_candidates": len(traced_states),
        "verified_candidate_set_superset": replay_matches_production,
        "superset_scope": (
            "union of the configured production true-model grid, a denser true-model grid, "
            "every traced terminal optimizer candidate, and the returned production candidate"
        ),
        "production_joint_success": production_joint,
        "oracle_joint_candidate_found": any_joint,
        "classification": classification,
        "global_infeasibility_certified": False,
        "replay_matches_production_return": replay_matches_production,
        "closest_true_risk": float(np.min(risks)) if len(risks) else None,
        "safe_model_candidate_count": len(safe_idx),
        "safe_and_tier2_candidate_count": len(plausible_idx),
    }


def _oracle_diagnosis(
    engine: PrescriptXAIEngine,
    alert_rows: pd.DataFrame,
    records: tuple[EvaluationRecord, ...],
    *,
    seed: int,
) -> dict[str, Any]:
    """Classify a deterministic sample of at least sixty failed headline results."""
    indexed = _records_by_key(records)
    outcome_by_key = {
        _key(row): row
        for row in alert_rows.itertuples()
    }
    failed = [
        record
        for record in records
        if not (
            record.model_valid
            and record.recourse_feasible
            and record.tier2_plausible
            and record.tier3_engineering_valid
            and record.tier4_coupling_valid
        )
    ]
    if len(failed) < 60:
        selected = failed
    else:
        rng = np.random.default_rng(seed)
        positions = np.sort(rng.choice(len(failed), size=60, replace=False))
        selected = [failed[int(index)] for index in positions]
    results = []
    state_features = tuple(
        dict.fromkeys(
            name
            for group in engine.taxonomy.feature_groups.model_dump().values()
            for name in group["features"]
        )
    )
    for record in selected:
        row = outcome_by_key[(record.engine_id, record.cycle)]
        row_values = row._asdict()
        original = {name: float(row_values[name]) for name in state_features}
        result = _oracle_for_failed_state(
            engine,
            original,
            indexed[(record.engine_id, record.cycle)],
            grid_points=ORACLE_GRID_POINTS,
        )
        results.append({"engine_id": record.engine_id, "cycle": record.cycle, **result})
    counts = Counter(item["classification"] for item in results)
    return {
        "headline_failed_record_count": len(failed),
        "sampled_failure_count": len(results),
        "sampling_seed": seed,
        "counts": dict(counts),
        "global_true_infeasibility_certified_count": sum(
            bool(item["global_infeasibility_certified"]) for item in results
        ),
        "results": results,
    }


def _sensitivity_run(
    base_engine: PrescriptXAIEngine,
    sample_rows: pd.DataFrame,
    *,
    label: str,
    updates: dict[str, Any],
    d_max: float,
    seed: int,
) -> dict[str, Any]:
    """Run one one-factor sensitivity on the identical saved states."""
    run_engine = _engine_with_settings(
        base_engine,
        recourse_updates=updates,
        mahalanobis_max=d_max,
        max_queries=len(sample_rows) + 1,
    )
    run = evaluate_states(run_engine, sample_rows)
    metrics = _population_outcomes(run_engine, sample_rows, run.records, seed=seed)
    return {
        "label": label,
        "effective_configuration_sha256": _config_hash(run_engine.config),
        "protocol_version": "v1" if d_max == 5.0 else "v2",
        "D_max": d_max,
        "k_max": run_engine.config.recourse.max_changed_features,
        "K": run_engine.config.recourse.rate_horizon_steps,
        "search_mode": run_engine.config.recourse.search_mode,
        "population": f"seeded saved-state sensitivity subset, n={len(sample_rows)}",
        "effective_solver_settings": _effective_solver_settings(run.records),
        "outcomes": metrics,
        "records": run.records,
    }


def _evaluate_holdout_protocols(
    engine: PrescriptXAIEngine,
    test_alerts: pd.DataFrame,
    headline_rows: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, tuple[EvaluationRecord, ...]]]:
    """Evaluate frozen v1 and v2 on the same all-alert holdout population."""
    holdout: dict[str, Any] = {}
    holdout_records: dict[str, tuple[EvaluationRecord, ...]] = {}
    first_rows = _first_alert_rows(test_alerts)
    headline_keys = {_key(row) for row in headline_rows.itertuples()}
    for protocol, d_max in (("v1", 5.0), ("v2", D_MAX_V2)):
        run_engine = _engine_with_settings(
            engine, mahalanobis_max=d_max, max_queries=len(test_alerts) + 1
        )
        run = evaluate_states(run_engine, test_alerts)
        holdout_records[protocol] = run.records
        record_index = _records_by_key(run.records)
        first_records = tuple(
            record_index[key]
            for key in (_key(row) for row in first_rows.itertuples())
            if key in record_index
        )
        headline_records = tuple(
            record for record in run.records
            if (record.engine_id, record.cycle) in headline_keys
        )
        populations: dict[str, Any] = {}
        for name, rows, records in (
            ("headline_sample", headline_rows, headline_records),
            ("all_alert_states", test_alerts, run.records),
            ("first_alert_per_engine", first_rows, first_records),
        ):
            populations[name] = _population_outcomes(
                run_engine,
                rows,
                records,
                seed=engine.config.seed + (0 if protocol == "v1" else 50),
            )
            populations[name]["strata"] = _strata_table(
                run_engine, rows, records, seed=engine.config.seed + 100
            )
            populations[name]["provenance"] = build_evaluation_provenance(
                run_engine, rows
            )
        holdout[protocol] = {
            "effective_configuration_sha256": _config_hash(run_engine.config),
            "protocol_version": protocol,
            "D_max": d_max,
            "k_max": run_engine.config.recourse.max_changed_features,
            "K": run_engine.config.recourse.rate_horizon_steps,
            "effective_solver_settings": _effective_solver_settings(run.records),
            "summary": run.summary.to_dict(),
            "infeasible_high_risk_state_count": run.infeasible_high_risk_states,
            **populations,
        }
    return holdout, holdout_records


def _evaluate_sensitivity(
    engine: PrescriptXAIEngine,
    headline_rows: pd.DataFrame,
    headline_records: tuple[EvaluationRecord, ...],
    baseline_configuration_hash: str,
) -> tuple[list[dict[str, Any]], tuple[EvaluationRecord, ...]]:
    """Run the fixed seeded one-factor sensitivity set on a shared 60-state sample."""
    headline_lookup = _records_by_key(headline_records)
    sensitivity_size = min(SENSITIVITY_SAMPLE, len(headline_rows))
    rng = np.random.default_rng(engine.config.seed + 1)
    positions = np.sort(
        rng.choice(len(headline_rows), size=sensitivity_size, replace=False)
    ) if sensitivity_size else np.asarray([], dtype=np.int64)
    rows = headline_rows.iloc[positions].copy()
    baseline_records = tuple(
        headline_lookup[key]
        for key in (_key(row) for row in rows.itertuples())
        if key in headline_lookup
    )
    sensitivity: list[dict[str, Any]] = [
        {
            "label": "baseline-k3-dist4-K1-Dmax5-thorough",
            "effective_configuration_sha256": baseline_configuration_hash,
            "protocol_version": "v1",
            "D_max": 5.0,
            "k_max": 3,
            "K": 1,
            "search_mode": "thorough",
            "population": f"seeded saved-state sensitivity subset, n={len(rows)}",
            "effective_solver_settings": _effective_solver_settings(baseline_records),
            "outcomes": _population_outcomes(
                engine, rows, baseline_records, seed=engine.config.seed + 300
            ),
            "records": baseline_records,
        }
    ]
    variants = [
        ("k5-only", {"max_changed_features": 5}, 5.0),
        ("max-distance-2-only", {"max_scaled_distance": 2.0}, 5.0),
        ("max-distance-6-only", {"max_scaled_distance": 6.0}, 5.0),
        ("K2-only", {"rate_horizon_steps": 2}, 5.0),
        ("K3-only", {"rate_horizon_steps": 3}, 5.0),
        ("K5-only", {"rate_horizon_steps": 5}, 5.0),
        ("K10-only", {"rate_horizon_steps": 10}, 5.0),
        ("Dmax8-only", {}, D_MAX_V2),
        ("fast-mode-only", {"search_mode": "fast"}, 5.0),
    ]
    fast_records: tuple[EvaluationRecord, ...] = ()
    for index, (label, updates, d_max) in enumerate(variants, start=1):
        result = _sensitivity_run(
            engine,
            rows,
            label=label,
            updates=updates,
            d_max=d_max,
            seed=engine.config.seed + 300 + index,
        )
        sensitivity.append(result)
        if label == "fast-mode-only":
            fast_records = tuple(result["records"])
    return sensitivity, fast_records


def _surrogate_diagnostics(engine: PrescriptXAIEngine, heldout: pd.DataFrame) -> dict[str, Any]:
    """Measure surrogate fidelity on actual held-out engine telemetry."""
    if engine.model.surrogate is None or engine.model.calibrator is None:
        return {"available": False, "reason": "bundle has no fitted surrogate or calibrator"}
    scaled = engine.model.scaler.transform(heldout[list(engine.model.feature_names)])
    surrogate_raw = engine.model.surrogate.predict_proba(scaled)
    surrogate_risk = engine.model.calibrator.transform(surrogate_raw)
    true_risk = engine.model.predict_risk(heldout[list(engine.model.feature_names)])
    false_safe = (surrogate_risk <= engine.config.model.safe_threshold) & (
        true_risk > engine.config.model.safe_threshold
    )
    surrogate_safe_count = int(np.sum(surrogate_risk <= engine.config.model.safe_threshold))
    fidelity = {
        "count": int(len(heldout)),
        "false_safe_count": int(false_safe.sum()),
        "false_safe_rate_among_surrogate_safe": (
            float(false_safe.sum() / surrogate_safe_count) if surrogate_safe_count else None
        ),
        "mae": float(np.mean(np.abs(true_risk - surrogate_risk))),
        "rank_correlation": float(pd.Series(true_risk).corr(pd.Series(surrogate_risk), method="spearman")),
        "agreement_at_tau_safe": float(
            np.mean((true_risk <= engine.config.model.safe_threshold) == (surrogate_risk <= engine.config.model.safe_threshold))
        ),
        "agreement_at_tau_danger": float(
            np.mean((true_risk >= engine.config.model.danger_threshold) == (surrogate_risk >= engine.config.model.danger_threshold))
        ),
    }
    return {"available": True, **fidelity}


def _write_k_curve(sensitivity: list[dict[str, Any]]) -> None:
    """Write a small SVG curve from measured K sensitivity rows."""
    points = [
        item
        for item in sensitivity
        if item["label"] == "baseline-k3-dist4-K1-Dmax5-thorough"
        or item["label"].startswith("K")
    ]
    points.sort(key=lambda item: int(item["K"]))
    if not points:
        raise ValueError("cannot render K curve without measured horizon points")
    width, height = 900, 520
    left, right, top, bottom = 86, 28, 44, 72
    plot_width, plot_height = width - left - right, height - top - bottom
    k_values = [int(item["K"]) for item in points]
    x_min, x_max = min(k_values), max(k_values)
    if x_min == x_max:
        x_max = x_min + 1

    def x_position(value: int) -> float:
        return left + (value - x_min) / (x_max - x_min) * plot_width

    def y_position(value: float) -> float:
        return top + (1.0 - min(1.0, max(0.0, value))) * plot_height

    series = (
        ("Tier 1 model validity", "#1759a6", "model_valid_all_queries"),
        ("Tier 2 plausibility", "#c45318", "tier2_plausible_all_queries"),
        ("Joint Tiers 2–4", "#328453", "tiers2_to4_joint_all_queries"),
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="450" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">Measured Phase 4 validity by assumed intervention horizon</text>',
    ]
    for tick in np.linspace(0.0, 1.0, 6):
        y = y_position(float(tick))
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#dddddd"/>')
        svg.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick:.1f}</text>')
    svg.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333333"/>',
            f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#333333"/>',
            f'<text x="{left + plot_width/2:.1f}" y="{height-20}" text-anchor="middle" font-family="sans-serif" font-size="14">Assumed intervention horizon K (steps)</text>',
            f'<text x="20" y="{top + plot_height/2:.1f}" transform="rotate(-90 20 {top + plot_height/2:.1f})" text-anchor="middle" font-family="sans-serif" font-size="14">Rate</text>',
        ]
    )
    for value in k_values:
        x = x_position(value)
        svg.append(f'<line x1="{x:.1f}" y1="{height-bottom}" x2="{x:.1f}" y2="{height-bottom+5}" stroke="#333333"/>')
        svg.append(f'<text x="{x:.1f}" y="{height-bottom+22}" text-anchor="middle" font-family="sans-serif" font-size="12">{value}</text>')
    for index, (label, color, metric_key) in enumerate(series):
        coords = []
        for item in points:
            estimate = item["outcomes"]["metrics"][metric_key]["estimate"]
            if estimate is not None:
                coords.append((x_position(int(item["K"])), y_position(float(estimate))))
        if coords:
            polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
            svg.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="3"/>')
            svg.extend(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}"/>'
                for x, y in coords
            )
        legend_y = top + 18 * index
        svg.append(f'<line x1="{width-220}" y1="{legend_y}" x2="{width-198}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<text x="{width-190}" y="{legend_y+4}" font-family="sans-serif" font-size="12">{label}</text>')
    svg.append("</svg>")
    K_CURVE_PATH.write_text("\n".join(svg), encoding="utf-8")


def _render_final_report(document: dict[str, Any]) -> str:
    """Render the measured closure evidence into a compact Markdown report."""
    def format_number(value: Any, digits: int = 3) -> str:
        return "—" if value is None else f"{float(value):.{digits}f}"

    def format_ci(metric: dict[str, Any], digits: int = 3) -> str:
        if metric.get("lower") is None or metric.get("upper") is None:
            return "—"
        return f"[{format_number(metric['lower'], digits)}, {format_number(metric['upper'], digits)}]"

    def format_rate_ci(metric: dict[str, Any] | None) -> str:
        if metric is None:
            return "—"
        return f"{format_number(metric.get('estimate'))} {format_ci(metric)}"

    lines = [
        "# Phase 4 final evaluation",
        "",
        "| Run metadata | Value |",
        "|---|---|",
        f"| Run ID | `{document['run_id']}` |",
        f"| Run timestamp UTC | {document['run_timestamp_utc']} |",
        f"| Evaluation/oracle source commit | `{document['source_commit']}` |",
        f"| Protocol v2 freeze commit | `{document['protocol_v2_freeze_commit']}` |",
        f"| Protocol document SHA-256 | `{document['protocol_v2_sha256']}` |",
        f"| Holdout and sensitivity measurement source | `{document['measurement_source_commits']['holdout_v1_v2']}` |",
        f"| Grouped OOF and official-test measurement source | `{document['measurement_source_commits']['grouped_cv_oof']}` |",
        "",
        "## Design targets and measured values",
        "",
        "Confidence intervals are 95% percentile bootstrap intervals resampling whole engines. The engine count and query count are printed per row. Tier 1 model validity and Tiers 2–4 physical checks are reported separately.",
        "",
    ]
    for protocol in ("v1", "v2"):
        for population_name in ("headline_sample", "all_alert_states", "first_alert_per_engine"):
            population = document["holdout_test"][protocol][population_name]
            config_hash = document["holdout_test"][protocol]["effective_configuration_sha256"]
            lines.extend(
                [
                    f"### {protocol.upper()} — {population_name.replace('_', ' ')}",
                    "",
                    f"Run ID `{document['run_id']}`; config SHA-256 `{config_hash}`; protocol {protocol}; `k_max={document['holdout_test'][protocol]['k_max']}`; `K={document['holdout_test'][protocol]['K']}`; `D_max={document['holdout_test'][protocol]['D_max']}`; population `{population_name}`.",
                    "",
                    "| Metric | Target | Measured | Engine-bootstrap 95% CI | Engines / queries | Gap to target |",
                    "|---|---:|---:|---:|---:|---:|",
                ]
            )
            rows = _population_target_rows(population)
            for row in rows:
                digits = 1 if "p95 ms" in row["metric"] else 3
                ci = format_ci(row, digits)
                gap = "—" if row["gap_to_target"] is None else f"{row['gap_to_target']:+.3f}"
                lines.append(
                    f"| {row['metric']} | {row['target']} | {format_number(row['estimate'], digits)} | {ci} | {row['engine_count']} / {row['n']} | {gap} |"
                )
            lines.append("")
    lines.extend(
        [
            "## Triage, risk-reduction histogram, and end-of-life concentration",
            "",
            "All rates below use the named query population; confidence intervals resample whole engines.",
            "",
        ]
    )
    for protocol in ("v1", "v2"):
        for population_name in ("headline_sample", "all_alert_states", "first_alert_per_engine"):
            population = document["holdout_test"][protocol][population_name]
            lines.extend(
                [
                    f"### {protocol.upper()} — {population_name.replace('_', ' ')}",
                    "",
                    f"Run `{document['run_id']}`; config `{document['holdout_test'][protocol]['effective_configuration_sha256']}`; protocol {protocol}; k={document['holdout_test'][protocol]['k_max']}; K={document['holdout_test'][protocol]['K']}; Dmax={document['holdout_test'][protocol]['D_max']}; queries={population['query_count']}; engines={population['engine_count']}.",
                    "",
                    "| Triage group | Count | Rate [engine-bootstrap 95% CI] | Engines / queries |",
                    "|---|---:|---:|---:|",
                ]
            )
            for group_name, triage in population["triage"].items():
                ci = triage["ci"]
                lines.append(
                    f"| {group_name} | {triage['count']} | {format_number(triage['rate'])} {format_ci(ci)} | {ci['engine_count']} / {ci['n']} |"
                )
            lines.extend(
                [
                    "",
                    "| Risk reduction bin (risk before − risk after) | Count | Rate [engine-bootstrap 95% CI] | Engines / queries |",
                    "|---|---:|---:|---:|",
                ]
            )
            for bin_name, result in population["risk_reduction_histogram"]["bins"].items():
                ci = result["engine_bootstrap_ci"]
                lines.append(
                    f"| {bin_name} | {result['count']} | {format_number(result['rate'])} {format_ci(ci)} | {ci['engine_count']} / {ci['n']} |"
                )
            lines.extend(
                [
                    "",
                    "| Life stage | Queries | Engines | RECOVERABLE [95% CI] | PARTIAL [95% CI] | ESCALATE [95% CI] |",
                    "|---|---:|---:|---:|---:|---:|",
                ]
            )
            for life_stage, rates in population["end_of_life_concentration"].items():
                lines.append(
                    f"| {life_stage} | {rates['n']} | {rates['engine_count']} | {format_rate_ci(rates['recoverable_rate'])} | {format_rate_ci(rates['partial_rate'])} | {format_rate_ci(rates['escalate_rate'])} |"
                )
            lines.append("")
    lines.extend(
        [
            "## Protocol v2 fresh-engine checks",
            "",
            "| Population | Protocol | Run/config hash | k / K / Dmax | Queries / engines | Tier 1 validity [95% CI] | Tier 2 all queries [95% CI] | Joint Tiers 2–4 [95% CI] |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for population_name in ("grouped_cv_oof", "official_test"):
        for protocol in ("v1", "v2"):
            result = document[population_name]["by_protocol"][protocol]
            outcomes = result["outcomes"]
            metrics = outcomes["metrics"]
            config_hash = result["effective_configuration_sha256"]
            lines.append(
                f"| {population_name} | {protocol} | `{document['run_id']}` / `{config_hash}` | {result['k_max']} / {result['K']} / {result['D_max']:.1f} | {outcomes['query_count']} / {outcomes['engine_count']} | {format_number(metrics['model_valid_all_queries']['estimate'])} {format_ci(metrics['model_valid_all_queries'])} | {format_number(metrics['tier2_plausible_all_queries']['estimate'])} {format_ci(metrics['tier2_plausible_all_queries'])} | {format_number(metrics['tiers2_to4_joint_all_queries']['estimate'])} {format_ci(metrics['tiers2_to4_joint_all_queries'])} |"
            )
    lines.extend(["", "## K horizon and one-factor sensitivity", ""])
    lines.extend(
        [
            "K multiplies the observed training-engine one-step telemetry rate limit. K>1 is a horizon assumption, not measured actuator dynamics.",
            "",
            "![Measured validity and plausibility over intervention horizon K](phase4_k_curve.svg)",
            "",
            "| K | Tier 1 validity | Tier 2 plausibility | Joint Tiers 2–4 | Engines / queries |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    k_curve = [
        item
        for item in document["sensitivity"]
        if item["label"] == "baseline-k3-dist4-K1-Dmax5-thorough"
        or item["label"].startswith("K")
    ]
    for item in sorted(k_curve, key=lambda row: row["K"]):
        metrics = item["outcomes"]["metrics"]
        lines.append(
            f"| {item['K']} | {format_number(metrics['model_valid_all_queries']['estimate'])} | {format_number(metrics['tier2_plausible_all_queries']['estimate'])} | {format_number(metrics['tiers2_to4_joint_all_queries']['estimate'])} | {item['outcomes']['engine_count']} / {item['outcomes']['query_count']} |"
        )
    lines.append("")
    lines.extend(
        [
            "| Run ID / variant | Config SHA-256 | Protocol | k_max | K | D_max | Population | Tier 1 [95% CI] | Tier 2 [95% CI] | Joint [95% CI] | Optimization p95 ms [95% CI] | Engines |",
            "|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for sensitivity in document["sensitivity"]:
        outcomes = sensitivity["outcomes"]
        metrics = outcomes["metrics"]
        lines.append(
            f"| {document['run_id']} / {sensitivity['label']} | {sensitivity['effective_configuration_sha256']} | {sensitivity['protocol_version']} | {sensitivity['k_max']} | {sensitivity['K']} | {sensitivity['D_max']:.1f} | {sensitivity['population']} | {format_number(metrics['model_valid_all_queries']['estimate'])} {format_ci(metrics['model_valid_all_queries'])} | {format_number(metrics['tier2_plausible_all_queries']['estimate'])} {format_ci(metrics['tier2_plausible_all_queries'])} | {format_number(metrics['tiers2_to4_joint_all_queries']['estimate'])} {format_ci(metrics['tiers2_to4_joint_all_queries'])} | {format_number(outcomes['optimization_latency']['p95_ms'], 1)} {format_ci(outcomes['optimization_latency'], 1)} | {outcomes['engine_count']} |"
        )
    lines.extend(["", "## Diagnostic evidence", ""])
    lines.append("### Constraint ladder (headline k≤3 sample, 200 states)")
    ladder = document["constraint_ladder"]
    lines.extend(
        [
            "",
            "| Stage | Count | Total | Rate | Engine-bootstrap 95% CI | Engines |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for stage, result in ladder.items():
        if not isinstance(result, dict) or "count" not in result:
            continue
        ci = result["engine_bootstrap_ci"]
        lines.append(
            f"| {stage} | {result['count']} | {result['total']} | {result['rate']:.3f} | [{ci[0]:.3f}, {ci[1]:.3f}] | {result['engine_count']} |"
        )
    lines.extend(["", ladder["note"], ""])
    oracle = document["oracle"]
    lines.extend(
        [
            "",
            "### Reference-search classification",
            "",
            f"Failed headline results: {oracle['headline_failed_record_count']}; sampled: {oracle['sampled_failure_count']}; classifications: `{oracle['counts']}`. No global physical infeasibility is certified because a finite grid plus terminal solver outputs does not cover the continuous action space.",
            "",
            "### Coupling residuals",
            "",
            "| Dependent sensor | Engine-grouped OOF R² | Residual standard deviation |",
            "|---|---:|---:|",
        ]
    )
    for feature, score in document["coupling_fit"]["r2"].items():
        residual = document["coupling_fit"]["residual_std"][feature]
        lines.append(f"| {feature} | {score:.4f} | {residual:.5g} |")
    lines.extend(
        [
            "",
            "### Surrogate fidelity and candidate residual checks",
            "",
            f"Surrogate holdout diagnostics: `{document['surrogate']}`.",
            f"Tier 4 dependent residual threshold exceedances on headline candidates: `{document['coupling_candidates']}`.",
            "",
            "### Strata and triage",
            "",
            "## Interpretation and evidence level",
            "",
            "The measured validity is conditional on observationally derived one-step sensor-proxy rate limits and the sampled population. K>1 results multiply that telemetry rate limit and are assumptions, not validated actuator horizons. The classifier can be driven toward very low predicted risk by changing sensor proxies; Tier 1 alone is weak evidence. C-MAPSS contains no intervention outcomes, actuator commands, or validated counterfactual simulator, so the evidence is E1 (dataset/model and software evaluation) and does not reach E2 validated simulation or E3 operational validation. No RUL-extension claim is supported.",
            "",
        ]
    )
    for section_name, section in (
        ("Headline strata, k≤3", document["headline_strata_k3"]),
        ("k≤5 one-factor sensitivity strata", document["sensitivity_strata_k5_60_state_sample"]),
    ):
        lines.extend([f"### {section_name}", ""])
        for family, entries in section.items():
            lines.extend(
                [
                    f"**{family}**",
                    "",
                    "| Stratum | Queries | Engines | Tier 1 [95% CI] | Tier 2 [95% CI] | Joint [95% CI] |",
                    "|---|---:|---:|---:|---:|---:|",
                ]
            )
            for label, result in entries.items():
                if result.get("n", 0) == 0:
                    lines.append(f"| {label} | 0 | 0 | — | — | — |")
                    continue
                lines.append(
                    f"| {label} | {result['n']} | {result['engine_count']} | {format_number(result['model_valid']['estimate'])} {format_ci(result['model_valid'])} | {format_number(result['tier2_all_queries']['estimate'])} {format_ci(result['tier2_all_queries'])} | {format_number(result['joint_success']['estimate'])} {format_ci(result['joint_success'])} |"
                )
            lines.append("")
    history = document["historical_count_audit"]
    lines.extend(
        [
            "The full risk-reduction histograms, per-population triage rates, effective runtime settings, and historical count audit are also stored in the JSON run artifact.",
            "",
            "### Historical count-collision audit",
            "",
            "The archived diagnosis table reported 112/200 Tier 1, 106/200 Tier 2, and 87/200 joint. Its stated runtime settings were `k_max=5`, `max_scaled_distance=6`, 3 restarts, 100 iterations, and a 10-point true-model grid. The matching saved per-query run is unavailable, so the cause of that table cannot be established.",
            "",
            "The saved k3 artifact used `k_max=3`, `max_scaled_distance=4`, 1 restart, 25 iterations, and a 5-point grid; it records 135/200 Tier 1, 158/200 Tier 2, and 127/200 joint. The saved k5 artifact used the expanded settings above and records 174/200, 161/200, and 156/200. These saved artifacts do not show identical outcomes.",
            "",
            "`max_scaled_distance` is a per-feature scaled movement radius, not the Mahalanobis `D_max`; the archived expanded run retained Mahalanobis `D_max=5`. In the fresh one-factor experiment, changing only `k_max` from 3 to 5 changed Tier 1/Tier 2/joint rates from 0.533/0.517/0.383 to 0.833/0.733/0.717. Changing only the movement radius to 2 or 6 left those rates at 0.533/0.517/0.383. All successful headline actions obey `k_max=3`; the report records bound, rate, and support checks separately.",
            "",
            history["interpretation"],
            "",
        ]
    )
    return "\n".join(lines)


def run() -> dict[str, Any]:
    """Run headline, protocol, sensitivity, oracle, coupling, surrogate, and OOF evaluations."""
    base_config = load_config(CONFIG_PATH)
    if base_config.recourse.max_changed_features != 3 or base_config.validation.mahalanobis_max != 5.0:
        raise ValueError("the frozen headline profile must use k_max=3 and protocol-v1 D_max=5.0")
    if not PROTOCOL_PATH.is_file():
        raise FileNotFoundError("commit docs/phase4_protocol_v2.md before v2 evaluation")
    source_commit = _commit()
    engine = PrescriptXAIEngine.from_files(CONFIG_PATH, TAXONOMY_PATH)
    archive = load_cmapss_archive(
        engine.config.data.root / engine.config.data.archive_name,
        engine.config.data.dataset,
    )
    artifact_paths = [engine.config.artifacts.model, engine.config.artifacts.mahalanobis]
    if engine.taxonomy.coupling is not None:
        artifact_paths.append(
            engine.config.artifacts.model.parent
            / engine.taxonomy.coupling.artifact_name.format(
                subset=engine.config.data.dataset
            )
        )
    checkpoint_context_data = {
        "version": CHECKPOINT_VERSION,
        "config_hash": _config_hash(engine.config),
        "taxonomy_sha256": _sha256_file(TAXONOMY_PATH),
        "dataset_archive_sha256": _sha256_file(
            engine.config.data.root / engine.config.data.archive_name
        ),
        "protocol_sha256": _sha256_file(PROTOCOL_PATH),
        "artifact_sha256": {
            str(path): _sha256_file(path) for path in artifact_paths
        },
    }

    def context_hash(value: dict[str, Any]) -> str:
        """Hash stage inputs with deterministic JSON serialization."""
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    checkpoint_context = context_hash(checkpoint_context_data)
    compatible_holdout_context = context_hash(
        {
            **checkpoint_context_data,
            "source_commit": COMPATIBLE_HOLDOUT_SOURCE_COMMIT,
        }
    )
    compatible_holdout_checkpoints = {
        COMPATIBLE_HOLDOUT_SOURCE_COMMIT: compatible_holdout_context
    }
    if engine.coupling is not None:
        coupled_features = set(engine.coupling.predictor_features) | set(
            engine.coupling.dependent_features
        )
        if coupled_features - set(engine.model.feature_names):
            compatible_holdout_checkpoints = {}
    initial_checkpoint = next(
        (
            checkpoint
            for name in ("holdout", "sensitivity", "grouped-cv", "official-test")
            if (
                checkpoint := _read_checkpoint(
                    name,
                    checkpoint_context,
                    compatible_context_hashes=compatible_holdout_checkpoints,
                )
            ) is not None
        ),
        None,
    )
    run_id = (
        str(initial_checkpoint["run_id"])
        if initial_checkpoint is not None
        else datetime.now(UTC).strftime("phase4-%Y%m%dT%H%M%SZ")
    )
    labeled = add_training_labels(
        to_model_frame(archive.train),
        engine.config.data.rul_cap,
        engine.config.horizon_H,
    )
    splits = split_engines(
        labeled,
        engine.config.data.train_fraction,
        engine.config.data.validation_fraction,
        engine.config.data.test_fraction,
        engine.config.seed,
        lifetime_buckets=engine.config.data.lifetime_buckets,
    )
    model_metrics = engine.model.metrics or {}
    expected_train = set(int(value) for value in splits.train_engine_ids)
    expected_validation = set(int(value) for value in splits.validation_engine_ids)
    expected_test = set(int(value) for value in splits.test_engine_ids)
    recorded_split = model_metrics.get("split_engines", {})
    calibration_ids = set(
        int(value)
        for value in model_metrics.get("calibration", {}).get("fit_engine_ids", [])
    )
    if set(engine.model.training_engine_ids) != expected_train:
        raise ValueError("saved model training engines do not match the frozen engine split")
    if set(engine.model.scaler.training_engine_ids) != expected_train:
        raise ValueError("saved scaler was not fitted on the frozen training engines")
    if set(engine.mahalanobis.training_engine_ids) != expected_train:
        raise ValueError("saved Tier 2 validator was not fitted on the frozen training engines")
    if engine.coupling is None or set(engine.coupling.training_engine_ids) != expected_train:
        raise ValueError("saved coupling model was not fitted on the frozen training engines")
    if calibration_ids != expected_validation:
        raise ValueError("saved calibrator must be fitted on validation engines only")
    if recorded_split and (
        set(recorded_split.get("validation", [])) != expected_validation
        or set(recorded_split.get("test_holdout", [])) != expected_test
    ):
        raise ValueError("saved model split provenance disagrees with current engine split")
    test_alerts = _alert_rows(engine, splits.test)
    headline_rows = _sample_headline_rows(
        engine,
        test_alerts,
        sample_size=base_config.evaluation.max_queries,
        seed=base_config.evaluation.random_seed,
    )
    all_actionable = sum(
        _has_feasible_actuator_intervals(engine, row)
        for _, row in test_alerts.iterrows()
    )
    LOGGER.info(
        "FD001 holdout: alerts=%d, actionable=%d, headline_sample=%d, engines=%d",
        len(test_alerts),
        all_actionable,
        len(headline_rows),
        test_alerts.engine_id.nunique(),
    )

    # Protocol v1 and frozen v2 are evaluated on identical holdout alert states.
    holdout_checkpoint = _read_checkpoint(
        "holdout",
        checkpoint_context,
        compatible_context_hashes=compatible_holdout_checkpoints,
    )
    if holdout_checkpoint is None:
        holdout, holdout_records = _evaluate_holdout_protocols(
            engine, test_alerts, headline_rows
        )
        _write_checkpoint(
            "holdout",
            checkpoint_context,
            run_id,
            {"holdout": holdout, "records": holdout_records},
        )
    else:
        payload = holdout_checkpoint["payload"]
        holdout = payload["holdout"]
        holdout_records = payload["records"]
        LOGGER.info("Resumed Phase 4 holdout records from checkpoint")

    # All-alert and first-alert views are taken from the full run; the headline sample is fixed
    # in Protocol v1 and remains identical under v2.
    headline_records_v1 = tuple(
        record
        for record in holdout_records["v1"]
        if (record.engine_id, record.cycle) in {_key(row) for row in headline_rows.itertuples()}
    )
    # Saved-state one-factor sensitivity; all variants use the same seeded 60 headline cases.
    headline_lookup = _records_by_key(headline_records_v1)
    sensitivity_size = min(SENSITIVITY_SAMPLE, len(headline_rows))
    rng = np.random.default_rng(engine.config.seed + 1)
    sensitivity_positions = np.sort(
        rng.choice(len(headline_rows), size=sensitivity_size, replace=False)
    ) if sensitivity_size else np.asarray([], dtype=np.int64)
    sensitivity_rows = headline_rows.iloc[sensitivity_positions].copy()
    baseline_sample_records = tuple(
        headline_lookup[key]
        for key in (_key(row) for row in sensitivity_rows.itertuples())
        if key in headline_lookup
    )
    sensitivity_checkpoint = _read_checkpoint(
        "sensitivity",
        checkpoint_context,
        compatible_context_hashes=compatible_holdout_checkpoints,
    )
    if sensitivity_checkpoint is None:
        sensitivity, fast_records = _evaluate_sensitivity(
            engine,
            headline_rows,
            headline_records_v1,
            holdout["v1"]["effective_configuration_sha256"],
        )
        _write_checkpoint(
            "sensitivity",
            checkpoint_context,
            run_id,
            {"sensitivity": sensitivity, "fast_records": fast_records},
        )
    else:
        payload = sensitivity_checkpoint["payload"]
        sensitivity = payload["sensitivity"]
        fast_records = payload["fast_records"]
        LOGGER.info("Resumed Phase 4 sensitivity records from checkpoint")

    # FAST/THOROUGH exact candidate comparison on identical saved states.
    thorough_index = _records_by_key(baseline_sample_records)
    fast_index = _records_by_key(fast_records)
    shared_success = [
        key
        for key in thorough_index.keys() & fast_index.keys()
        if thorough_index[key].recourse_feasible and fast_index[key].recourse_feasible
    ]
    exact_match_count = sum(
        thorough_index[key].candidate_state == fast_index[key].candidate_state
        and thorough_index[key].final_risk == fast_index[key].final_risk
        for key in shared_success
    )

    # Protocol v2 and v1 candidate distance against the real alert and low-risk validation tails.
    validation_risk = engine.model.predict_risk(
        splits.validation[list(engine.model.feature_names)]
    )
    validation_distance = _distance_rows(engine, splits.validation)
    validation_alert_distances = validation_distance[
        validation_risk >= engine.config.model.danger_threshold
    ]
    validation_low_risk_distances = validation_distance[
        validation_risk < engine.config.model.danger_threshold
    ]
    low_risk_p95 = float(np.quantile(validation_low_risk_distances, 0.95, method="higher"))
    alert_p95 = (
        float(np.quantile(validation_alert_distances, 0.95, method="higher"))
        if len(validation_alert_distances)
        else None
    )
    dmax_tail: dict[str, Any] = {
        "validation_alert_state_count": len(validation_alert_distances),
        "validation_alert_engine_count": int(
            splits.validation.loc[
                validation_risk >= engine.config.model.danger_threshold, "engine_id"
            ].nunique()
        ),
        "validation_alert_Dm_p95_nearest_rank": alert_p95,
        "validation_low_risk_state_count": len(validation_low_risk_distances),
        "validation_low_risk_engine_count": int(
            splits.validation.loc[
                validation_risk < engine.config.model.danger_threshold, "engine_id"
            ].nunique()
        ),
        "validation_low_risk_Dm_p95_nearest_rank": low_risk_p95,
        "candidate_share_above_validation_low_risk_p95": {},
        "candidate_distance_summaries": {},
    }
    for protocol in ("v1", "v2"):
        protocol_records = holdout_records[protocol]
        valid_returns = [record for record in protocol_records if record.recourse_feasible]
        distance_records = [
            record for record in valid_returns if record.final_mahalanobis_distance is not None
        ]
        distances = [float(record.final_mahalanobis_distance) for record in distance_records]
        distance_above_tail = np.asarray(distances) > low_risk_p95
        dmax_tail["candidate_share_above_validation_low_risk_p95"][protocol] = {
            "count": int(distance_above_tail.sum()),
            "denominator": len(distances),
            "rate": float(np.mean(distance_above_tail)) if distances else None,
            "engine_bootstrap_ci": (
                _bootstrap(
                    pd.DataFrame({"engine_id": [record.engine_id for record in distance_records]}),
                    distance_above_tail.tolist(),
                    seed=engine.config.seed + (501 if protocol == "v1" else 502),
                )
                if distances
                else None
            ),
        }
        dmax_tail["candidate_distance_summaries"][protocol] = {
            "returned_candidate_count": len(distances),
            "mean_Dm": float(np.mean(distances)) if distances else None,
            "median_Dm": float(np.median(distances)) if distances else None,
            "p95_Dm": float(np.quantile(distances, 0.95, method="higher")) if distances else None,
            "real_alert_state_mean_Dm": float(np.mean(_distance_rows(engine, test_alerts))) if len(test_alerts) else None,
            "real_low_risk_validation_mean_Dm": float(np.mean(validation_low_risk_distances)),
        }

    # Coupling fit quality is based on engine-grouped OOF residuals in the saved fit artifact.
    if engine.coupling is None:
        coupling_fit: dict[str, Any] = {"available": False}
    else:
        coupling_fit = {
            "available": True,
            "r2": engine.coupling.metrics.r2,
            "residual_std": engine.coupling.residual_std,
            "r2_floor": engine.coupling.metrics.r2_floor,
            "below_r2_floor": list(engine.coupling.metrics.below_r2_floor),
            "cross_validation_folds": engine.coupling.metrics.cross_validation_folds,
            "fit_engine_count": engine.coupling.metrics.training_engine_count,
            "fit_row_count": engine.coupling.metrics.training_row_count,
            "fit_engine_ids": list(engine.coupling.training_engine_ids),
        }
        train_view = labeled[labeled.engine_id.isin(engine.coupling.training_engine_ids)]
        engine.coupling.write_diagnostic_report(OUTPUT_ROOT / "coupling-fit", train_view)
    coupling_candidates = {
        f"headline_sample_{protocol}": _coupling_candidate_diagnostics(
            tuple(
                record
                for record in holdout_records[protocol]
                if (record.engine_id, record.cycle)
                in {_key(row) for row in headline_rows.itertuples()}
            )
        )
        for protocol in ("v1", "v2")
    }
    coupling_candidates.update(
        {
            f"all_alert_states_{protocol}": _coupling_candidate_diagnostics(
                holdout_records[protocol]
            )
            for protocol in ("v1", "v2")
        }
    )

    surrogate = _surrogate_diagnostics(engine, splits.test)

    # Oracle uses the headline failure rows, with a fixed seeded sample of at least sixty when
    # available. It reports candidate-set misses and never calls them globally infeasible.
    oracle = _oracle_diagnosis(
        engine,
        headline_rows,
        headline_records_v1,
        seed=engine.config.seed + 60,
    )

    # Five-fold outer OOF and official test engines are fresh engine groups for protocol comparison.
    taxonomy = load_taxonomy(TAXONOMY_PATH)
    grouped_checkpoint = _read_checkpoint("grouped-cv", checkpoint_context)
    if grouped_checkpoint is None:
        grouped_cv = _run_grouped_cv(
            engine,
            labeled,
            taxonomy,
            sample_size=200,
            seed=engine.config.seed + 500,
        )
        _write_checkpoint(
            "grouped-cv", checkpoint_context, run_id, {"grouped_cv": grouped_cv}
        )
    else:
        grouped_cv = grouped_checkpoint["payload"]["grouped_cv"]
        LOGGER.info("Resumed grouped out-of-fold records from checkpoint")
    official = _official_test_frame(engine, archive)
    official_alerts = _alert_rows(engine, official)
    official_checkpoint = _read_checkpoint("official-test", checkpoint_context)
    if official_checkpoint is None:
        official_results: dict[str, Any] = {"all_alert_rows": len(official_alerts)}
        for protocol, d_max in (("v1", 5.0), ("v2", D_MAX_V2)):
            official_engine = _engine_with_settings(
                engine, mahalanobis_max=d_max, max_queries=len(official_alerts) + 1
            )
            official_run = evaluate_states(official_engine, official_alerts)
            official_results.setdefault("by_protocol", {})[protocol] = {
                "records": official_run.records,
                "population": "official FD001 test engines; RUL labels from official file",
                "protocol_version": protocol,
                "effective_solver_settings": _effective_solver_settings(official_run.records),
                "outcomes": _population_outcomes(
                    official_engine,
                    official_alerts,
                    official_run.records,
                    seed=engine.config.seed + (800 if protocol == "v1" else 900),
                ),
                "effective_configuration_sha256": _config_hash(official_engine.config),
                "k_max": official_engine.config.recourse.max_changed_features,
                "K": official_engine.config.recourse.rate_horizon_steps,
                "D_max": d_max,
            }
        _write_checkpoint(
            "official-test", checkpoint_context, run_id, {"official_results": official_results}
        )
    else:
        official_results = official_checkpoint["payload"]["official_results"]
        LOGGER.info("Resumed official test records from checkpoint")

    # Historical run explanation: d_max=6 was a scaled movement radius, not Mahalanobis D_max.
    dirty_profile_path = ROOT / "configs/experiments/phase4-thorough-expanded.yaml"
    dirty_config = load_config(dirty_profile_path)
    ladder = _constraint_ladder(
        engine,
        headline_rows,
        headline_records_v1,
        seed=engine.config.seed + 1729,
    )
    sensitivity_k5 = next(item for item in sensitivity if item["label"] == "k5-only")
    headline_strata = holdout["v1"]["headline_sample"]["strata"]
    sensitivity_strata = _strata_table(
        engine,
        sensitivity_rows,
        tuple(sensitivity_k5["records"]),
        seed=engine.config.seed + 1200,
    )
    document: dict[str, Any] = {
        "run_id": run_id,
        "run_timestamp_utc": datetime.now(UTC).isoformat(),
        "source_commit": source_commit,
        "measurement_source_commits": {
            "holdout_v1_v2": holdout_checkpoint.get("source_commit", source_commit)
            if holdout_checkpoint is not None
            else source_commit,
            "sensitivity": sensitivity_checkpoint.get("source_commit", source_commit)
            if sensitivity_checkpoint is not None
            else source_commit,
            "grouped_cv_oof": grouped_checkpoint.get("source_commit", source_commit)
            if grouped_checkpoint is not None
            else source_commit,
            "official_test": official_checkpoint.get("source_commit", source_commit)
            if official_checkpoint is not None
            else source_commit,
        },
        "protocol_v2_freeze_commit": "5f88d27b329a3ff673f841e525b154bfc853432c",
        "protocol_v2_sha256": _sha256_file(PROTOCOL_PATH),
        "dataset": "FD001",
        "model_training_commit": engine.model.git_commit,
        "model_config_sha256": engine.model.config_hash,
        "model_training_engine_ids": list(engine.model.training_engine_ids),
        "calibration_engine_ids": list(
            engine.model.metrics.get("calibration", {}).get("fit_engine_ids", [])
        ) if engine.model.metrics else [],
        "holdout_engine_ids": list(splits.test_engine_ids),
        "headline_population_definition": "up to 200 seeded-uniform actionable high-risk states from the 15-engine held-out split",
        "headline_population_protocol_commit": "f531682b09096abbd3abc69b633580e926ac49c8",
        "headline_population_protocol_date": "2026-10-18",
        "thresholds": {
            "tau_danger": engine.config.tau_danger,
            "tau_safe": engine.config.tau_safe,
            "D_max_v1": 5.0,
            "D_max_v2": D_MAX_V2,
        },
        "holdout_alert_population": {
            "all_alert_count": len(test_alerts),
            "all_alert_engine_count": int(test_alerts.engine_id.nunique()),
            "actionable_alert_count": all_actionable,
            "headline_sample_count": len(headline_rows),
            "headline_sample_engine_count": int(headline_rows.engine_id.nunique()) if len(headline_rows) else 0,
            "first_alert_count": len(_first_alert_rows(test_alerts)),
            "first_alert_engine_count": int(_first_alert_rows(test_alerts).engine_id.nunique()) if len(test_alerts) else 0,
        },
        "holdout_test": holdout,
        "sensitivity": sensitivity,
        "fast_vs_thorough": {
            "shared_success_count": len(shared_success),
            "identical_state_and_risk_count": exact_match_count,
            "identical_rate": exact_match_count / len(shared_success) if shared_success else None,
            "fast_mode_optimization_p95_ms": next(
                item["outcomes"]["optimization_latency"]["p95_ms"]
                for item in sensitivity
                if item["label"] == "fast-mode-only"
            ),
            "target_p95_ms": 1_800.0,
            "target_passed": bool(
                next(
                    item["outcomes"]["optimization_latency"]["p95_ms"]
                    for item in sensitivity
                    if item["label"] == "fast-mode-only"
                )
                <= 1_800.0
            ),
        },
        "historical_dmax_6_explanation": {
            "value": dirty_config.recourse.max_scaled_distance,
            "meaning": "max_scaled_distance: per-feature scaled-space movement trust radius",
            "not": "Mahalanobis D_max; the dirty expanded run retained D_max=5.0",
            "old_effective_settings": dirty_config.recourse.model_dump(mode="json"),
        },
        "historical_count_audit": _historical_count_audit(),
        "validation_distribution": dmax_tail,
        "constraint_ladder": ladder,
        "headline_strata_k3": headline_strata,
        "sensitivity_strata_k5_60_state_sample": sensitivity_strata,
        "oracle": oracle,
        "coupling_fit": coupling_fit,
        "coupling_candidates": coupling_candidates,
        "surrogate": surrogate,
        "grouped_cv_oof": grouped_cv,
        "official_test": official_results,
        "environment": {
            "effective_config": engine.config.model_dump(mode="json"),
            "effective_config_sha256": _config_hash(engine.config),
            "taxonomy_sha256": _sha256_file(TAXONOMY_PATH),
            "dataset_archive_sha256": _sha256_file(engine.config.data.root / engine.config.data.archive_name),
            "protocol_file_sha256": _sha256_file(PROTOCOL_PATH),
            "config_path": str(CONFIG_PATH.relative_to(ROOT)),
            "python_version": subprocess.run(
                ["python", "--version"], check=True, capture_output=True, text=True
            ).stdout.strip(),
        },
    }
    _write_k_curve(sensitivity)
    _write_json(REPORT_PATH, document)
    FINAL_DOC_PATH.write_text(_render_final_report(document), encoding="utf-8")
    _write_json(OUTPUT_ROOT / f"{run_id}.json", document)
    return document


def _constraint_ladder(
    engine: PrescriptXAIEngine,
    sample_rows: pd.DataFrame,
    records: tuple[EvaluationRecord, ...],
    *,
    seed: int,
) -> dict[str, Any]:
    """Report a cumulative observed acceptance funnel for the saved recourse candidates."""
    del seed
    indexed = _records_by_key(records)
    rows = list(sample_rows.itertuples())
    sampled_records = [indexed.get(_key(row)) for row in rows]
    total = len(rows)
    if not total:
        return {}
    cumulative = np.ones(total, dtype=bool)
    stages: dict[str, np.ndarray] = {}
    record_present = np.asarray([record is not None for record in sampled_records], dtype=bool)
    stages["query has evaluated solver record"] = record_present
    cumulative &= record_present
    bounded_sparse = np.asarray(
        [
            record is not None
            and record.actuator_bound_violations == 0
            and record.rate_limit_violations == 0
            and record.changed_features <= engine.config.recourse.max_changed_features
            for record in sampled_records
        ],
        dtype=bool,
    )
    cumulative &= bounded_sparse
    stages["bounds, rate limit and k_max"] = cumulative.copy()
    model_safe = np.asarray(
        [bool(record and record.model_valid) for record in sampled_records], dtype=bool
    )
    cumulative &= model_safe
    stages["true calibrated model safe (Tier 1)"] = cumulative.copy()
    tier2 = np.asarray(
        [bool(record and record.tier2_plausible) for record in sampled_records], dtype=bool
    )
    cumulative &= tier2
    stages["Tier 2 Mahalanobis plausible"] = cumulative.copy()
    tier3 = np.asarray(
        [bool(record and record.tier3_engineering_valid) for record in sampled_records],
        dtype=bool,
    )
    cumulative &= tier3
    stages["Tier 3 engineering valid"] = cumulative.copy()
    tier4 = np.asarray(
        [bool(record and record.tier4_coupling_valid) for record in sampled_records],
        dtype=bool,
    )
    cumulative &= tier4
    stages["Tier 4 sensor coupling valid"] = cumulative.copy()
    ladder: dict[str, Any] = {}
    engine_ids = np.asarray([int(row.engine_id) for row in rows], dtype=np.int64)
    for index, (name, passed) in enumerate(stages.items()):
        interval = engine_bootstrap_interval(
            engine_ids,
            passed,
            seed=engine.config.seed + 1729 + index,
            replicates=BOOTSTRAP_REPLICATES,
        )
        ladder[name] = {
            "count": int(passed.sum()),
            "total": total,
            "rate": float(passed.mean()),
            "engine_count": interval.engine_count,
            "engine_bootstrap_ci": [interval.lower, interval.upper],
        }
    return {
        **ladder,
        "population": f"saved headline k<=3 states, n={total}",
        "note": "Cumulative observed pass counts for the saved k<=3 candidates. This is not a causal constraint-removal experiment; the K sensitivity is reported separately.",
    }


def main() -> None:
    """Run the full Phase 4 closure diagnostic and report its output path."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = run()
    LOGGER.info("Phase 4 closure data saved to %s", REPORT_PATH)
    LOGGER.info("Phase 4 final report saved to %s", FINAL_DOC_PATH)
    LOGGER.info("Run ID %s, source commit %s", result["run_id"], result["source_commit"])


if __name__ == "__main__":
    main()
