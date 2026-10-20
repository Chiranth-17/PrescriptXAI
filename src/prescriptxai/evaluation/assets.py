"""Prepare versioned, engine-disjoint experiment assets without selecting on recourse."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import joblib
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import FeatureTaxonomy, load_taxonomy
from prescriptxai.data.cmapss import load_cmapss_archive, to_model_frame
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.evaluation.experiments import StudyConfig, file_hash, source_revision
from prescriptxai.models.registry import ModelBundle, load_model_bundle, save_model_bundle
from prescriptxai.models.train import train_risk_model
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, save_mahalanobis_validator
from prescriptxai.validation.tier4_coupling import calibrate_coupling_thresholds


def dataset_frames(config: AppConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read real telemetry and derive official cycle-level RUL without simulated trajectories."""
    data = load_cmapss_archive(config.data.root / config.data.archive_name, config.data.dataset)
    train = add_training_labels(to_model_frame(data.train), None, config.horizon_H)
    official = to_model_frame(data.test)
    terminals = official.groupby("engine_id").cycle.max()
    rul = dict(zip(data.test_rul.unit_id, data.test_rul.rul, strict=True))
    official["rul"] = [
        rul[int(unit)] + terminals[int(unit)] - cycle
        for unit, cycle in zip(official.engine_id, official.cycle, strict=True)
    ]
    official["failure_label"] = (official.rul <= config.horizon_H).astype(int)
    official["engine_id"] += 10000
    return train, official


def bundle_partitions(
    bundle: ModelBundle,
    evaluation_engine_ids: tuple[int, ...] | None = None,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """Require persisted fitting/validation/test IDs instead of inferring leakage safety."""
    metadata = (bundle.metrics or {}).get("split_engines")
    if not isinstance(metadata, dict):
        raise ValueError("model lacks explicit engine partitions")
    if "test_holdout" not in metadata and evaluation_engine_ids is None:
        raise ValueError("outer evaluation IDs must be supplied from frozen provenance")
    test_ids = metadata.get("test_holdout", evaluation_engine_ids)
    if test_ids is None:
        raise ValueError("evaluation engine IDs are unavailable")
    if evaluation_engine_ids is not None and set(test_ids) != set(evaluation_engine_ids):
        raise ValueError("explicit evaluation IDs disagree with saved test partition")
    parts = (
        tuple(int(v) for v in metadata["train"]),
        tuple(int(v) for v in metadata["validation"]),
        tuple(int(v) for v in test_ids),
    )
    if any(not p for p in parts) or any(
        set(parts[a]) & set(parts[b]) for a, b in ((0, 1), (0, 2), (1, 2))
    ):
        raise ValueError("model engine partitions are empty or overlap")
    return parts


def grouped_partitions(
    frame: pd.DataFrame,
    study: StudyConfig,
    validation_fraction: float,
    lifetime_buckets: int,
) -> list[tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]]:
    """Stratify engine lifetime buckets; each engine is outer test exactly once."""
    lifetimes = frame.groupby("engine_id").cycle.max().sort_index()
    ids = lifetimes.index.to_numpy(dtype=int)
    buckets = pd.qcut(
        lifetimes.rank(method="first"), q=lifetime_buckets, labels=False, duplicates="drop"
    ).to_numpy()
    splitter = StratifiedKFold(study.grouped_folds, shuffle=True, random_state=study.split_seed)
    result = []
    for remaining, heldout in splitter.split(ids, buckets):
        fitting, validation = train_test_split(
            ids[remaining],
            test_size=validation_fraction,
            random_state=study.split_seed,
            stratify=buckets[remaining],
        )
        result.append(
            (
                tuple(sorted(map(int, fitting))),
                tuple(sorted(map(int, validation))),
                tuple(sorted(map(int, ids[heldout]))),
            )
        )
    if sorted(v for _, _, test in result for v in test) != sorted(ids.tolist()):
        raise ValueError("outer folds do not cover each engine exactly once")
    return result


