"""Bounded comparison methods execute real coupling without applying plausibility filters."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.bounds import check_bound_violations, check_rate_violations
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import (
    ActuatorConstraint,
    BoundsSpec,
    FeatureSpec,
    FeatureTaxonomy,
    RateLimitSpec,
    load_taxonomy,
)
from prescriptxai.data.preprocess import fit_feature_scaler
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.baselines import bounded_l1_baseline, single_actuator_baseline


def _fitted_baseline_inputs() -> tuple[
    ModelBundle, FeatureTaxonomy, SensorCouplingModel, AppConfig
]:
    """Fit two-control Ridge coupling on test data with a declared analytic risk predictor."""
    bundle, taxonomy, training = make_recourse_fixture()
    training["coolant"] = [-1.0, 1.0, -0.5, 0.5, 0.0, -0.25, 0.25, 0.75]
    training["sensor"] = 2.0 + 0.8 * training.actuator - 0.2 * training.coolant
    settings = load_taxonomy(Path("configs/features.yaml"))
    specs = tuple(
        feature.model_copy(update={"bounds": BoundsSpec(minimum=None, maximum=None)})
        if feature.name == "sensor"
        else feature
        for feature in taxonomy.features
    ) + (
        FeatureSpec(
            name="coolant",
            label="Second test actuator",
            unit="-",
            group="controllable",
            cmapss_column="s3",
            bounds=BoundsSpec(minimum=-1.0, maximum=1.0),
            max_rate_of_change=RateLimitSpec(absolute=2.0),
        ),
    )
    taxonomy = taxonomy.model_copy(
        deep=True,
        update={
            "features": specs,
            "coupling": settings.coupling,
            "bound_estimation": settings.bound_estimation,
        },
    )
    taxonomy.feature_groups.controllable_actuators.features.append("coolant")
    taxonomy.actuator_constraints["coolant"] = ActuatorConstraint(
        minimum=-1.0, maximum=1.0, max_change_per_step=2.0
    )
    names = ("actuator", "sensor", "coolant")
    taxonomy = taxonomy.fit_training_bounds(training, columns=names)
    scaler = fit_feature_scaler(training, names)
    bundle.scaler = scaler
    bundle.feature_names = names
    coupling = SensorCouplingModel.fit(
        training, taxonomy, training_engine_ids=bundle.training_engine_ids, failure_horizon=30
    )
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_iterations = 40
    config.recourse.restarts = 1
    config.recourse.alpha_steps = 2
    config.recourse.l1_escalation_steps = 1
    config.recourse.max_changed_features = 2
    return bundle, taxonomy, coupling, config


@pytest.mark.parametrize("single", [False, True])
def test_bounded_baselines_run_with_reference_coupling_and_no_plausibility_filter(
    single: bool,
) -> None:
    """A failed learned residual stays failed while a bounded model-safe action is found."""
    bundle, taxonomy, coupling, config = _fitted_baseline_inputs()
    initial = {"actuator": -1.0, "sensor": 100.0, "coolant": 0.0}
    original_rules = coupling.evaluate_learned_constraints(initial)
    assert not all(rule.passed for rule in original_rules)
    baseline = single_actuator_baseline if single else bounded_l1_baseline
    result = baseline(initial, bundle, taxonomy, config, coupling)
    assert result.failure_reason != "coupling_model_unavailable"
    assert result.solver_calls > 0
    assert result.model_valid
    assert len(result.deltas) <= (1 if single else 2)
    assert result.actuator_constraints_feasible
    assert not check_bound_violations(
        result.state,
        taxonomy,
        features=taxonomy.active_controllable_feature_names(bundle.feature_names),
    )
    assert not check_rate_violations(initial, result.state, taxonomy)
    assert result.state["sensor"] != initial["sensor"]
    expected = coupling.propagate(result.state, reference_state=initial)
    assert result.state == pytest.approx(expected)
    candidate_rules = coupling.evaluate_learned_constraints(result.state)
    assert not all(rule.passed for rule in candidate_rules)
    np.testing.assert_allclose(
        [rule.margin for rule in candidate_rules],
        [rule.margin for rule in original_rules],
        rtol=0,
        atol=1e-10,
    )
    assert result.final_risk == pytest.approx(
        float(bundle.predict_risk(pd.DataFrame([result.state]))[0])
    )


def test_single_actuator_baseline_keeps_other_actuator_bounds() -> None:
    """A second actuator requiring projection cannot be ignored to claim a single-action success."""
    bundle, taxonomy, coupling, config = _fitted_baseline_inputs()
    initial = {"actuator": -1.0, "sensor": 100.0, "coolant": 1.05}
    result = single_actuator_baseline(initial, bundle, taxonomy, config, coupling)
    assert result.solver_calls > 0
    assert not result.model_valid
    assert len(result.deltas) <= 1
    assert not check_bound_violations(
        result.state,
        taxonomy,
        features=taxonomy.active_controllable_feature_names(bundle.feature_names),
    )
    assert not check_rate_violations(initial, result.state, taxonomy)
