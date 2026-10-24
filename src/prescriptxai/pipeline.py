"""Application engine joining model prediction, recourse, and validation."""

from __future__ import annotations

import hashlib
import json
import logging
from _thread import RLock
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path
from time import perf_counter_ns
from typing import Literal, TypeAlias, cast
from uuid import uuid4

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray
from pydantic import ValidationError

from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.bounds import check_bound_violations, check_rate_violations
from prescriptxai.constraints.coupling import SensorCouplingModel, apply_coupling_for_bundle
from prescriptxai.constraints.taxonomy import FeatureTaxonomy, load_taxonomy
from prescriptxai.logging_utils import current_run_id
from prescriptxai.models.registry import ModelBundle, load_model_bundle
from prescriptxai.recourse.optimizer import OptimizationResult, _delta_mappings, optimize_recourse
from prescriptxai.schemas import (
    Assessment,
    Explanation,
    FailureInformation,
    FeatureDelta,
    InputContext,
    RecourseOutcome,
    RecourseResult,
    StageTimings,
)
from prescriptxai.validation.pipeline import (
    ValidationReport,
    load_mahalanobis_validator,
    try_load_coupling_model,
    validate_candidate,
    verify_validator_compatibility,
)
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator

LOGGER = logging.getLogger(__name__)


def _default_coupling_path(
    taxonomy: FeatureTaxonomy, subset: str, artifact_root: Path
) -> Path | None:
    """Return the configured coupling artifact path when taxonomy metadata defines one."""
    if taxonomy.coupling is None:
        return None
    return artifact_root / taxonomy.coupling.artifact_name.format(subset=subset)


@dataclass(frozen=True)
class RecommendationResult:
    """One user request with distinct optimizer, model, and physical outcomes."""

    optimization: OptimizationResult
    validation: ValidationReport
    outcome: RecourseOutcome
    optimization_ms: float
    validation_ms: float


@dataclass
class PrescriptXAIEngine:
    """Configured PrescriptXAI inference and recourse engine."""

    config: AppConfig
    taxonomy: FeatureTaxonomy
    model: ModelBundle
    mahalanobis: MahalanobisValidator
    coupling: SensorCouplingModel | None = None
    predictor_lock: RLock = field(default_factory=RLock, repr=False)

    @classmethod
    def from_files(
        cls,
        config_path: Path,
        taxonomy_path: Path,
        model_path: Path | None = None,
        mahalanobis_path: Path | None = None,
        coupling_path: Path | None = None,
    ) -> PrescriptXAIEngine:
        """Load an engine from configured YAML and fitted artifacts."""
        config = load_config(config_path)
        taxonomy = load_taxonomy(taxonomy_path)
        model = load_model_bundle(model_path or config.artifacts.model)
        resolved_bounds = getattr(model, "resolved_bounds", None)
        if resolved_bounds:
            taxonomy = taxonomy.with_resolved_bounds(
                resolved_bounds, getattr(model, "resolved_rate_limits", None)
            )
        mahalanobis = load_mahalanobis_validator(mahalanobis_path or config.artifacts.mahalanobis)
        verify_validator_compatibility(mahalanobis, model, config)
        if not taxonomy.active_controllable_feature_names(model.feature_names):
            raise ValueError("at least one configured controllable proxy must be a model feature")
        resolved_coupling_path = (
            coupling_path
            or config.artifacts.coupling
            or _default_coupling_path(
                taxonomy, config.data.dataset, (model_path or config.artifacts.model).parent
            )
        )
        coupling = (
            try_load_coupling_model(resolved_coupling_path)
            if resolved_coupling_path is not None
            else None
        )
        if not getattr(model, "resolved_bounds", None) and coupling is not None:
            taxonomy = taxonomy.with_resolved_bounds(
                coupling.resolved_bounds, getattr(coupling, "resolved_rate_limits", None)
            )
        taxonomy.validate_model_feature_coverage(model.feature_names)
        missing_bounds = [
            name
            for name, spec in taxonomy.feature_by_name().items()
            if name in model.feature_names
            and (spec.bounds.minimum is None or spec.bounds.maximum is None)
        ]
        if missing_bounds:
            raise ValueError(
                "model artifact has no training-derived physical bounds for "
                f"{sorted(missing_bounds)}; retrain or fit the coupling artifact"
            )
        return cls(config, taxonomy, model, mahalanobis, coupling)

    def recommend(self, state: Mapping[str, float]) -> RecommendationResult:
        """Generate an actuator-only candidate and run all configured validation tiers."""
        raw_state = {name: float(value) for name, value in state.items()}
        missing = set(self.model.feature_names) - set(raw_state)
        if missing:
            raise ValueError(f"state is missing model features: {sorted(missing)}")
        optimization_started = perf_counter_ns()
        optimization = optimize_recourse(
            raw_state,
            self.model,
            self.taxonomy,
            self.config,
            self.coupling,
            self.mahalanobis,
        )
        optimization_ms = (perf_counter_ns() - optimization_started) / 1_000_000
        validation_started = perf_counter_ns()
        validation = validate_candidate(
            raw_state,
            optimization.state,
            self.model,
            self.taxonomy,
            self.mahalanobis,
            self.config,
            self.coupling,
        )
        validation_ms = (perf_counter_ns() - validation_started) / 1_000_000
        outcome = validation.as_outcome(
            optimization.initial_risk,
            optimization.final_risk,
            optimization.deltas,
            recourse_feasible=(
                optimization.model_valid
                and optimization.failure_reason is None
                and optimization.actuator_constraints_feasible
                and len(optimization.deltas) <= self.config.recourse.max_changed_features
            ),
        )
        LOGGER.info(
            "Recourse request completed: model_valid=%s physical_valid=%s success=%s",
            outcome.model_valid,
            outcome.tier2_plausible
            and outcome.tier3_engineering_valid
            and outcome.tier4_coupling_valid,
            outcome.success,
        )
        return RecommendationResult(
            optimization, validation, outcome, optimization_ms, validation_ms
        )


