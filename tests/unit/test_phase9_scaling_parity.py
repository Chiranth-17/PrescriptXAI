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
def test_scaler_fast_path_is_bitwise_equal_to_standard_scaler(
    with_mean: bool,
    with_std: bool,
    dtype: type,
) -> None:
    """Preserve subtraction/division order, constants, optional flags and input ownership."""
    rng = np.random.default_rng(17)
    training = rng.normal(size=(80, 4)) * np.asarray([1e-8, 1.0, 1e5, 0.0])
    training += np.asarray([1e-4, 30.0, 1e6, 2.0])
    scaler = StandardScaler(with_mean=with_mean, with_std=with_std).fit(training)
    names = tuple(f"sensor_{index}" for index in range(4))
    fitted = FittedFeatureScaler(names, (1, 2, 3, 4), scaler)
    raw = pd.DataFrame(training.astype(dtype), columns=names)
    before = raw.copy(deep=True)
    actual = fitted.transform(raw)
    expected = scaler.transform(raw.to_numpy(dtype=float))
    np.testing.assert_array_equal(actual, expected, strict=True)
    pd.testing.assert_frame_equal(raw, before)
    assert not np.shares_memory(actual, raw.to_numpy())
    np.testing.assert_allclose(scaler.inverse_transform(actual), raw, atol=1e-9, rtol=1e-12)


def test_scaler_rejects_unfitted_and_incompatible_widths() -> None:
    """Avoid replacing the library's fitted/shape checks with permissive arithmetic."""
    raw = pd.DataFrame({"sensor": [1.0, 2.0]})
    for scaler in (StandardScaler(), StandardScaler().fit(np.ones((2, 2)))):
        with pytest.raises(ValueError):
            FittedFeatureScaler(("sensor",), (1,), scaler).transform(raw)
