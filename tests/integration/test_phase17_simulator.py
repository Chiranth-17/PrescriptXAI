"""Exercise the simulator against retained telemetry and fitted FD001 artifacts."""

from __future__ import annotations

import json
from concurrent.futures import CancelledError, ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path
from threading import Event

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import DEFAULT_MACHINE, MachineRegistry
from prescriptxai.api import create_app
from prescriptxai.core.data_quality import RecommendationWithheld
from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.objectives import METRICS
from prescriptxai.dashboard.prescription_job import PrescriptionJob
from prescriptxai.dashboard.scenario_report import scenario_report
from prescriptxai.dashboard.simulator_data import parse_settings, sequential_risks
from prescriptxai.dashboard.state import load_settings
from prescriptxai.machine_schema import MachineRecourseResult
from prescriptxai.machines import scope_archive_runtime
from prescriptxai.pipeline import InputError, PrescriptXAI
from prescriptxai.scenarios import scenario_presets

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


def test_scorecard_numbers_come_from_saved_engine_intervals() -> None:
    """Compare each displayed measurement, target and interval with its saved source."""
    settings = load_settings(Path("configs/dashboard.yaml"))
    summary = json.loads((settings.report_directory / "summary.json").read_text(encoding="utf-8"))
    page = AppTest.from_file(str(APP), default_timeout=45)
    page.run()
    page.sidebar.radio[0].set_value("Advanced")
    page.run()
    page.sidebar.radio[1].set_value("Objectives scorecard")
    page.run()
    assert not page.exception and not page.error and not page.warning[1:]
    assert "Objectives scorecard" in [heading.value for heading in page.header]
    group = page.selectbox[0].value
    data = summary["groups"][group]
    populations = {
        "All alerts": {name: metric["ci"] for name, metric in data["metrics"].items()},
        "First alert": data["strata"]["first_alert_versus_all_same_mode"]["first_alert"],
    }
    targets = summary["manifest"]["configuration"]["targets"]
    metric_columns = {
        "Measured": "estimate",
        "CI lower": "lower",
        "CI upper": "upper",
        "Engines": "engine_count",
        "Denominator": "denominator",
    }
    labels = {label: name for name, label in METRICS.items()}
    table = page.dataframe[0].value
    assert set(table["Population"]) == populations.keys()
    assert len(table) == sum(len(values.keys() & METRICS.keys()) for values in populations.values())
    for row in table.to_dict(orient="records"):
        name = labels[row["Objective"]]
        ci = populations[row["Population"]][name]
        for column, key in metric_columns.items():
            assert row[column] == ci[key]
        if name in targets:
            assert row["Target"] == targets[name]
        else:
            assert pd.isna(row["Target"])
    stages_by_mode = summary["latency"]["modes"]
    for displayed, stages in zip(page.dataframe[1:], stages_by_mode.values(), strict=True):
        assert len(displayed.value) == len(stages)
        for row in displayed.value.to_dict(orient="records"):
            saved = stages[row["Stage"]]
            assert row["Upper budget (ms)"] == saved["upper_budget_ms"]
            assert row["Engines"] == saved["engine_count"]
            if saved["p95_ms"] is None:
                assert pd.isna(row["p95 (ms)"])
                assert row["Finding"] == "Unmeasured"
            else:
                assert row["p95 (ms)"] == saved["p95_ms"]
                assert row["CI lower"] == saved["p95_engine_ci"]["lower"]
                assert row["CI upper"] == saved["p95_engine_ci"]["upper"]


