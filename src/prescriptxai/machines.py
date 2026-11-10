"""Wire configured data adapters to the existing fitted numerical runtime."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Sequence
from contextlib import closing
from dataclasses import dataclass
from hashlib import file_digest, sha256
from pathlib import Path
from typing import Literal

import pandas as pd

from prescriptxai.adapters.base import DatasetAdapter
from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.config import AppConfig
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import FeatureSpec, FeatureTaxonomy, build_feature_taxonomy
from prescriptxai.core.data_quality import require_clean_window
from prescriptxai.core.decision import MachineDecision
from prescriptxai.data.splits import EngineSplits
from prescriptxai.machine_schema import FeedbackRecord, ReplayFollowUp
from prescriptxai.machine_spec import MachineSpec
from prescriptxai.models.registry import ModelBundle, load_model_bundle, save_model_bundle
from prescriptxai.models.train import TrainingResult, fit_partitioned_risk_model
from prescriptxai.pipeline import PrescriptXAI, PrescriptXAIEngine
from prescriptxai.validation.pipeline import (
    fit_mahalanobis_validator,
    load_mahalanobis_validator,
    save_mahalanobis_validator,
    verify_validator_compatibility,
)
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator
from prescriptxai.validation.tier4_coupling import calibrate_coupling_thresholds

ModelName = Literal["xgb", "mlp", "lstm"]


def machine_taxonomy(spec: MachineSpec) -> FeatureTaxonomy:
    """Project machine policy onto the shared solver's typed feature masks."""
    return build_feature_taxonomy(
        dataset=spec.machine_id,
        features=tuple(
            FeatureSpec(
                name=feature.id,
                label=feature.label,
                unit=feature.unit,
                cmapss_column=feature.column,
                group=feature.legacy_group
                or (
                    "controllable"
                    if feature.role == "controllable"
                    else "dependent"
                    if feature.role == "sensor"
                    else "immutable_operational"
                ),
                bounds=feature.bounds,
                max_rate_of_change=feature.step_limit,
                direction=feature.direction,
                controllable_proxy=feature.proxy,
                proxy_note=feature.why if feature.proxy else None,
            )
            for feature in spec.measurement_features
        ),
        bound_estimation=spec.validation.bound_estimation,
        coupling=spec.validation.fitted_coupling,
        coupling_rules=spec.validation.coupling_rules,
    )


def machine_settings(spec: MachineSpec, base: AppConfig, protocol: str) -> AppConfig:
    """Apply the declared policies without changing the base configuration."""
    if protocol not in spec.validation.plausibility:
        raise ValueError(f"unknown protocol {protocol!r} for {spec.machine_id}")
    config = base.model_copy(deep=True)
    config.horizon_H = config.data.failure_horizon = spec.failure.horizon
    config.tau_safe = config.model.safe_threshold = spec.failure.tau_safe
    config.tau_danger = config.model.danger_threshold = spec.failure.tau_danger
    config.data.dataset = spec.dataset.subset or "FD001"
    config.recourse.max_changed_features = spec.k_max
    config.recourse.rate_horizon_steps = spec.validation.intervention_steps
    config.validation.mahalanobis_max = spec.validation.plausibility[protocol]
    config.validation.simulator_enabled = False
    config.pipeline.delta_min = spec.delta_min
    config.pipeline.escalation_message = spec.sentences.escalation
    config.latency_budget = spec.latency_budgets[
        "FAST" if config.pipeline.default_mode == "fast" else "THOROUGH"
    ]
    return AppConfig.model_validate(config.model_dump())


def _model_partitions(adapter: DatasetAdapter, rows: pd.DataFrame, seed: int) -> EngineSplits:
    partitions = adapter.split(seed, frame=rows)
    numbers = {unit: index for index, unit in enumerate(rows["unit_id"].unique(), start=1)}
    frames = [
        part.assign(engine_id=part["unit_id"].map(numbers), cycle=part["time_index"]).drop(
            columns="unit_id"
        )
        for part in (partitions.train, partitions.validation, partitions.test)
    ]
    identities = [
        tuple(sorted(int(value) for value in frame["engine_id"].unique())) for frame in frames
    ]
    return EngineSplits(
        frames[0], frames[1], frames[2], identities[0], identities[1], identities[2]
    )


