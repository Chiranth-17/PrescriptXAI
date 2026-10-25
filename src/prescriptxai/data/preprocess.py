"""RUL labels and train-only raw/scaled feature mappings for C-MAPSS."""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from prescriptxai.artifacts import load_trusted_pickle


def _engine_column(frame: pd.DataFrame) -> str:
    """Choose canonical unit provenance, accepting the previous model vocabulary."""
    if "unit_id" in frame.columns:
        return "unit_id"
    if "engine_id" in frame.columns:
        return "engine_id"
    raise ValueError("frame must contain unit_id or engine_id provenance")


def add_training_labels(
    frame: pd.DataFrame, rul_cap: int | None, failure_horizon: int
) -> pd.DataFrame:
    """Add run-to-failure RUL and ``y = 1[RUL <= failure_horizon]``.

    ``rul_cap`` optionally caps the reported RUL; ``None`` leaves it uncapped. Labels use exact,
    uncapped RUL. ``failure_label`` remains a compatibility alias for the existing model API.
    """
    if (rul_cap is not None and rul_cap <= 0) or failure_horizon <= 0:
        raise ValueError("failure_horizon and an enabled rul_cap must be positive")
    if frame.empty:
        raise ValueError("cannot label an empty dataframe")
    engine_column = _engine_column(frame)
    required = {engine_column, "cycle"}
    if not required.issubset(frame.columns):
        raise ValueError(f"frame must contain columns {sorted(required)}")
    if frame[[engine_column, "cycle"]].isna().any().any():
        raise ValueError("engine IDs and cycles must not be missing")
    if not np.isfinite(frame[[engine_column, "cycle"]].to_numpy(dtype=float)).all():
        raise ValueError("engine IDs and cycles must be finite")
    if (frame["cycle"] < 1).any():
        raise ValueError("cycles must be positive")
    if frame.duplicated([engine_column, "cycle"]).any():
        raise ValueError("frame contains duplicate engine/cycle rows")
    result = frame.copy()
    terminal_cycle = result.groupby(engine_column, sort=False)["cycle"].transform("max")
    exact_rul = terminal_cycle - result["cycle"]
    result["rul"] = exact_rul if rul_cap is None else exact_rul.clip(upper=rul_cap)
    labels = (exact_rul <= failure_horizon).astype("int8")
    result["y"] = labels
    result["failure_label"] = labels
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
        if getattr(self.scaler, "n_features_in_", None) != len(self.feature_names):
            raise ValueError("scaler has not been fitted for the configured feature width")
        # Same dense float64 operations/order as StandardScaler.transform. The named-frame
        # and finite-value checks above already cover its repeated array validation.
        scaled = values.copy()
        if self.scaler.with_mean:
            scaled -= self.scaler.mean_
        if self.scaler.with_std:
            scaled /= self.scaler.scale_
        return scaled


def fit_feature_scaler(
    training_frame: pd.DataFrame, feature_names: tuple[str, ...]
) -> FittedFeatureScaler:
    """Fit standardization using only rows in the supplied training-engine partition."""
    if training_frame.empty:
        raise ValueError("training dataframe must not be empty")
    if not feature_names:
        raise ValueError("feature_names must not be empty")
    if len(feature_names) != len(set(feature_names)):
        raise ValueError("feature_names must be unique")
    missing = set(feature_names) - set(training_frame.columns)
    if missing:
        raise ValueError(f"training dataframe is missing features: {sorted(missing)}")
    engine_column = _engine_column(training_frame)
    values = training_frame.loc[:, feature_names].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("training features must be finite")
    scaler = StandardScaler().fit(values)
    engine_ids = tuple(sorted(int(value) for value in training_frame[engine_column].unique()))
    return FittedFeatureScaler(feature_names, engine_ids, scaler)


