"""Integration tests for engine-safe training and artifact persistence."""

from pathlib import Path

import numpy as np
import pandas as pd

from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.models.registry import load_model_bundle, save_model_bundle
from prescriptxai.models.train import train_risk_model


def _training_fixture() -> pd.DataFrame:
    """Synthetic rows used only to verify training flow and persistence."""
    return pd.DataFrame(
        [
            {
                "engine_id": engine,
                "cycle": cycle,
                "op_setting_1": float(engine % 3),
                "op_setting_2": float(engine % 2),
                "op_setting_3": float(cycle / 10),
                **{
                    f"sensor_{sensor}": float(engine * cycle * sensor / 100)
                    for sensor in range(1, 22)
                },
            }
            for engine in range(1, 31)
            for cycle in range(1, 9)
        ]
    )


def test_training_calibrates_on_train_engines_and_round_trips_bundle(tmp_path: Path) -> None:
    """Training split, scaler provenance, calibration, and artifact metadata round-trip."""
    config = load_config(Path("configs/default.yaml"))
    config.data.failure_horizon = 2
    config.model.calibration_folds = 3
    config.model.xgb_n_estimators = 8
    config.model.xgb_max_depth = 2
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    result = train_risk_model(_training_fixture(), config, taxonomy)

    assert set(result.bundle.training_engine_ids) == set(result.splits.train_engine_ids)
    assert set(result.bundle.training_engine_ids).isdisjoint(result.splits.validation_engine_ids)
    assert len(result.validation_labels) == len(result.splits.validation)
    assert result.validation_risk.shape == result.validation_labels.shape
    assert np.isfinite(result.validation_risk).all()

    artifact_path = save_model_bundle(result.bundle, tmp_path / "models" / "fixture.joblib")
    reloaded = load_model_bundle(artifact_path, expected_features=result.bundle.feature_names)
    np.testing.assert_allclose(
        result.bundle.predict_risk(result.splits.validation),
        reloaded.predict_risk(result.splits.validation),
    )
