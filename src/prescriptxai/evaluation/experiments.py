"""Versioned study configuration, observations and atomic resumable evidence storage."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sqlite3
import subprocess
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from prescriptxai.config import AppConfig
from prescriptxai.schemas import InputContext


class StudyConfig(BaseModel):
    """Precommitted experimental design; numerical choices are loaded from YAML."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    study_version: str
    frozen_solver_config: Path
    output_root: Path
    artifact_root: Path
    datasets: dict[str, list[Literal["xgb", "mlp", "lstm"]]]
    optional_datasets: dict[str, bool]
    solver_seeds: list[int]
    model_seed: int = Field(ge=0)
    split_seed: int = Field(ge=0)
    d_max_versions: dict[str, float]
    grouped_folds: int = Field(ge=2)
    workers: int = Field(ge=1)
    cpu_threads_per_worker: int = Field(ge=1)
    headline_mode: Literal["fast"]
    headline_population: Literal["all_alerts"]
    thorough_population: Literal["first_alert_per_engine"]
    development_max_queries: int = Field(ge=1)
    diagnostic_max_queries: int = Field(ge=1)
    oracle_max_failed_queries: int = Field(ge=1)
    diagnostic_seed: int = Field(ge=0)
    bootstrap_replicates: int = Field(ge=100)
    bootstrap_confidence: float = Field(gt=0, lt=1)
    latency_runs_per_mode: int = Field(ge=1000)
    latency_warmups_per_mode: int = Field(ge=1)
    diagnostic_models: list[str]
    diagnostic_solver_seed: int = Field(ge=0)
    oracle_grid_points: int = Field(ge=2)
    oracle_chunk_rows: int = Field(ge=1)
    checkpoint_every_queries: Literal[1]
    tau_safe_grid: list[float]
    k_max_grid: list[int]
    horizon_H_grid: list[int]
    K_grid: list[int]
    alpha_grid: list[float]
    beta_grid: list[float]
    gamma_grid: list[float]
    d_max_quantile_grid: list[float]
    d_max_methods: list[Literal["empirical", "chi_square"]]
    reference_distributions: list[Literal["all_cycles", "healthy_to_moderate"]]
    risk_band_edges: list[float]
    rul_bucket_edges: list[float]
    life_fraction_edges: list[float]
    risk_reduction_edges: list[float]
    unconstrained_free_rate_fraction: float = Field(gt=0)
    dice_enabled: bool
    targets: dict[str, float]
    assumptions: list[str]

    @model_validator(mode="after")
    def check_design(self) -> StudyConfig:
        """Reject duplicate seeds, invalid probability grids and unordered bins."""
        if not self.solver_seeds or len(set(self.solver_seeds)) != len(self.solver_seeds):
            raise ValueError("solver seeds must be nonempty and unique")
        if any(s < 0 for s in self.solver_seeds):
            raise ValueError("seeds must be nonnegative")
        for values in (self.tau_safe_grid, self.d_max_quantile_grid):
            if not values or any(not 0 < v < 1 for v in values):
                raise ValueError("probability grids must be nonempty and inside (0,1)")
        for counts in (self.k_max_grid, self.horizon_H_grid, self.K_grid):
            if not counts or any(v < 1 for v in counts):
                raise ValueError("count grids must be positive")
        for values in (self.alpha_grid, self.beta_grid, self.gamma_grid):
            if not values or any(v < 0 for v in values):
                raise ValueError("objective grids must be nonnegative")
        for edges in (
            self.risk_band_edges,
            self.rul_bucket_edges,
            self.life_fraction_edges,
            self.risk_reduction_edges,
        ):
            if len(edges) < 2 or any(a >= b for a, b in zip(edges, edges[1:], strict=False)):
                raise ValueError("histogram edges must strictly increase")
        if not self.datasets or any(not models for models in self.datasets.values()):
            raise ValueError("datasets and models must be nonempty")
        if not self.d_max_versions or any(v <= 0 for v in self.d_max_versions.values()):
            raise ValueError("D_max must be positive")
        return self


