"""Engine-disjoint predictor fitting, validation calibration, and holdout evaluation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TypedDict

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from prescriptxai.config import AppConfig
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.data.cmapss import to_model_frame
from prescriptxai.data.preprocess import (
    FittedFeatureScaler,
    add_training_labels,
    fit_feature_scaler,
)
from prescriptxai.data.splits import EngineSplits, split_engines
from prescriptxai.evaluation.metrics import predictor_metrics, surrogate_fidelity
from prescriptxai.models.base import FailureModel
from prescriptxai.models.calibration import (
    calibration_diagnostics,
    fit_probability_calibrator,
)
from prescriptxai.models.registry import ModelBundle
from prescriptxai.models.torch_models import LSTMFailureModel, MLPFailureModel
from prescriptxai.models.xgb_model import XGBFailureModel


@dataclass(frozen=True)
class TrainingResult:
    """Fitted predictor, engine partitions, and independent validation/holdout diagnostics."""

    bundle: ModelBundle
    splits: EngineSplits
    validation_labels: NDArray[np.int64]
    validation_risk: NDArray[np.float64]
    test_labels: NDArray[np.int64]
    test_risk: NDArray[np.float64]
    metrics: dict[str, object]
    test_probabilities_before_calibration: NDArray[np.float64]
    surrogate_test_risk: NDArray[np.float64] | None


class _TorchModelOptions(TypedDict):
    """Constructor options shared by the configured torch architectures."""

    hidden_dims: tuple[int, ...]
    learning_rate: float
    epochs: int
    batch_size: int
    seed: int
    device: str
    early_stopping_patience: int
    gradient_clip_norm: float
    deterministic: bool


def _model_feature_names(
    taxonomy: FeatureTaxonomy,
    frame: pd.DataFrame,
    training_frame: pd.DataFrame,
    variance_threshold: float,
    variance_features: frozenset[str] | None = None,
) -> tuple[str, ...]:
    """Select declared snapshot inputs, dropping only sensors constant on training engines."""
    excluded = {"engine_id", "cycle"}
    declared = tuple(
        feature
        for group in taxonomy.feature_groups.model_dump().values()
        for feature in group["features"]
        if feature not in excluded
    )
    if not declared:
        raise ValueError("feature taxonomy declares no model inputs")
    if len(declared) != len(set(declared)):
        raise ValueError("feature taxonomy contains duplicate model inputs")
    missing = set(declared) - set(frame.columns)
    if missing:
        raise ValueError(f"training data is missing configured features: {sorted(missing)}")
    retained: list[str] = []
    for name in declared:
        filter_variance = (
            name.startswith("sensor_") if variance_features is None else name in variance_features
        )
        if filter_variance:
            variance = float(training_frame[name].to_numpy(dtype=float).var())
            if variance <= variance_threshold:
                continue
        retained.append(name)
    if not retained:
        raise ValueError("training feature filtering removed every declared input")
    return tuple(retained)


def _build_estimator(config: AppConfig, model_name: str) -> FailureModel:
    """Construct the requested predictor using all configured deterministic settings."""
    model = config.model
    if model_name == "xgb":
        return XGBFailureModel(config.seed, model)
    common: _TorchModelOptions = {
        "hidden_dims": tuple(model.torch_hidden_dims),
        "learning_rate": model.torch_learning_rate,
        "epochs": model.torch_epochs,
        "batch_size": model.torch_batch_size,
        "seed": config.seed,
        "device": model.torch_device,
        "early_stopping_patience": model.torch_early_stopping_patience,
        "gradient_clip_norm": model.torch_gradient_clip_norm,
        "deterministic": model.torch_deterministic,
    }
    if model_name == "mlp":
        return MLPFailureModel(**common)
    if model_name == "lstm":
        return LSTMFailureModel(window=model.lstm_window, **common)
    raise ValueError("model must be one of xgb, mlp, or lstm")


def make_engine_sequences(
    frame: pd.DataFrame,
    feature_names: tuple[str, ...],
    window: int,
    scaler: FittedFeatureScaler,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Create padded rolling windows within engines without crossing partition boundaries.

    Before an engine has ``window`` rows, its first scaled observation is repeated on the left.
    The label is the current row's label. During recourse only the newest window row is mutable;
    all earlier rows are observed history and remain fixed.
    """
    if window < 1 or frame.empty:
        raise ValueError("sequence window must be positive and input frame nonempty")
    if not {"engine_id", "cycle", "failure_label"}.issubset(frame.columns):
        raise ValueError("sequence input requires engine_id, cycle, and failure_label columns")
    windows: list[NDArray[np.float64]] = []
    targets: list[int] = []
    for _, engine in frame.sort_values(["engine_id", "cycle"]).groupby("engine_id", sort=False):
        raw = engine.loc[:, list(feature_names)]
        values = scaler.transform(raw)
        labels = engine["failure_label"].to_numpy(dtype=np.int64)
        for end in range(len(engine)):
            start = max(0, end - window + 1)
            current = values[start : end + 1]
            if len(current) < window:
                padding = np.repeat(current[:1], window - len(current), axis=0)
                current = np.concatenate((padding, current), axis=0)
            windows.append(np.asarray(current, dtype=np.float64))
            targets.append(int(labels[end]))
    return np.stack(windows), np.asarray(targets, dtype=np.int64)


