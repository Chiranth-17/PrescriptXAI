"""Exercise the simulator against retained telemetry and fitted FD001 artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import DEFAULT_MACHINE, MachineRegistry
from prescriptxai.api import create_app
from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.simulator_data import parse_settings
from prescriptxai.machines import scope_archive_runtime
from prescriptxai.pipeline import InputError, PrescriptXAI

APP = Path("src/prescriptxai/dashboard/simulator_app.py").resolve()


@pytest.fixture(scope="module")
def replay() -> tuple[MachineDecision, PrescriptXAI, pd.DataFrame]:
    """Use the original fitted snapshot profile and genuine archive rows."""
    registry = MachineRegistry()
    adapter = registry.open(DEFAULT_MACHINE)
    assert isinstance(adapter, CmapssAdapter)
    rows = adapter.load_official()
    runtime = PrescriptXAI.from_config(Path("configs/experiments/phase7-FD001-xgb-v1.yaml"))
    return scope_archive_runtime(adapter.spec, "v1", runtime), runtime, rows


def _window(rows: pd.DataFrame, unit: str, time: str) -> pd.DataFrame:
    return rows.loc[(rows["unit_id"].map(str) == unit) & (rows["time_index"] <= float(time))]


def test_simulated_risk_is_authoritative_and_input_bound(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Check preview provenance, recorded parity, edit masking and precise hashing."""
    decision, _, rows = replay
    first_unit = str(rows["unit_id"].iloc[0])
    window = rows.loc[rows["unit_id"].map(str) == first_unit]
    recorded = decision.simulate_risk(window, {})
    assert recorded.assessment == decision.assess(window, "fast")
    assert recorded.input_hash == decision.input_hash(window, {})
    feature, (lower, upper) = next(iter(decision.control_bounds().items()))
    altered = decision.simulate_risk(window, {feature: lower})
    assert altered.input_hash != recorded.input_hash
    assert altered.assessment.machine_id == DEFAULT_MACHINE
    assert altered.assessment.synthetic
    with pytest.raises(InputError, match="slider bounds"):
        decision.simulate_risk(window, {feature: upper + 1})
    frozen = next(feature.id for feature in decision.spec.features if feature.role == "frozen")
    with pytest.raises(InputError, match="only configured controllable"):
        decision.simulate_risk(window, {frozen: lower})
    with pytest.raises(ValueError, match="missing_value"):
        decision.simulate_risk(window.drop(columns=feature), {})


def test_simulation_http_rejects_stale_and_withholds_unconfirmed(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """The scoped HTTP route gives risk without publishing unconfirmed actions."""
    decision, runtime, rows = replay
    client = TestClient(create_app(runtime))
    spec = client.get(f"/machines/{DEFAULT_MACHINE}/spec")
    assert spec.status_code == 200
    assert spec.json()["machine_id"] == DEFAULT_MACHINE
    assert client.get("/machines/absent/spec").status_code == 404
    scenarios = client.get(f"/machines/{DEFAULT_MACHINE}/scenarios")
    assert scenarios.status_code == 200
    assert len(scenarios.json()) == 4
    assert all(len(row["case_id"]) == 64 for row in scenarios.json())
    window = rows.iloc[:2]
    request = {
        "machine_id": DEFAULT_MACHINE,
        "rows": window.to_dict(orient="records"),
        "protocol_version": "v1",
    }
    risk = client.post("/simulate/risk", json=request)
    assert risk.status_code == 200, risk.text
    expected = decision.simulate_risk(window, {})
    assert risk.json() == expected.model_dump(mode="json")
    stale = client.post("/simulate/prescribe", json={**request, "input_hash": "0" * 64})
    assert stale.status_code == 409
    withheld = client.post(
        "/simulate/prescribe", json={**request, "input_hash": expected.input_hash}
    )
    assert withheld.status_code == 422
    assert "limits not yet confirmed by an engineer" in withheld.json()["detail"]
    invalid = client.post("/simulate/risk", json={**request, "controls": {"unknown": True}})
    assert invalid.status_code == 422


def test_simulator_view_and_url_restore(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Drive the installed dashboard with real observations and restore a simulated edit."""
    decision, _, rows = replay
    page = AppTest.from_file(str(APP), default_timeout=45).run()
    assert not page.exception and not page.error
    assert [widget.value for widget in page.subheader] == [
        "1. Set the conditions",
        "2. Predicted risk",
        "3. Prescription",
        "4. Was it followed?",
    ]
    assert any("limits not yet confirmed" in widget.value for widget in page.info)
    assert len(page.metric) == 1
    window = _window(rows, page.query_params["unit"], page.query_params["time"])
    labels = {feature.label: feature.id for feature in decision.spec.measurement_features}
    score = decision.simulate_risk(window, {}).assessment.risk
    for slider in page.slider:
        name = labels[slider.label.rsplit(" (", 1)[0]]
        lower, upper = decision.control_bounds()[name]
        assert (slider.min, slider.max) == (lower, upper)
        for candidate in (lower, upper):
            edited = decision.simulate_risk(window, {name: candidate}).assessment.risk
            if f"{edited:.1%}" != f"{score:.1%}":
                slider.set_value(candidate)
                break
        else:
            continue
        break
    else:
        pytest.fail("The recorded observation offers no visible change across its controls")
    page.run()
    assert not page.exception and not page.error
    assert page.metric[0].value == f"{edited:.1%}"
    assert json.loads(page.query_params["settings"]) == {name: candidate}
    restored = AppTest.from_file(str(APP), default_timeout=45)
    restored.query_params.update(page.query_params)
    restored.run()
    assert not restored.exception and restored.metric[0].value == page.metric[0].value
    next(button for button in page.button if button.label == "Reset settings").click()
    page.run()
    assert not page.exception and page.metric[0].value == f"{score:.1%}"
    assert json.loads(page.query_params["settings"]) == {}


@pytest.mark.parametrize("encoded", ["[]", '{"frozen":1}', '{"control":true}', '{"control":NaN}'])
def test_link_rejects_invalid_control_values(encoded: str) -> None:
    """Reject malformed, frozen, boolean and nonfinite URL control values."""
    with pytest.raises(ValueError):
        parse_settings(encoded, {"control": (0.0, 1.0)})


def test_presets_and_advanced_navigation() -> None:
    """Open a saved case study and keep the advanced workspace observational."""
    page = AppTest.from_file(str(APP), default_timeout=45).run()
    preset = next(
        button for button in page.button if button.label == "Case study (selected by rule)"
    )
    preset.click()
    page.run()
    assert not page.exception and not page.error
    assert page.query_params["unit"] == "82" and page.query_params["time"] == "156.0"
    page.sidebar.radio[0].set_value("Advanced")
    page.run()
    assert not page.exception
    assert "Operator Console" not in page.sidebar.radio[1].options
    page.sidebar.radio[1].set_value("About and Limitations")
    page.run()
    assert any("About" in header.value for header in page.header)
