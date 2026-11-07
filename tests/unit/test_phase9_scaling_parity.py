"""Exact scaling parity against the installed library on measured hot-path inputs."""

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from prescriptxai.data.preprocess import FittedFeatureScaler


@pytest.mark.parametrize(
    "with_mean,with_std", [(True, True), (False, True), (True, False), (False, False)]
)
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
@pytest.mark.parametrize("order", ["C", "F"])
def test_scaler_fast_path_is_bitwise_equal_to_standard_scaler(
    with_mean: bool,
    with_std: bool,
    dtype: type,
    order: str,
) -> None:
    """Preserve subtraction/division order, constants, optional flags and input ownership."""
    rng = np.random.default_rng(17)
    training = rng.normal(size=(80, 4)) * np.asarray([1e-8, 1.0, 1e5, 0.0])
    training += np.asarray([1e-4, 30.0, 1e6, 2.0])
    scaler = StandardScaler(with_mean=with_mean, with_std=with_std).fit(training)
    names = tuple(f"sensor_{index}" for index in range(4))
    fitted = FittedFeatureScaler(names, (1, 2, 3, 4), scaler)
    raw = pd.DataFrame(np.array(training, dtype=dtype, order=order), columns=names)
    before = raw.copy(deep=True)
    actual = fitted.transform(raw)
    expected = scaler.transform(raw.to_numpy(dtype=float))
    np.testing.assert_array_equal(actual, expected, strict=True)
    assert actual.strides == expected.strides
    pd.testing.assert_frame_equal(raw, before)
    assert not np.shares_memory(actual, raw.to_numpy())
    np.testing.assert_allclose(scaler.inverse_transform(actual), raw, atol=1e-9, rtol=1e-12)


@pytest.mark.parametrize("width", [18, 24])
@pytest.mark.parametrize("order", ["C", "F"])
def test_two_row_scaling_preserves_tensor_reduction_layout(width: int, order: str) -> None:
    """Before/after batches preserve the library's layout and float32 inference arithmetic."""
    import torch

    rng = np.random.default_rng(1729)
    training = rng.normal(size=(80, width))
    scaler = StandardScaler().fit(training)
    names = tuple(f"feature_{index}" for index in range(width))
    raw = pd.DataFrame(np.array(training[:2], order=order), columns=names)
    fitted = FittedFeatureScaler(names, (1, 2), scaler)
    expected = scaler.transform(raw.to_numpy(dtype=float))
    actual = fitted.transform(raw)
    np.testing.assert_array_equal(actual, expected, strict=True)
    assert actual.strides == expected.strides
    expected_tensor = torch.as_tensor(expected).float()
    actual_tensor = torch.as_tensor(actual).float()
    assert actual_tensor.stride() == expected_tensor.stride()
    weights = torch.as_tensor(rng.normal(size=(width, 17)), dtype=torch.float32)
    torch.testing.assert_close(actual_tensor @ weights, expected_tensor @ weights, rtol=0, atol=0)


def test_scaler_rejects_unfitted_and_incompatible_widths() -> None:
    """Avoid replacing the library's fitted/shape checks with permissive arithmetic."""
    raw = pd.DataFrame({"sensor": [1.0, 2.0]})
    for scaler in (StandardScaler(), StandardScaler().fit(np.ones((2, 2)))):
        with pytest.raises(ValueError):
            FittedFeatureScaler(("sensor",), (1,), scaler).transform(raw)
