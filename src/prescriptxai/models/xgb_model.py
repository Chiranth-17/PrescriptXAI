"""Deterministic XGBoost construction and the positive-probability model adapter."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from numpy.typing import NDArray
from xgboost import XGBClassifier

from prescriptxai.artifacts import load_trusted_joblib
from prescriptxai.config import ModelConfig
from prescriptxai.models.base import FailureModel, validate_binary_labels, validate_feature_matrix


def build_xgb_estimator(
    seed: int,
    config: ModelConfig,
    scale_pos_weight: float = 1.0,
    early_stopping_rounds: int | None = None,
) -> XGBClassifier:
    """Create the configured CPU XGBoost binary classifier."""
    return XGBClassifier(
        n_estimators=config.xgb_n_estimators,
        max_depth=config.xgb_max_depth,
        learning_rate=config.xgb_learning_rate,
        subsample=config.xgb_subsample,
        colsample_bytree=config.xgb_colsample_bytree,
        reg_lambda=config.xgb_reg_lambda,
        scale_pos_weight=scale_pos_weight,
        early_stopping_rounds=early_stopping_rounds,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        n_jobs=1,
        random_state=seed,
    )


class XGBFailureModel(FailureModel):
    """XGBoost binary classifier exposing a one-dimensional failure probability."""

    def __init__(self, seed: int, config: ModelConfig) -> None:
        self.seed = seed
        self.config = config
        self.estimator: XGBClassifier | None = None

    def fit(
        self,
        features: NDArray[np.float64],
        labels: NDArray[np.float64],
        validation_data: tuple[NDArray[np.float64], NDArray[np.float64]] | None = None,
    ) -> XGBFailureModel:
        """Fit with training-only class weights and optional validation early stopping."""
        validate_feature_matrix(features)
        validate_binary_labels(labels, features.shape[0])
        labels_int = np.asarray(labels, dtype=np.int64)
        positive_count = int(labels_int.sum())
        negative_count = len(labels_int) - positive_count
        weight = negative_count / positive_count
        self.estimator = build_xgb_estimator(
            self.seed,
            self.config,
            weight,
            self.config.xgb_early_stopping_rounds if validation_data is not None else None,
        )
        fit_args: dict[str, object] = {}
        if validation_data is not None:
            validation_features, validation_labels = validation_data
            validate_feature_matrix(validation_features, features.shape[1])
            validation_int = np.asarray(validation_labels, dtype=np.int64)
            validate_binary_labels(validation_int, validation_features.shape[0])
            fit_args["eval_set"] = [(validation_features, validation_int)]
            fit_args["verbose"] = False
        self.estimator.fit(features, labels_int, **fit_args)
        return self

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Return positive-class probabilities for all finite input rows."""
        if self.estimator is None:
            raise ValueError("XGBoost model has not been fitted")
        validate_feature_matrix(features, int(self.estimator.n_features_in_))
        probabilities = np.asarray(self.estimator.predict_proba(features)[:, 1], dtype=np.float64)
        if (
            not np.isfinite(probabilities).all()
            or ((probabilities < 0) | (probabilities > 1)).any()
        ):
            raise ValueError("model generated invalid failure probabilities")
        return probabilities

    def save(self, path: Path) -> Path:
        """Persist this fitted predictor to disk."""
        if self.estimator is None:
            raise ValueError("cannot save an unfitted XGBoost model")
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: Path) -> XGBFailureModel:
        """Load a fitted XGBoost predictor artifact."""
        loaded = load_trusted_joblib(path)
        if not isinstance(loaded, cls):
            raise ValueError("artifact is not an XGBFailureModel")
        return loaded
