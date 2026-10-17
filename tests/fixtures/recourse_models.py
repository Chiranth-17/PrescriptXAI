"""Explicitly synthetic recourse model fixture; never used for benchmark reports."""

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray

from prescriptxai.constraints.taxonomy import (
    ActuatorConstraint,
    BoundsSpec,
    CouplingRule,
    FeatureGroup,
    FeatureGroups,
    FeatureSpec,
    FeatureTaxonomy,
    RateLimitSpec,
)
from prescriptxai.data.preprocess import fit_feature_scaler
from prescriptxai.models.registry import ModelBundle


class SigmoidEstimator:
    """Deterministic toy predictor used only in recourse tests."""

    classes_ = np.array([0, 1])
    supports_gradients = True

    def predict_proba(self, features: NDArray[np.float64]) -> NDArray[np.float64]:
        """Risk falls as the scaled actuator increases."""
        positive = 1.0 / (1.0 + np.exp(5.0 * features[:, 0]))
        return np.column_stack((1.0 - positive, positive))

    def torch_forward(self, features: torch.Tensor) -> torch.Tensor:
        """Differentiable counterpart of the fixture classifier's failure probability."""
        return torch.sigmoid(-5.0 * features[:, 0])


def make_recourse_fixture() -> tuple[ModelBundle, FeatureTaxonomy, pd.DataFrame]:
    """Build synthetic scaler, model, and constraints for logic tests only."""
    training = pd.DataFrame(
        {
            "engine_id": [1, 1, 2, 2, 3, 3, 4, 4],
            "actuator": [-2.0, -1.0, 0.0, 1.0, 2.0, 1.5, 0.5, -0.5],
            "sensor": [2.0] * 8,
        }
    )
    scaler = fit_feature_scaler(training, ("actuator", "sensor"))
    bundle = ModelBundle(
        estimator=SigmoidEstimator(),
        scaler=scaler,
        feature_names=("actuator", "sensor"),
        training_engine_ids=scaler.training_engine_ids,
        model_type="test-only-sigmoid",
        seed=17,
    )
    taxonomy = FeatureTaxonomy(
        schema_version=1,
        dataset="unit-test-fixture",
        feature_groups=FeatureGroups(
            controllable_actuators=FeatureGroup(features=["actuator"]),
            immutable_operational=FeatureGroup(features=[]),
            immutable_environmental=FeatureGroup(features=[]),
            dependent_sensors=FeatureGroup(features=["sensor"]),
            context=FeatureGroup(features=[]),
        ),
        actuator_constraints={
            "actuator": ActuatorConstraint(minimum=-2.0, maximum=2.0, max_change_per_step=4.0)
        },
        coupling_rules=[
            CouplingRule(
                name="actuator_below_sensor",
                feature_a="actuator",
                feature_b="sensor",
                relation="less_than",
                tolerance=0.0,
            )
        ],
        features=(
            FeatureSpec(
                name="actuator",
                label="actuator",
                unit="-",
                group="controllable",
                cmapss_column="s1",
                bounds=BoundsSpec(minimum=-2.0, maximum=2.0),
                max_rate_of_change=RateLimitSpec(absolute=4.0),
            ),
            FeatureSpec(
                name="sensor",
                label="sensor",
                unit="-",
                group="dependent",
                cmapss_column="s2",
                bounds=BoundsSpec(minimum=0.0, maximum=10.0),
            ),
        ),
    )
    return bundle, taxonomy, training
