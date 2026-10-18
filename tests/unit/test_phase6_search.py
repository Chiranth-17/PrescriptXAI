"""Verify semantics-preserving batch coupling checks and baseline isolation."""

from pathlib import Path

import numpy as np
import pytest
import torch

from fixtures.cmapss import make_cmapss_frame
from fixtures.recourse_models import SigmoidEstimator, make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.data.cmapss import to_model_frame
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.recourse.optimizer import RecourseOptimizer
from prescriptxai.validation.pipeline import fit_mahalanobis_validator
from prescriptxai.validation.tier4_coupling import (
    calibrate_coupling_thresholds,
    coupling_pass_mask,
    validate_sensor_coupling,
)


class OpposingGradient(SigmoidEstimator):
    """Supply deliberately misleading test gradients so the true-model grid is necessary."""

    def torch_forward(self, features: torch.Tensor) -> torch.Tensor:
        """Push toward the wrong end while preserving genuine true-model scoring."""
        return torch.sigmoid(5 * features[:, 0] + 10)


@pytest.mark.parametrize("mode", ["fast", "thorough"])
@pytest.mark.parametrize("with_validator", [True, False])
def test_disabled_validation_does_not_filter_grid(mode: str, with_validator: bool) -> None:
    """A baseline's excluded coupling constraints cannot silently affect its selected grid row."""
    bundle, taxonomy, training = make_recourse_fixture()
    bundle.estimator = OpposingGradient()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.search_mode = mode
    config.recourse.max_iterations = 2
    config.recourse.alpha_steps = config.recourse.restarts = 1
    config.recourse.l1_escalation_steps = 1
    config.recourse.true_model_grid_points = 5
    # Every safe point violates this intentional test-only rule.
    taxonomy.coupling_rules[0].tolerance = -10
    validator = (
        fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
        if with_validator
        else None
    )
    result = RecourseOptimizer(
        bundle, taxonomy, mahalanobis=validator, validate_plausibility=False
    ).solve({"actuator": -2, "sensor": 2}, config)
    assert result.model_valid and result.state["actuator"] > 0
    assert not validate_sensor_coupling(result.state, taxonomy).valid


@pytest.mark.parametrize("backend", ["ridge", "gradient_boosting", "mlp"])
def test_batched_coupling_contains_every_scalar_pass_with_omitted_dependents(backend: str) -> None:
    """True backend residual checks agree by named fields, including untouched dropped sensors."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    taxonomy.coupling.backend = backend
    taxonomy.coupling.torch_epochs = 2
    taxonomy.coupling.mlp_max_iter = 5
    taxonomy.coupling.gradient_boosting_estimators = 5
    frame = add_training_labels(
        to_model_frame(make_cmapss_frame(3, min_cycles=90, max_cycles=93)), None, 30
    )
    coupling = SensorCouplingModel.fit(
        frame, taxonomy, training_engine_ids=(1, 2), failure_horizon=30
    )
    coupling = calibrate_coupling_thresholds(
        coupling,
        frame.loc[frame.engine_id == 3],
        (3,),
        reference_distribution="healthy_to_moderate",
        min_rul=30,
    )
    original = frame.iloc[0].to_dict()
    omitted = coupling.dependent_features[0]
    names = tuple(n for n in coupling.feature_names if n != omitted)
    rows = frame.loc[:9, names].to_numpy(dtype=float, copy=True)
    # Include a deliberately inconsistent candidate in the same batch.
    rows[-1, names.index(coupling.dependent_features[1])] += 100
    mask = coupling_pass_mask(rows, names, original, taxonomy, coupling)
    exact = np.asarray(
        [
            validate_sensor_coupling(
                {**original, **dict(zip(names, row, strict=True))}, taxonomy, coupling
            ).valid
            for row in rows
        ]
    )
    assert np.all(mask[exact])
    assert not mask[-1]
    assert mask.shape == (10,)
    assert not coupling_pass_mask(rows, names, original, taxonomy, None)[-1]


def test_rule_boundary_batch_is_inclusive() -> None:
    """Exact hand-written rule boundaries remain eligible for final scalar acceptance."""
    _, taxonomy, _ = make_recourse_fixture()
    rows = np.asarray([[2, 2], [2 + 1e-8, 2], [1, 2]], dtype=float)
    mask = coupling_pass_mask(rows, ("actuator", "sensor"), {}, taxonomy, None)
    np.testing.assert_array_equal(mask, [True, False, True])
