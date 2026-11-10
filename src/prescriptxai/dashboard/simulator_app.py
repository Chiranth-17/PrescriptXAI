"""Operator-facing Streamlit simulator for a selected observed machine trajectory."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from concurrent.futures import CancelledError
from math import isclose
from pathlib import Path
from threading import Event
from time import perf_counter
from typing import cast
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.core.data_quality import RecommendationWithheld
from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.app import main as advanced_pages
from prescriptxai.dashboard.backend import computation_pool
from prescriptxai.dashboard.data import file_identity
from prescriptxai.dashboard.prescription_job import PrescriptionJob
from prescriptxai.dashboard.scenario_report import scenario_report
from prescriptxai.dashboard.simulator_data import (
    SimulatorRegistry,
    observed_rows,
    parse_settings,
    simulator_decision,
    simulator_settings,
)
from prescriptxai.dashboard.simulator_followup import render_follow_up
from prescriptxai.dashboard.simulator_prescription import (
    prescription_checks,
    render_recommendation,
)
from prescriptxai.dashboard.state import DashboardSettings
from prescriptxai.machine_schema import MachineRecourseResult, ReplayFollowUp, SimulatedRisk
from prescriptxai.machine_spec import MachineSpec
from prescriptxai.pipeline import ArtifactError
from prescriptxai.scenarios import Scenario, scenario_presets

STYLE = """
<style>
@media (prefers-color-scheme: light) {
  .stApp { background: #f3f5f8; }
  [data-testid="stVerticalBlockBorderWrapper"] { background: #fff; border-color: #dde3ea; }
}
[data-testid="stHeading"] h1, [data-testid="stHeading"] h2,
[data-testid="stHeading"] h3 { letter-spacing: -0.02em; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; }
.stButton button, .stDownloadButton button,
.stSelectbox [role="combobox"], .stExpander summary { min-height: 44px; }
[data-testid="stAppDeployButton"] { display: none; }
[data-testid="stMetricValue"] { font-family: ui-monospace, Consolas, monospace; }
[data-testid="stSlider"] { min-height: 64px; }
.stApp { --psx-focus: #1d4ed8; }
.stApp :is(button, [role="combobox"], summary):focus-visible,
.stApp [data-testid="stSlider"]:has(input[type="range"]:focus-visible) {
  outline: 3px solid var(--psx-focus);
  outline-offset: 3px;
}
@media (prefers-color-scheme: dark) {
  .stApp { --psx-focus: #9ac0ff; }
}
@media (max-width: 600px) {
  [data-testid="stMainBlockContainer"] { padding-inline: 1rem; }
  [data-testid="stHeading"] h1 { font-size: 2rem; }
  [data-testid="stHorizontalBlock"] { flex-direction: column; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { width: 100%; min-width: 0; }
}
</style>
"""


def _pick(scenario: Scenario) -> None:
    st.session_state["simulator_pick"] = scenario
    st.session_state["simulator_revision"] = st.session_state.get("simulator_revision", 0) + 1


def _location(
    machine_id: str, frame: pd.DataFrame, preset: Scenario | None
) -> tuple[str, float, pd.DataFrame]:
    units = sorted(frame["unit_id"].map(str).unique().tolist())
    unit_key = f"simulator-unit:{machine_id}"
    current = st.query_params.get("unit", units[0])
    if preset is not None and preset.unit in units:
        st.session_state[unit_key] = preset.unit
    unit = st.selectbox(
        "Recorded unit", units, index=units.index(current) if current in units else 0, key=unit_key
    )
    observed = frame.loc[frame["unit_id"].map(str) == unit].sort_values("time_index")
    times = [float(value) for value in observed["time_index"]]
    time_key = f"simulator-time:{machine_id}:{unit}"
    if preset is not None and preset.unit == unit and preset.time in times:
        st.session_state[time_key] = preset.time
    raw_time = st.query_params.get("time", "")
    time = next((value for value in times if str(value) == raw_time), times[-1])
    picked_time = (
        st.select_slider(
            "Recorded time",
            times,
            value=None if time_key in st.session_state else time,
            key=time_key,
        )
        if len(times) > 1
        else time
    )
    return unit, picked_time, observed.loc[observed["time_index"] <= picked_time]


def _settings(
    decision: MachineDecision, window: pd.DataFrame, selection: str, restored: str
) -> dict[str, float]:
    limits = decision.control_bounds()
    incoming = parse_settings(restored, limits)
    features = {feature.id: feature for feature in decision.spec.measurement_features}
    controls = {}
    for name, (lower, upper) in limits.items():
        original = float(window[name].iloc[-1])
        feature = features[name]
        if not lower <= original <= upper and name not in incoming:
            st.caption(f"{feature.label}: recorded value is outside the slider range.")
            continue
        value = st.slider(
            f"{feature.label} ({feature.unit})",
            min_value=lower,
            max_value=upper,
            value=incoming.get(name, original),
            key=f"simulator-setting:{selection}:{name}",
            help=feature.why,
        )
        if value != original:
            controls[name] = value
    return controls


def _risk_panel(preview: SimulatedRisk, elapsed: float) -> None:
    score = preview.assessment
    band = "Alert" if score.alert else "Low" if score.risk <= score.tau_safe else "Watch"
    st.metric("Predicted risk now", f"{score.risk:.1%}")
    st.caption(f"{band} · Predicted risk for the selected conditions · {elapsed:.1f} ms")
    if preview.unusual:
        st.warning(
            "This combination of conditions is unusual for real equipment. "
            "The risk estimate may be less reliable."
        )


def _cancel_prescription() -> None:
    job = cast(PrescriptionJob | None, st.session_state.pop("simulator_job", None))
    if job is not None:
        job.cancel()


@st.fragment(run_every=0.15)
def _wait_for_prescription(job: PrescriptionJob) -> None:
    if st.session_state.get("simulator_job") is not job or job.future.done():
        st.rerun()
    st.info("Calculating…")


def _manual_comparison(
    decision: MachineDecision,
    window: pd.DataFrame,
    preview: SimulatedRisk,
    controls: dict[str, float],
) -> None:
    reference = cast(
        tuple[str, MachineRecourseResult] | None, st.session_state.get("simulator_reference")
    )
    if reference is None or reference[0] != decision.input_hash(window, {}):
        st.session_state.pop("simulator_reference", None)
        st.info("Restore recorded settings to calculate a prescription for comparison.")
        return
    try:
        applied = decision.validate_controls(window, controls, "fast")
    except ValueError:
        st.info("These edited settings could not be checked for comparison.")
        return
    if not isclose(applied.risk_after, preview.assessment.risk, rel_tol=0, abs_tol=1e-9):
        st.info("The independent checks could not be reconciled with this risk preview.")
        return
    for label, result in (
        ("Your edited settings", applied),
        ("Prescription for the recorded settings", reference[1]),
    ):
        checks = prescription_checks(result)
        passed = sum(value for _, value in checks)
        st.write(
            f"{label} · {result.risk_after:.1%} predicted risk · {passed} of {len(checks)} checks"
        )
    st.caption("The prescription is a reference for the recorded settings only.")


def _prescription(
    decision: MachineDecision,
    window: pd.DataFrame,
    preview: SimulatedRisk,
    controls: dict[str, float],
    worker: Callable[[], MachineDecision],
    report_directory: Path,
) -> MachineRecourseResult | None:
    input_hash = preview.input_hash
    job = cast(PrescriptionJob | None, st.session_state.get("simulator_job"))
    if job is not None and job.input_hash != input_hash:
        _cancel_prescription()
        job = None
    if decision.spec.alerts_only:
        _cancel_prescription()
        st.session_state.pop("simulator_reference", None)
        st.info(f"Recommendation withheld: {decision.spec.limits_label}")
        return None
    if controls:
        _cancel_prescription()
        _manual_comparison(decision, window, preview, controls)
        return None
    if not preview.assessment.alert:
        _cancel_prescription()
        st.info("No action needed at the current alert threshold.")
        return None
    reference = cast(
        tuple[str, MachineRecourseResult] | None, st.session_state.get("simulator_reference")
    )
    if reference is not None and reference[0] == input_hash:
        render_recommendation(decision, window, reference[1], report_directory)
        return reference[1]
    if job is None:
        snapshot = window.copy(deep=True)

        def solve(cancelled: Event) -> MachineRecourseResult:
            isolated = worker()
            if isolated.input_hash(snapshot, {}) != input_hash:
                raise RecommendationWithheld("The model or recorded conditions changed")
            if cancelled.is_set():
                raise CancelledError()
            return isolated.recommend(snapshot, "fast")

        job = PrescriptionJob.start(computation_pool(), input_hash, solve)
        st.session_state["simulator_job"] = job
    if not job.future.done():
        _wait_for_prescription(job)
        return None
    try:
        result = job.future.result()
    except CancelledError:
        _cancel_prescription()
        st.info("Calculation cancelled.")
        return None
    except RecommendationWithheld as error:
        st.warning(str(error))
        return None
    render_recommendation(decision, window, result, report_directory)
    st.session_state["simulator_reference"] = (input_hash, result)
    return result


def _simulator(spec: MachineSpec, registry: MachineRegistry) -> None:
    st.caption("Synthetic or sample machine data" if spec.synthetic else "Recorded replay data")
    st.badge(spec.limits_label, color="orange" if spec.limits_status == "demonstration" else "blue")
    settings_path = Path(os.environ.get("PRESCRIPTXAI_DASHBOARD_CONFIG", "configs/dashboard.yaml"))
    settings = simulator_settings(settings_path, file_identity(settings_path))
    decision = simulator_decision(registry, spec.machine_id, settings)
    adapter = registry.open(spec.machine_id)
    frame = observed_rows(
        spec.machine_id, spec.spec_hash, settings.telemetry_population, file_identity(adapter.path)
    )
    presets = scenario_presets(
        registry, spec.machine_id, settings.telemetry_population, spec.spec_hash
    )
    with st.container(horizontal=True, wrap=True):
        for preset in presets:
            st.button(preset.name, on_click=_pick, args=(preset,), help="Example selected by rule")
        if st.button("Reset settings"):
            st.session_state["simulator_revision"] = (
                st.session_state.get("simulator_revision", 0) + 1
            )
            st.query_params.pop("settings", None)
    preset = st.session_state.pop("simulator_pick", None)
    revision = st.session_state.get("simulator_revision", 0)
    st.subheader("1. Set the conditions")
    st.markdown("**Situation (fixed)**")
    unit, time, window = _location(spec.machine_id, frame, preset)
    with st.expander("Fixed context"):
        for feature in spec.measurement_features:
            if feature.role == "frozen":
                st.write(f"{feature.label} · {float(window[feature.id].iloc[-1]):g} {feature.unit}")
    selection = json.dumps((spec.spec_hash, decision.runtime_identity, unit, time, revision))
    restore = (
        st.query_params.get("settings", "")
        if preset is None
        and st.query_params.get("machine") == spec.machine_id
        and st.query_params.get("spec") == spec.spec_hash
        and st.query_params.get("unit") == unit
        and st.query_params.get("time") == str(time)
        else ""
    )
    _interactive(
        decision, registry, settings, frame, unit, time, window, selection, restore
    )
    with st.expander("About this view and how it was checked"):
        st.write("SDG 9 · Advisory maintenance replay and model-based checks.")
        st.write(spec.limits_label)
        st.write(spec.data_source)
        st.write(spec.validation.rate_assumption)
        st.caption(f"Machine configuration: {spec.spec_hash}")


def _report_error(error: Exception) -> None:
    _cancel_prescription()
    st.session_state.pop("simulator_reference", None)
    message = str(error)
    st.error(
        message
        if message.startswith("Recommendation withheld:")
        else f"Recommendation withheld: {message}"
    )


@st.fragment
def _interactive(
    decision: MachineDecision,
    registry: MachineRegistry,
    settings: DashboardSettings,
    frame: pd.DataFrame,
    unit: str,
    time: float,
    window: pd.DataFrame,
    selection: str,
    restore: str,
) -> None:
    """Rerun the editable controls and their dependent outputs as one view."""
    try:
        _render_interactive(
            decision, registry, settings, frame, unit, time, window, selection, restore
        )
    except (ArtifactError, OSError, ValueError, KeyError, TypeError) as error:
        _report_error(error)


def _render_interactive(
    decision: MachineDecision,
    registry: MachineRegistry,
    settings: DashboardSettings,
    frame: pd.DataFrame,
    unit: str,
    time: float,
    window: pd.DataFrame,
    selection: str,
    restore: str,
) -> None:
    spec = decision.spec
    conditions, predictions = st.columns([1, 1])
    with conditions, st.container(border=True):
        st.markdown("**Current adjustable settings**")
        controls = _settings(decision, window, selection, restore)
    params = {
        "machine": spec.machine_id,
        "spec": spec.spec_hash,
        "unit": unit,
        "time": str(time),
        "settings": json.dumps(controls, sort_keys=True, separators=(",", ":")),
    }
    with st.expander("Copy replay settings"):
        st.code("?" + urlencode(params), language=None)
    with predictions:
        with st.container(border=True):
            st.subheader("2. Predicted risk")
            started = perf_counter()
            preview = decision.simulate_risk(window, controls)
            _risk_panel(preview, (perf_counter() - started) * 1000)
        with st.container(border=True):
            st.subheader("3. Prescription")
            result = _prescription(
                decision,
                window,
                preview,
                controls,
                lambda: simulator_decision(registry, spec.machine_id, settings, isolated=True),
                settings.report_directory,
            )
    with st.container(border=True):
        st.subheader("4. Was it followed?")
        scope = (
            ReplayFollowUp(
                input_hash=preview.input_hash,
                unit=unit,
                time=time,
                risk_before=result.risk_before,
                prescription_risk=result.risk_after,
                config_hash=result.config_hash,
            )
            if result is not None
            else None
        )
        feedback = render_follow_up(decision, window, frame, result, scope, settings.follow_up)
    current = {
        name: controls.get(name, float(window[name].iloc[-1])) for name in decision.control_bounds()
    }
    st.download_button(
        "Download scenario report",
        scenario_report(spec, unit, time, current, preview, result, feedback),
        "prescriptxai-scenario.html",
        "text/html",
        on_click="ignore",
    )
    # Publish the settings link after the risk and every dependent output.
    if st.query_params.to_dict() != params:
        st.query_params.from_dict(params)



def main() -> None:
    """Render the machine-scoped workflow or the retained analysis pages."""
    st.set_page_config(
        page_title="PrescriptXAI Operations Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.html(STYLE)
    workspace = st.sidebar.radio("Workspace", ("Simulator", "Advanced"))
    try:
        registry = SimulatorRegistry()
        specs = {spec.machine_id: spec for spec in registry.list()}
        machines = list(specs)
        requested = st.query_params.get("machine", machines[0])
        if requested not in specs:
            requested = machines[0]
        if workspace == "Advanced":
            _cancel_prescription()
            st.session_state.pop("simulator_reference", None)
            advanced_pages(advanced=True, spec=specs[requested])
            return
        st.title("PrescriptXAI Operations Dashboard")
        st.caption("Explore recorded conditions and predicted risk in an advisory simulator.")
        machine = st.selectbox(
            "Machine",
            machines,
            index=machines.index(requested),
            format_func=lambda name: specs[name].display_name,
        )
        _simulator(specs[machine], registry)
    except (ArtifactError, OSError, ValueError, KeyError, TypeError) as error:
        _report_error(error)


if __name__ == "__main__":
    main()
