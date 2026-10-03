"""Application engine joining model prediction, recourse, and validation."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns

from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.taxonomy import FeatureTaxonomy, load_taxonomy
from prescriptxai.models.registry import ModelBundle, load_model_bundle
from prescriptxai.recourse.optimizer import OptimizationResult, optimize_recourse
from prescriptxai.schemas import RecourseOutcome
from prescriptxai.validation.pipeline import (
    ValidationReport,
    load_mahalanobis_validator,
    validate_candidate,
)
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator

LOGGER = logging.getLogger(__name__)


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

    @classmethod
    def from_files(
        cls,
        config_path: Path,
        taxonomy_path: Path,
        model_path: Path | None = None,
        mahalanobis_path: Path | None = None,
    ) -> PrescriptXAIEngine:
        """Load an engine from configured YAML and fitted artifacts."""
        config = load_config(config_path)
        taxonomy = load_taxonomy(taxonomy_path)
        model = load_model_bundle(model_path or config.artifacts.model)
        mahalanobis = load_mahalanobis_validator(mahalanobis_path or config.artifacts.mahalanobis)
        if model.feature_names != mahalanobis.feature_names:
            raise ValueError("model and Mahalanobis artifacts have different feature orders")
        if set(taxonomy.feature_groups.controllable_actuators.features) - set(model.feature_names):
            raise ValueError("configured actuators must be model input features")
        return cls(config, taxonomy, model, mahalanobis)

    def recommend(self, state: Mapping[str, float]) -> RecommendationResult:
        """Generate an actuator-only candidate and run all configured validation tiers."""
        raw_state = {name: float(value) for name, value in state.items()}
        missing = set(self.model.feature_names) - set(raw_state)
        if missing:
            raise ValueError(f"state is missing model features: {sorted(missing)}")
        optimization_started = perf_counter_ns()
        optimization = optimize_recourse(raw_state, self.model, self.taxonomy, self.config)
        optimization_ms = (perf_counter_ns() - optimization_started) / 1_000_000
        validation_started = perf_counter_ns()
        validation = validate_candidate(
            raw_state,
            optimization.state,
            self.model,
            self.taxonomy,
            self.mahalanobis,
            self.config,
        )
        validation_ms = (perf_counter_ns() - validation_started) / 1_000_000
        outcome = validation.as_outcome(
            optimization.initial_risk,
            optimization.final_risk,
            optimization.deltas,
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
