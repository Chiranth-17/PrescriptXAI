"""Operator-facing Streamlit simulator for a selected observed machine trajectory."""

from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter
from typing import cast
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.core.data_quality import RecommendationWithheld
from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.app import main as advanced_pages
from prescriptxai.dashboard.data import file_identity
from prescriptxai.dashboard.simulator_data import (
    observed_rows,
    parse_settings,
    simulator_decision,
)
from prescriptxai.dashboard.state import load_settings
from prescriptxai.machine_schema import MachineRecourseResult, SimulatedRisk
from prescriptxai.machine_spec import MachineSpec
from prescriptxai.machines import record_feedback
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
.stButton button, .stDownloadButton button { min-height: 44px; }
[data-testid="stAppDeployButton"] { display: none; }
[data-testid="stMetricValue"] { font-family: ui-monospace, Consolas, monospace; }
[data-testid="stSlider"] { min-height: 64px; }
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


def _render_recommendation(decision: MachineDecision, result: MachineRecourseResult) -> None:
    features = {feature.id: feature for feature in decision.spec.measurement_features}
    explanation = decision.explain_result(result)
    if not result.alert:
        st.info("No action needed at the current alert threshold.")
        return
    st.metric("Predicted risk with the prescription", f"{result.risk_after:.1%}")
    st.caption(f"{len(result.action_features)} of {decision.spec.k_max} allowed changes")
    for name, reason in zip(result.action_features, explanation.actions, strict=True):
        feature = features[name]
        st.markdown(
            f"**{feature.label}** · {result.original_state[name]:.6g} → "
            f"{result.new_state[name]:.6g} {feature.unit}"
        )
        st.caption(reason)
    report = result.validation_report
    for label, passed in (
        ("Predicted safe", report.model_valid),
        ("Looks like normal behaviour", report.plausible),
        ("Within control limits", report.tier3_engineering.passed),
        ("Sensors stay consistent", report.tier4_sensor_coupling.passed),
    ):
        st.write(f"{'Pass' if passed else 'Fail'} · {label}")
    st.caption("Model-based checks. Changes are advisory.")


def _prescription(
    decision: MachineDecision,
    window: pd.DataFrame,
    preview: SimulatedRisk,
    controls: dict[str, float],
) -> MachineRecourseResult | None:
    if not decision.spec.confirmation.confirmed:
        st.info("Recommendation withheld: Alerts only: limits not yet confirmed by an engineer")
        return None
    if controls:
        st.info("Return to recorded settings to request a prescription.")
        return None
    input_hash = preview.input_hash
    saved = cast(tuple[str, MachineRecourseResult] | None, st.session_state.get("simulator_result"))
    if saved is not None and saved[0] != input_hash:
        del st.session_state["simulator_result"]
        saved = None
    if preview.assessment.alert and st.button("Calculate prescription"):
        st.session_state.pop("simulator_result", None)
        try:
            with st.spinner("Calculating…"):
                result = decision.recommend(window, "fast")
        except RecommendationWithheld as error:
            st.warning(str(error))
            return None
        saved = (input_hash, result)
        st.session_state["simulator_result"] = saved
    if saved is not None:
        result = saved[1]
        _render_recommendation(decision, result)
        return result
    if not preview.assessment.alert:
        st.info("No action needed at the current alert threshold.")
    return None


def _follow_up(
    decision: MachineDecision,
    window: pd.DataFrame,
    result: MachineRecourseResult | None,
) -> None:
    if result is None or not result.action_features:
        st.caption("A current prescription is needed to record applied settings.")
        return
    labels = {feature.id: feature.label for feature in decision.spec.measurement_features}
    limits = decision.control_bounds()
    applied = {}
    for name in result.action_features:
        lower, upper = limits[name]
        applied[name] = st.slider(
            f"Applied {labels[name]}",
            lower,
            upper,
            result.new_state[name],
            key=f"applied:{result.run_id}:{name}",
        )
    if st.button("Record this follow-up"):
        feedback = decision.feedback(window, result, applied)
        record_feedback(feedback)
        st.success(f"Recorded locally · Adherence {feedback.adherence:.0%}")
        st.metric("Predicted risk with applied settings", f"{feedback.applied_risk:.1%}")


def _simulator(spec: MachineSpec, registry: MachineRegistry) -> None:
    st.caption("Synthetic or sample machine data" if spec.synthetic else "Recorded replay data")
    if not spec.confirmation.confirmed:
        st.info("Alerts only: limits not yet confirmed by an engineer")
    settings = load_settings(
        Path(os.environ.get("PRESCRIPTXAI_DASHBOARD_CONFIG", "configs/dashboard.yaml"))
    )
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
    conditions, predictions = st.columns([1, 1])
    with conditions, st.container(border=True):
        st.subheader("1. Set the conditions")
        unit, time, window = _location(spec.machine_id, frame, preset)
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
        controls = _settings(decision, window, selection, restore)
    params = {
        "machine": spec.machine_id,
        "spec": spec.spec_hash,
        "unit": unit,
        "time": str(time),
        "settings": json.dumps(controls, sort_keys=True, separators=(",", ":")),
    }
    if st.query_params.to_dict() != params:
        st.query_params.from_dict(params)
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
            result = _prescription(decision, window, preview, controls)
    with st.container(border=True):
        st.subheader("4. Was it followed?")
        _follow_up(decision, window, result)
    with st.expander("About this view and how it was checked"):
        st.write("SDG 9 · Advisory maintenance replay and model-based checks.")
        st.write(spec.data_source)
        st.write(spec.validation.rate_assumption)
        st.caption(f"Machine configuration: {spec.spec_hash}")


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
        registry = MachineRegistry()
        specs = {spec.machine_id: spec for spec in registry.list()}
        machines = list(specs)
        requested = st.query_params.get("machine", machines[0])
        if requested not in specs:
            requested = machines[0]
        if workspace == "Advanced":
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
        message = str(error)
        st.error(
            message
            if message.startswith("Recommendation withheld:")
            else f"Recommendation withheld: {message}"
        )


if __name__ == "__main__":
    main()