def load_study(path: Path) -> StudyConfig:
    """Load and validate a committed study YAML."""
    return StudyConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def content_hash(value: object) -> str:
    """Hash canonical finite JSON, including ordering-independent mapping keys."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_hash(path: Path) -> str:
    """Fingerprint an exact input or fitted artifact."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_revision(*, require_clean: bool = True) -> str:
    """Require committed experimental behavior and return its source revision."""
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], text=True
    )
    if require_clean and any(
        line[3:].startswith(("src/", "scripts/", "configs/", "docs/evaluation_protocol"))
        for line in dirty.splitlines()
    ):
        raise ValueError("commit experimental code/config/protocol before fitting or measuring")
    return revision


def runtime_manifest() -> dict[str, object]:
    """Record package versions and hardware without inferring performance."""
    versions: dict[str, str | None] = {}
    for package in (
        "prescriptxai",
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "torch",
        "xgboost",
        "pydantic",
        "dice-ml",
    ):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "package_versions": versions,
    }


def mark_stage_complete(directory: Path, stage: str, source: str, count: int) -> None:
    """Atomically record verified stage completion without losing earlier stages."""
    path = directory / "stages.json"
    status = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    status[stage] = {"complete": True, "source": source, "observations": count}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(status, indent=2), encoding="utf-8")
    temporary.replace(path)


def audit_stage_completion(
    directory: Path, manifest: dict[str, Any], study: StudyConfig
) -> dict[str, bool]:
    """Verify completion flags against saved query identities and measured sample counts."""
    path = directory / "stages.json"
    flags = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    expected = manifest.get("expected_queries", {})
    with closing(sqlite3.connect(directory / "records.sqlite3")) as connection:
        paired = "json_extract(payload,'$.population')='paired_internal_diagnostic'"
        diagnostic_count = connection.execute(
            "SELECT COUNT(*) FROM records WHERE " + paired
        ).fetchone()[0]
        total_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        failed = connection.execute(
            "SELECT case_id,json_extract(payload,'$.group') FROM records WHERE "
            + paired
            + " AND json_extract(payload,'$.variant')='full' "
            "AND json_extract(payload,'$.joint')=0 ORDER BY case_id"
        ).fetchall()
    counts = {"diagnostics": diagnostic_count, "quality": total_count - diagnostic_count}
    status = {
        stage: (
            flags.get(stage, {}).get("complete", False)
            and flags[stage].get("source") == manifest["git_hash"]
            and flags[stage].get("observations") == counts[stage] == expected.get(stage)
        )
        for stage in counts
    }
    reference_path = directory / "reference.json"
    reference = (
        json.loads(reference_path.read_text(encoding="utf-8")) if reference_path.exists() else {}
    )
    expected_reference = manifest.get("expected_reference_case_ids")
    expected_oracles = set()
    per_group: dict[str, int] = {}
    for case_id, group in failed:
        if per_group.get(group, 0) < study.oracle_max_failed_queries:
            expected_oracles.add(case_id)
            per_group[group] = per_group.get(group, 0) + 1
    status["reference"] = bool(
        status["diagnostics"]
        and expected_reference is not None
        and set(reference) == set(expected_reference)
        and all("leverage" in item for item in reference.values())
        and {key for key, item in reference.items() if "oracle" in item} == expected_oracles
        and flags.get("reference", {}).get("complete", False)
        and flags["reference"].get("source") == manifest["git_hash"]
        and flags["reference"].get("observations") == len(expected_reference)
    )
    latency_path = directory / "latency.json"
    latency_database = directory / "latency.sqlite3"
    status["latency"] = False
    if latency_path.exists() and latency_database.exists():
        latency = json.loads(latency_path.read_text(encoding="utf-8"))
        with closing(sqlite3.connect(latency_database)) as connection:
            samples = dict(connection.execute("SELECT mode,COUNT(*) FROM samples GROUP BY mode"))
        status["latency"] = bool(
            flags.get("latency", {}).get("complete", False)
            and flags["latency"].get("source") == manifest["git_hash"]
            and flags["latency"].get("observations") == study.latency_runs_per_mode * 2
            and latency["labels"]["git_hash"] == manifest["git_hash"]
            and all(
                samples.get(mode.lower()) == study.latency_runs_per_mode
                and latency.get("modes", {}).get(mode, {}).get("pipeline_ms", {}).get("count")
                == study.latency_runs_per_mode
                for mode in ("FAST", "THOROUGH")
            )
        )
    return status


