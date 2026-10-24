"""Pure chart/export checks use live computed fixture results rather than performance literals."""

import json
from io import StringIO
from pathlib import Path

import pandas as pd
import pytest

from fixtures.operator_artifacts import write_operator_fixture
from integration.test_phase8_backend import preview_service  # noqa: F401
from prescriptxai.dashboard.backend import contribution_data, profile_identity
from prescriptxai.dashboard.plots import (
    calibration_chart,
    comparison_chart,
    evidence_bars,
    history_chart,
    mahalanobis_gauge,
    risk_gauge,
    waterfall_chart,
)
from prescriptxai.dashboard.presentation import (
    action_table,
    printable_summary,
    result_csv,
    scaled_comparison,
)
from prescriptxai.dashboard.state import load_settings
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import InputContext


def test_charts_have_actual_values_and_thresholds() -> None:
    """Figures preserve supplied probabilities, thresholds, additive deltas and labels."""
    gauge = risk_gauge(0.4, 0.8, 0.2)
    assert gauge.data[0].value == 0.4 and gauge.data[0].gauge.threshold.value == 0.8
    history = history_chart(pd.DataFrame({"cycle": [1, 2], "risk": [0.3, 0.7]}), 0.8, 0.2)
    assert list(history.data[0].y) == [0.3, 0.7]
    assert [shape.y0 for shape in history.layout.shapes] == [0.8, 0.2]
    assert "Observed risk" in history.layout.title.text
    waterfall = waterfall_chart(["a", "b"], [-0.3, -0.4], 0.9, 0.2, "sequential")
    assert list(waterfall.data[0].measure) == ["absolute", "relative", "relative", "total"]
    assert sum(waterfall.data[0].y[:-1]) == pytest.approx(0.2)
    dm = mahalanobis_gauge(6, 5)
    assert dm.data[0].value == 6 and dm.data[0].gauge.threshold.value == 5
    curve = calibration_chart([{"mean_probability": 0.4, "fraction_positive": 0.5}])
    assert list(curve.data[1].y) == [0.5]


def test_charts_keep_empty_and_locked_data_explicit() -> None:
    """Empty evidence does not create fake observations and locked features are visible."""
    assert not history_chart(pd.DataFrame(), 0.8, 0.2).data
    assert not mahalanobis_gauge(None, None).data
    assert not comparison_chart(pd.DataFrame()).data
    assert len(calibration_chart([]).data) == 1  # Ideal reference only, no measured bins.
    assert list(evidence_bars([], [], "Unavailable").data[0].y) == []
    frame = pd.DataFrame([{"feature": "frozen", "locked": True, "before": 0, "after": 0}])
    assert comparison_chart(frame).data[0].x[0] == "frozen [LOCKED]"


def test_tables_scaled_units_and_safe_exports(preview_service: PrescriptXAI) -> None:  # noqa: F811
    """Every export preserves real status/risk/evidence/provenance, including rejected actions."""
    result = preview_service.recommend({"actuator": -2.0, "sensor": 2.0})
    info = preview_service.info()
    table = action_table(result, info)
    assert len(table) <= preview_service.config.recourse.k_max
    assert table.iloc[0].raw_change == result.delta_per_feature["actuator"].raw_delta
    scaled = scaled_comparison(result, info)
    assert scaled.loc[scaled.feature == "actuator", "after"].iloc[0] - scaled.loc[
        scaled.feature == "actuator", "before"
    ].iloc[0] == pytest.approx(table.iloc[0].scaled_change)
    rejected = preview_service.validate_controls(result.original_state, {"actuator": 100})
    csv = pd.read_csv(StringIO(result_csv(rejected, info)))
    assert csv.iloc[0].status == "ESCALATE" and csv.iloc[0].candidate_kind == "diagnostic"
    assert csv.iloc[0].config_hash == rejected.config_hash
    assert csv.iloc[0].risk_after == pytest.approx(rejected.risk_after)
    info["feature_metadata"]["actuator"]["label"] = "<script>alert('x')</script>"
    page = printable_summary(rejected, info)
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "Closest diagnostic candidate" in page and rejected.config_hash in page
    unchanged = preview_service.recommend({"actuator": 2.0, "sensor": 2.0})
    assert action_table(unchanged, info).empty
    assert pd.read_csv(StringIO(result_csv(unchanged, info))).iloc[0].status == "NO_INTERVENTION"


def test_contributions_reproduce_actual_candidate_and_conserve_risk(tmp_path: Path) -> None:
    """Real fitted-model subset revalidation conserves risk under both attribution methods."""
    settings = load_settings(write_operator_fixture(tmp_path))
    path = next(iter(settings.profiles["FD001"].values()))
    service = PrescriptXAI.from_config(path)
    state = {"actuator": -2.0, "sensor": 2.0}
    result = service.recommend(state)
    values = contribution_data(
        str(path),
        profile_identity(path),
        settings.model_dump_json(),
        json.dumps(state),
        InputContext().model_dump_json(),
        json.dumps({n: result.new_state[n] for n in result.action_features}),
        "fast",
    )
    assert values["before"] == result.risk_before
    assert values["after"] == result.risk_after
    assert sum(values["sequential"]) == pytest.approx(result.risk_after - result.risk_before)
    assert sum(values["averaged"]) == pytest.approx(sum(values["sequential"]))
    assert values["evaluations"] == 2 ** len(result.action_features)
