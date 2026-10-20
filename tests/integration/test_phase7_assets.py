"""Genuine fitting, legacy metadata migration and fixed engine partitions on fixture telemetry."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from fixtures.cmapss import make_cmapss_frame, write_cmapss_archive
from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.data.cmapss import to_model_frame
from prescriptxai.evaluation.assets import (
    bundle_partitions,
    dataset_frames,
    grouped_partitions,
    migrate_legacy_predictor,
    prepare_bundle_assets,
)
from prescriptxai.evaluation.experiments import file_hash, load_study
from prescriptxai.models.registry import load_model_bundle, save_model_bundle
from prescriptxai.models.train import train_risk_model


def test_fitted_asset_partitions_migration_and_covariances(tmp_path: Path) -> None:
    """Migrate real fitted weights unchanged and fit validators/calibration on separate engines."""
    config = load_config(Path("configs/default.yaml"))
    config.model_choice = config.model.risk_estimator = "torch"
    config.model.torch_epochs = 2
    config.model.torch_hidden_dims = [4]
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    frame = to_model_frame(make_cmapss_frame(12, min_cycles=90, max_cycles=110))
    partitions = (tuple(range(1, 9)), (9, 10), (11, 12))
    trained = train_risk_model(frame, config, taxonomy, "mlp", engine_partitions=partitions)
    assert bundle_partitions(trained.bundle) == partitions
    assert trained.metrics["calibration"]["fit_engine_ids"] == [9, 10]
    original = tmp_path / "original-v2.joblib"
    trained.bundle.artifact_version = 2
    joblib.dump(trained.bundle, original)
    source_hash = file_hash(original)
    before = trained.bundle.predict_risk(frame)
    migrated = migrate_legacy_predictor(original, tmp_path / "model.joblib", frame, taxonomy)
    np.testing.assert_array_equal(before, migrated.predict_risk(frame))
    assert file_hash(original) == source_hash and migrated.artifact_version == 3
    assert migrated.metrics["metadata_migration"]["source_sha256"] == source_hash
    with pytest.raises(ValueError, match="version-2"):
        migrate_legacy_predictor(
            tmp_path / "model.joblib", tmp_path / "wrong.joblib", frame, taxonomy
        )
    # Labels are derived from complete real fixture histories, never used as predictor inputs.
    frame["rul"] = frame.groupby("engine_id").cycle.transform("max") - frame.cycle
    asset = prepare_bundle_assets(
        config, taxonomy, frame, tmp_path / "model.joblib", tmp_path / "fit", {"v1": 5.0, "v2": 8.0}
    )
    resumed = prepare_bundle_assets(
        config, taxonomy, frame, tmp_path / "model.joblib", tmp_path / "fit", {"v1": 5.0, "v2": 8.0}
    )
    assert asset["hashes"] == resumed["hashes"]
    assert asset["fit_ids"] == list(partitions[0]) and asset["validation_ids"] == [9, 10]
    assert asset["coupling_calibration"]["engine_ids"] == [9, 10]
    bundle = load_model_bundle(tmp_path / "model.joblib")
    bundle.metrics["split_engines"].pop("test_holdout")
    with pytest.raises(ValueError, match="outer evaluation"):
        bundle_partitions(bundle)
    assert bundle_partitions(bundle, (11, 12)) == partitions
    bundle.metrics["split_engines"]["test_holdout"] = [12]
    with pytest.raises(ValueError, match="disagree"):
        bundle_partitions(bundle, (11, 12))
    bundle.metrics["split_engines"]["validation"] = [1]
    with pytest.raises(ValueError, match="overlap"):
        bundle_partitions(bundle)
    bundle.metrics = {}
    with pytest.raises(ValueError, match="explicit"):
        bundle_partitions(bundle)
    for bad in (
        (partitions[0], (1,), partitions[2]),
        (partitions[0], (), partitions[2]),
        (partitions[0], partitions[1], (12,)),
    ):
        with pytest.raises(ValueError, match="partition"):
            train_risk_model(frame, config, taxonomy, "mlp", engine_partitions=bad)
    save_model_bundle(migrated, tmp_path / "unchanged.joblib")


def test_official_rul_derivation_and_grouped_folds(tmp_path: Path) -> None:
    """Official truncated-file RUL is terminal RUL plus remaining observed cycles."""
    config = load_config(Path("configs/default.yaml"))
    path = write_cmapss_archive(tmp_path / "CMAPSSData.zip", train_engine_count=30)
    config.data.root, config.data.archive_name = path.parent, path.name
    training, official = dataset_frames(config)
    assert official.iloc[0].rul == 35 and official.iloc[29].rul == 6
    assert official.engine_id.min() == 10001
    study = load_study(Path("configs/experiments/phase7-study.yaml"))
    folds = grouped_partitions(training, study, 0.2, 3)
    assert folds == grouped_partitions(training, study, 0.2, 3)
    assert sorted(i for _, _, test in folds for i in test) == list(range(1, 31))
    for fit, validation, test in folds:
        assert set(fit).isdisjoint(validation) and set(test).isdisjoint(fit + validation)
    assert isinstance(training, pd.DataFrame)
