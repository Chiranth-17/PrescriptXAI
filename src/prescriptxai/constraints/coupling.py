"""Learned sensor coupling propagation and Tier 4 constraint evaluation."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPRegressor
from torch import Tensor, nn

from prescriptxai.constraints.taxonomy import CouplingRule, FeatureTaxonomy, load_taxonomy
from prescriptxai.data.preprocess import FittedFeatureScaler

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleEvaluation:
    """Outcome with signed compliance margin and explanation."""

    name: str
    passed: bool
    margin: float
    explanation: str


@dataclass(frozen=True)
class CouplingFitMetrics:
    """Per-dependent-sensor fit quality on the training regime."""

    r2: dict[str, float]
    residual_std: dict[str, float]
    below_r2_floor: tuple[str, ...]
    torch_surrogate_mae: dict[str, float] | None = None
    r2_floor: float = 0.0
    cross_validation_folds: int = 2
    training_engine_count: int = 0
    training_row_count: int = 0


@dataclass
class SensorCouplingModel:
    """Predict dependent sensors from controllable proxies and frozen operating settings."""

    dependent_features: tuple[str, ...]
    predictor_features: tuple[str, ...]
    models: dict[str, Any]
    residual_std: dict[str, float]
    metrics: CouplingFitMetrics
    residual_sigma_k: float
    feature_names: tuple[str, ...]
    torch_models: dict[str, nn.Module]
    resolved_bounds: dict[str, tuple[float, float]]
    resolved_rate_limits: dict[str, float] | None = None
    training_engine_ids: tuple[int, ...] = ()
    fit_engine_ids: tuple[int, ...] = ()

    def save(self, path: Path) -> Path:
        """Persist the fitted coupling model."""
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, path: Path) -> SensorCouplingModel:
        """Load a persisted coupling model."""
        if not path.is_file():
            raise FileNotFoundError(path)
        loaded: object = joblib.load(path)
        if not isinstance(loaded, SensorCouplingModel):
            raise ValueError("artifact does not contain a SensorCouplingModel")
        if not getattr(loaded, "training_engine_ids", ()):
            loaded.training_engine_ids = ()
            LOGGER.warning(
                "Coupling artifact %s has no training-engine provenance; refit before "
                "evaluating engine-disjoint recourse",
                path,
            )
        if not getattr(loaded, "fit_engine_ids", ()):
            loaded.fit_engine_ids = ()
        return loaded

    @classmethod
    def fit(
        cls,
        frame: pd.DataFrame,
        taxonomy: FeatureTaxonomy,
        *,
        training_engine_ids: Sequence[int],
        failure_horizon: int,
        seed: int = 1729,
    ) -> SensorCouplingModel:
        """Fit one regressor per dependent sensor on healthy-to-moderate degradation rows."""
        if taxonomy.coupling is None:
            raise ValueError("taxonomy is missing coupling configuration")
        coupling = taxonomy.coupling
        engine_column = "engine_id" if "engine_id" in frame.columns else "unit_id"
        if engine_column not in frame.columns:
            raise ValueError("training frame must contain engine provenance")
        declared_ids = tuple(sorted(int(value) for value in training_engine_ids))
        if not declared_ids or len(declared_ids) != len(set(declared_ids)):
            raise ValueError("training_engine_ids must be nonempty and unique")
        if any(value != integer for value, integer in zip(
            sorted(training_engine_ids), declared_ids, strict=True
        )):
            raise ValueError("training_engine_ids must contain integer IDs")
        train_rows = frame[frame[engine_column].isin(training_engine_ids)].copy()
        if train_rows.empty:
            raise ValueError("no training-engine rows supplied for coupling fit")
        observed_ids = tuple(sorted(int(value) for value in train_rows[engine_column].unique()))
        if observed_ids != declared_ids:
            raise ValueError("coupling frame is missing declared training engines")
        active_features = tuple(
            spec.name
            for spec in taxonomy.features
            if spec.group != "context" and spec.name in train_rows.columns
        )
        if not active_features:
            raise ValueError("training frame contains no configured telemetry features")
        resolved_taxonomy = taxonomy.fit_training_bounds(train_rows, columns=active_features)
        resolved_taxonomy.validate_bounds_against_observed(train_rows, columns=active_features)
        resolved_specs = resolved_taxonomy.feature_by_name()
        resolved_bounds = {
            name: (float(spec.bounds.minimum), float(spec.bounds.maximum))
            for name, spec in resolved_specs.items()
            if name in active_features
            and spec.bounds.minimum is not None
            and spec.bounds.maximum is not None
        }
        resolved_rate_limits = {
            name: constraint.max_change_per_step
            for name, constraint in resolved_taxonomy.actuator_constraints.items()
        }
        if "rul" in train_rows.columns:
            regime = train_rows["rul"] > max(coupling.min_rul_cycles, failure_horizon)
            train_rows = train_rows.loc[regime]
        if train_rows.empty:
            raise ValueError("no rows remain after applying the healthy-to-moderate regime filter")
        available = set(active_features)
        dependent = tuple(sorted(taxonomy.dependent_feature_names() & available))
        predictors = tuple(
            sorted(
                (taxonomy.controllable_feature_names() & available)
                | (
                    frozenset(taxonomy.feature_groups.immutable_operational.features)
                    | frozenset(taxonomy.feature_groups.immutable_environmental.features)
                ) & available
            )
        )
        if not dependent:
            raise ValueError("no dependent sensors are present in the training frame")
        if not predictors:
            raise ValueError("no configured predictor features are present in the training frame")
        missing = (set(dependent) | set(predictors)) - set(train_rows.columns)
        if missing:
            raise ValueError(f"training frame is missing coupling columns: {sorted(missing)}")
        models: dict[str, Any] = {}
        r2_scores: dict[str, float] = {}
        residual_std: dict[str, float] = {}
        predictor_matrix = train_rows.loc[:, predictors].to_numpy(dtype=float)
        if not np.isfinite(predictor_matrix).all():
            raise ValueError("coupling predictors must be finite")
        engine_groups = train_rows[engine_column].to_numpy()
        unique_engines = np.unique(engine_groups)
        fold_count = min(coupling.cross_validation_folds, len(unique_engines))
        if fold_count < 2:
            raise ValueError("coupling quality needs at least two training engines")
        cross_validator = GroupKFold(n_splits=fold_count)
        for target in dependent:
            target_values = train_rows[target].to_numpy(dtype=float)
            if not np.isfinite(target_values).all():
                raise ValueError(f"coupling target {target!r} must be finite")
            out_of_fold = np.empty_like(target_values, dtype=float)
            for fit_indices, score_indices in cross_validator.split(
                predictor_matrix, target_values, engine_groups
            ):
                fold_model = _build_backend(coupling, seed)
                fold_model.fit(predictor_matrix[fit_indices], target_values[fit_indices])
                out_of_fold[score_indices] = np.asarray(
                    fold_model.predict(predictor_matrix[score_indices]), dtype=float
                )
            model = _build_backend(coupling, seed)
            model.fit(predictor_matrix, target_values)
            residuals = target_values - out_of_fold
            r2_scores[target] = float(r2_score(target_values, out_of_fold))
            residual_std[target] = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
            models[target] = model
        torch_models: dict[str, nn.Module] = {}
        torch_fidelity: dict[str, float] = {}
        for target in dependent:
            teacher = models[target]
            if isinstance(teacher, Ridge):
                torch_models[target] = TorchLinearRegressor(
                    np.asarray(teacher.coef_, dtype=float).reshape(-1),
                    float(teacher.intercept_),
                )
                torch_fidelity[target] = 0.0
            else:
                teacher_values = np.asarray(teacher.predict(predictor_matrix), dtype=float)
                torch_model = _fit_torch_surrogate(
                    predictor_matrix,
                    teacher_values,
                    hidden_dims=coupling.torch_hidden_dims,
                    epochs=coupling.torch_epochs,
                    learning_rate=coupling.torch_learning_rate,
                    seed=seed,
                )
                torch_models[target] = torch_model
                surrogate_values = torch_model(
                    torch.tensor(predictor_matrix, dtype=torch.float64)
                ).detach().numpy().reshape(-1)
                torch_fidelity[target] = float(
                    np.mean(np.abs(teacher_values - surrogate_values))
                )
        below_floor = tuple(
            sorted(name for name, score in r2_scores.items() if score < coupling.min_r2)
        )
        metrics = CouplingFitMetrics(
            r2=r2_scores,
            residual_std=residual_std,
            below_r2_floor=below_floor,
            torch_surrogate_mae=torch_fidelity,
            r2_floor=coupling.min_r2,
            cross_validation_folds=fold_count,
            training_engine_count=len(unique_engines),
            training_row_count=len(train_rows),
        )
        model_feature_names = tuple(dict.fromkeys((*predictors, *dependent)))
        return cls(
            dependent_features=dependent,
            predictor_features=predictors,
            models=models,
            residual_std=residual_std,
            metrics=metrics,
            residual_sigma_k=coupling.residual_sigma_k,
            feature_names=model_feature_names,
            torch_models=torch_models,
            resolved_bounds=resolved_bounds,
            resolved_rate_limits=resolved_rate_limits,
            training_engine_ids=declared_ids,
            fit_engine_ids=tuple(int(value) for value in unique_engines),
        )

    def propagate(
        self,
        values: Mapping[str, float],
        *,
        reference_state: Mapping[str, float] | None = None,
    ) -> dict[str, float]:
        """Predict dependent sensors, optionally preserving observed reference residuals.

        Recourse uses ``d' = d + g(c') - g(c)`` with a fixed observed reference ``(c, d)``.
        This guarantees that zero control change produces zero dependent change. Without a
        reference this remains an absolute conditional-mean prediction ``d' = g(c')``.
        Neither operation identifies a causal intervention effect from observational telemetry.
        """
        state = dict(values)
        missing = set(self.predictor_features) - set(state)
        if missing:
            raise ValueError(f"state is missing coupling predictors: {sorted(missing)}")
        predictor_vector = np.asarray(
            [float(state[name]) for name in self.predictor_features], dtype=float
        ).reshape(1, -1)
        if not np.isfinite(predictor_vector).all():
            raise ValueError("coupling predictor values must be finite")
        reference_predictors: NDArray[np.float64] | None = None
        if reference_state is not None:
            required = set(self.predictor_features) | set(self.dependent_features)
            missing_reference = required - set(reference_state)
            if missing_reference:
                raise ValueError(
                    f"reference state is missing coupling fields: {sorted(missing_reference)}"
                )
            if any(not np.isfinite(reference_state[name]) for name in required):
                raise ValueError("coupling reference values must be finite")
            reference_predictors = np.asarray(
                [[reference_state[name] for name in self.predictor_features]], dtype=float
            )
        for target in self.dependent_features:
            model = self.models[target]
            predicted = float(np.asarray(model.predict(predictor_vector), dtype=float)[0])
            if reference_state is not None and reference_predictors is not None:
                baseline = float(np.asarray(model.predict(reference_predictors), dtype=float)[0])
                predicted = float(reference_state[target]) + (predicted - baseline)
            state[target] = predicted
        return state

    def propagate_batch(
        self,
        raw_features: NDArray[np.float64],
        feature_names: tuple[str, ...],
        *,
        reference_state: NDArray[np.float64] | None = None,
    ) -> NDArray[np.float64]:
        """Propagate a finite batch with one fixed reference vector or row-aligned references."""
        matrix = np.asarray(raw_features, dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] != len(feature_names) or len(matrix) == 0:
            raise ValueError("coupling features must be a nonempty matrix in feature order")
        if not np.isfinite(matrix).all():
            raise ValueError("coupling features must be finite")
        if len(feature_names) != len(set(feature_names)):
            raise ValueError("coupling feature names must be unique")
        missing = (set(self.predictor_features) | set(self.dependent_features)) - set(feature_names)
        if missing:
            raise ValueError(f"feature order missing coupling fields: {sorted(missing)}")
        positions = {name: index for index, name in enumerate(feature_names)}
        predictor_indices = [positions[name] for name in self.predictor_features]
        reference: NDArray[np.float64] | None = None
        if reference_state is not None:
            reference = np.asarray(reference_state, dtype=np.float64)
            if reference.ndim == 1:
                reference = reference.reshape(1, -1)
            if (
                reference.ndim != 2
                or reference.shape[1] != matrix.shape[1]
                or reference.shape[0] not in (1, matrix.shape[0])
            ):
                raise ValueError("reference must be one feature vector or match the feature batch")
            if not np.isfinite(reference).all():
                raise ValueError("coupling reference values must be finite")
        output = matrix.copy()
        for target in self.dependent_features:
            index = positions[target]
            model = self.models[target]
            predicted = np.asarray(model.predict(matrix[:, predictor_indices]), dtype=np.float64)
            if reference is not None:
                baseline = np.asarray(
                    model.predict(reference[:, predictor_indices]), dtype=np.float64
                )
                predicted = reference[:, index] + (predicted - baseline)
            output[:, index] = predicted
        return output

    def propagate_torch_module(self, feature_names: tuple[str, ...]) -> TorchCouplingPropagation:
        """Build a differentiable propagation module aligned to the model feature order."""
        return TorchCouplingPropagation.from_model(self, feature_names)

    def propagate_scaled_torch_module(
        self, scaler: FittedFeatureScaler
    ) -> ScaledTorchCouplingPropagation:
        """Build a differentiable propagation module accepting scaled model features."""
        return ScaledTorchCouplingPropagation(
            self.propagate_torch_module(scaler.feature_names), scaler
        )

    def evaluate_learned_constraints(
        self, values: Mapping[str, float]
    ) -> tuple[RuleEvaluation, ...]:
        """Check |actual - predicted| <= k * residual_std for each dependent sensor."""
        state = dict(values)
        missing = (set(self.predictor_features) | set(self.dependent_features)) - set(state)
        if missing:
            raise ValueError(f"state is missing coupling fields: {sorted(missing)}")
        predictor_vector = np.asarray(
            [float(state[name]) for name in self.predictor_features], dtype=float
        ).reshape(1, -1)
        if not np.isfinite(predictor_vector).all() or any(
            not np.isfinite(float(state[name])) for name in self.dependent_features
        ):
            raise ValueError("coupling state values must be finite")
        evaluations: list[RuleEvaluation] = []
        for target in self.dependent_features:
            actual = float(state[target])
            predicted = float(
                np.asarray(self.models[target].predict(predictor_vector), dtype=float)[0]
            )
            tolerance = self.residual_sigma_k * self.residual_std[target]
            residual = abs(actual - predicted)
            passed = residual <= tolerance + 1e-12
            margin = tolerance - residual
            evaluations.append(
                RuleEvaluation(
                    name=f"learned_{target}",
                    passed=passed,
                    margin=margin,
                    explanation=(
                        f"{target}: |actual {actual:.4g} - predicted {predicted:.4g}| "
                        f"= {residual:.4g} vs limit {tolerance:.4g} "
                        f"({self.residual_sigma_k:g} sigma)"
                    ),
                )
            )
        return tuple(evaluations)

    def evaluate_yaml_rules(
        self, values: Mapping[str, float], taxonomy: FeatureTaxonomy
    ) -> tuple[RuleEvaluation, ...]:
        """Evaluate configured hand-written coupling rules."""
        active = set(values)
        return tuple(
            evaluate_rule(values, rule)
            for rule in taxonomy.coupling_rules
            if rule.feature_a in active and rule.feature_b in active
        )

    def evaluate_all_constraints(
        self, values: Mapping[str, float], taxonomy: FeatureTaxonomy
    ) -> tuple[RuleEvaluation, ...]:
        """Combine learned residual bounds and configured engineering rules."""
        return self.evaluate_learned_constraints(values) + self.evaluate_yaml_rules(
            values, taxonomy
        )

    def write_diagnostic_report(self, output_stem: Path, frame: pd.DataFrame) -> tuple[Path, Path]:
        """Write HTML and PNG summaries of coupling fit quality."""
        output_stem.parent.mkdir(parents=True, exist_ok=True)
        html_path = output_stem.with_suffix(".html")
        png_path = output_stem.with_suffix(".png")
        rows = [
            "<html><body><h1>Sensor coupling fit</h1>",
            "<p>R² and residual σ use deterministic engine-grouped out-of-fold predictions. "
            f"The configured R² floor is {self.metrics.r2_floor:.4f}; "
            f"fit used {self.metrics.cross_validation_folds} folds, "
            f"{self.metrics.training_engine_count} training engines, and "
            f"{self.metrics.training_row_count} healthy-to-moderate rows.</p>",
            "<table border='1' cellpadding='6'>",
            "<tr><th>Dependent</th><th>R²</th><th>Residual σ</th><th>Below floor</th></tr>",
        ]
        for target in self.dependent_features:
            below = "yes" if target in self.metrics.below_r2_floor else "no"
            rows.append(
                "<tr>"
                f"<td>{escape(target)}</td>"
                f"<td>{self.metrics.r2[target]:.4f}</td>"
                f"<td>{self.residual_std[target]:.4g}</td>"
                f"<td>{below}</td>"
                "</tr>"
            )
        rows.append("</table></body></html>")
        html_path.write_text("\n".join(rows), encoding="utf-8")
        _write_coupling_png(
            png_path,
            self.metrics.r2,
            frame,
            self.dependent_features,
            self.metrics.r2_floor,
        )
        return html_path, png_path


class TorchLinearRegressor(nn.Module):
    """Exact differentiable representation of one fitted Ridge relation."""

    _weights: Tensor
    _bias: Tensor

    def __init__(self, weights: NDArray[np.float64], bias: float) -> None:
        super().__init__()
        self.register_buffer("_weights", torch.as_tensor(weights, dtype=torch.float64))
        self.register_buffer("_bias", torch.as_tensor([bias], dtype=torch.float64))

    def forward(self, predictors: Tensor) -> Tensor:
        """Predict one dependent sensor in raw physical units."""
        values = predictors.to(dtype=self._weights.dtype)
        return (values @ self._weights + self._bias).unsqueeze(-1)


class StandardizedTorchRegressor(nn.Module):
    """Differentiable MLP surrogate with input and output normalization."""

    _input_mean: Tensor
    _input_scale: Tensor
    _output_mean: Tensor
    _output_scale: Tensor

    def __init__(
        self,
        input_mean: NDArray[np.float64],
        input_scale: NDArray[np.float64],
        output_mean: float,
        output_scale: float,
        network: nn.Sequential,
    ) -> None:
        super().__init__()
        self.register_buffer("_input_mean", torch.as_tensor(input_mean, dtype=torch.float64))
        self.register_buffer("_input_scale", torch.as_tensor(input_scale, dtype=torch.float64))
        self.register_buffer("_output_mean", torch.as_tensor([output_mean], dtype=torch.float64))
        self.register_buffer("_output_scale", torch.as_tensor([output_scale], dtype=torch.float64))
        self.network = network.double()

    def forward(self, predictors: Tensor) -> Tensor:
        """Predict a dependent sensor from raw-unit telemetry."""
        values = predictors.to(dtype=self._input_mean.dtype)
        normalized = (values - self._input_mean) / self._input_scale
        prediction = self.network(normalized) * self._output_scale + self._output_mean
        return cast(Tensor, prediction)


class TorchCouplingPropagation(nn.Module):
    """Differentiable dependent-sensor propagation in raw physical units."""

    _models: nn.ModuleList
    _dependent_indices: Tensor
    _predictor_indices: Tensor

    def __init__(
        self,
        feature_names: tuple[str, ...],
        dependent_indices: NDArray[np.int64],
        predictor_indices: NDArray[np.int64],
        regressors: Sequence[nn.Module],
    ) -> None:
        super().__init__()
        self._models = nn.ModuleList(regressors)
        self.register_buffer(
            "_dependent_indices", torch.as_tensor(dependent_indices, dtype=torch.long)
        )
        self.register_buffer(
            "_predictor_indices", torch.as_tensor(predictor_indices, dtype=torch.long)
        )
        self.feature_names = feature_names

    @classmethod
    def from_model(
        cls, coupling: SensorCouplingModel, feature_names: tuple[str, ...]
    ) -> TorchCouplingPropagation:
        """Construct torch propagation from a fitted sklearn ridge coupling model."""
        name_to_index = {name: index for index, name in enumerate(feature_names)}
        missing_predictors = set(coupling.predictor_features) - set(name_to_index)
        if missing_predictors:
            raise ValueError(
                "feature order missing coupling predictors: "
                f"{sorted(missing_predictors)}"
            )
        # A model/scaler may intentionally omit constant dependent sensors. They cannot affect
        # its prediction or optimization, so propagate only dependent fields represented in the
        # fitted feature order. Predictor fields remain mandatory because the learned relation
        # cannot be evaluated without them.
        active_dependents = tuple(
            name for name in coupling.dependent_features if name in name_to_index
        )
        predictor_indices = np.asarray(
            [name_to_index[name] for name in coupling.predictor_features], dtype=np.int64
        )
        dependent_indices = np.asarray(
            [name_to_index[name] for name in active_dependents], dtype=np.int64
        )
        missing_models = set(active_dependents) - set(coupling.torch_models)
        if missing_models:
            raise ValueError(f"coupling artifact is missing torch models: {sorted(missing_models)}")
        regressors = [coupling.torch_models[name] for name in active_dependents]
        return cls(feature_names, dependent_indices, predictor_indices, regressors)

    def forward(self, features: Tensor, reference_features: Tensor | None = None) -> Tensor:
        """Propagate raw features, preserving residuals when a fixed reference is supplied."""
        if features.ndim != 2 or features.shape[1] != len(self.feature_names) or not len(features):
            raise ValueError("features must be a nonempty batch matrix in feature order")
        if not torch.isfinite(features).all():
            raise ValueError("coupling features must be finite")
        output = features.clone()
        if not self._models:
            return output
        predictors = features.index_select(1, self._predictor_indices.to(features.device))
        predictions = torch.cat([model(predictors) for model in self._models], dim=1)
        if reference_features is not None:
            reference = _reference_tensor(reference_features, features)
            reference_predictors = reference.index_select(
                1, self._predictor_indices.to(features.device)
            )
            baseline = torch.cat([model(reference_predictors) for model in self._models], dim=1)
            observed = reference.index_select(1, self._dependent_indices.to(features.device))
            predictions = observed + (predictions - baseline)
        for column, target_index in enumerate(self._dependent_indices):
            output[:, int(target_index)] = predictions[:, column]
        return output


class ScaledTorchCouplingPropagation(nn.Module):
    """Apply raw-unit coupling while accepting and returning model-scaled feature rows."""

    _mean: Tensor
    _scale: Tensor

    def __init__(
        self, propagation: TorchCouplingPropagation, scaler: FittedFeatureScaler
    ) -> None:
        super().__init__()
        self.propagation = propagation
        self.register_buffer("_mean", torch.as_tensor(scaler.scaler.mean_, dtype=torch.float64))
        self.register_buffer("_scale", torch.as_tensor(scaler.scaler.scale_, dtype=torch.float64))

    def forward(
        self, scaled_features: Tensor, reference_scaled_features: Tensor | None = None
    ) -> Tensor:
        """Propagate dependent values with explicit scaled-to-raw and raw-to-scaled maps."""
        if scaled_features.ndim != 2 or scaled_features.shape[1] != len(self._mean):
            raise ValueError("scaled features must be a batch matrix in the fitted feature order")
        original_dtype = scaled_features.dtype
        mean = self._mean.to(scaled_features.device)
        scale = self._scale.to(scaled_features.device)
        raw = scaled_features.to(torch.float64) * scale + mean
        if reference_scaled_features is not None:
            reference = _reference_tensor(reference_scaled_features, scaled_features)
            reference_raw = reference.to(torch.float64) * scale + mean
            propagated = self.propagation(raw, reference_raw)
            output = scaled_features.clone()
            for target_index in self.propagation._dependent_indices:
                index = int(target_index)
                output[:, index] = reference[:, index] + (
                    (propagated[:, index] - reference_raw[:, index]) / scale[index]
                ).to(original_dtype)
            return output
        propagated = self.propagation(raw)
        scaled = (propagated - mean) / scale
        return cast(Tensor, scaled).to(dtype=original_dtype)


def _reference_tensor(reference_features: Tensor, features: Tensor) -> Tensor:
    """Validate and detach an observed reference so it cannot become an optimization variable."""
    reference = reference_features.detach().to(device=features.device, dtype=features.dtype)
    if reference.ndim == 1:
        reference = reference.unsqueeze(0)
    if (
        reference.ndim != 2
        or reference.shape[1] != features.shape[1]
        or reference.shape[0] not in (1, features.shape[0])
    ):
        raise ValueError("reference must be one feature vector or match the feature batch")
    if not torch.isfinite(reference).all():
        raise ValueError("coupling reference values must be finite")
    return reference


def _build_backend(config: Any, seed: int) -> Any:  # noqa: ANN401
    """Construct the configured sklearn regressor backend."""
    if config.backend == "ridge":
        return Ridge(alpha=config.ridge_alpha)
    if config.backend == "gradient_boosting":
        return GradientBoostingRegressor(
            n_estimators=config.gradient_boosting_estimators,
            max_depth=config.gradient_boosting_max_depth,
            learning_rate=config.gradient_boosting_learning_rate,
            random_state=seed,
        )
    if config.backend == "mlp":
        return MLPRegressor(
            hidden_layer_sizes=config.mlp_hidden_dims,
            max_iter=config.mlp_max_iter,
            learning_rate_init=config.mlp_learning_rate,
            random_state=seed,
        )
    raise ValueError(f"unsupported coupling backend {config.backend!r}")


def _fit_torch_surrogate(
    predictors: NDArray[np.float64],
    teacher_values: NDArray[np.float64],
    *,
    hidden_dims: tuple[int, ...],
    epochs: int,
    learning_rate: float,
    seed: int,
) -> StandardizedTorchRegressor:
    """Distill a nonlinear coupling regressor into a deterministic torch MLP."""
    if predictors.ndim != 2 or teacher_values.shape != (len(predictors),):
        raise ValueError("torch coupling distillation data has incompatible shapes")
    if not np.isfinite(predictors).all() or not np.isfinite(teacher_values).all():
        raise ValueError("torch coupling distillation data must be finite")
    input_mean = predictors.mean(axis=0)
    input_scale = predictors.std(axis=0)
    input_scale[input_scale <= np.finfo(float).eps] = 1.0
    output_mean = float(teacher_values.mean())
    output_scale = float(teacher_values.std())
    if output_scale <= np.finfo(float).eps:
        output_scale = 1.0
    normalized_x = torch.as_tensor(
        (predictors - input_mean) / input_scale, dtype=torch.float64
    )
    normalized_y = torch.as_tensor(
        ((teacher_values - output_mean) / output_scale).reshape(-1, 1), dtype=torch.float64
    )
    torch.manual_seed(seed)
    layers: list[nn.Module] = []
    input_size = predictors.shape[1]
    for hidden_size in hidden_dims:
        layers.extend((nn.Linear(input_size, hidden_size), nn.Tanh()))
        input_size = hidden_size
    layers.append(nn.Linear(input_size, 1))
    network = nn.Sequential(*layers).double()
    regressor = StandardizedTorchRegressor(
        input_mean, input_scale, output_mean, output_scale, network
    )
    optimizer = torch.optim.Adam(regressor.network.parameters(), lr=learning_rate)
    for _ in range(epochs):
        prediction = regressor.network(normalized_x)
        loss = torch.mean((prediction - normalized_y) ** 2)
        optimizer.zero_grad()
        loss.backward()  # type: ignore[no-untyped-call]
        optimizer.step()
    return regressor


def evaluate_rule(values: Mapping[str, float], rule: CouplingRule) -> RuleEvaluation:
    """Return validity, margin, and explanation for one configured relationship."""
    if rule.feature_a not in values or rule.feature_b not in values:
        raise ValueError(f"state is missing a feature required by coupling rule {rule.name!r}")
    value_a = float(values[rule.feature_a])
    value_b = float(values[rule.feature_b])
    if not np.isfinite(value_a) or not np.isfinite(value_b):
        raise ValueError(f"coupling rule {rule.name!r} requires finite feature values")
    if rule.relation == "less_than":
        margin = value_b + rule.tolerance - value_a
        passed = margin >= -1e-12
        explanation = (
            f"{rule.feature_a} ({value_a:g}) must be <= {rule.feature_b} ({value_b:g}) "
            f"+ tolerance {rule.tolerance:g}; margin {margin:g}"
        )
    elif rule.relation == "greater_than":
        margin = value_a - value_b + rule.tolerance
        passed = margin >= -1e-12
        explanation = (
            f"{rule.feature_a} ({value_a:g}) must be >= {rule.feature_b} ({value_b:g}) "
            f"- tolerance {rule.tolerance:g}; margin {margin:g}"
        )
    else:
        if rule.slope is None or rule.intercept is None:
            raise ValueError(f"linear coupling rule {rule.name!r} has no coefficients")
        expected = rule.slope * value_a + rule.intercept
        residual = abs(value_b - expected)
        margin = rule.tolerance - residual
        passed = margin >= -1e-12
        explanation = (
            f"{rule.feature_b} ({value_b:g}) vs linear prediction {expected:g} "
            f"from {rule.feature_a}; residual {residual:g}, tolerance {rule.tolerance:g}, "
            f"margin {margin:g}"
        )
    return RuleEvaluation(rule.name, passed, margin, explanation)


def validate_couplings(
    values: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
    coupling: SensorCouplingModel | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Check learned and configured coupling rules."""
    if coupling is None and not taxonomy.coupling_rules:
        return False, ("no sensor coupling rules are configured",)
    evaluations: list[RuleEvaluation] = []
    if coupling is not None:
        evaluations.extend(coupling.evaluate_all_constraints(values, taxonomy))
    else:
        evaluations.extend(evaluate_rule(values, rule) for rule in taxonomy.coupling_rules)
    failures = tuple(
        f"{item.name}: {item.explanation} (margin={item.margin:g})"
        for item in evaluations
        if not item.passed
    )
    return not failures, failures