class ExperimentObservation(BaseModel):
    """Internal experimental record; frozen public schemas remain unchanged."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    case_id: str
    group: str
    dataset: str
    model: str
    population: str
    protocol: str
    variant: str
    mode: Literal["FAST", "THOROUGH"]
    seed: int
    engine_id: int
    cycle: int
    risk_before: float = Field(ge=0, le=1)
    risk_after: float = Field(ge=0, le=1)
    surrogate_after: float | None
    original: dict[str, float]
    candidate: dict[str, float]
    changed_features: list[str]
    sparsity: int = Field(ge=0)
    proxy_sparsity: int = Field(default=0, ge=0)
    raw_l1: float = Field(ge=0)
    scaled_l1: float = Field(ge=0)
    returned: bool
    action_feasible: bool
    tier2: bool
    tier3: bool
    tier4: bool
    joint: bool
    status: Literal["NO_INTERVENTION", "RECOVERABLE", "PARTIAL", "ESCALATE"]
    reason: str | None
    evidence_level: str
    mahalanobis_before: float
    mahalanobis_after: float
    tier4_margin: float | None
    immutable_violations: int = Field(ge=0)
    bound_violations: int = Field(ge=0)
    rate_violations: int = Field(ge=0)
    rul: float = Field(ge=0)
    life_fraction: float = Field(gt=0, le=1)
    first_alert: bool
    timings: dict[str, float]
    config_hash: str
    config_path: str
    k_max: int
    K: int
    D_max: float
    solver_tau_safe: float
    solver_tau_danger: float
    solver_settings: dict[str, Any]
    validation: dict[str, Any]


class QueryCase(BaseModel):
    """One reproducible model/context/query with its immutable experiment labels."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    case_id: str
    group: str
    dataset: str
    model: str
    population: str
    protocol: str
    variant: str
    mode: Literal["fast", "thorough"]
    config_path: Path
    config: AppConfig
    state: dict[str, float]
    context: InputContext | None
    rul: float
    first_alert: bool
    policy: dict[str, bool] | None = None
    free_rate_fraction: float


class ExperimentStore:
    """SQLite transactions checkpoint each query and reject incompatible resumption."""

    def __init__(self, directory: Path, manifest: Mapping[str, object]) -> None:
        """Create a study folder or verify identical immutable resume inputs."""
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory
        path = directory / "manifest.json"
        encoded = json.dumps(dict(manifest), sort_keys=True, indent=2, allow_nan=False)
        if path.exists():
            if json.loads(path.read_text(encoding="utf-8")) != dict(manifest):
                raise ValueError("resume manifest mismatch: config/source/artifacts/cohort changed")
        else:
            temporary = path.with_suffix(".tmp")
            temporary.write_text(encoded, encoding="utf-8")
            temporary.replace(path)
        self.connection = sqlite3.connect(directory / "records.sqlite3")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS records (case_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS cases (case_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        self.connection.commit()

    def register_case(self, case: QueryCase) -> None:
        """Persist exact effective configuration and observed history before execution."""
        payload = case.model_dump_json()
        previous = self.connection.execute(
            "SELECT payload FROM cases WHERE case_id=?", (case.case_id,)
        ).fetchone()
        if previous and json.loads(previous[0]) != json.loads(payload):
            raise ValueError("case identity was reused for different effective inputs")
        if not previous:
            with self.connection:
                self.connection.execute("INSERT INTO cases VALUES (?,?)", (case.case_id, payload))

    def completed(self) -> set[str]:
        """Return committed query IDs; interrupted uncommitted work is retried."""
        return {row[0] for row in self.connection.execute("SELECT case_id FROM records")}

    def save(self, record: ExperimentObservation) -> None:
        """Commit one measured query exactly once, rejecting conflicting duplicates."""
        encoded = record.model_dump_json()
        existing = self.connection.execute(
            "SELECT payload FROM records WHERE case_id=?", (record.case_id,)
        ).fetchone()
        if existing:
            if json.loads(existing[0]) != json.loads(encoded):
                raise ValueError("completed query cannot be replaced with a different result")
            return
        with self.connection:
            self.connection.execute("INSERT INTO records VALUES (?,?)", (record.case_id, encoded))

    def records(self) -> list[ExperimentObservation]:
        """Read in stable query order for deterministic aggregation/export."""
        return [
            ExperimentObservation.model_validate_json(row[0])
            for row in self.connection.execute("SELECT payload FROM records ORDER BY case_id")
        ]

    def close(self) -> None:
        """Flush and close the evidence database."""
        self.connection.close()
