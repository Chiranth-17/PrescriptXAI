"""RUL labels and training-only feature scaling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def add_training_labels(frame: pd.DataFrame, rul_cap: int, failure_horizon: int) -> pd.DataFrame:
    """Add exact run-to-failure RUL and configurable binary failure labels.

    RUL is `max_cycle(engine) - cycle`; the model label is `1[RUL <= failure_horizon]`.
    ``rul_cap`` caps the regression-style RUL feature only after exact RUL has been derived.
    """
    if rul_cap <= 0 or failure_horizon <= 0:
        raise ValueError("rul_cap and failure_horizon must be positive")
    if frame.empty:
        raise ValueError("cannot label an empty dataframe")
    required = {"engine_id", "cycle"}
    if not required.issubset(frame.columns):
        raise ValueError(f"frame must contain columns {sorted(required)}")
    if frame[["engine_id", "cycle"]].isna().any().any():
        raise ValueError("engine IDs and cycles must not be missing")
    if not np.isfinite(frame[["engine_id", "cycle"]].to_numpy(dtype=float)).all():
        raise ValueError("engine IDs and cycles must be finite")
    if (frame["cycle"] < 1).any():
        raise ValueError("cycles must be positive")
    if frame.duplicated(["engine_id", "cycle"]).any():
        raise ValueError("frame contains duplicate engine/cycle rows")
    result = frame.copy()
    terminal_cycle = result.groupby("engine_id", sort=False)["cycle"].transform("max")
    exact_rul = terminal_cycle - result["cycle"]
    result["rul"] = exact_rul.clip(upper=rul_cap)
    result["failure_label"] = (exact_rul <= failure_horizon).astype("int8")
    return result


@dataclass
class FittedFeatureScaler:
    """Standard scaler with explicit feature order and training-engine provenance."""

    feature_names: tuple[str, ...]
    training_engine_ids: tuple[int, ...]
    scaler: StandardScaler

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        """Transform a nonempty finite dataframe in the recorded feature order."""
        if frame.empty:
            raise ValueError("cannot transform an empty dataframe")
        if tuple(frame.columns) != self.feature_names:
            raise ValueError("feature columns/order do not match the fitted scaler")
        values = frame.to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("features must be finite")
        return cast(np.ndarray, self.scaler.transform(values))


def fit_feature_scaler(
    training_frame: pd.DataFrame, feature_names: tuple[str, ...]
) -> FittedFeatureScaler:
    """Fit standardization using only rows in the training-engine partition.

    `StandardScaler` maps constant features to finite zeros by using unit scale for zero-variance
    columns. Feature names and engine IDs are persisted alongside the fitted transform.
    """
    if training_frame.empty:
        raise ValueError("training dataframe must not be empty")
    if not feature_names:
        raise ValueError("feature_names must not be empty")
    if len(feature_names) != len(set(feature_names)):
        raise ValueError("feature_names must be unique")
    missing = set(feature_names) - set(training_frame.columns)
    if missing:
        raise ValueError(f"training dataframe is missing features: {sorted(missing)}")
    if "engine_id" not in training_frame.columns:
        raise ValueError("training dataframe must contain engine_id provenance")
    values = training_frame.loc[:, feature_names].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("training features must be finite")
    scaler = StandardScaler()
    scaler.fit(values)
    engine_ids = tuple(sorted(int(value) for value in training_frame["engine_id"].unique()))
    return FittedFeatureScaler(feature_names, engine_ids, scaler)