def fit_and_persist_coupling(
    train_frame: pd.DataFrame,
    taxonomy_path: Path,
    output_path: Path,
    *,
    training_engine_ids: Sequence[int],
    failure_horizon: int,
    report_stem: Path | None = None,
    seed: int = 1729,
) -> SensorCouplingModel:
    """Fit coupling on training engines, optionally write diagnostics, and persist."""
    taxonomy = load_taxonomy(taxonomy_path)
    model = SensorCouplingModel.fit(
        train_frame,
        taxonomy,
        training_engine_ids=training_engine_ids,
        failure_horizon=failure_horizon,
        seed=seed,
    )
    model.save(output_path)
    if report_stem is not None:
        model.write_diagnostic_report(report_stem, train_frame)
    return model


def _write_coupling_png(
    path: Path,
    r2_values: dict[str, float],
    frame: pd.DataFrame,
    dependent_features: tuple[str, ...],
    r2_floor: float,
) -> None:
    """Render an engine-held-out R2 bar chart and configured floor without matplotlib."""
    width, height, margin = 1100, 560, 65
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((margin, 20), "Engine-grouped out-of-fold coupling R2", fill="black", font=font)
    if not dependent_features:
        image.save(path)
        return
    scores = [r2_values[target] for target in dependent_features]
    lower = min(-0.1, min(scores))
    upper = max(1.0, max(scores))
    if upper <= lower:
        upper = lower + 1.0
    plot_top, plot_bottom = margin, height - margin - 28
    plot_height = plot_bottom - plot_top
    zero_y = plot_top + int(upper / (upper - lower) * plot_height)
    draw.line((margin, zero_y, width - margin, zero_y), fill="#555")
    draw.text((8, max(0, zero_y - 6)), "0", fill="#333", font=font)
    floor_y = plot_top + int((upper - r2_floor) / (upper - lower) * plot_height)
    for start in range(margin, width - margin, 20):
        draw.line((start, floor_y, min(start + 10, width - margin), floor_y), fill="#cc3333")
    draw.text((width - margin - 72, floor_y - 14), f"floor {r2_floor:.2f}", fill="#a22", font=font)
    bar_width = (width - 2 * margin) // max(len(dependent_features), 1)
    for index, target in enumerate(dependent_features):
        score = r2_values.get(target, 0.0)
        score_y = plot_top + int((upper - score) / (upper - lower) * plot_height)
        x0 = margin + index * bar_width + 8
        draw.rectangle(
            (x0, min(zero_y, score_y), x0 + bar_width - 16, max(zero_y, score_y)),
            fill="#3366cc" if score >= 0 else "#cc6633",
        )
        draw.text((x0, plot_bottom + 5), target.replace("sensor_", "s"), fill="black", font=font)
        draw.text((x0, min(zero_y, score_y) - 14), f"{score:.2f}", fill="black", font=font)
    image.save(path)


def apply_coupling_for_bundle(
    state: Mapping[str, float],
    coupling: SensorCouplingModel | None,
    scaler: FittedFeatureScaler | None = None,
    *,
    reference_state: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Propagate dependent sensors when a coupling model is available."""
    if coupling is None:
        return dict(state)
    return coupling.propagate(state, reference_state=reference_state)