@dataclass(frozen=True)
class FittedMachine:
    """Training diagnostics and the verified runtime inputs for one spec."""

    spec: MachineSpec
    protocol: str
    config: AppConfig
    training: TrainingResult
    validator: MahalanobisValidator
    coupling: SensorCouplingModel | None

    def decision(self) -> MachineDecision:
        """Expose the in-memory fit through the same guarded decision boundary."""
        return _decision(
            self.spec,
            self.protocol,
            self.config,
            self.training.bundle,
            self.validator,
            self.coupling,
        )


def fit_machine(
    adapter: DatasetAdapter, base: AppConfig, protocol: str, model: ModelName
) -> FittedMachine:
    """Train and calibrate a machine from declared labels and disjoint source units."""
    spec = adapter.spec
    config = machine_settings(spec, base, protocol)
    model_choices: dict[ModelName, Literal["xgboost", "torch", "lstm"]] = {
        "xgb": "xgboost",
        "mlp": "torch",
        "lstm": "lstm",
    }
    config.model_choice = config.model.risk_estimator = model_choices[model]
    rows = adapter.load()
    for _, unit in rows.groupby("unit_id", sort=False):
        require_clean_window(unit, spec)
    rows = rows.assign(
        failure_label=adapter.failure_labels(spec.failure.horizon, frame=rows),
        rul=adapter.remaining_life(frame=rows),
    )
    splits = _model_partitions(adapter, rows, config.seed)
    taxonomy = machine_taxonomy(spec)
    fit = fit_partitioned_risk_model(
        splits,
        config,
        taxonomy,
        model,
        variance_features=frozenset(
            feature.id
            for feature in spec.measurement_features
            if feature.legacy_group == "dependent" or feature.role in {"sensor", "controllable"}
        ),
    )
    fit.metrics.update(
        {
            "machine_id": spec.machine_id,
            "spec_hash": spec.spec_hash,
            "protocol_version": protocol,
            "synthetic": spec.synthetic,
            "dataset": spec.machine_id,
        }
    )
    validator = fit_mahalanobis_validator(splits.train, fit.bundle, splits.train_engine_ids, config)
    coupling = None
    if spec.validation.fitted_coupling is not None:
        coupling = SensorCouplingModel.fit(
            splits.train,
            taxonomy,
            training_engine_ids=splits.train_engine_ids,
            failure_horizon=spec.failure.horizon,
            seed=config.seed,
        )
        coupling = calibrate_coupling_thresholds(
            coupling,
            splits.validation,
            splits.validation_engine_ids,
            reference_distribution=config.validation.coupling_calibration_reference,
            min_rul=config.validation.healthy_min_rul,
            evaluation_engine_ids=splits.test_engine_ids,
        )
    return FittedMachine(spec, protocol, config, fit, validator, coupling)


def _decision(
    spec: MachineSpec,
    protocol: str,
    config: AppConfig,
    bundle: ModelBundle,
    validator: MahalanobisValidator,
    coupling: SensorCouplingModel | None,
    runtime_identity: str | None = None,
) -> MachineDecision:
    verify_validator_compatibility(validator, bundle, config)
    taxonomy = machine_taxonomy(spec).with_resolved_bounds(
        bundle.resolved_bounds or {},
        bundle.resolved_rate_limits,
    )
    taxonomy.validate_model_feature_coverage(bundle.feature_names)
    runtime = PrescriptXAI(PrescriptXAIEngine(config, taxonomy, bundle, validator, coupling))
    return MachineDecision(
        spec,
        runtime,
        bundle.feature_names,
        protocol,
        history_rows=max(0, int(getattr(bundle.estimator, "window", 1)) - 1),
        runtime_identity=runtime_identity,
    )