def test_prescription_jobs_discard_superseded_work(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Cancel queued work, discard a running response, and preserve real publication policy."""
    decision, _, rows = replay
    window = rows.iloc[:2]
    before = decision.input_hash(window, {})
    after = decision.input_hash(rows.iloc[:1], {})
    entered, release = Event(), Event()

    def check_policy(_: Event) -> MachineRecourseResult:
        entered.set()
        assert release.wait(5)
        return decision.recommend(window, "fast")

    with ThreadPoolExecutor(max_workers=1) as executor:
        running = PrescriptionJob.start(executor, before, check_policy)
        try:
            assert entered.wait(5)
            queued = PrescriptionJob.start(executor, before, check_policy)
            queued.cancel()
            running.cancel()
            current = PrescriptionJob.start(
                executor, after, lambda _: decision.recommend(rows.iloc[:1], "fast")
            )
        finally:
            release.set()
        assert current.input_hash != running.input_hash
        with pytest.raises(CancelledError):
            queued.future.result(timeout=5)
        with pytest.raises(CancelledError):
            running.future.result(timeout=5)
        with pytest.raises(RecommendationWithheld, match="limits not yet confirmed"):
            current.future.result(timeout=5)


def test_waterfall_replays_saved_case_with_real_predictor(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Recompute attribution for a historical candidate without publishing it as advice."""
    decision, _, rows = replay
    case = scenario_presets(MachineRegistry(), DEFAULT_MACHINE, "test", decision.spec.spec_hash)[0]
    source = load_settings(Path("configs/dashboard.yaml")).report_directory / "records.jsonl"
    with source.open(encoding="utf-8") as file:
        saved = next(json.loads(line) for line in file if case.case_id in line)
    window = _window(rows, case.unit, str(case.time))
    names = sorted(
        set(saved["changed_features"]) & decision.control_bounds().keys(),
        key=lambda name: (-abs(saved["candidate"][name] - saved["original"][name]), name),
    )
    controls = {name: saved["candidate"][name] for name in names}
    assert len(controls) >= 2
    risks = sequential_risks(decision, window, controls)
    assert len(risks) == len(controls) + 1
    assert risks[0] == pytest.approx(saved["risk_before"], abs=1e-9, rel=0)
    assert risks[-1] == pytest.approx(saved["risk_after"], abs=1e-9, rel=0)
    assert sum(before - after for before, after in pairwise(risks)) == pytest.approx(
        saved["risk_before"] - saved["risk_after"], abs=1e-9, rel=0
    )
    assert not decision.spec.confirmation.confirmed


def test_scenario_report_keeps_alerts_only_and_escapes_content(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Export actual selected risk, machine provenance and the withheld state offline."""
    decision, _, rows = replay
    window = rows.iloc[:2]
    control, (lower, _) = next(iter(decision.control_bounds().items()))
    edits = {control: lower}
    prediction = decision.simulate_risk(window, edits)
    html = scenario_report(decision.spec, "<script>", 2.0, edits, prediction, None, None)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "Alerts only: limits not yet confirmed by an engineer" in html
    assert f"Predicted risk now: {prediction.assessment.risk:.1%}" in html
    assert prediction.input_hash in html
    assert decision.spec.spec_hash in html
    assert prediction.assessment.config_hash in html
    assert "Synthetic or sample machine data" in html


def test_feedback_summary_scopes_an_empty_log(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
    tmp_path: Path,
) -> None:
    """Read scoped source groups without creating a database or requiring a fitted solve."""
    decision, runtime, _ = replay
    client = TestClient(create_app(runtime, machine_artifacts=tmp_path))
    query = {"machine_id": DEFAULT_MACHINE}
    default = client.get("/feedback/summary", params=query)
    assert default.status_code == 200
    body = default.json()
    assert body["spec_hash"] == decision.spec.spec_hash and body["synthetic"]
    assert body["groups"] == [
        {
            "source": "operator",
            "label": "Operator (this session)",
            "count": 0,
            "mean_adherence": None,
        }
    ]
    opt_in = client.get("/feedback/summary", params={**query, "include_simulated": "true"})
    assert opt_in.json()["groups"][-1]["label"] == "Simulated operator (demo)"
    assert (
        client.get("/feedback/summary", params={**query, "protocol_version": "bad"}).status_code
        == 422
    )
    assert client.get("/feedback/summary", params={"machine_id": "unregistered"}).status_code == 404
    assert not (tmp_path / "feedback.sqlite3").exists()
