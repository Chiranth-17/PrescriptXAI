"""Reproducible C-MAPSS preparation and data-quality artifact generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from prescriptxai.data.cmapss import add_test_labels, load_cmapss_archive, verify_row_counts
from prescriptxai.data.download import verify_archive
from prescriptxai.data.preprocess import RegimeAwarePreprocessor, add_training_labels
from prescriptxai.data.splits import EngineSplits, split_engines


@dataclass(frozen=True)
class PreparedCmapss:
    """Prepared partitions and paths to reproducible quality/preprocessor artifacts."""

    splits: EngineSplits
    preprocessor: RegimeAwarePreprocessor
    report: dict[str, Any]
    report_path: Path
    preprocessor_path: Path
    dropped_sensors_path: Path
    partition_paths: dict[str, Path]


def _class_balance(frame: pd.DataFrame) -> dict[str, int]:
    """Count positive and negative labels without omitting an absent class."""
    counts = frame["y"].value_counts().to_dict()
    return {str(label): int(counts.get(label, 0)) for label in (0, 1)}


def _regime_counts(frame: pd.DataFrame) -> dict[str, int]:
    """Count rows assigned to each fitted operating regime."""
    counts = frame["operating_regime"].value_counts().sort_index()
    return {str(regime): int(count) for regime, count in counts.items()}


def prepare_cmapss(
    archive_path: Path,
    subset: str,
    processed_root: Path,
    artifact_root: Path,
    seed: int,
    failure_horizon: int,
    rul_cap: int | None,
    variance_threshold: float,
    regime_k: int,
    lifetime_buckets: int,
    train_fraction: float,
    validation_fraction: float,
    test_fraction: float,
    rolling_features: bool = False,
    rolling_window: int = 5,
    expected_sha256: str | None = None,
    expected_row_counts: dict[str, int] | None = None,
) -> PreparedCmapss:
    """Prepare real C-MAPSS data, fitting all learned transforms on train engines only.

    The training file is split by engine before variance filtering, regime clustering, or
    standardization. The official truncated test file receives its NASA-provided RUL labels.
    Processed CSV columns retain raw sensors and add explicit ``*_scaled`` columns.
    """
    source_sha256 = verify_archive(archive_path, expected_sha256)
    dataset = load_cmapss_archive(archive_path, subset)
    row_count_integrity = verify_row_counts(dataset, expected_row_counts)
    labeled = add_training_labels(dataset.train, rul_cap, failure_horizon)
    splits = split_engines(
        labeled,
        train_fraction,
        validation_fraction,
        test_fraction,
        seed,
        engine_column="unit_id",
        lifetime_buckets=lifetime_buckets,
    )
    preprocessor = RegimeAwarePreprocessor.fit(
        splits.train,
        subset,
        variance_threshold,
        regime_k,
        seed,
        rolling_features=rolling_features,
        rolling_window=rolling_window,
        engine_column="unit_id",
    )
    official_test = add_test_labels(
        dataset.test,
        dataset.test_rul,
        failure_horizon,
        rul_cap,
    )
    raw_partitions = {
        "train": splits.train,
        "validation": splits.validation,
        "holdout": splits.test,
        "official_test": official_test,
    }
    processed = {name: preprocessor.transform(frame) for name, frame in raw_partitions.items()}

    processed_root.mkdir(parents=True, exist_ok=True)
    artifact_root.mkdir(parents=True, exist_ok=True)
    partition_paths: dict[str, Path] = {}
    for name, frame in processed.items():
        path = processed_root / f"{subset}_{name}.csv"
        frame.to_csv(path, index=False, float_format="%.17g")
        partition_paths[name] = path

    preprocessor_path = preprocessor.save(artifact_root / f"{subset}_preprocessor.pkl")
    dropped_sensors_path = artifact_root / f"{subset}_dropped_sensors.json"
    dropped_sensors_path.write_text(
        json.dumps(
            {
                "subset": subset,
                "variance_threshold": variance_threshold,
                "dropped_sensors": list(preprocessor.dropped_sensor_names),
                "retained_sensors": list(preprocessor.retained_sensor_names),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    feature_names = [
        "op_setting_1",
        "op_setting_2",
        "op_setting_3",
        *preprocessor.retained_sensor_names,
    ]
    report: dict[str, Any] = {
        "subset": subset,
        "source": {
            "archive": archive_path.name,
            "sha256": source_sha256,
            "expected_sha256": expected_sha256,
            "row_count_integrity": row_count_integrity,
        },
        "row_counts": {
            "raw_train": int(len(dataset.train)),
            "raw_official_test": int(len(dataset.test)),
            **{name: int(len(frame)) for name, frame in processed.items()},
        },
        "engine_counts": {
            "raw_train": int(dataset.train["unit_id"].nunique()),
            "official_test": int(dataset.test["unit_id"].nunique()),
            "train": len(splits.train_engine_ids),
            "validation": len(splits.validation_engine_ids),
            "holdout": len(splits.test_engine_ids),
        },
        "split_engine_ids": {
            "train": list(splits.train_engine_ids),
            "validation": list(splits.validation_engine_ids),
            "holdout": list(splits.test_engine_ids),
        },
        "class_balance": {
            "all_training_engines": _class_balance(labeled),
            "train": _class_balance(splits.train),
            "validation": _class_balance(splits.validation),
            "holdout": _class_balance(splits.test),
            "official_test": _class_balance(official_test),
        },
        "feature_set": {
            "retained_model_features": feature_names,
            "dropped_sensors": list(preprocessor.dropped_sensor_names),
            "retained_sensors": list(preprocessor.retained_sensor_names),
            "scaled_columns": [f"{name}_scaled" for name in preprocessor.retained_sensor_names],
        },
        "regime_counts": {name: _regime_counts(frame) for name, frame in processed.items()},
        "preprocessing": preprocessor.metadata(),
        "checks": {
            "train_validation_engine_overlap": bool(
                set(splits.train_engine_ids) & set(splits.validation_engine_ids)
            ),
            "train_holdout_engine_overlap": bool(
                set(splits.train_engine_ids) & set(splits.test_engine_ids)
            ),
            "validation_holdout_engine_overlap": bool(
                set(splits.validation_engine_ids) & set(splits.test_engine_ids)
            ),
            "scalers_and_clusters_fit_engine_ids": list(preprocessor.training_engine_ids),
            "rolling_features_enabled": rolling_features,
        },
    }
    report_path = processed_root / f"{subset}_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return PreparedCmapss(
        splits=splits,
        preprocessor=preprocessor,
        report=report,
        report_path=report_path,
        preprocessor_path=preprocessor_path,
        dropped_sensors_path=dropped_sensors_path,
        partition_paths=partition_paths,
    )
