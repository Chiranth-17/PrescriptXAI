"""Persisted calibrator arithmetic must not change an existing search silently."""

import pickle

import numpy as np
import pytest
import torch

from prescriptxai.models.calibration import ProbabilityCalibrator


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
@pytest.mark.parametrize("method", ["sigmoid", "temperature", "isotonic"])
def test_legacy_artifact_values_gradients_and_roundtrip(method: str, dtype: torch.dtype) -> None:
    """Version1 objects reproduce the historical tensor expression after deserialization."""
    calibrator = ProbabilityCalibrator(method).fit(
        np.array([0.0, 0.1, 0.4, 0.6, 0.9, 1.0]), np.array([0, 0, 0, 1, 1, 1])
    )
    calibrator.tensor_map_version = 1
    restored = pickle.loads(pickle.dumps(calibrator))
    values = torch.tensor([0.0, 1e-8, 0.13, 0.41, 0.83, 1.0], dtype=dtype, requires_grad=True)
    bounded = values.clamp(1e-7, 1 - 1e-7)
    if method == "sigmoid":
        expected = torch.sigmoid(calibrator.slope * torch.logit(bounded) + calibrator.intercept)
    elif method == "temperature":
        expected = torch.sigmoid(torch.logit(bounded) / calibrator.temperature)
    else:
        x = torch.tensor(calibrator.model.X_thresholds_, dtype=dtype)
        y = torch.tensor(calibrator.model.y_thresholds_, dtype=dtype)
        indices = torch.searchsorted(x, bounded).clamp(1, len(x) - 1)
        fraction = ((bounded - x[indices - 1]) / (x[indices] - x[indices - 1]).clamp_min(
            torch.finfo(dtype).eps
        )).clamp(0, 1)
        expected = y[indices - 1] + fraction * (y[indices] - y[indices - 1])
    actual = restored.transform_tensor(values)
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
    actual_gradient = torch.autograd.grad(actual.sum(), values, retain_graph=True)[0]
    expected_gradient = torch.autograd.grad(expected.sum(), values)[0]
    torch.testing.assert_close(actual_gradient, expected_gradient, rtol=0, atol=0)
    assert actual.dtype == dtype


@pytest.mark.parametrize("version", [None, 0, 3, True, "1"])
def test_unknown_arithmetic_version_is_rejected(version: object) -> None:
    """Unknown metadata cannot silently choose a different search map."""
    calibrator = ProbabilityCalibrator("temperature")
    calibrator.tensor_map_version = version
    with pytest.raises(ValueError, match="map version"):
        calibrator.transform_tensor(torch.tensor([0.5]))
    with pytest.raises(ValueError, match="map version"):
        calibrator.transform(np.array([0.5]))


@pytest.mark.parametrize("bad", [[float("nan")], [float("inf")], [-1.0], [2.0], [], [[0.5]]])
def test_version1_artifact_retains_hardened_input_validation(bad: list) -> None:
    """Legacy arithmetic does not bypass finite/range/shape guards."""
    calibrator = ProbabilityCalibrator("temperature")
    calibrator.tensor_map_version = 1
    with pytest.raises(ValueError, match="probabilit"):
        calibrator.transform_tensor(torch.tensor(bad, dtype=torch.float64))


def test_fitting_a_legacy_object_explicitly_versions_the_new_fit() -> None:
    """Newly fitted objects record current arithmetic even when reusing an old instance."""
    calibrator = ProbabilityCalibrator("temperature")
    calibrator.tensor_map_version = 1
    calibrator.fit(np.array([0.1, 0.9]), np.array([0, 1]))
    assert calibrator.tensor_map_version == 2
    assert pickle.loads(pickle.dumps(calibrator)).tensor_map_version == 2


@pytest.mark.parametrize("method", ["sigmoid", "temperature", "isotonic"])
def test_legacy_unfitted_map_is_rejected(method: str) -> None:
    """Missing fitted parameters cannot become a compatibility fallback."""
    calibrator = ProbabilityCalibrator(method)
    calibrator.tensor_map_version = 1
    with pytest.raises(ValueError, match="fitted"):
        calibrator.transform_tensor(torch.tensor([0.5]))


def test_legacy_constant_isotonic_has_finite_zero_gradient() -> None:
    """A flat single-knot map has its mathematical zero derivative."""
    calibrator = ProbabilityCalibrator("isotonic").fit(
        np.array([0.5, 0.5]), np.array([0, 1])
    )
    calibrator.tensor_map_version = 1
    values = torch.tensor([0.1, 0.9], requires_grad=True)
    calibrated = calibrator.transform_tensor(values)
    torch.testing.assert_close(calibrated, torch.tensor([0.5, 0.5]), atol=0, rtol=0)
    calibrated.sum().backward()
    torch.testing.assert_close(values.grad, torch.zeros(2), atol=0, rtol=0)


def test_ambiguous_standalone_map_preserves_current_arithmetic() -> None:
    """Missing metadata alone must not roll back a post-hardening saved object."""
    calibrator = ProbabilityCalibrator("temperature").fit(
        np.array([0.1, 0.9]), np.array([0, 1])
    )
    values = torch.tensor([0.0, 0.13, 1.0], requires_grad=True)
    expected = calibrator.transform_tensor(values)
    del calibrator.tensor_map_version
    restored = pickle.loads(pickle.dumps(calibrator))
    actual = restored.transform_tensor(values)
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
    assert actual.dtype == torch.float64
