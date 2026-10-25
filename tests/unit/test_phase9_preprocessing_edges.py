"""Inverse scaling must reject ambiguous regimes and malformed measured columns."""

import numpy as np
import pandas as pd
import pytest

from fixtures.cmapss import make_cmapss_frame
from prescriptxai.data.preprocess import RegimeAwarePreprocessor


@pytest.fixture
def preprocessing() -> tuple[RegimeAwarePreprocessor, pd.DataFrame]:
    """Fit genuine train-only statistics and retain their measured raw rows."""
    frame = make_cmapss_frame(2, 10, 10)
    fitted = RegimeAwarePreprocessor.fit(frame, "FD001", 0, 1, 17)
    return fitted, frame


@pytest.mark.parametrize("regime", [0.5, False, np.nan, np.inf, None, "0", -1, 99])
def test_inverse_scaling_rejects_noninteger_unknown_or_boolean_regimes(
    preprocessing: tuple[RegimeAwarePreprocessor, pd.DataFrame],
    regime: object,
) -> None:
    """Truncating a regime would apply a different mean and scale without operator knowledge."""
    fitted, raw = preprocessing
    transformed = fitted.transform(raw).astype({"operating_regime": object})
    transformed.loc[:, "operating_regime"] = regime
    with pytest.raises(ValueError, match="regime"):
        fitted.inverse_transform(transformed)


def test_preprocessor_missing_empty_nonfinite_and_rolling_inputs_are_clear(
    preprocessing: tuple[RegimeAwarePreprocessor, pd.DataFrame],
) -> None:
    """Reach negative transforms without replacing fitted statistics or expected outputs."""
    fitted, raw = preprocessing
    transformed = fitted.transform(raw)
    scaled = f"{fitted.retained_sensor_names[0]}_scaled"
    for frame, message in (
        (transformed.iloc[:0], "empty"),
        (transformed.drop(columns="operating_regime"), "operating_regime"),
        (transformed.drop(columns=scaled), "missing scaled"),
        (transformed.assign(**{scaled: np.nan}), "finite"),
        (transformed.assign(**{scaled: np.inf}), "finite"),
    ):
        with pytest.raises(ValueError, match=message):
            fitted.inverse_transform(frame)
    for frame in (raw.iloc[:0], raw.drop(columns="s1"), raw.assign(s1=np.nan)):
        with pytest.raises(ValueError):
            fitted.transform(frame)
    fitted.rolling_features = True
    with pytest.raises(ValueError, match="rolling features require"):
        fitted.transform(raw.drop(columns="unit_id"))
