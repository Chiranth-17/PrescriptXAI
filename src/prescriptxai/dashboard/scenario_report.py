"""Build an offline HTML receipt for the dashboard's current replay."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape

from prescriptxai.dashboard.simulator_prescription import prescription_checks
from prescriptxai.machine_schema import FeedbackRecord, MachineRecourseResult, SimulatedRisk
from prescriptxai.machine_spec import MachineSpec


def scenario_report(
    spec: MachineSpec,
    unit: str,
    time: float,
    settings: Mapping[str, float],
    preview: SimulatedRisk,
    result: MachineRecourseResult | None,
    feedback: FeedbackRecord | None,
) -> str:
    """Use plain escaped text and export only what the active view can publish."""
    score = preview.assessment
    features = {feature.id: feature for feature in spec.measurement_features}
    setting_rows = "".join(
        f"<li>{escape(features[name].label)}: {value:g} {escape(features[name].unit)}</li>"
        for name, value in settings.items()
    )
    source = "Synthetic or sample machine data" if spec.synthetic else "Recorded replay data"
    prescription = "<p>No prescription was published for these inputs.</p>"
    follow_up = "<p>No follow-up is attached to this report.</p>"
    if not spec.confirmation.confirmed:
        prescription = "<p>Alerts only: limits not yet confirmed by an engineer.</p>"
    elif result is not None:
        actions = "".join(
            f"<li>{escape(features[name].label)}: {result.original_state[name]:g} to "
            f"{result.new_state[name]:g} {escape(features[name].unit)}</li>"
            for name in result.action_features
        )
        checks = "".join(
            f"<li>{escape(label)}: {'Pass' if passed else 'Fail'}</li>"
            for label, passed in prescription_checks(result)
        )
        prescription = (
            f"<p>Run {escape(result.run_id)}. Predicted risk with prescription: "
            f"{result.risk_after:.1%}.</p><ul>{actions}</ul><ul>{checks}</ul>"
        )
        if feedback is not None and feedback.result_run_id == result.run_id:
            label = (
                "Simulated operator (demo)"
                if feedback.source == "simulated_operator"
                else "Operator (this session)"
            )
            follow_up = (
                f"<p>{label}. Adherence: {feedback.adherence:.0%}. "
                f"Predicted risk with applied settings: {feedback.applied_risk:.1%}.</p>"
            )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>PrescriptXAI scenario report</title>"
        "<h1>PrescriptXAI scenario report</h1>"
        f"<p>{escape(spec.display_name)} · {source} · unit {escape(unit)}, time {time:g}</p>"
        f"<p>Data source: {escape(spec.data_source)}</p>"
        "<p>Advisory replay and model-based checks. Physical outcomes were not measured.</p>"
        "<h2>Current settings and predicted risk</h2>"
        f"<ul>{setting_rows}</ul><p>Predicted risk now: {score.risk:.1%}.</p>"
        f"<h2>Prescription</h2>{prescription}<h2>Follow-up</h2>{follow_up}"
        "<h2>Provenance</h2>"
        f"<p>Machine {escape(spec.machine_id)} · spec {escape(spec.spec_hash)} · "
        f"protocol {escape(score.protocol_version)} · configuration {escape(score.config_hash)}"
        f" · input {escape(preview.input_hash)}</p></html>"
    )
