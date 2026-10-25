"""Fitting identity decoding is strict before any set comparison or integer cast."""

import numpy as np
import pytest

from prescriptxai.artifacts import ArtifactLoadError, validate_engine_ids


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        "1",
        [True],
        [np.bool_(True)],
        [1.5],
        [0],
        [-1],
        [np.inf],
        [np.nan],
        [1, 1],
        ["1"],
        [10**1000],
        [1 + 2j],
    ],
)
def test_invalid_declared_fitting_ids_are_typed(value: object) -> None:
    """Invalid identities cannot masquerade as known fitting engines through numeric coercion."""
    with pytest.raises(ArtifactLoadError, match="invalid engine IDs"):
        validate_engine_ids(value)


def test_numpy_integral_fitting_ids_keep_exact_order_independent_identity() -> None:
    """Legitimate NumPy engine provenance is supported without dropping duplicate evidence."""
    assert validate_engine_ids([np.int64(3), np.float64(1), 2]) == (1, 2, 3)
