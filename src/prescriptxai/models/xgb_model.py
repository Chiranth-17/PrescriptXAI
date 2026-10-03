"""Deterministic XGBoost classifier construction."""

from __future__ import annotations

from xgboost import XGBClassifier

from prescriptxai.config import ModelConfig


def build_xgb_estimator(seed: int, config: ModelConfig) -> XGBClassifier:
    """Create the configured CPU XGBoost binary classifier."""
    return XGBClassifier(
        n_estimators=config.xgb_n_estimators,
        max_depth=config.xgb_max_depth,
        learning_rate=config.xgb_learning_rate,
        subsample=config.xgb_subsample,
        colsample_bytree=config.xgb_colsample_bytree,
        reg_lambda=config.xgb_reg_lambda,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        n_jobs=1,
        random_state=seed,
    )
