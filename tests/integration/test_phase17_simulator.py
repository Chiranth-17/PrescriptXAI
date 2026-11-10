"""Exercise the simulator against retained telemetry and fitted FD001 artifacts."""

from __future__ import annotations

import json
import sys
from concurrent.futures import CancelledError, ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path
from threading import Event
from typing import Any

import pandas as pd
import pytest
import yaml
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from typer.testing import CliRunner

from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import DEFAULT_MACHINE, MachineRegistry
from prescriptxai.api import create_app
from prescriptxai.cli import app
from prescriptxai.config import load_config
from prescriptxai.core.data_quality import RecommendationWithheld
from prescriptxai.core.decision import MachineDecision, action_adherence, simulated_settings
from prescriptxai.dashboard.objectives import METRICS
from prescriptxai.dashboard.prescription_job import PrescriptionJob
from prescriptxai.dashboard.scenario_report import (
    _followup_section,
    _prescription_section,
    scenario_report,
)
from prescriptxai.dashboard.simulator_data import (
    observed_rows,
    parse_settings,
    replay_trend,
    sequential_risks,
    simulator_decision,
)
from prescriptxai.dashboard.state import load_settings
from prescriptxai.machine_schema import MachineRecourseResult, ReplayFollowUp
from prescriptxai.machine_spec import DEMONSTRATION_LIMITS_LABEL, MachineSpec
from prescriptxai.machines import record_feedback_batch, scope_archive_runtime
from prescriptxai.pipeline import InputError, PrescriptXAI
from prescriptxai.scenarios import scenario_presets


def _app_test() -> AppTest:
    return AppTest.from_string(
        "from prescriptxai.dashboard.simulator_app import main\nmain()", default_timeout=45
    )


@pytest.fixture(autouse=True)
def restore_test_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Restore pytest's entrypoint after Streamlit runs its temporary main module."""
    monkeypatch.setitem(sys.modules, "__main__", sys.modules["__main__"])


@pytest.fixture(scope="module")
def replay() -> tuple[MachineDecision, PrescriptXAI, pd.DataFrame]:
    """Use the original fitted snapshot profile and genuine archive rows."""
    registry = MachineRegistry()
    adapter = registry.open(DEFAULT_MACHINE)
    assert isinstance(adapter, CmapssAdapter)
    rows = adapter.load_official()
    runtime = PrescriptXAI.from_config(Path("configs/experiments/phase7-FD001-xgb-v1.yaml"))
    return scope_archive_runtime(adapter.spec, "v1", runtime), runtime, rows


@pytest.fixture
def alerts_spec(monkeypatch: pytest.MonkeyPatch) -> MachineSpec:
    """Expose the same real archive under an isolated, unclassified spec."""
    current = MachineRegistry.get
    spec = MachineSpec.model_validate(
        {**MachineRegistry().get(DEFAULT_MACHINE).model_dump(), "limits_status": None}
    )

    def get(registry: MachineRegistry, machine_id: str) -> MachineSpec:
        return spec if machine_id == DEFAULT_MACHINE else current(registry, machine_id)

    monkeypatch.setattr(MachineRegistry, "get", get)
    return spec


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


