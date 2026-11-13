"""Render a current prescription with independent checks and measured explanations."""

from __future__ import annotations

from itertools import pairwise
from math import isclose
from pathlib import Path
from time import perf_counter

import pandas as pd
import streamlit as st

from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.backend import OperatorError
from prescriptxai.dashboard.data import file_identity, saved_json
from prescriptxai.dashboard.plots import waterfall_chart
from prescriptxai.dashboard.simulator_data import sequential_risks
from prescriptxai.machine_schema import MachineRecourseResult
from prescriptxai.schemas import Explanation


def prescription_checks(result: MachineRecourseResult) -> tuple[tuple[str, bool], ...]:
    """Use the same four independent labels in the dashboard and scenario report."""
    report = result.validation_report
    return (
        ("Predicted safe", report.model_valid),
        ("Looks like normal behaviour", report.plausible),
        ("Within control limits", report.tier3_engineering.passed),
        ("Sensors stay consistent", report.tier4_sensor_coupling.passed),
    )


def _risk_drop_target(report_directory: Path) -> float | None:
    path = report_directory / "summary.json"
    try:
        summary = saved_json(str(path), file_identity(path))
        target = summary["manifest"]["configuration"]["targets"]["risk_reduction"]
        if type(target) in (int, float) and 0 <= target <= 1:
            return float(target)
    except (OperatorError, KeyError, TypeError):
        pass
    return None


def render_recommendation(
    decision: MachineDecision,
    window: pd.DataFrame,
    result: MachineRecourseResult,
    report_directory: Path,
) -> None:
    """Show results only after publication and input binding have succeeded."""
    explanation = decision.explain_result(result)
    _render_measured_result(decision, window, result, explanation, report_directory)


def _render_measured_result(
    decision: MachineDecision,
    window: pd.DataFrame,
    result: MachineRecourseResult,
    explanation: Explanation,
    report_directory: Path,
) -> None:
    if not result.alert:
        st.info("No action needed at the current alert threshold.")
        return
    features = {feature.id: feature for feature in decision.spec.measurement_features}
    names = sorted(
        result.action_features,
        key=lambda name: (-abs(result.delta_per_feature[name].scaled_delta or 0.0), name),
    )
    proposed = {name: result.new_state[name] for name in names}
    try:
        risks = sequential_risks(decision, window, proposed)
    except ValueError:
        risks = ()
    matches = bool(risks) and (
        isclose(risks[0], result.risk_before, rel_tol=0, abs_tol=1e-9)
        and isclose(risks[-1], result.risk_after, rel_tol=0, abs_tol=1e-9)
    )
    changes = dict(zip(names, (b - a for a, b in pairwise(risks)), strict=True)) if matches else {}
    target = _risk_drop_target(report_directory)
    started = perf_counter()
    st.metric("Predicted risk with the prescription", f"{result.risk_after:.1%}")
    st.caption("Fixable now · Advisory model-based checks")
    count, cap = len(names), decision.spec.k_max
    st.badge(f"{count} of {cap} allowed changes", color="blue" if count <= cap else "gray")
    drop = result.risk_before - result.risk_after
    label = f"Risk drop: {drop * 100:.1f} points"
    if target is not None:
        label += f" · Target {target * 100:g}+ points"
        label += " · Met" if drop >= target else " · Below target"
    else:
        label += " · Target unavailable"
    st.badge(label, color="blue" if target is not None and drop >= target else "gray")
    reasons = dict(zip(result.action_features, explanation.actions, strict=True))
    limits = decision.control_bounds()
    for name in names:
        feature = features[name]
        before, after = result.original_state[name], result.new_state[name]
        change = f" ({(after - before) / abs(before):+.1%})" if before else ""
        with st.container(border=True, key=f"psx-action-{name}"):
            st.write(f"{feature.label} · {before:.6g} → {after:.6g} {feature.unit}{change}")
            lower, upper = limits[name]
            if lower <= after <= upper and lower < upper:
                st.progress(
                    (after - lower) / (upper - lower), text="Position within control bounds"
                )
            st.caption(reasons[name])
            if name in changes:
                st.caption(
                    f"Change in predicted risk at this step: {changes[name] * 100:+.1f} points"
                )
    frozen = [feature.label for feature in features.values() if feature.role == "frozen"]
    if frozen:
        st.caption("Not changed: " + ", ".join(frozen))
    for index, (label, passed) in enumerate(prescription_checks(result)):
        status = "pass" if passed else "fail"
        with st.container(key=f"psx-check-{index}-{status}"):
            st.write(f"{'Pass' if passed else 'Fail'} · {label}")
    with st.expander("Why this?"):
        if matches:
            chart = waterfall_chart(
                [features[name].label for name in names],
                [changes[name] for name in names],
                risks[0],
                risks[-1],
                "largest scaled change first",
            )
            chart.update_layout(title="Predicted risk after each setting change")
            chart.update_yaxes(tickformat=".0%")
            st.plotly_chart(chart, width="stretch")
        else:
            st.warning("The risk breakdown could not be reconciled to this prescription.")
    render_ms = (perf_counter() - started) * 1000
    _timing(decision, result, render_ms)


def _timing(decision: MachineDecision, result: MachineRecourseResult, render_ms: float) -> None:
    timings, budgets = result.timings, decision.spec.latency_budgets[result.mode]
    with st.expander("How long did it take?"):
        if timings.pipeline_ms is not None:
            status = (
                "within budget"
                if timings.pipeline_ms <= budgets.pipeline_max_ms
                else ("over budget")
            )
            st.caption(f"Computed in {timings.pipeline_ms / 1000:.2f} s · {status}")
        for label, measured, budget in (
            ("Input processing", timings.ingestion_ms, budgets.ingestion_max_ms),
            ("Model scoring", timings.inference_ms, budgets.inference_max_ms),
            ("Finding settings", timings.optimization_ms, budgets.optimization_max_ms),
            ("Checking settings", timings.validation_ms, budgets.validation_max_ms),
            ("Building this panel", render_ms, budgets.dashboard_max_ms),
        ):
            if measured is not None:
                st.caption(f"{label} · {measured:.2f} ms (budget {budget:g} ms)")
        st.caption("This run's server measurements exclude debounce and browser paint.")
