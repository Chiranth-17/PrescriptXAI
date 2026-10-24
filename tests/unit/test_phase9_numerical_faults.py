"""Adversarial numerical regressions found during the independent Phase 9 audit."""

from pathlib import Path

import numpy as np
import pytest
import torch

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.constraints.bounds import allowed_interval, check_rate_violations
from prescriptxai.evaluation.metrics import predictor_metrics
from prescriptxai.models.calibration import ProbabilityCalibrator, calibration_diagnostics
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
@pytest.mark.parametrize("method", ["temperature", "sigmoid", "isotonic"])
def test_tensor_calibration_matches_true_numpy_at_endpoints(
    dtype: torch.dtype, method: str
) -> None:
    """True and differentiable paths agree even where clipping can flip a safe verdict."""
    calibrator = ProbabilityCalibrator(method).fit(
        np.asarray([0.0, 0.1, 0.4, 0.6, 0.9, 1.0]), np.asarray([0, 0, 0, 1, 1, 1])
    )
    if method == "temperature":
        calibrator.temperature = 15.0
    tensor = torch.tensor([0.0, 1e-8, 0.2, 0.8, 1.0], dtype=dtype, requires_grad=True)
    expected = calibrator.transform(tensor.detach().double().numpy())
    actual = calibrator.transform_tensor(tensor)
    np.testing.assert_allclose(actual.detach().double().numpy(), expected, atol=2e-7, rtol=1e-7)
    actual.sum().backward()
    assert tensor.grad is not None and torch.isfinite(tensor.grad).all()


@pytest.mark.parametrize("values", [[float("nan")], [float("inf")], [-1.0], [2.0], [], [[0.5]]])
def test_tensor_calibration_rejects_invalid_probabilities(values: list) -> None:
    """Tensor probability validation is as strict as the reported NumPy risk path."""
    calibrator = ProbabilityCalibrator("temperature")
    calibrator.temperature = 1.0
    with pytest.raises(ValueError, match="probabilit"):
        calibrator.transform_tensor(torch.tensor(values, dtype=torch.float64))


@pytest.mark.parametrize("labels", [[0.9, 1.1], [float("nan"), 1.0], [-0.1, 1.0]])
def test_metrics_reject_nonbinary_labels_before_integer_coercion(labels: list) -> None:
    """Malformed labels cannot silently become apparently perfect binary diagnostics."""
    with pytest.raises(ValueError, match="binary"):
        predictor_metrics(np.asarray(labels), np.asarray([0.1, 0.9]), 0.8)
    with pytest.raises(ValueError, match="binary"):
        calibration_diagnostics(np.asarray(labels), np.asarray([0.1, 0.9]))


@pytest.mark.parametrize("horizon", [float("nan"), float("inf"), 1.5, True, 0, -1])
def test_rate_horizon_is_a_positive_integer(horizon: int) -> None:
    """Malformed direct-library K cannot expand a rate box to the whole hard interval."""
    _, taxonomy, _ = make_recourse_fixture()
    with pytest.raises(ValueError, match="positive integer"):
        allowed_interval(0.0, taxonomy.actuator_constraints["actuator"], horizon_steps=horizon)
    with pytest.raises(ValueError, match="positive integer"):
        check_rate_violations({"actuator": 0.0}, {"actuator": 1.0}, taxonomy, horizon_steps=horizon)


@pytest.mark.parametrize("regime", [0.9, float("nan"), float("inf"), False])
def test_regime_ids_cannot_be_fractional_or_boolean(regime: float) -> None:
    """An explicit regime label must identify the actual fitted regime without truncation."""
    bundle, _, training = make_recourse_fixture()
    validator = fit_mahalanobis_validator(
        training, bundle, bundle.training_engine_ids, load_config(Path("configs/default.yaml"))
    )
    with pytest.raises(ValueError, match="regime"):
        validator.distance_batch(np.zeros((1, 2)), regime_ids=np.asarray([regime]))