def test_simulation_http_rejects_stale_and_scores_demonstration(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """The scoped HTTP route binds risk and demonstration prescriptions to the request."""
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
    response = client.post(
        "/simulate/prescribe", json={**request, "input_hash": expected.input_hash}
    )
    assert response.status_code == 200, response.text
    assert DEMONSTRATION_LIMITS_LABEL in response.json()["decision"]["warnings"]
    invalid = client.post("/simulate/risk", json={**request, "controls": {"unknown": True}})
    assert invalid.status_code == 422


def test_simulator_view_and_url_restore(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Drive the installed dashboard with real observations and restore a simulated edit."""
    decision, _, rows = replay
    page = _app_test().run()
    assert not page.exception and not page.error
    assert [widget.value for widget in page.subheader] == [
        "1. Set the conditions",
        "2. Predicted risk",
        "3. Prescription",
        "4. Was it followed?",
    ]
    assert any(DEMONSTRATION_LIMITS_LABEL in widget.value for widget in page.markdown)
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
    restored = _app_test()
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


def test_presets_and_advanced_navigation(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Verify every saved preset against the real model and keep Advanced observational."""
    decision, _, rows = replay
    page = _app_test().run()
    presets = scenario_presets(MachineRegistry(), DEFAULT_MACHINE, "test", decision.spec.spec_hash)
    assert len(presets) == 4
    for preset in presets:
        next(button for button in page.button if button.label == preset.name).click()
        page.run()
        assert not page.exception and not page.error
        assert page.query_params["unit"] == preset.unit
        assert float(page.query_params["time"]) == preset.time
        window = _window(rows, preset.unit, str(preset.time))
        score = decision.simulate_risk(window, {}).assessment.risk
        assert page.metric[0].value == f"{score:.1%}"
        assert len(page.metric) == 1
        assert any(DEMONSTRATION_LIMITS_LABEL in widget.value for widget in page.markdown)
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
    page = _app_test()
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
    alerts_spec: MachineSpec,
) -> None:
    """Cancel queued work, discard a running response, and preserve real publication policy."""
    _, runtime, rows = replay
    decision = scope_archive_runtime(alerts_spec, "v1", runtime)
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


@pytest.fixture(scope="module")
def case_evidence(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load the registered archived case and its original observation window."""
    decision, _, rows = replay
    case = scenario_presets(MachineRegistry(), DEFAULT_MACHINE, "test", decision.spec.spec_hash)[0]
    source = load_settings(Path("configs/dashboard.yaml")).report_directory / "records.jsonl"
    with source.open(encoding="utf-8") as file:
        saved = next(json.loads(line) for line in file if case.case_id in line)
    return _window(rows, case.unit, str(case.time)), saved


def test_waterfall_replays_saved_case_with_real_predictor(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
    case_evidence: tuple[pd.DataFrame, dict[str, Any]],
) -> None:
    """Recompute attribution for a historical candidate without publishing it as advice."""
    decision, _, _ = replay
    window, saved = case_evidence
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


def test_scenario_report_labels_demonstration_and_escapes_content(
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
    assert DEMONSTRATION_LIMITS_LABEL in html
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


def test_followup_labels_and_reproducible_demo_settings() -> None:
    """Check configured boundaries and verify demos stay within the interpolation endpoints."""
    config = load_settings(Path("configs/dashboard.yaml")).follow_up
    assert config.adherence_label(config.followed_at) == "Followed as recommended"
    assert config.adherence_label(config.partial_at) == "Followed partly"
    assert config.adherence_label(config.partial_at - 0.01) == "Not followed"
    assert config.adherence_label(config.followed_at - 0.01) == "Followed partly"
    original, recommendation = {"a": 10.0, "b": 20.0}, {"a": 8.0, "b": 24.0}
    assert action_adherence(original, recommendation, recommendation) == {"a": 1.0, "b": 1.0}
    assert action_adherence(original, recommendation, {"a": 12.0, "b": 16.0}) == {
        "a": 0.0,
        "b": 0.0,
    }
    assert action_adherence(original, recommendation, {"a": 9.0, "b": 22.0}) == {
        "a": 0.5,
        "b": 0.5,
    }
    demo = simulated_settings(original, recommendation, config.demo_seed, config.demo_count)
    assert demo == simulated_settings(original, recommendation, config.demo_seed, config.demo_count)
    assert demo != simulated_settings(
        original, recommendation, config.demo_seed + 1, config.demo_count
    )
    for applied in demo:
        assert 8.0 <= applied["a"] <= 10.0 and 20.0 <= applied["b"] <= 24.0
        values = action_adherence(original, recommendation, applied)
        assert values["a"] == pytest.approx(values["b"])


def test_followup_trend_uses_only_actual_later_windows(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """Check later same-unit timestamps, archived labels and genuine recalibrated risks."""
    decision, _, rows = replay
    unit = str(rows["unit_id"].iloc[0])
    track = rows.loc[rows["unit_id"].map(str) == unit].sort_values("time_index")
    start = float(track["time_index"].iloc[0])
    control, (lower, _) = next(iter(decision.control_bounds().items()))
    applied = {control: lower}
    trend = replay_trend(decision, rows, unit, start, applied, 3)
    expected = track.iloc[1:4]
    assert trend["Recorded time"].tolist() == expected["time_index"].tolist()
    assert trend["Recorded remaining life"].tolist() == expected["remaining_life"].tolist()
    for row in trend.to_dict(orient="records"):
        window = _window(rows, unit, str(row["Recorded time"]))
        before = decision.simulate_risk(window, {}).assessment
        after = decision.simulate_risk(window, applied).assessment
        assert row["Recorded settings (model prediction)"] == before.risk
        assert row["Applied settings (model prediction)"] == after.risk
        assert row["Safe level"] == before.tau_safe
        assert row["Alert level"] == before.tau_danger
    assert replay_trend(decision, rows, unit, float(track["time_index"].max()), applied, 30).empty
    assert not decision.spec.confirmation.confirmed


def test_feedback_cli_aliases_preserve_alerts_only(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
    tmp_path: Path,
    alerts_spec: MachineSpec,
) -> None:
    """Exercise both add spellings and the demo command without bypassing confirmation."""
    _, runtime, rows = replay
    decision = scope_archive_runtime(alerts_spec, "v1", runtime)
    window = next(
        candidate
        for index in range(min(len(rows), 30))
        if not decision.assess(candidate := rows.iloc[index : index + 1], "fast").alert
    )
    state, context = decision._observed(window)
    actual = decision._runtime.recommend(state, context, "fast")
    assert not actual.alert
    scoped = MachineRecourseResult.from_decision(
        actual,
        machine_id=decision.spec.machine_id,
        spec_hash=decision.spec.spec_hash,
        protocol_version=decision.protocol_version,
        synthetic=decision.spec.synthetic,
    )
    window_path = tmp_path / "window.json"
    result_path = tmp_path / "result.json"
    applied_path = tmp_path / "applied.json"
    log_path = tmp_path / "feedback.sqlite3"
    window_path.write_text(window.to_json(orient="records", double_precision=15), encoding="utf-8")
    result_path.write_text(scoped.model_dump_json(), encoding="utf-8")
    applied_path.write_text("{}", encoding="utf-8")
    common = [
        "--result",
        str(result_path),
        "--log",
        str(log_path),
        "--config",
        "configs/experiments/phase7-FD001-xgb-v1.yaml",
    ]
    runner = CliRunner()
    for form in (
        [str(window_path), "--applied", str(applied_path)],
        ["add", str(window_path), "--applied", str(applied_path)],
        ["simulate", str(window_path), "--seed", "42", "--count", "2"],
    ):
        result = runner.invoke(app, ["--machine", DEFAULT_MACHINE, "feedback", *form, *common])
        assert result.exit_code != 0
        assert "Recommendation withheld: Alerts only" in result.output
        assert "confirmed by an engineer" in result.output
        assert not log_path.exists()


def test_archived_result_panels_render_actual_checks_and_feedback(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
    case_evidence: tuple[pd.DataFrame, dict[str, Any]],
    tmp_path: Path,
    alerts_spec: MachineSpec,
) -> None:
    """Exercise display components against rechecked evidence without confirming the machine."""
    decision, _, rows = replay
    window, saved = case_evidence
    controls = {
        name: saved["candidate"][name]
        for name in saved["changed_features"]
        if name in decision.control_bounds()
    }
    state, context = decision._observed(window)
    result = decision._scoped(decision._runtime.validate_controls(state, controls, context, "fast"))
    assert result.status == "RECOVERABLE" and result.joint
    assert result.risk_after == pytest.approx(saved["risk_after"], abs=1e-9, rel=0)
    applied = {name: (state[name] + result.new_state[name]) / 2 for name in result.action_features}
    demo = decision._measure_feedback(window, result, applied, "simulated_operator")
    scope = ReplayFollowUp(
        input_hash=decision.input_hash(window, {}),
        unit=str(window["unit_id"].iloc[-1]),
        time=float(window["time_index"].iloc[-1]),
        risk_before=result.risk_before,
        prescription_risk=result.risk_after,
        config_hash=result.config_hash,
        demo_seed=1729,
    )
    log = tmp_path / "feedback.sqlite3"
    record_feedback_batch([(demo, scope)], log)
    features = {feature.id: feature for feature in decision.spec.measurement_features}
    assert f"{result.risk_after:.1%}" in _prescription_section(features, result)
    reason = "<check settings>"
    noted = scope.model_copy(update={"reason": reason, "stated_choice": "Not followed"})
    html = _followup_section(features, demo, noted)
    assert "Simulated operator (demo)" in html and "&lt;check settings&gt;" in html
    preview = decision.simulate_risk(window, {})
    withheld = scenario_report(
        decision.spec, scope.unit, scope.time, {}, preview, result, (demo, noted)
    )
    assert DEMONSTRATION_LIMITS_LABEL in withheld
    assert "Predicted risk with prescription" in withheld
    assert "&lt;check settings&gt;" in withheld
    blocked_html = scenario_report(
        alerts_spec, scope.unit, scope.time, {}, preview, result, (demo, noted)
    )
    assert "Alerts only" in blocked_html and reason not in blocked_html
    assert "Predicted risk with prescription" not in blocked_html
    settings = load_settings(Path("configs/dashboard.yaml"))
    renderer = AppTest.from_string(
        """
import streamlit as st
from prescriptxai.dashboard.simulator_followup import (
    _applied_inputs, _feedback_log, _render_applied, _trend_panel, render_follow_up,
)
from prescriptxai.dashboard.simulator_prescription import _render_measured_result
d, w, rows, r, e, f, scope, settings, log = st.session_state["evidence"]
st.caption("Archived evidence only")
_render_measured_result(d, w, r, e, settings.report_directory)
labels = {feature.id: feature.label for feature in d.spec.measurement_features}
_render_applied(f, r, labels, settings.follow_up)
_applied_inputs(d, r, labels)
assert render_follow_up(st.session_state["alerts"], w, rows, r, scope, settings.follow_up) is None
_trend_panel(d, rows, scope, f, 3)
_trend_panel(d, w, scope, f, 3)
_trend_panel(d, rows.drop(columns=d.features[0]), scope, f, 3)
_feedback_log(d, settings.follow_up, log)
""",
        default_timeout=45,
    )
    renderer.session_state["alerts"] = scope_archive_runtime(alerts_spec, "v1", replay[1])
    renderer.session_state["evidence"] = (
        decision,
        window,
        rows,
        result,
        decision._explanation(result),
        demo,
        scope,
        settings,
        log,
    )
    renderer.run()
    assert not renderer.exception
    assert len(renderer.get("plotly_chart")) == 2
    assert renderer.metric[0].value == f"{result.risk_after:.1%}"
    assert renderer.metric[-1].value == f"{demo.applied_risk:.1%}"
    assert any("No follow-ups" in item.value for item in renderer.info)
    assert any("no later recorded observations" in item.value for item in renderer.info)
    assert any("could not be checked" in item.value for item in renderer.info)
    renderer.checkbox[0].set_value(True).run()
    assert not renderer.exception
    assert renderer.dataframe[-1].value.iloc[0]["Source"] == "Simulated operator (demo)"
    renderer.radio[0].set_value("Not followed").run()
    assert not renderer.exception
    assert renderer.text_input[0].label == "Reason (optional)"
    assert renderer.slider[0].value == state[result.action_features[0]]
    assert not any(button.label == "Record this follow-up" for button in renderer.button)
    damaged = window.drop(columns=decision.features[0])
    missing_summary = settings.model_copy(update={"report_directory": tmp_path})
    renderer.session_state["evidence"] = (
        decision,
        damaged,
        rows,
        result,
        decision._explanation(result),
        demo,
        scope,
        missing_summary,
        log,
    )
    renderer.run()
    assert not renderer.exception
    assert len(renderer.get("plotly_chart")) == 1
    assert any("could not be reconciled" in item.value for item in renderer.warning)
    assert any("Target unavailable" in item.value for item in renderer.markdown)
    assert not decision.spec.confirmation.confirmed
    client = TestClient(create_app(replay[1], machine_artifacts=tmp_path / "api"))
    blocked = client.post(
        "/feedback",
        json={
            "machine_id": DEFAULT_MACHINE,
            "rows": window.to_dict(orient="records"),
            "result": result.model_dump(mode="json"),
            "applied": applied,
        },
    )
    assert blocked.status_code == 422 and "Alerts only" in blocked.json()["detail"]
    assert not (tmp_path / "api" / "feedback.sqlite3").exists()


def test_simulator_rejects_unknown_controls_before_showing_a_score(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
) -> None:
    """An edited share link cannot add settings outside the declared controls."""
    decision, _, rows = replay
    unit = str(rows["unit_id"].iloc[0])
    time = str(float(rows["time_index"].iloc[0]))
    page = _app_test()
    page.query_params.update(
        {
            "machine": DEFAULT_MACHINE,
            "spec": decision.spec.spec_hash,
            "unit": unit,
            "time": time,
            "settings": '{"unknown":1}',
        }
    )
    page.run()
    assert not page.exception and not page.metric
    assert any("Recommendation withheld" in item.value for item in page.error)


def test_cli_regenerates_registered_presets_and_input_bound_previews(tmp_path: Path) -> None:
    """Regenerate the complete registered selection and risk-only cache without replacing it."""
    target, cache = tmp_path / "scenarios.yaml", tmp_path / "preview.json"
    args = [
        "--machine",
        DEFAULT_MACHINE,
        "scenarios",
        "generate",
        "--output",
        str(target),
        "--preview-cache",
        str(cache),
        "--profile",
        "configs/experiments/phase7-FD001-xgb-v1.yaml",
    ]
    runner = CliRunner()
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    regenerated = yaml.safe_load(target.read_text(encoding="utf-8"))
    original = yaml.safe_load(
        (Path("configs/machines") / DEFAULT_MACHINE / "scenarios.yaml").read_text(encoding="utf-8")
    )
    for name in ("scenarios", "selection_config_sha256", "saved_results_sha256"):
        assert regenerated[name] == original[name]
    previews = json.loads(cache.read_text(encoding="utf-8"))["previews"]
    assert [row["case_id"] for row in previews] == [row["case_id"] for row in original["scenarios"]]
    assert all(set(row["preview"]) == {"input_hash", "unusual", "assessment"} for row in previews)
    assert all(len(row["preview"]["input_hash"]) == 64 for row in previews)
    original_bytes = target.read_bytes()
    refused = runner.invoke(app, args)
    assert refused.exit_code != 0 and "scenario output already exists" in refused.output
    assert target.read_bytes() == original_bytes


def test_replay_routes_fail_closed_on_invalid_inputs_and_local_evidence(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
    tmp_path: Path,
) -> None:
    """Verify public validation paths without loading untrusted inputs as live evidence."""
    decision, runtime, rows = replay
    local_registry = MachineRegistry(tmp_path / "machines")
    path = local_registry.root / DEFAULT_MACHINE / "scenarios.yaml"
    path.parent.mkdir(parents=True)
    config = runtime.config.model_copy(deep=True)
    config.pipeline.max_batch_rows = 1
    with TestClient(
        create_app(runtime, config, registry=local_registry, machine_artifacts=tmp_path)
    ) as client:
        assert client.get("/machines/unknown/scenarios").status_code == 404
        assert client.get("/machines/UPPER/spec").status_code == 422
        route = f"/machines/{DEFAULT_MACHINE}/scenarios"
        assert client.get(route).json() == []
        path.write_text("machine_id: other_machine", encoding="utf-8")
        assert client.get(route).status_code == 422
        path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "machine_id": DEFAULT_MACHINE,
                    "spec_hash": decision.spec.spec_hash,
                    "population": "test",
                }
            ),
            encoding="utf-8",
        )
        assert client.get(route).status_code == 422
        request = {"machine_id": DEFAULT_MACHINE, "rows": rows.iloc[:2].to_dict(orient="records")}
        oversized = client.post("/simulate/risk", json=request)
        assert oversized.status_code == 422 and "row limit" in oversized.json()["detail"]
        request["rows"] = [{"time_index": 1}]
        bad_window = client.post("/simulate/risk", json=request)
        assert (
            bad_window.status_code == 422
            and "Recommendation withheld" in bad_window.json()["detail"]
        )
        (tmp_path / "feedback.sqlite3").write_bytes(b"invalid SQLite")
        summary = client.get("/feedback/summary", params={"machine_id": DEFAULT_MACHINE})
        assert summary.status_code == 503 and "log unavailable" in summary.json()["detail"]
    with pytest.raises(ValueError, match="configuration changed"):
        observed_rows(DEFAULT_MACHINE, "0" * 64, "test", "test-stale-spec")
    isolated = simulator_decision(
        MachineRegistry(),
        DEFAULT_MACHINE,
        load_settings(Path("configs/dashboard.yaml")),
        isolated=True,
    )
    assert isolated is not decision
    window = rows.iloc[:1]
    assert isolated.simulate_risk(window, {}) == decision.simulate_risk(window, {})


def test_saved_objectives_distinguish_missing_evidence(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
    tmp_path: Path,
) -> None:
    """A missing report and an archive with no matching groups remain explicit."""
    decision, _, _ = replay
    panel = AppTest.from_string(
        """
import streamlit as st
from prescriptxai.dashboard.objectives import objectives_page
spec, directory = st.session_state["objective_scope"]
objectives_page(spec, directory)
"""
    )
    panel.session_state["objective_scope"] = (decision.spec, tmp_path)
    panel.run()
    assert not panel.exception and not panel.dataframe
    assert any("unavailable" in warning.value for warning in panel.warning)
    (tmp_path / "summary.json").write_text('{"groups":{}}', encoding="utf-8")
    panel.run()
    assert not panel.exception and not panel.dataframe
    assert any("No saved held-out" in message.value for message in panel.info)


def test_cli_archive_history_is_used_without_padding() -> None:
    """Exercise the retained LSTM through the supported recorded-engine CLI path."""
    profile = Path("configs/experiments/phase7-FD001-lstm-v1.yaml")
    service = PrescriptXAI.from_config(profile)
    config = load_config(profile)
    from prescriptxai.cli import _select_context, _select_state

    context = _select_context(None, 1, 100, service)
    assert context is not None and context.history is not None
    assert len(context.history) == service.engine.model.estimator.window - 1
    score = service.assess(_select_state(None, 1, 100, config), context)
    runner = CliRunner()
    base = ["assess", "--config", str(profile), "--engine-id", "1", "--cycle"]
    result = runner.invoke(app, [*base, "100"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["risk"] == score.risk
    missing = runner.invoke(app, [*base, "1"])
    assert (
        missing.exit_code != 0 and "LSTM requires" in missing.output and "padded" in missing.output
    )
    unknown = runner.invoke(app, [*base, "100000"])
    assert unknown.exit_code != 0 and "engine/cycle not found" in unknown.output


def test_cli_validates_existing_archive_without_download() -> None:
    """Exercise the archive preflight using the actual retained checksum and counts."""
    from prescriptxai.data.download import verify_archive

    profile = Path("configs/experiments/phase7-FD001-xgb-v1.yaml")
    config = load_config(profile)
    path = config.data.root / config.data.archive_name
    assert path.is_file()
    digest = verify_archive(path, config.data.dataset_sha256)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--machine",
            DEFAULT_MACHINE,
            "data",
            "download",
            "--config",
            str(profile),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Verified existing C-MAPSS archive" in result.stdout and digest in result.stdout


def test_unusual_replay_edits_warn_without_publishing_actions(
    replay: tuple[MachineDecision, PrescriptXAI, pd.DataFrame],
    case_evidence: tuple[pd.DataFrame, dict[str, Any]],
) -> None:
    """Extreme but bounded fitted controls keep the actual model risk visible with a warning."""
    decision, _, _ = replay
    window, _ = case_evidence
    bounds = decision.control_bounds()
    options = [
        {
            name: limits[(position + shift) % 2]
            for position, (name, limits) in enumerate(bounds.items())
        }
        for shift in range(2)
    ] + [{name: limits[1] for name, limits in bounds.items()}]
    controls, result = next(
        (values, preview)
        for values in options
        if (preview := decision.simulate_risk(window, values)).unusual
    )
    page = _app_test()
    page.query_params.update(
        {
            "machine": DEFAULT_MACHINE,
            "spec": decision.spec.spec_hash,
            "unit": str(window["unit_id"].iloc[-1]),
            "time": str(float(window["time_index"].iloc[-1])),
            "settings": json.dumps(controls),
        }
    )
    page.run()
    assert not page.exception and not page.error
    assert [metric.value for metric in page.metric] == [f"{result.assessment.risk:.1%}"]
    assert any("unusual" in warning.value for warning in page.warning)
    assert not any(button.label == "Record this follow-up" for button in page.button)