def _partition_arrays(
    frame: pd.DataFrame,
    feature_names: tuple[str, ...],
    scaler: FittedFeatureScaler,
    model_name: str,
    config: AppConfig,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Return scaled snapshot rows or within-engine sequence windows."""
    if model_name == "lstm":
        return make_engine_sequences(frame, feature_names, config.model.lstm_window, scaler)
    return (
        scaler.transform(frame.loc[:, list(feature_names)]),
        frame["failure_label"].to_numpy(dtype=np.int64),
    )


def _git_commit() -> str | None:
    """Read the package's build/checkout commit independently of the working directory."""
    from prescriptxai.provenance import source_identity

    commit = source_identity().get("git_commit")
    return str(commit) if commit else None


def _configuration_hash(config: AppConfig, selected_model: str) -> str:
    """Hash the fully validated config for artifact provenance."""
    payload = config.model_dump(mode="json")
    payload["selected_model"] = selected_model
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def train_risk_model(
    training_telemetry: pd.DataFrame,
    config: AppConfig,
    taxonomy: FeatureTaxonomy,
    model_name: str | None = None,
    *,
    engine_partitions: tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]] | None = None,
) -> TrainingResult:
    """Fit on train engines, calibrate on validation engines, and evaluate held-out engines.

    The internal holdout is never used for stopping, calibration, surrogate fitting, or model
    selection. NASA's official truncated test file is not substituted for this engine holdout.
    """
    selected_model = model_name or {
        "xgboost": "xgb",
        "torch": "mlp",
        "lstm": "lstm",
    }.get(config.model.risk_estimator, "xgb")
    if selected_model not in {"xgb", "mlp", "lstm"}:
        raise ValueError("model must be one of xgb, mlp, or lstm")
    model_telemetry = to_model_frame(training_telemetry)
    labeled = add_training_labels(model_telemetry, config.data.rul_cap, config.data.failure_horizon)
    if engine_partitions is None:
        splits = split_engines(
            labeled,
            config.data.train_fraction,
            config.data.validation_fraction,
            config.data.test_fraction,
            config.seed,
            lifetime_buckets=config.data.lifetime_buckets,
        )
    else:
        train_ids, val_ids, test_ids = engine_partitions
        sets = [set(values) for values in engine_partitions]
        observed = set(int(v) for v in labeled.engine_id.unique())
        if (
            any(not values or len(values) != len(set(values)) for values in engine_partitions)
            or sets[0] & sets[1]
            or sets[0] & sets[2]
            or sets[1] & sets[2]
            or set.union(*sets) != observed
        ):
            raise ValueError("explicit engine partitions must be nonempty, disjoint and complete")
        splits = EngineSplits(
            labeled.loc[labeled.engine_id.isin(train_ids)].copy(),
            labeled.loc[labeled.engine_id.isin(val_ids)].copy(),
            labeled.loc[labeled.engine_id.isin(test_ids)].copy(),
            train_ids,
            val_ids,
            test_ids,
        )
    return fit_partitioned_risk_model(splits, config, taxonomy, selected_model)


