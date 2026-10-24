"""Loaded learned relationships must be complete before runtime evaluation."""

from copy import deepcopy
from pathlib import Path

import joblib
import pandas as pd
import pytest

from prescriptxai.constraints.coupling import SensorCouplingModel
from unit.test_coupling_reference import coupling_data  # noqa: F401


@pytest.mark.parametrize("fault", ["models", "torch_models", "residual_std", "sigma", "empty"])
def test_missing_or_invalid_coupling_models_fail_at_load(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],  # noqa: F811
    tmp_path: Path,
    fault: str,
) -> None:
    """A missing dependent model produces a typed failure instead of a request-time KeyError."""
    coupling = deepcopy(coupling_data[0])
    name = coupling.dependent_features[0]
    if fault == "sigma":
        coupling.residual_sigma_k = float("nan")
    elif fault == "empty":
        coupling.dependent_features = ()
    else:
        getattr(coupling, fault).pop(name)
    path = tmp_path / "coupling.joblib"
    joblib.dump(coupling, path)
    with pytest.raises(ValueError, match="coupling"):
        SensorCouplingModel.load(path)
