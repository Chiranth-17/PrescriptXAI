"""Build an offline HTML receipt for the dashboard's current replay."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape

from prescriptxai.dashboard.simulator_prescription import prescription_checks
from prescriptxai.machine_schema import (
    FeedbackRecord,
    MachineRecourseResult,
    ReplayFollowUp,
    SimulatedRisk,
)
from prescriptxai.machine_spec import MachineFeature, MachineSpec


def _prescription_section(
    features: Mapping[str, MachineFeature], result: MachineRecourseResult
) -> str:
    actions = "".join(
        f"<li>{escape(features[name].label)}: {result.original_state[name]:g} to "
        f"{result.new_state[name]:g} {escape(features[name].unit)}</li>"
        for name in result.action_features
    )
    checks = "".join(
        f"<li>{escape(label)}: {'Pass' if passed else 'Fail'}</li>"
        for label, passed in prescription_checks(result)
    )
    return (
        f"<p>Run {escape(result.run_id)}. Predicted risk with prescription: "
        f"{result.risk_after:.1%}.</p><ul>{actions}</ul><ul>{checks}</ul>"
    )


def _followup_section(
    features: Mapping[str, MachineFeature], record: FeedbackRecord, scope: ReplayFollowUp
) -> str:
    label = (
        "Simulated operator (demo)"
        if record.source == "simulated_operator"
        else "Operator (this session)"
    )
    applied = "".join(
        f"<li>{escape(features[name].label)}: {value:g} {escape(features[name].unit)}</li>"
        for name, value in record.applied.items()
    )
    passed = record.applied_tier_passes.values()
    reason = f"<p>Reported reason: {escape(scope.reason)}</p>" if scope.reason else ""
    choice = f"<p>Reported choice: {escape(scope.stated_choice)}</p>" if scope.stated_choice else ""
    return (
        f"<p>{label}. Adherence: {record.adherence:.0%}. "
        f"Predicted risk with applied settings: {record.applied_risk:.1%}. "
        f"Applied settings passed {sum(passed)} of {len(passed)} checks.</p>"
        f"{choice}{reason}<ul>{applied}</ul>"
    )


def scenario_report(
    spec: MachineSpec,
    unit: str,
    time: float,
    settings: Mapping[str, float],
    preview: SimulatedRisk,
    result: MachineRecourseResult | None,
    feedback: tuple[FeedbackRecord, ReplayFollowUp] | None,
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
    if spec.alerts_only:
        prescription = f"<p>{escape(spec.limits_label)}.</p>"
    elif result is not None:
        prescription = _prescription_section(features, result)
        if feedback is not None:
            record, scope = feedback
            if (
                record.result_run_id == result.run_id
                and record.machine_id == spec.machine_id
                and record.spec_hash == spec.spec_hash
                and record.protocol_version == score.protocol_version
                and record.synthetic == spec.synthetic
                and scope.config_hash == result.config_hash
                and scope.input_hash == preview.input_hash
                and scope.unit == unit
                and scope.time == time
            ):
                follow_up = _followup_section(features, record, scope)
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>PrescriptXAI scenario report</title>"
        "<h1>PrescriptXAI scenario report</h1>"
        f"<p>{escape(spec.display_name)} · {source} · unit {escape(unit)}, time {time:g}</p>"
        f"<p>{escape(spec.limits_label)}</p>"
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