def scope_archive_runtime(
    spec: MachineSpec,
    protocol: str,
    runtime: PrescriptXAI,
) -> MachineDecision:
    """Attach named policy to compatible retained archive artifacts."""
    if runtime.config.data.dataset != spec.dataset.subset:
        raise ValueError("retained runtime subset differs from this machine spec")
    config = machine_settings(spec, runtime.config, protocol)
    model = runtime.engine.model
    metrics = model.metrics or {}
    for field, expected in (("dataset", spec.dataset.subset), ("horizon_H", spec.failure.horizon)):
        if field in metrics and metrics[field] != expected:
            raise ValueError(f"retained model {field} differs from this machine spec")
    return _decision(
        spec,
        protocol,
        config,
        model,
        runtime.engine.mahalanobis,
        runtime.engine.coupling,
        runtime.engine.artifact_identity,
    )


def _artifact_directory(spec: MachineSpec, protocol: str, root: Path) -> Path:
    if protocol not in spec.validation.plausibility:
        raise ValueError(f"unknown protocol version: {protocol}")
    protocol_key = sha256(protocol.encode("utf-8")).hexdigest()[:16]
    return root / spec.machine_id / spec.spec_hash / protocol_key


def save_machine_fit(fit: FittedMachine, root: Path = Path("artifacts/machines")) -> Path:
    """Persist one fit to a fresh spec-scoped directory with a completion marker."""
    target = _artifact_directory(fit.spec, fit.protocol, root)
    target.mkdir(parents=True, exist_ok=False)
    paths = [
        save_model_bundle(fit.training.bundle, target / "model.joblib"),
        save_mahalanobis_validator(fit.validator, target / "validator.joblib"),
    ]
    if fit.coupling is not None:
        paths.append(fit.coupling.save(target / "coupling.joblib"))
    hashes = {}
    for path in paths:
        with path.open("rb") as stream:
            hashes[path.name] = file_digest(stream, "sha256").hexdigest()
    pending = target / "complete.pending.json"
    pending.write_text(
        json.dumps(
            {
                "machine_id": fit.spec.machine_id,
                "spec_hash": fit.spec.spec_hash,
                "protocol_version": fit.protocol,
                "config": fit.config.model_dump(mode="json"),
                "files": hashes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    pending.replace(target / "complete.json")
    return target


def load_machine_decision(
    spec: MachineSpec,
    protocol: str,
    root: Path = Path("artifacts/machines"),
) -> MachineDecision:
    """Load a complete local fit only for the exact machine, spec and protocol."""
    directory = _artifact_directory(spec, protocol, root)
    complete = json.loads((directory / "complete.json").read_text(encoding="utf-8"))
    expected = {
        "machine_id": spec.machine_id,
        "spec_hash": spec.spec_hash,
        "protocol_version": protocol,
    }
    names = {"model.joblib", "validator.joblib"}
    if spec.validation.fitted_coupling is not None:
        names.add("coupling.joblib")
    hashes = complete.get("files")
    if (
        not isinstance(hashes, dict)
        or set(hashes) != names
        or any(not isinstance(value, str) or len(value) != 64 for value in hashes.values())
    ):
        raise ValueError("machine artifact manifest is incomplete")
    for key, value in expected.items():
        if complete.get(key) != value:
            raise ValueError(f"machine artifact {key} differs from the selected spec")
    bundle = load_model_bundle(
        directory / "model.joblib",
        require_calibrated=True,
        expected_sha256=hashes["model.joblib"],
    )
    if any((bundle.metrics or {}).get(key) != value for key, value in expected.items()):
        raise ValueError("model bundle provenance differs from the selected spec")
    config = machine_settings(spec, AppConfig.model_validate(complete["config"]), protocol)
    validator = load_mahalanobis_validator(
        directory / "validator.joblib",
        expected_sha256=hashes["validator.joblib"],
    )
    coupling = (
        SensorCouplingModel.load(
            directory / "coupling.joblib", expected_sha256=hashes["coupling.joblib"]
        )
        if "coupling.joblib" in hashes
        else None
    )
    identity = sha256(json.dumps(complete, sort_keys=True).encode()).hexdigest()
    return _decision(spec, protocol, config, bundle, validator, coupling, identity)


def record_feedback(
    record: FeedbackRecord, path: Path = Path("artifacts/machines/feedback.sqlite3")
) -> None:
    """Append one compatible feedback record transactionally to the local log."""
    record_feedback_batch([(record, None)], path)


def record_feedback_batch(
    records: Sequence[tuple[FeedbackRecord, ReplayFollowUp | None]],
    path: Path = Path("artifacts/machines/feedback.sqlite3"),
) -> None:
    """Commit the replay context and every checked outcome in one transaction."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as database, database:
        database.execute(
            "CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
        )
        database.execute(
            "CREATE TABLE IF NOT EXISTS replay_followup "
            "(feedback_id INTEGER PRIMARY KEY REFERENCES feedback(id), payload TEXT NOT NULL)"
        )
        for record, details in records:
            cursor = database.execute(
                "INSERT INTO feedback(payload) VALUES (?)", (record.model_dump_json(),)
            )
            if details is not None:
                database.execute(
                    "INSERT INTO replay_followup(feedback_id, payload) VALUES (?, ?)",
                    (cursor.lastrowid, details.model_dump_json()),
                )


def read_feedback(
    spec: MachineSpec,
    protocol: str,
    path: Path = Path("artifacts/machines/feedback.sqlite3"),
    *,
    include_simulated: bool = False,
) -> list[FeedbackRecord]:
    """Read compatible feedback records for the active scope."""
    return [
        record
        for record, _ in read_feedback_log(
            spec, protocol, path, include_simulated=include_simulated
        )
    ]


def read_feedback_log(
    spec: MachineSpec,
    protocol: str,
    path: Path = Path("artifacts/machines/feedback.sqlite3"),
    *,
    include_simulated: bool = False,
) -> list[tuple[FeedbackRecord, ReplayFollowUp | None]]:
    """Read one exact machine/spec/protocol log, excluding demo sources by default."""
    if protocol not in spec.validation.plausibility:
        raise ValueError(f"unknown protocol version: {protocol}")
    if not path.exists():
        return []
    spec_hash = spec.spec_hash
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as database:
        sidecar = database.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'replay_followup'"
        ).fetchone()
        query = (
            "SELECT f.payload, r.payload FROM feedback f "
            "LEFT JOIN replay_followup r ON r.feedback_id = f.id ORDER BY f.id"
            if sidecar
            else "SELECT payload, NULL FROM feedback ORDER BY id"
        )
        records = []
        for payload, extra in database.execute(query):
            record = FeedbackRecord.model_validate_json(payload)
            if (
                record.machine_id == spec.machine_id
                and record.spec_hash == spec_hash
                and record.protocol_version == protocol
                and record.synthetic == spec.synthetic
                and (include_simulated or record.source == "operator")
            ):
                details = ReplayFollowUp.model_validate_json(extra) if extra is not None else None
                records.append((record, details))
    return records


def resolve_machine_decision(
    registry: MachineRegistry,
    machine_id: str,
    protocol: str,
    artifact_root: Path = Path("artifacts/machines"),
    legacy: PrescriptXAI | Callable[[], PrescriptXAI] | None = None,
) -> MachineDecision:
    """Resolve a named fit or a compatible retained archive runtime."""
    spec = registry.get(machine_id)
    directory = _artifact_directory(spec, protocol, artifact_root)
    if spec.dataset.adapter == "cmapss" and not directory.exists() and legacy is not None:
        runtime = legacy() if callable(legacy) else legacy
        return scope_archive_runtime(spec, protocol, runtime)
    return load_machine_decision(spec, protocol, artifact_root)


def machine_summary(spec: MachineSpec) -> dict[str, object]:
    """Describe published machine identity and declared limits."""
    return {
        "machine_id": spec.machine_id,
        "spec_hash": spec.spec_hash,
        "display_name": spec.display_name,
        "unit_word": spec.unit_word,
        "unit_plural": spec.unit_plural,
        "synthetic": spec.synthetic,
        "data_source": spec.data_source,
        "alerts_only": spec.alerts_only,
        "limits_status": spec.limits_status,
        "limits_label": spec.limits_label,
        "protocol_versions": sorted(spec.validation.plausibility),
        "features": [
            {
                "id": feature.id,
                "label": feature.label,
                "unit": feature.unit,
                "role": feature.role,
                "bounds": feature.bounds.model_dump(),
            }
            for feature in spec.measurement_features
        ],
    }
