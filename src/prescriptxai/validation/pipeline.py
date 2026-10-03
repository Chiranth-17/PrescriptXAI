"""Orchestration for independent model and physical validity tiers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from prescriptxai.config import AppConfig
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.models.registry import ModelBundle
from prescriptxai.schemas import DeltaMapping, RecourseOutcome
from prescriptxai.validation.base import TierResult
from prescriptxai.validation.tier1_model import validate_model_risk
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator
from prescriptxai.validation.tier3_engineering import validate_engineering
from prescriptxai.validation.tier4_coupling import validate_sensor_coupling


def save_mahalanobis_validator(validator: MahalanobisValidator, path: Path) -> Path:
    """Persist fitted Tier 2 statistics and training-engine provenance."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(validator, path)
    return path


def load_mahalanobis_validator(path: Path) -> MahalanobisValidator:
    """Load fitted Tier 2 statistics from a configured local artifact."""
    if not path.is_file():
        raise FileNotFoundError(path)
    loaded: object = joblib.load(path)
    if not isinstance(loaded, MahalanobisValidator):
        raise ValueError("artifact does not contain a MahalanobisValidator")
    return loaded


@dataclass(frozen=True)
class ValidationReport:
    """Four separate tier results and aggregate outcome."""

    tier1_model: TierResult
    tier2_plausibility: TierResult
    tier3_engineering: TierResult
    tier4_coupling: TierResult

    @property
    def model_valid(self) -> bool:
        """Whether the predictor target-risk check passed."""
        return self.tier1_model.valid

    @property
    def physical_valid(self) -> bool:
        """Whether the three independent physical plausibility checks passed."""
        return all(
            tier.valid
            for tier in (self.tier2_plausibility, self.tier3_engineering, self.tier4_coupling)
        )

    @property
    def success(self) -> bool:
        """Whether model safety and all required physical checks passed."""
        return self.model_valid and self.physical_valid

    def as_outcome(
        self, initial_risk: float, final_risk: float, deltas: tuple[DeltaMapping, ...]
    ) -> RecourseOutcome:
        """Convert the separate tier results to a public machine-readable outcome."""
        return RecourseOutcome(
            initial_risk=initial_risk,
            final_risk=final_risk,
            model_valid=self.model_valid,
            tier2_plausible=self.tier2_plausibility.valid,
            tier3_engineering_valid=self.tier3_engineering.valid,
            tier4_coupling_valid=self.tier4_coupling.valid,
            deltas=deltas,
            success=self.success,
        )


def fit_mahalanobis_validator(
    training_frame: pd.DataFrame,
    bundle: ModelBundle,
    expected_training_engine_ids: tuple[int, ...],
    config: AppConfig,
) -> MahalanobisValidator:
    """Fit Tier 2 only from rows of declared training engines using the model's scaler."""
    if "engine_id" not in training_frame.columns:
        raise ValueError("training frame must contain engine_id provenance")
    observed_ids = tuple(sorted(int(value) for value in training_frame["engine_id"].unique()))
    if observed_ids != tuple(sorted(expected_training_engine_ids)):
        raise ValueError("Tier 2 rows must contain exactly the model's training engines")
    raw_features = training_frame[list(bundle.feature_names)]
    scaled = bundle.scaler.transform(raw_features)
    return MahalanobisValidator.fit(
        scaled,
        bundle.feature_names,
        training_frame["engine_id"].to_numpy(dtype=np.int64),
        expected_training_engine_ids,
        config.validation.mahalanobis_max,
        config.validation.covariance_regularization,
    )


def validate_candidate(
    initial_state: Mapping[str, float],
    candidate_state: Mapping[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    mahalanobis: MahalanobisValidator,
    config: AppConfig,
) -> ValidationReport:
    """Run Tiers 1–4 without combining model and physical validity."""
    candidate_frame = pd.DataFrame([dict(candidate_state)])
    final_risk = float(bundle.predict_risk(candidate_frame)[0])
    tier1 = validate_model_risk(final_risk, config.model.safe_threshold)
    raw_features = candidate_frame[list(bundle.feature_names)]
    scaled_candidate = bundle.scaler.transform(raw_features)[0]
    if mahalanobis.feature_names != bundle.feature_names:
        raise ValueError("Mahalanobis and model feature orders do not match")
    tier2 = mahalanobis.validate(np.asarray(scaled_candidate, dtype=float))
    tier3 = validate_engineering(initial_state, candidate_state, taxonomy)
    tier4 = validate_sensor_coupling(candidate_state, taxonomy)
    return ValidationReport(tier1, tier2, tier3, tier4)