def _resolved_taxonomy(taxonomy: FeatureTaxonomy, bundle: ModelBundle) -> FeatureTaxonomy:
    if not bundle.resolved_bounds or not bundle.resolved_rate_limits:
        raise ValueError("model requires resolved train-only proxy bounds/rates")
    return taxonomy.with_resolved_bounds(bundle.resolved_bounds, bundle.resolved_rate_limits)


def prepare_bundle_assets(
    config: AppConfig,
    taxonomy: FeatureTaxonomy,
    frame: pd.DataFrame,
    model_path: Path,
    root: Path,
    cutoffs: dict[str, float],
    *,
    coupling_source: Path | None = None,
    evaluation_engine_ids: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    """Fit exact-feature-order validators and validation-only residual calibration."""
    bundle = load_model_bundle(model_path)
    fit_ids, val_ids, test_ids = bundle_partitions(bundle, evaluation_engine_ids)
    root.mkdir(parents=True, exist_ok=True)
    training = frame.loc[frame.engine_id.isin(fit_ids)].copy()
    validation = frame.loc[frame.engine_id.isin(val_ids)].copy()
    resolved = _resolved_taxonomy(taxonomy, bundle)
    coupling_path = root / "coupling.joblib"
    if coupling_source is not None and not coupling_path.exists():
        shutil.copyfile(coupling_source, coupling_path)
    if not coupling_path.exists():
        columns = ["engine_id", "cycle", "rul", *bundle.feature_names]
        coupling = SensorCouplingModel.fit(
            training.loc[:, columns],
            resolved,
            training_engine_ids=fit_ids,
            failure_horizon=config.horizon_H,
            seed=config.seed,
        )
        coupling = calibrate_coupling_thresholds(
            coupling,
            validation,
            val_ids,
            reference_distribution=config.validation.coupling_calibration_reference,
            min_rul=max(config.horizon_H, config.validation.healthy_min_rul),
            evaluation_engine_ids=test_ids,
        )
        coupling.save(coupling_path)
    else:
        coupling = SensorCouplingModel.load(coupling_path)
        if (
            tuple(coupling.training_engine_ids) != fit_ids
            or tuple(coupling.calibration_engine_ids) != val_ids
        ):
            raise ValueError("persisted coupling partition mismatch")
    paths: dict[str, Any] = {"model": str(model_path), "coupling": str(coupling_path)}
    for version, cutoff in cutoffs.items():
        local = config.model_copy(deep=True)
        local.validation.mahalanobis_max = cutoff
        path = root / f"mahalanobis-{version}.joblib"
        if not path.exists():
            validator = fit_mahalanobis_validator(training, bundle, fit_ids, local)
            save_mahalanobis_validator(validator, path)
        paths["mahalanobis_" + version] = str(path)
    return {
        "paths": paths,
        "feature_names": list(bundle.feature_names),
        "fit_ids": list(fit_ids),
        "validation_ids": list(val_ids),
        "test_ids": list(test_ids),
        "hashes": {name: file_hash(Path(path)) for name, path in paths.items()},
        "coupling_calibration": coupling.calibration_report,
    }


def migrate_legacy_predictor(
    source: Path,
    destination: Path,
    training: pd.DataFrame,
    taxonomy: FeatureTaxonomy,
) -> ModelBundle:
    """Copy v2 fitted weights/scaler/calibrator unchanged and add train-derived metadata.

    This explicit trusted-local migration preserves original artifacts. No legacy validation
    scores or parameters are manufactured. Only bounds/rates and registry version are enriched.
    """
    bundle = joblib.load(source)
    if not isinstance(bundle, ModelBundle) or bundle.artifact_version != 2:
        raise ValueError("migration requires a trusted version-2 ModelBundle")
    training = training.loc[training.engine_id.isin(bundle.training_engine_ids)]
    fitted = taxonomy.fit_training_bounds(training, columns=bundle.feature_names)
    bounds = {
        name: (spec.bounds.minimum, spec.bounds.maximum)
        for name, spec in fitted.feature_by_name().items()
        if name in bundle.feature_names
    }
    bundle.resolved_bounds = cast(dict[str, tuple[float, float]], bounds)
    bundle.resolved_rate_limits = {
        name: limit.max_change_per_step for name, limit in fitted.actuator_constraints.items()
    }
    bundle.artifact_version = 3
    bundle.metrics = {
        **(bundle.metrics or {}),
        "metadata_migration": {
            "source": str(source),
            "source_sha256": file_hash(source),
            "predictor_scaler_calibrator_unchanged": True,
            "bounds_rates_source": "training engines only; frozen YAML percentile/rate rule",
        },
    }
    save_model_bundle(bundle, destination)
    return bundle


def prepare_study_assets(study: StudyConfig) -> dict[str, Any]:
    """Prepare all declared models/folds and H sensitivities; resume existing exact assets."""
    revision = source_revision()
    index_path = study.artifact_root / "index.json"
    if index_path.exists():
        previous: dict[str, Any] = json.loads(index_path.read_text(encoding="utf-8"))
        for key, asset in previous["models"].items():
            for name, path in asset["paths"].items():
                if file_hash(Path(path)) != asset["hashes"][name]:
                    raise ValueError(f"asset changed since checkpoint: {key}/{name}")
        from prescriptxai.evaluation.study import verify_asset_index

        try:
            verify_asset_index(study, previous)
        except ValueError as error:
            if not str(error).startswith("asset preparation is incomplete"):
                raise
        else:
            seal_preparation_inputs(study, previous)
            return previous
    signature = {
        "asset_code_hashes": {
            str(path): file_hash(path)
            for path in (
                Path("src/prescriptxai/evaluation/assets.py"),
                Path("src/prescriptxai/models/train.py"),
                Path("src/prescriptxai/models/registry.py"),
                Path("src/prescriptxai/constraints/taxonomy.py"),
                Path("src/prescriptxai/constraints/coupling.py"),
                Path("src/prescriptxai/validation/pipeline.py"),
                Path("src/prescriptxai/validation/tier4_coupling.py"),
            )
        },
        "study": study.model_dump(mode="json"),
        "taxonomy_sha256": file_hash(Path("configs/features.yaml")),
        "fold_provenance_sha256": file_hash(Path("artifacts/phase5/funnel.json")),
        "base_configs": {
            str(path): file_hash(path)
            for path in sorted(Path("configs/experiments").glob("phase7-FD*.yaml"))
        },
    }
    signature_path = study.artifact_root / "preparation.json"
    signature_path.parent.mkdir(parents=True, exist_ok=True)
    if signature_path.exists():
        if json.loads(signature_path.read_text(encoding="utf-8")) != signature:
            raise ValueError("asset resume source/config mismatch; preserve prior preparation")
    else:
        signature_path.write_text(json.dumps(signature, indent=2), encoding="utf-8")
    index: dict[str, Any] = {"preparation_source": revision, "models": {}}
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    old_provenance_path = Path("artifacts/phase5/funnel.json")
    old_provenance = json.loads(old_provenance_path.read_text(encoding="utf-8"))["provenance"]
    for subset, models in study.datasets.items():
        for model in models:
            config = load_config(Path(f"configs/experiments/phase7-{subset}-{model}-v1.yaml"))
            frame, _ = dataset_frames(config)
            root = study.artifact_root / f"{subset}-{model}"
            root.mkdir(parents=True, exist_ok=True)
            label = "xgboost" if model == "xgb" else model
            path = config.artifacts.model
            if subset == "FD001" and model in {"mlp", "lstm"} and not path.exists():
                migrate_legacy_predictor(
                    Path(f"artifacts/{subset}-{label}.joblib"), path, frame, taxonomy
                )
            if not path.exists():
                result = train_risk_model(frame, config, taxonomy, model)
                save_model_bundle(result.bundle, path)
            index["models"][f"{subset}/{model}/base"] = prepare_bundle_assets(
                config,
                taxonomy,
                frame,
                path,
                root,
                study.d_max_versions,
                coupling_source=(
                    load_config(study.frozen_solver_config).artifacts.coupling
                    if subset == "FD001"
                    else None
                ),
            )
            folds: list[tuple[tuple[int, ...], ...]]
            if subset == "FD001":
                folds = [
                    tuple(
                        tuple(old_provenance[f"fold-{i}/v1"][name])
                        for name in (
                            "fitting_engine_ids",
                            "validation_engine_ids",
                            "evaluation_engine_ids",
                        )
                    )
                    for i in range(1, study.grouped_folds + 1)
                ]
            else:
                folds = list(
                    grouped_partitions(
                        frame, study, config.data.validation_fraction, config.data.lifetime_buckets
                    )
                )
            for number, partitions in enumerate(folds, start=1):
                fold_root = root / f"fold-{number}"
                if subset == "FD001" and model == "xgb":
                    fold_path = Path(old_provenance[f"fold-{number}/v1"]["model_path"])
                else:
                    fold_path = fold_root / "model.joblib"
                    if not fold_path.exists():
                        result = train_risk_model(
                            frame, config, taxonomy, model, engine_partitions=cast(Any, partitions)
                        )
                        save_model_bundle(result.bundle, fold_path)
                index["models"][f"{subset}/{model}/fold-{number}"] = prepare_bundle_assets(
                    config,
                    taxonomy,
                    frame,
                    fold_path,
                    fold_root,
                    study.d_max_versions,
                    coupling_source=(
                        load_config(
                            Path(f"configs/experiments/phase6-fold-{number}-v1.yaml")
                        ).artifacts.coupling
                        if subset == "FD001"
                        else None
                    ),
                    evaluation_engine_ids=tuple(partitions[2]),
                )
                index_path.parent.mkdir(parents=True, exist_ok=True)
                index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
            if f"{subset}/{model}" in study.diagnostic_models:
                for horizon in study.horizon_H_grid:
                    if horizon == config.horizon_H:
                        continue
                    horizon_root = root / f"H-{horizon}"
                    horizon_path = horizon_root / "model.joblib"
                    local = config.model_copy(deep=True)
                    local.horizon_H = local.data.failure_horizon = horizon
                    if not horizon_path.exists():
                        result = train_risk_model(
                            frame,
                            local,
                            taxonomy,
                            model,
                            engine_partitions=bundle_partitions(load_model_bundle(path)),
                        )
                        save_model_bundle(result.bundle, horizon_path)
                    index["models"][f"{subset}/{model}/H-{horizon}"] = prepare_bundle_assets(
                        local, taxonomy, frame, horizon_path, horizon_root, study.d_max_versions
                    )
    index_path.write_text(json.dumps(index, indent=2, allow_nan=False), encoding="utf-8")
    seal_preparation_inputs(study, index)
    return index


def seal_preparation_inputs(study: StudyConfig, index: dict[str, Any]) -> None:
    """Seal current completed assets and verify archive/source identities on every later resume.

    The original preparation commit is retained. Existing legacy preparations have a dated
    post-preparation seal, not a retroactive claim that omitted inputs were signed before fitting.
    """
    config = load_config(study.frozen_solver_config)
    archive_hash = file_hash(config.data.root / config.data.archive_name)
    historical = json.loads(Path("artifacts/phase6/pipeline.json").read_text(encoding="utf-8"))
    expected = historical.get("archive_sha256")
    if expected is not None and archive_hash != expected:
        raise ValueError("raw archive differs from historical frozen measurement")
    sources = {"archive": archive_hash}
    for model in ("xgboost", "mlp", "lstm"):
        path = Path(f"artifacts/FD001-{model}.joblib")
        sources[str(path)] = file_hash(path)
    seal = {
        "preparation_source": index["preparation_source"],
        "index_sha256": content_hash_for_assets(index),
        "input_hashes": sources,
        "initial_signature_sha256": file_hash(study.artifact_root / "preparation.json"),
    }
    path = study.artifact_root / "completed-seal.json"
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if {key: saved.get(key) for key in seal} != seal:
            raise ValueError("completed preparation input/asset seal changed")
    else:
        path.write_text(
            json.dumps(
                {
                    **seal,
                    "sealed_at_utc": datetime.now(UTC).isoformat(),
                    "seal_source": source_revision(require_clean=False),
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def content_hash_for_assets(index: dict[str, Any]) -> str:
    """Canonical fingerprint with original per-asset preparation provenance retained."""
    from prescriptxai.evaluation.experiments import content_hash

    return content_hash(index)