class InputError(ValueError):
    """Base typed error for invalid raw telemetry or observed context."""


class FeatureError(InputError):
    """Missing, extra, duplicate, or incorrectly ordered features."""


class UnitError(InputError):
    """Supplied units disagree with the configured raw physical units."""


class HistoryError(InputError):
    """Observed LSTM history is missing or incorrectly shaped."""


class ArtifactError(ValueError):
    """Configured fitted artifacts cannot support the requested predictor."""


RawInput: TypeAlias = Mapping[str, float] | pd.Series | NDArray[np.float64] | Sequence[float]
_CACHE: OrderedDict[str, PrescriptXAIEngine] = OrderedDict()
_CACHE_LOCK = RLock()


class _LatestSequenceEstimator:
    """Expose a real LSTM's last row as a snapshot variable, keeping observed history fixed."""

    supports_gradients = True

    def __init__(self, bundle: ModelBundle, history: NDArray[np.float64]) -> None:
        self.base = bundle.estimator
        self.prefix = bundle.scaler.scaler.transform(history) if len(history) else history.copy()
        self.device = getattr(self.base, "device", "cpu")

    def predict_proba(self, latest: NDArray[np.float64]) -> NDArray[np.float64]:
        """Evaluate genuine fixed-prefix sequences with new latest rows."""
        prefix = np.repeat(self.prefix[None, :, :], len(latest), axis=0)
        return np.asarray(
            self.base.predict_proba(np.concatenate([prefix, latest[:, None, :]], axis=1)),
            dtype=float,
        )

    def torch_forward(self, latest: torch.Tensor) -> torch.Tensor:
        """Differentiate only latest; the observed prefix is detached and constant."""
        prefix = torch.as_tensor(self.prefix, dtype=latest.dtype, device=latest.device).detach()
        sequence = torch.cat(
            [prefix.unsqueeze(0).expand(len(latest), -1, -1), latest.unsqueeze(1)], dim=1
        )
        return cast(torch.Tensor, self.base.torch_forward(sequence))


