"""Deterministic engine-grouped training and validation prediction workflow."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.calibration import CalibratedClassifierCV

from prescriptxai.config import AppConfig
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.data.cmapss import to_model_frame
from prescriptxai.data.preprocess import (
    FittedFeatureScaler,
    add_training_labels,
    fit_feature_scaler,
)
from prescriptxai.data.splits import EngineSplits, split_engines
from prescriptxai.models.base import RiskEstimator
from prescriptxai.models.calibration import fit_group_calibrator
from prescriptxai.models.registry import ModelBundle
from prescriptxai.models.torch_models import TorchMLPClassifier
from prescriptxai.models.xgb_model import build_xgb_estimator


@dataclass(frozen=True)
class TrainingResult:
    """Trained bundle, engine partitions, and untouched validation predictions."""

    bundle: ModelBundle
    splits: EngineSplits
    validation_labels: NDArray[np.int64]
    validation_risk: NDArray[np.float64]


def _model_feature_names(taxonomy: FeatureTaxonomy, frame: pd.DataFrame) -> tuple[str, ...]:
    """Collect declared telemetry features while excluding engine and cycle identifiers."""
    excluded = {"engine_id", "cycle"}
    names = tuple(
        feature
        for group in taxonomy.feature_groups.model_dump().values()
        for feature in group["features"]
        if feature not in excluded
    )
    if not names:
        raise ValueError("feature taxonomy declares no model features")
    if len(names) != len(set(names)):
        raise ValueError("feature taxonomy contains duplicate model features")
    missing = set(names) - set(frame.columns)
    if missing:
        raise ValueError(f"training data is missing configured features: {sorted(missing)}")
    return names


def _build_estimator(config: AppConfig) -> RiskEstimator:
    """Construct the estimator selected in YAML configuration."""
    if config.model.risk_estimator == "xgboost":
        return build_xgb_estimator(config.seed, config.model)
    return TorchMLPClassifier(
        hidden_dims=tuple(config.model.torch_hidden_dims),
        learning_rate=config.model.torch_learning_rate,
        epochs=config.model.torch_epochs,
        batch_size=config.model.torch_batch_size,
        seed=config.seed,
        device=config.model.torch_device,
    )


def train_risk_model(
    training_telemetry: pd.DataFrame,
    config: AppConfig,
    taxonomy: FeatureTaxonomy,
) -> TrainingResult:
    """Split engines, fit training-only preprocessing, calibrate, and score validation engines.

    The input is the run-to-failure training telemetry. The official C-MAPSS test RUL file is not
    used as recourse evidence or merged into training.
    """
    model_telemetry = to_model_frame(training_telemetry)
    labeled = add_training_labels(
        model_telemetry,
        config.data.rul_cap,
        config.data.failure_horizon,
    )
    splits = split_engines(
        labeled,
        config.data.train_fraction,
        config.data.validation_fraction,
        config.data.test_fraction,
        config.seed,
        lifetime_buckets=config.data.lifetime_buckets,
    )
    feature_names = _model_feature_names(taxonomy, labeled)
    scaler: FittedFeatureScaler = fit_feature_scaler(splits.train, feature_names)
    x_train = scaler.transform(splits.train[list(feature_names)])
    y_train = splits.train["failure_label"].to_numpy(dtype=np.int64)
    train_engine_ids = splits.train["engine_id"].to_numpy(dtype=np.int64)
    estimator = _build_estimator(config)
    calibrated: CalibratedClassifierCV = fit_group_calibrator(
        estimator,
        x_train,
        y_train,
        train_engine_ids,
        config.model,
    )
    bundle = ModelBundle(
        estimator=calibrated,
        scaler=scaler,
        feature_names=feature_names,
        training_engine_ids=splits.train_engine_ids,
        model_type=config.model.risk_estimator,
        seed=config.seed,
    )
    validation_labels = splits.validation["failure_label"].to_numpy(dtype=np.int64)
    validation_risk = bundle.predict_risk(splits.validation)
    return TrainingResult(bundle, splits, validation_labels, validation_risk)