def fit_partitioned_risk_model(
    splits: EngineSplits,
    config: AppConfig,
    taxonomy: FeatureTaxonomy,
    selected_model: str,
    *,
    variance_features: frozenset[str] | None = None,
) -> TrainingResult:
    """Fit, calibrate and score already labeled, unit-disjoint model rows."""
    feature_names = _model_feature_names(
        taxonomy, splits.train, splits.train, config.data.variance_threshold, variance_features
    )
    taxonomy.validate_model_feature_coverage(feature_names)
    taxonomy = taxonomy.fit_training_bounds(splits.train, columns=feature_names)
    taxonomy.validate_bounds_against_observed(splits.train, columns=feature_names)
    scaler = fit_feature_scaler(splits.train, feature_names)
    x_train, y_train = _partition_arrays(
        splits.train, feature_names, scaler, selected_model, config
    )
    x_validation, y_validation = _partition_arrays(
        splits.validation, feature_names, scaler, selected_model, config
    )
    x_test, y_test = _partition_arrays(splits.test, feature_names, scaler, selected_model, config)
    estimator = _build_estimator(config, selected_model)
    estimator.fit(x_train, y_train, validation_data=(x_validation, y_validation))

    validation_before = estimator.predict_proba(x_validation)
    calibrator = fit_probability_calibrator(
        validation_before, y_validation, config.model.calibration_method
    )
    validation_after = calibrator.transform(validation_before)
    test_before = estimator.predict_proba(x_test)
    test_after = calibrator.transform(test_before)

    surrogate: MLPFailureModel | None = None
    surrogate_test_risk: NDArray[np.float64] | None = None
    fidelity: dict[str, object] | None = None
    if selected_model == "xgb":
        surrogate_candidate = _build_estimator(config, "mlp")
        if not isinstance(surrogate_candidate, MLPFailureModel):
            raise TypeError("XGBoost distillation requires an MLPFailureModel")
        surrogate = surrogate_candidate
        train_teacher = estimator.predict_proba(x_train)
        validation_teacher = validation_before
        surrogate.fit_distillation(
            x_train,
            train_teacher,
            (x_validation, validation_teacher),
        )
        surrogate_test_raw = surrogate.predict_proba(x_test)
        surrogate_test_risk = calibrator.transform(surrogate_test_raw)
        fidelity = surrogate_fidelity(
            test_after,
            surrogate_test_risk,
            config.tau_safe,
            config.tau_danger,
        )

    validation_engine_ids = tuple(sorted(int(value) for value in splits.validation_engine_ids))
    if set(validation_engine_ids) & set(splits.train_engine_ids):
        raise ValueError("train and validation engine IDs overlap")
    if set(splits.test_engine_ids) & (set(splits.train_engine_ids) | set(validation_engine_ids)):
        raise ValueError("test holdout engine IDs overlap with train or validation")
    test_calibration_before = calibration_diagnostics(
        y_test, test_before, config.model.calibration_bins
    )
    test_calibration_after = calibration_diagnostics(
        y_test, test_after, config.model.calibration_bins
    )
    validation_calibration_before = calibration_diagnostics(
        y_validation, validation_before, config.model.calibration_bins
    )
    validation_calibration_after = calibration_diagnostics(
        y_validation, validation_after, config.model.calibration_bins
    )
    metrics: dict[str, object] = {
        "dataset": config.data.dataset,
        "model": selected_model,
        "horizon_H": config.data.failure_horizon,
        "tau_danger": config.tau_danger,
        "tau_safe": config.tau_safe,
        "feature_names": list(feature_names),
        "split_engines": {
            "train": list(splits.train_engine_ids),
            "validation": list(splits.validation_engine_ids),
            "test_holdout": list(splits.test_engine_ids),
            "train_validation_overlap": False,
            "train_test_overlap": False,
            "validation_test_overlap": False,
        },
        "calibration": {
            "method": config.model.calibration_method,
            "fit_engine_ids": list(splits.validation_engine_ids),
            "validation_before": validation_calibration_before,
            "validation_after": validation_calibration_after,
            "test_before": test_calibration_before,
            "test_after": test_calibration_after,
        },
        "test_holdout": predictor_metrics(y_test, test_after, config.tau_danger),
        "surrogate_fidelity": fidelity,
    }
    resolved_bounds: dict[str, tuple[float, float]] = {}
    for name in feature_names:
        bound_spec = taxonomy.feature_by_name()[name].bounds
        if bound_spec.minimum is None or bound_spec.maximum is None:
            raise ValueError(f"training bounds were not resolved for model feature {name!r}")
        resolved_bounds[name] = (bound_spec.minimum, bound_spec.maximum)
    resolved_rate_limits = {
        name: constraint.max_change_per_step
        for name, constraint in taxonomy.actuator_constraints.items()
    }
    metrics["resolved_rate_limits"] = resolved_rate_limits
    bundle = ModelBundle(
        estimator=estimator,
        scaler=scaler,
        feature_names=feature_names,
        training_engine_ids=splits.train_engine_ids,
        model_type=selected_model,
        seed=config.seed,
        calibrator=calibrator,
        surrogate=surrogate,
        config_hash=_configuration_hash(config, selected_model),
        git_commit=_git_commit(),
        metrics=metrics,
        resolved_bounds=resolved_bounds,
        resolved_rate_limits=resolved_rate_limits,
    )
    return TrainingResult(
        bundle=bundle,
        splits=splits,
        validation_labels=y_validation,
        validation_risk=validation_after,
        test_labels=y_test,
        test_risk=test_after,
        metrics=metrics,
        test_probabilities_before_calibration=test_before,
        surrogate_test_risk=surrogate_test_risk,
    )