@dataclass
class RegimeAwarePreprocessor:
    """Train-only sensor filtering and regime-wise standardization.

    Sensor values remain in raw columns and scaled values use ``*_scaled`` columns. For FD002
    and FD004, operating settings are standardized and clustered with KMeans; other subsets use
    one global regime. All fitted values use training engines only.
    """

    subset: str
    training_engine_ids: tuple[int, ...]
    sensor_names: tuple[str, ...]
    retained_sensor_names: tuple[str, ...]
    dropped_sensor_names: tuple[str, ...]
    setting_names: tuple[str, ...]
    variance_threshold: float
    regime_k: int
    seed: int
    rolling_features: bool
    rolling_window: int
    settings_scaler: StandardScaler | None
    clusterer: KMeans | None
    regime_means: dict[int, dict[str, float]]
    regime_scales: dict[int, dict[str, float]]
    regime_row_counts: dict[int, int]

    @classmethod
    def fit(
        cls,
        training_frame: pd.DataFrame,
        subset: str,
        variance_threshold: float,
        regime_k: int,
        seed: int,
        rolling_features: bool = False,
        rolling_window: int = 5,
        engine_column: str | None = None,
        sensor_names: tuple[str, ...] | None = None,
        setting_names: tuple[str, ...] = ("op_setting_1", "op_setting_2", "op_setting_3"),
    ) -> RegimeAwarePreprocessor:
        """Fit filtering, optional regimes, and sensor statistics on training data."""
        if subset not in {"FD001", "FD002", "FD003", "FD004"}:
            raise ValueError("subset must be FD001, FD002, FD003, or FD004")
        if training_frame.empty:
            raise ValueError("training dataframe must not be empty")
        if not np.isfinite(variance_threshold) or variance_threshold < 0:
            raise ValueError("variance_threshold must be finite and non-negative")
        if regime_k < 1 or seed < 0 or rolling_window < 1:
            raise ValueError("regime_k, rolling_window, and seed must be valid")
        engine_column = engine_column or _engine_column(training_frame)
        if engine_column not in training_frame.columns:
            raise ValueError(f"training dataframe is missing {engine_column}")
        sensor_names = sensor_names or tuple(f"s{index}" for index in range(1, 22))
        missing = (set(sensor_names) | set(setting_names) | {engine_column}) - set(
            training_frame.columns
        )
        if missing:
            raise ValueError(f"training dataframe is missing features: {sorted(missing)}")
        sensor_values = training_frame.loc[:, sensor_names].to_numpy(dtype=float)
        setting_values = training_frame.loc[:, setting_names].to_numpy(dtype=float)
        if not np.isfinite(sensor_values).all() or not np.isfinite(setting_values).all():
            raise ValueError("training features must be finite")
        if training_frame[engine_column].isna().any():
            raise ValueError("training engine IDs must not be missing")

        variances = np.var(sensor_values, axis=0)
        retained = tuple(
            name
            for name, variance in zip(sensor_names, variances, strict=True)
            if variance > variance_threshold
        )
        dropped = tuple(name for name in sensor_names if name not in retained)
        if not retained:
            raise ValueError("variance filtering removed every sensor")

        settings_scaler: StandardScaler | None = None
        clusterer: KMeans | None = None
        if subset in {"FD002", "FD004"}:
            settings_scaler = StandardScaler().fit(setting_values)
            scaled_settings = settings_scaler.transform(setting_values)
            distinct_settings = np.unique(scaled_settings, axis=0).shape[0]
            cluster_count = min(regime_k, len(training_frame), distinct_settings)
            clusterer = KMeans(n_clusters=cluster_count, random_state=seed, n_init=10)
            regime_ids = clusterer.fit_predict(scaled_settings)
        else:
            regime_ids = np.zeros(len(training_frame), dtype=np.int32)

        means: dict[int, dict[str, float]] = {}
        scales: dict[int, dict[str, float]] = {}
        row_counts: dict[int, int] = {}
        active_values = training_frame.loc[:, retained].to_numpy(dtype=float)
        for regime in sorted(int(value) for value in np.unique(regime_ids)):
            mask = regime_ids == regime
            regime_values = active_values[mask]
            mean = regime_values.mean(axis=0)
            scale = regime_values.std(axis=0)
            scale = np.where(scale <= np.finfo(float).eps, 1.0, scale)
            means[regime] = dict(zip(retained, mean.astype(float).tolist(), strict=True))
            scales[regime] = dict(zip(retained, scale.astype(float).tolist(), strict=True))
            row_counts[regime] = int(mask.sum())

        engine_ids = tuple(sorted(int(value) for value in training_frame[engine_column].unique()))
        return cls(
            subset=subset,
            training_engine_ids=engine_ids,
            sensor_names=tuple(sensor_names),
            retained_sensor_names=retained,
            dropped_sensor_names=dropped,
            setting_names=tuple(setting_names),
            variance_threshold=float(variance_threshold),
            regime_k=regime_k,
            seed=seed,
            rolling_features=rolling_features,
            rolling_window=rolling_window,
            settings_scaler=settings_scaler,
            clusterer=clusterer,
            regime_means=means,
            regime_scales=scales,
            regime_row_counts=row_counts,
        )

    def assign_regimes(self, frame: pd.DataFrame) -> np.ndarray:
        """Assign deterministic regimes from fitted settings scaling and KMeans."""
        if frame.empty:
            raise ValueError("cannot assign regimes for an empty dataframe")
        if self.clusterer is None or self.settings_scaler is None:
            return np.zeros(len(frame), dtype=np.int32)
        missing = set(self.setting_names) - set(frame.columns)
        if missing:
            raise ValueError(f"dataframe is missing operating settings: {sorted(missing)}")
        settings = frame.loc[:, self.setting_names].to_numpy(dtype=float)
        if not np.isfinite(settings).all():
            raise ValueError("operating settings must be finite")
        scaled = self.settings_scaler.transform(settings)
        return cast(np.ndarray, self.clusterer.predict(scaled)).astype(np.int32)

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Append regime labels and scaled sensor columns while preserving raw units."""
        if frame.empty:
            raise ValueError("cannot transform an empty dataframe")
        missing = set(self.retained_sensor_names) - set(frame.columns)
        if missing:
            raise ValueError(f"dataframe is missing sensors: {sorted(missing)}")
        raw_values = frame.loc[:, self.retained_sensor_names].to_numpy(dtype=float)
        if not np.isfinite(raw_values).all():
            raise ValueError("sensor values must be finite")
        regimes = self.assign_regimes(frame)
        output = frame.copy()
        present_dropped = [name for name in self.dropped_sensor_names if name in output.columns]
        output.drop(columns=present_dropped, inplace=True)
        output["operating_regime"] = regimes
        scaled_names = [f"{name}_scaled" for name in self.retained_sensor_names]
        for regime in np.unique(regimes):
            regime_int = int(regime)
            if regime_int not in self.regime_means:
                raise ValueError(f"no training statistics were fitted for regime {regime_int}")
            mask = regimes == regime
            means = np.asarray(
                [self.regime_means[regime_int][n] for n in self.retained_sensor_names]
            )
            scales = np.asarray(
                [self.regime_scales[regime_int][n] for n in self.retained_sensor_names]
            )
            values = output.loc[mask, self.retained_sensor_names].to_numpy(dtype=float)
            output.loc[mask, scaled_names] = (values - means) / scales
        if self.rolling_features:
            unit_column = "unit_id" if "unit_id" in output else "engine_id"
            if unit_column not in output:
                raise ValueError("rolling features require unit_id or engine_id")
            for name in self.retained_sensor_names:
                output[f"{name}_rollmean_{self.rolling_window}"] = output.groupby(
                    unit_column, sort=False
                )[name].transform(
                    lambda values: values.rolling(self.rolling_window, min_periods=1).mean()
                )
        return output

    def inverse_transform(self, transformed_frame: pd.DataFrame) -> pd.DataFrame:
        """Reconstruct retained raw sensors from scaled columns with 1e-8 tolerance."""
        if transformed_frame.empty:
            raise ValueError("cannot inverse-transform an empty dataframe")
        if "operating_regime" not in transformed_frame:
            raise ValueError("transformed dataframe must contain operating_regime")
        scaled_names = [f"{name}_scaled" for name in self.retained_sensor_names]
        missing = set(scaled_names) - set(transformed_frame.columns)
        if missing:
            raise ValueError(f"transformed dataframe is missing scaled sensors: {sorted(missing)}")
        raw_regimes = transformed_frame["operating_regime"].to_numpy()
        if any(
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, float, np.integer, np.floating))
            or not np.isfinite(value)
            or value < 0
            or value != int(value)
            for value in raw_regimes
        ):
            raise ValueError("operating_regime values must be finite nonnegative integers")
        if any(int(value) not in self.regime_means for value in raw_regimes):
            raise ValueError("no training statistics were fitted for an operating_regime")
        regimes: NDArray[np.int64] = np.asarray(raw_regimes, dtype=np.int64)
        output = transformed_frame.copy()
        for regime in np.unique(regimes):
            regime_int = int(regime)
            if regime_int not in self.regime_means:
                raise ValueError(f"no training statistics were fitted for regime {regime_int}")
            mask = regimes == regime
            means = np.asarray(
                [self.regime_means[regime_int][n] for n in self.retained_sensor_names]
            )
            scales = np.asarray(
                [self.regime_scales[regime_int][n] for n in self.retained_sensor_names]
            )
            scaled = output.loc[mask, scaled_names].to_numpy(dtype=float)
            if not np.isfinite(scaled).all():
                raise ValueError("scaled sensor values must be finite")
            output.loc[mask, self.retained_sensor_names] = scaled * scales + means
        return output

    def metadata(self) -> dict[str, object]:
        """Return JSON-ready fitted preprocessing metadata for audit reports."""
        return {
            "subset": self.subset,
            "training_engine_ids": list(self.training_engine_ids),
            "sensor_names": list(self.sensor_names),
            "retained_sensor_names": list(self.retained_sensor_names),
            "dropped_sensor_names": list(self.dropped_sensor_names),
            "variance_threshold": self.variance_threshold,
            "regime_k_requested": self.regime_k,
            "regime_row_counts_fit": {str(k): v for k, v in self.regime_row_counts.items()},
            "regime_means": {str(k): v for k, v in self.regime_means.items()},
            "regime_scales": {str(k): v for k, v in self.regime_scales.items()},
            "rolling_features": self.rolling_features,
            "rolling_window": self.rolling_window,
        }

    def save(self, path: Path) -> Path:
        """Persist fitted clustering and train-only statistics for future transforms."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as output:
            pickle.dump(self, output, protocol=pickle.HIGHEST_PROTOCOL)
        return path

    @classmethod
    def load(cls, path: Path) -> RegimeAwarePreprocessor:
        """Load an artifact produced locally by :meth:`save`."""
        loaded = load_trusted_pickle(path)
        if not isinstance(loaded, cls):
            raise ValueError(f"artifact at {path} is not a {cls.__name__}")
        return loaded