class PrescriptXAI:
    """Public typed decision support facade; core results contain no plots."""

    def __init__(self, engine: PrescriptXAIEngine) -> None:
        self.engine = engine
        self.config = engine.config.model_copy(deep=True)
        self.model_version = (
            f"{engine.model.model_type}:artifact-"
            f"{engine.model.artifact_version}:{engine.model.config_hash}"
        )

    @property
    def config_hash(self) -> str:
        """Fingerprint current facade settings without mutating the cached engine."""
        encoded = json.dumps(self.config.model_dump(mode="json"), sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def from_config(cls, config: AppConfig | Path | str) -> PrescriptXAI:
        """Load/cache artifact contents by fingerprints, without caching recommendations."""
        settings = (
            load_config(Path(config))
            if isinstance(config, (str, Path))
            else config.model_copy(deep=True)
        )
        selected = settings.pipeline.model_artifacts.get(settings.model_choice)
        if selected is not None:
            settings.artifacts = selected.model_copy(deep=True)
            settings.paths.model = selected.model
            settings.paths.mahalanobis = selected.mahalanobis
            settings.paths.evaluation_report = selected.evaluation_report
        paths = [
            settings.pipeline.taxonomy_path,
            settings.artifacts.model,
            settings.artifacts.mahalanobis,
        ]
        if settings.artifacts.coupling is not None:
            paths.append(settings.artifacts.coupling)
        try:
            hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        except OSError as error:
            raise ArtifactError(str(error)) from error
        identity = hashlib.sha256(
            (settings.model_dump_json() + json.dumps(hashes)).encode()
        ).hexdigest()
        with _CACHE_LOCK:
            if identity not in _CACHE:
                try:
                    taxonomy = load_taxonomy(settings.pipeline.taxonomy_path)
                    model = load_model_bundle(settings.artifacts.model)
                except (ValueError, OSError, TypeError) as error:
                    raise ArtifactError(str(error)) from error
                expected = {"xgboost": "xgboost", "torch": "mlp", "lstm": "lstm"}[
                    settings.model_choice
                ]
                if {"xgb": "xgboost", "torch": "mlp"}.get(
                    model.model_type, model.model_type
                ) != expected:
                    raise ArtifactError(
                        f"configured {expected} but loaded {model.model_type}; "
                        "configure pipeline.model_artifacts"
                    )
                try:
                    if model.resolved_bounds:
                        taxonomy = taxonomy.with_resolved_bounds(
                            model.resolved_bounds, model.resolved_rate_limits
                        )
                    validator = load_mahalanobis_validator(settings.artifacts.mahalanobis)
                    verify_validator_compatibility(validator, model, settings)
                    coupling = (
                        SensorCouplingModel.load(settings.artifacts.coupling)
                        if settings.artifacts.coupling
                        else None
                    )
                    if not model.resolved_bounds and coupling is not None:
                        taxonomy = taxonomy.with_resolved_bounds(
                            coupling.resolved_bounds, coupling.resolved_rate_limits
                        )
                    taxonomy.validate_model_feature_coverage(model.feature_names)
                    if not taxonomy.active_controllable_feature_names(model.feature_names):
                        raise ValueError(
                            "at least one configured controllable proxy must be a model feature"
                        )
                    missing_bounds = [
                        name
                        for name, spec in taxonomy.feature_by_name().items()
                        if name in model.feature_names
                        and (spec.bounds.minimum is None or spec.bounds.maximum is None)
                    ]
                    if missing_bounds:
                        raise ValueError(f"unresolved training-derived bounds: {missing_bounds}")
                    if coupling is not None:
                        if set(coupling.training_engine_ids) != set(model.training_engine_ids):
                            raise ValueError(
                                "coupling fitting engines differ from model fitting engines"
                            )
                        calibration = (model.metrics or {}).get("calibration", {})
                        expected_ids = (
                            calibration.get("fit_engine_ids", [])
                            if isinstance(calibration, dict)
                            else []
                        )
                        if (
                            not expected_ids
                            or set(coupling.calibration_engine_ids) != set(expected_ids)
                            or not coupling.calibration_report
                        ):
                            raise ValueError(
                                "coupling residual calibration must match model validation engines"
                            )
                        if not set(coupling.predictor_features).issubset(
                            model.feature_names
                        ) or not set(coupling.dependent_features).issubset(
                            taxonomy.feature_by_name()
                        ):
                            raise ValueError(
                                "coupling predictors/dependents are incompatible "
                                "with model/taxonomy"
                            )
                    for key, expected_value in (
                        ("dataset", settings.data.dataset),
                        ("horizon_H", settings.horizon_H),
                    ):
                        if (
                            key in (model.metrics or {})
                            and (model.metrics or {})[key] != expected_value
                        ):
                            raise ValueError(f"model {key} differs from configured value")
                    _CACHE[identity] = PrescriptXAIEngine(
                        settings, taxonomy, model, validator, coupling
                    )
                except (ValueError, OSError) as error:
                    raise ArtifactError(str(error)) from error
                while len(_CACHE) > settings.pipeline.artifact_cache_size:
                    _CACHE.popitem(last=False)
            _CACHE.move_to_end(identity)
            return cls(_CACHE[identity])

    @classmethod
    def from_artifacts(cls, path: Path | str) -> PrescriptXAI:
        """Load a YAML config or directory containing pipeline.yaml; paths stay explicit."""
        target = Path(path)
        return cls.from_config(target / "pipeline.yaml" if target.is_dir() else target)

    def _normalize(
        self, raw: RawInput, context: InputContext | Mapping[str, object] | None, *, complete: bool
    ) -> tuple[dict[str, float], InputContext]:
        try:
            observed = (
                context
                if isinstance(context, InputContext)
                else InputContext.model_validate(context or {})
            )
        except ValidationError as error:
            raise (
                HistoryError(str(error)) if "history" in str(error) else InputError(str(error))
            ) from error
        names = self.engine.model.feature_names
        if observed.feature_names is not None and observed.feature_names != names:
            raise FeatureError(
                "vector/history feature order differs from saved model feature order"
            )
        values: dict[str, float]
        if isinstance(raw, pd.Series):
            if raw.index.has_duplicates:
                raise FeatureError("duplicate Series columns")
            if any(not isinstance(name, str) for name in raw.index):
                raise FeatureError("Series columns must have string names")
            values = cast(dict[str, float], raw.to_dict())
        elif isinstance(raw, Mapping):
            values = dict(raw)
        else:
            array = np.asarray(raw)
            if array.ndim != 1 or len(array) != len(names):
                raise FeatureError(
                    f"vector must have shape ({len(names)},) in saved model feature order"
                )
            if observed.feature_names is not None and observed.feature_names != names:
                raise FeatureError("vector feature order differs from saved model feature order")
            values = dict(zip(names, array, strict=True))
        for name, value in observed.telemetry.items():
            if name in values and values[name] != value:
                raise FeatureError(f"conflicting observed value for {name}")
            values[name] = value
        for name in ("engine_id", "cycle"):
            value = getattr(observed, name)
            if value is not None:
                if name in values and values[name] != value:
                    raise FeatureError(f"conflicting context {name}")
                values[name] = value
        specs = self.engine.taxonomy.feature_by_name()
        unknown = set(values) - (set(specs) | set(names))
        required = set(names)
        if complete:
            required |= {
                name
                for group in self.engine.taxonomy.feature_groups.model_dump().values()
                for name in group["features"]
            }
        if unknown or required - set(values):
            raise FeatureError(
                f"missing columns: {sorted(required - set(values))}; "
                f"unknown columns: {sorted(unknown)}"
            )
        if any(isinstance(value, (bool, np.bool_)) for value in values.values()):
            raise InputError("boolean telemetry is not a numeric physical measurement")
        try:
            normalized = {str(name): float(value) for name, value in values.items()}
        except (TypeError, ValueError) as error:
            raise InputError("telemetry values must be numeric in raw units") from error
        if not np.isfinite(list(normalized.values())).all():
            raise InputError("telemetry contains NaN or infinity")
        for name, unit in observed.units.items():
            if name not in specs or specs[name].unit != unit:
                raise UnitError(
                    f"unit for {name} must be "
                    f"{specs[name].unit if name in specs else 'a known configured feature'}"
                )
        for name in ("engine_id", "cycle"):
            if name in normalized and (
                normalized[name] < 1 or normalized[name] != int(normalized[name])
            ):
                raise InputError(f"{name} must be a positive integer")
        return normalized, observed

    def _bundle(self, context: InputContext) -> ModelBundle:
        if not hasattr(self.engine.model.estimator, "window"):
            if context.history is not None:
                raise HistoryError("history is accepted only for an LSTM model")
            return self.engine.model
        width = len(self.engine.model.feature_names)
        window = int(self.engine.model.estimator.window)
        try:
            history = np.asarray(context.history, dtype=float)
        except (TypeError, ValueError) as error:
            raise HistoryError("history must be a rectangular numeric array") from error
        if window == 1 and (context.history is None or not context.history):
            history = np.empty((0, width), dtype=float)
        if history.shape != (window - 1, width) or not np.isfinite(history).all():
            raise HistoryError(
                f"LSTM requires actual prior history of shape ({window - 1}, {width}) "
                "in saved feature order"
            )
        return replace(
            self.engine.model, estimator=_LatestSequenceEstimator(self.engine.model, history)
        )

    def assess(
        self,
        x_raw: RawInput,
        context: InputContext | Mapping[str, object] | None = None,
        mode: Literal["fast", "thorough"] | None = None,
    ) -> Assessment:
        """Return true calibrated risk; below alert does not mean below the safe target."""
        state, observed = self._normalize(x_raw, context, complete=False)
        with self.engine.predictor_lock:
            risk = float(self._bundle(observed).predict_risk(pd.DataFrame([state]))[0])
        selected_mode = mode or self.config.pipeline.default_mode
        if not isinstance(selected_mode, str) or selected_mode not in {"fast", "thorough"}:
            raise InputError("mode must be fast or thorough")
        return Assessment(
            mode="FAST" if selected_mode == "fast" else "THOROUGH",
            risk=risk,
            alert=risk >= self.config.tau_danger,
            tau_danger=self.config.tau_danger,
            tau_safe=self.config.tau_safe,
            model_version=self.model_version,
            config_hash=self.config_hash,
            seed=self.config.seed,
        )

    def recommend(
        self,
        x_raw: RawInput,
        context: InputContext | Mapping[str, object] | None = None,
        mode: Literal["fast", "thorough"] | None = None,
    ) -> RecourseResult:
        """Gate, solve with request-local settings, and return all independent checks."""
        started = perf_counter_ns()
        state, observed = self._normalize(x_raw, context, complete=True)
        ingestion = (perf_counter_ns() - started) / 1e6
        selected_mode = mode or self.config.pipeline.default_mode
        if not isinstance(selected_mode, str) or selected_mode not in {"fast", "thorough"}:
            raise InputError("mode must be fast or thorough")
        with self.engine.predictor_lock:
            bundle = self._bundle(observed)
            before = perf_counter_ns()
            risk = float(bundle.predict_risk(pd.DataFrame([state]))[0])
            inference = (perf_counter_ns() - before) / 1e6
            config = self.config.model_copy(deep=True)
            config.recourse.search_mode = selected_mode
            before = perf_counter_ns()
            if risk < config.tau_danger:
                optimization = OptimizationResult(
                    state,
                    (),
                    risk,
                    risk,
                    True,
                    risk <= config.tau_safe,
                    "no intervention required: below alert threshold",
                    0.0,
                    actuator_constraints_feasible=not check_bound_violations(
                        state,
                        self.engine.taxonomy,
                        features=self.engine.taxonomy.active_controllable_feature_names(
                            bundle.feature_names
                        ),
                    ),
                )
                optimization_ms = 0.0
            else:
                optimization = optimize_recourse(
                    state,
                    bundle,
                    self.engine.taxonomy,
                    config,
                    self.engine.coupling,
                    self.engine.mahalanobis,
                )
                optimization_ms = (perf_counter_ns() - before) / 1e6
            before = perf_counter_ns()
            validation = validate_candidate(
                state,
                optimization.state,
                bundle,
                self.engine.taxonomy,
                self.engine.mahalanobis,
                config,
                self.engine.coupling,
            )
            validation_ms = (perf_counter_ns() - before) / 1e6
            final_risk = validation.tier1_model.measurement
            if final_risk is None:
                raise ArtifactError("final Tier 1 rescore did not return a true risk")
            surrogate = []
            if bundle.supports_gradients:
                estimator = (
                    bundle.estimator
                    if getattr(bundle.estimator, "supports_gradients", False)
                    else bundle.surrogate
                )
                with torch.no_grad():
                    scaled = bundle.scaler.transform(
                        pd.DataFrame([state, optimization.state])[list(bundle.feature_names)]
                    )
                    surrogate = (
                        bundle.torch_forward(
                            torch.as_tensor(
                                scaled,
                                dtype=torch.float32,
                                device=getattr(estimator, "device", "cpu"),
                            )
                        )
                        .detach()
                        .cpu()
                        .numpy()
                        .tolist()
                    )
        return self._compose_result(
            state, optimization, validation, bundle, config, selected_mode,
            StageTimings(
                ingestion_ms=ingestion, inference_ms=inference,
                optimization_ms=optimization_ms, validation_ms=validation_ms,
            ), started, surrogate,
        )

    def validate_controls(
        self,
        x_raw: RawInput,
        controls: Mapping[str, float],
        context: InputContext | Mapping[str, object] | None = None,
        mode: Literal["fast", "thorough"] | None = None,
    ) -> RecourseResult:
        """Preview named proxy controls through the production propagation, tiers and triage.

        This method performs no optimization and does not project invalid controls into a
        passing interval. Bounds, rate, sparsity and coupling failures remain visible. Only
        configured control features may be edited; the original observed history is fixed.
        """
        started = perf_counter_ns()
        state, observed = self._normalize(x_raw, context, complete=True)
        if not isinstance(controls, Mapping):
            raise InputError("controls must be named raw-unit measurements")
        selected_mode = mode or self.config.pipeline.default_mode
        if selected_mode not in {"fast", "thorough"}:
            raise InputError("mode must be fast or thorough")
        actions = self.engine.taxonomy.active_controllable_feature_names(
            self.engine.model.feature_names
        )
        if set(controls) - set(actions):
            raise FeatureError("only configured controllable proxies may be edited")
        if any(isinstance(value, (bool, np.bool_)) for value in controls.values()):
            raise InputError("boolean controls are not physical measurements")
        try:
            proposed = {**state, **{name: float(value) for name, value in controls.items()}}
        except (TypeError, ValueError) as error:
            raise InputError("controls must be finite raw-unit numbers") from error
        if not np.isfinite(list(proposed.values())).all():
            raise InputError("controls must be finite raw-unit numbers")
        ingestion = (perf_counter_ns() - started) / 1e6
        config = self.config.model_copy(deep=True)
        config.recourse.search_mode = selected_mode
        with self.engine.predictor_lock:
            bundle = self._bundle(observed)
            before = perf_counter_ns()
            risk = float(bundle.predict_risk(pd.DataFrame([state]))[0])
            inference = (perf_counter_ns() - before) / 1e6
            if risk < config.tau_danger and proposed != state:
                raise InputError("below the alert gate: no manual intervention is required")
            candidate = apply_coupling_for_bundle(
                proposed, self.engine.coupling, reference_state=state
            )
            before = perf_counter_ns()
            validation = validate_candidate(
                state, candidate, bundle, self.engine.taxonomy, self.engine.mahalanobis,
                config, self.engine.coupling, mode="collect_all",
            )
            validation_ms = (perf_counter_ns() - before) / 1e6
        final_risk = validation.tier1_model.measurement
        if final_risk is None:
            raise ArtifactError("manual Tier 1 rescore did not return a true risk")
        scales = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
        deltas = _delta_mappings(
            {name: (candidate[name] - state[name]) / scales[name] for name in actions},
            actions, state, self.engine.taxonomy.feature_by_name(),
            np.asarray([scales[name] for name in actions]), 0.0,
        )
        feasible = not check_bound_violations(
            candidate, self.engine.taxonomy, features=actions
        ) and not check_rate_violations(
            state, candidate, self.engine.taxonomy,
            horizon_steps=config.recourse.rate_horizon_steps,
        )
        support_exceeded = len(deltas) > config.recourse.k_max
        feasible = feasible and not support_exceeded
        optimization = OptimizationResult(
            candidate, deltas, risk, final_risk, True, validation.model_valid,
            "Manual control preview; no optimization performed.", None,
            failure_reason=(
                "manual_sparsity_exceeded" if support_exceeded
                else None if validation.joint and feasible else "manual_validation_failed"
            ),
            actuator_constraints_feasible=feasible,
            effective_solver_settings={"manual_preview": True, "mode": selected_mode},
        )
        result = self._compose_result(
            state, optimization, validation, bundle, config, selected_mode,
            StageTimings(
                ingestion_ms=ingestion, inference_ms=inference,
                optimization_ms=0.0, validation_ms=validation_ms,
            ), started,
        )
        return result.model_copy(
            update={"warnings": (*result.warnings, optimization.message)}
        )

    def _compose_result(
        self,
        state: dict[str, float],
        optimization: OptimizationResult,
        validation: ValidationReport,
        bundle: ModelBundle,
        config: AppConfig,
        selected_mode: Literal["fast", "thorough"],
        timings: StageTimings,
        started: int,
        surrogate: Sequence[float] = (),
    ) -> RecourseResult:
        """Share the frozen result/delta/triage composition for solves and manual previews."""
        risk = optimization.initial_risk
        final_risk = validation.tier1_model.measurement
        if final_risk is None:
            raise ArtifactError("final Tier 1 rescore did not return a true risk")
        specs = self.engine.taxonomy.feature_by_name()
        actions = self.engine.taxonomy.active_controllable_feature_names(bundle.feature_names)
        feasible = (
            optimization.actuator_constraints_feasible
            and len(optimization.deltas) <= config.recourse.k_max
        )
        physical = validation.physical_valid
        alert = risk >= config.tau_danger
        status = (
            "NO_INTERVENTION"
            if not alert
            else "RECOVERABLE"
            if validation.model_valid and physical and feasible
            else "PARTIAL"
            if physical
            and feasible
            and final_risk > config.tau_safe
            and risk - final_risk >= config.pipeline.delta_min
            else "ESCALATE"
        )
        deltas = {}
        scale = dict(zip(bundle.feature_names, bundle.scaler.scaler.scale_, strict=True))
        for name, current in state.items():
            change = optimization.state[name] - current
            if change != 0:
                lower, upper = specs[name].bounds.minimum, specs[name].bounds.maximum
                span = upper - lower if lower is not None and upper is not None else None
                deltas[name] = FeatureDelta(
                    raw_delta=change,
                    percent_change=change / abs(current) * 100 if current else None,
                    percent_of_range=change / span * 100 if span else None,
                    scaled_delta=change / scale[name] if name in scale else None,
                    role="action"
                    if name in actions
                    else "dependent"
                    if name in self.engine.taxonomy.feature_groups.dependent_sensors.features
                    else "other",
                )
        failure = None
        if status in {"PARTIAL", "ESCALATE"}:
            failure = FailureInformation(
                reason=optimization.failure_reason or "validation_failed",
                message=optimization.message,
                closest_candidate=optimization.state,
                risk_reached=final_risk,
                failing_tiers=validation.failing_tiers,
                suggested_escalation=config.pipeline.escalation_message,
            )
        effective = config.model_dump(mode="json")
        effective_hash = hashlib.sha256(json.dumps(effective, sort_keys=True).encode()).hexdigest()
        return RecourseResult(
            original_state=state,
            new_state=optimization.state,
            delta_per_feature=deltas,
            risk_before=risk,
            risk_after=final_risk,
            validation_report=validation.to_schema(),
            timings=timings.model_copy(
                update={"pipeline_ms": (perf_counter_ns() - started) / 1e6}
            ),
            warnings=tuple(w for tier in validation.tiers().values() for w in tier.warnings),
            alert=alert,
            status=cast(Literal["NO_INTERVENTION", "RECOVERABLE", "PARTIAL", "ESCALATE"], status),
            triage=None
            if status == "NO_INTERVENTION"
            else cast(Literal["RECOVERABLE", "PARTIAL", "ESCALATE"], status),
            mode="FAST" if selected_mode == "fast" else "THOROUGH",
            surrogate_risk_before=surrogate[0] if surrogate else None,
            surrogate_risk_after=surrogate[1] if surrogate else None,
            failure=failure,
            assumptions=validation.assumptions,
            proxy_assumptions=True,
            action_features=tuple(n for n in deltas if n in actions),
            action_feasible=feasible,
            config_hash=effective_hash,
            model_version=self.model_version,
            seed=config.seed,
            run_id=current_run_id() if current_run_id() != "unassigned" else uuid4().hex,
            tau_danger=config.tau_danger,
            tau_safe=config.tau_safe,
            delta_min=config.pipeline.delta_min,
            solver_settings=optimization.effective_solver_settings,
        )

    def recommend_batch(
        self,
        frame: pd.DataFrame,
        mode: Literal["fast", "thorough"] | None = None,
        *,
        workers: int | None = None,
        contexts: Sequence[InputContext | None] | None = None,
    ) -> list[RecourseResult]:
        """Return input-order results, optionally using isolated worker processes."""
        selected_mode = mode or self.config.pipeline.default_mode
        if not isinstance(selected_mode, str) or selected_mode not in {"fast", "thorough"}:
            raise InputError("mode must be fast or thorough")
        if not isinstance(frame, pd.DataFrame) or frame.empty or frame.columns.has_duplicates:
            raise FeatureError("batch must be a nonempty DataFrame with unique columns")
        if len(frame) > self.config.pipeline.max_batch_rows:
            raise InputError("batch exceeds configured max_batch_rows")
        if contexts is not None and len(contexts) != len(frame):
            raise InputError("contexts length must match batch rows")
        count = workers if workers is not None else self.config.pipeline.batch_workers
        if count < 1 or count > self.config.pipeline.max_workers:
            raise InputError("workers outside configured range")
        observed = list(contexts) if contexts is not None else [None] * len(frame)
        records = [
            (cast(dict[str, float], row.to_dict()), selected_mode, ctx)
            for (_, row), ctx in zip(frame.iterrows(), observed, strict=True)
        ]
        if count == 1:
            return [self.recommend(row, ctx, selected_mode) for row, _, ctx in records]
        devices = [
            getattr(self.engine.model.estimator, "device", "cpu"),
            getattr(self.engine.model.surrogate, "device", "cpu"),
        ]
        if self.config.model.torch_device != "cpu" or any(
            str(device).split(":")[0] != "cpu" for device in devices
        ):
            raise InputError("multiprocessing requires CPU artifacts")
        e = self.engine
        with ProcessPoolExecutor(
            max_workers=count,
            initializer=_initialize_worker,
            initargs=(
                self.config.model_copy(deep=True),
                e.taxonomy,
                e.model,
                e.mahalanobis,
                e.coupling,
            ),
        ) as pool:
            return list(pool.map(_recommend_worker, records))

    def explain_result(self, result: RecourseResult) -> Explanation:
        """Describe measured raw-unit actions without plotting or claiming efficacy."""
        specs = self.engine.taxonomy.feature_by_name()
        actions = []
        for name in () if result.status == "ESCALATE" else result.action_features:
            delta = result.delta_per_feature[name]
            amount = (
                f"{abs(delta.percent_change):.3g}%"
                if delta.percent_change is not None
                else f"{abs(delta.raw_delta):.3g} {specs[name].unit}"
            )
            actions.append(
                f"{'Reduce' if delta.raw_delta < 0 else 'Increase'} {specs[name].label} "
                f"by {amount} (from {result.original_state[name]:.6g} to "
                f"{result.new_state[name]:.6g} {specs[name].unit}); proxy assumption."
            )
        summary: str = "no intervention required" if not result.alert else result.status
        if result.status == "ESCALATE" and result.failure is not None:
            summary += ": " + result.failure.suggested_escalation
        elif result.status == "PARTIAL":
            summary += ": true risk remains above the safe target"
        return Explanation(
            summary=summary,
            actions=tuple(actions),
            risk_before=result.risk_before,
            risk_after=result.risk_after,
            verdict={
                "model_valid": result.validation_report.model_valid,
                "plausible": result.validation_report.plausible,
                "constraints_ok": result.validation_report.constraints_ok,
                "joint": result.validation_report.joint,
            },
            evidence_level=result.evidence_level,
            warnings=(*result.warnings, *result.assumptions),
        )

    def info(self) -> dict[str, object]:
        """Describe loaded artifacts, thresholds and proxy assumptions without API secrets."""
        return {
            "model_version": self.model_version,
            "schema_version": "2.0.0",
            "config_hash": self.config_hash,
            "dataset": self.config.data.dataset,
            "model_choice": self.config.model_choice,
            "history_rows": max(0, int(getattr(self.engine.model.estimator, "window", 1)) - 1),
            "artifacts": self.config.artifacts.model_dump(mode="json"),
            "tau_danger": self.config.tau_danger,
            "tau_safe": self.config.tau_safe,
            "D_max": self.engine.mahalanobis.max_distance,
            "feature_names": self.engine.model.feature_names,
            "feature_groups": self.engine.taxonomy.feature_groups.model_dump(),
            "units": {n: s.unit for n, s in self.engine.taxonomy.feature_by_name().items()},
            "feature_metadata": {
                name: spec.model_dump(mode="json")
                for name, spec in self.engine.taxonomy.feature_by_name().items()
            },
            "scaling": {
                "feature_names": self.engine.model.feature_names,
                "mean": self.engine.model.scaler.scaler.mean_.tolist(),
                "scale": self.engine.model.scaler.scaler.scale_.tolist(),
            },
            "assumptions": [
                "C-MAPSS controls, bounds, rates and K are proxies/assumptions; no RUL extension."
            ],
        }


_WORKER: PrescriptXAI | None = None


def _initialize_worker(
    config: AppConfig,
    taxonomy: FeatureTaxonomy,
    model: ModelBundle,
    mahalanobis: MahalanobisValidator,
    coupling: SensorCouplingModel | None,
) -> None:
    """Initialize one independent process without serializing a thread lock."""
    global _WORKER
    _WORKER = PrescriptXAI(PrescriptXAIEngine(config, taxonomy, model, mahalanobis, coupling))


def _recommend_worker(
    item: tuple[dict[str, float], Literal["fast", "thorough"], InputContext | None],
) -> RecourseResult:
    """Evaluate one batch item in its initialized process."""
    assert _WORKER is not None
    return _WORKER.recommend(item[0], item[2], item[1])
