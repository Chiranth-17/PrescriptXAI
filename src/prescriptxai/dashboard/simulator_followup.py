"""Applied-setting checks and local replay feedback presentation."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from prescriptxai.config import FollowUpSettings
from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.plots import PALETTE
from prescriptxai.dashboard.simulator_data import replay_trend
from prescriptxai.machine_schema import FeedbackRecord, MachineRecourseResult, ReplayFollowUp
from prescriptxai.machines import read_feedback_log, record_feedback_batch

SOURCE_LABELS = {
    "operator": "Operator (local log)",
    "simulated_operator": "Simulated operator (demo)",
}
ReportedChoice = Literal["Followed as recommended", "Followed partly", "Not followed"]
CHOICES: tuple[ReportedChoice, ...] = ("Followed as recommended", "Followed partly", "Not followed")


def _trend_panel(
    decision: MachineDecision,
    observations: pd.DataFrame,
    details: ReplayFollowUp,
    feedback: FeedbackRecord,
    steps: int,
) -> None:
    try:
        trend = replay_trend(
            decision, observations, details.unit, details.time, feedback.applied, steps
        )
    except ValueError:
        st.info("The future recorded windows could not be checked for these settings.")
        return
    if trend.empty:
        st.info("There are no later recorded observations for this unit.")
        return
    figure = go.Figure()
    for series, color, dash in (
        ("Recorded settings (model prediction)", PALETTE[0], "solid"),
        ("Applied settings (model prediction)", PALETTE[1], "solid"),
        ("Safe level", PALETTE[2], "dash"),
        ("Alert level", PALETTE[4], "dash"),
    ):
        figure.add_scatter(
            x=trend["Recorded time"],
            y=trend[series],
            name=series,
            mode="lines+markers",
            line={"color": color, "dash": dash},
        )
    figure.update_layout(
        xaxis_title="Recorded time", yaxis_title="Predicted risk", yaxis_tickformat=".0%"
    )
    st.plotly_chart(figure, width="stretch")
    st.caption(
        "Each point replays a later recorded window with the same applied settings. "
        "This comparison uses model predictions and makes no claim about machine response."
    )
    observed = trend[["Recorded time", "Recorded remaining life", "Recorded event"]].dropna(
        axis=1, how="all"
    )
    if len(observed.columns) > 1:
        st.caption("Archive outcomes and labels for the same times")
        st.dataframe(observed, hide_index=True, width="stretch")


def _feedback_log(
    decision: MachineDecision,
    settings: FollowUpSettings,
    path: Path = Path("artifacts/machines/feedback.sqlite3"),
) -> None:
    with st.expander("Follow-up log"):
        include_demo = st.checkbox("Include simulated operator records")
        try:
            entries = read_feedback_log(
                decision.spec, decision.protocol_version, path, include_simulated=include_demo
            )
        except (OSError, ValueError, sqlite3.Error):
            st.warning("The local follow-up log is unavailable.")
            return
        st.caption(
            f"{decision.spec.machine_id} · configuration {decision.spec.spec_hash} · "
            f"rules {decision.protocol_version} · "
            f"assumed horizon {decision.spec.validation.intervention_steps} step(s) · local replay"
        )
        if not entries:
            st.info("No follow-ups in this view.")
            return
        rows = []
        for record, detail in reversed(entries):
            rows.append(
                {
                    "Source": SOURCE_LABELS[record.source],
                    "Data": "Synthetic or sample" if record.synthetic else "Recorded replay",
                    "Run": record.result_run_id,
                    "Model configuration": detail.config_hash if detail else None,
                    "Unit": detail.unit if detail else None,
                    "Time": detail.time if detail else None,
                    "Predicted risk before": detail.risk_before if detail else None,
                    "Predicted risk applied": record.applied_risk,
                    "Agreement": record.adherence,
                    "Measured outcome": settings.adherence_label(record.adherence),
                    "Reported choice": detail.stated_choice if detail else None,
                    "Reason": detail.reason if detail else None,
                    "Demo seed": detail.demo_seed if detail else None,
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def _render_applied(
    feedback: FeedbackRecord,
    result: MachineRecourseResult,
    labels: dict[str, str],
    settings: FollowUpSettings,
) -> None:
    recorded, actual = st.columns(2)
    recorded.metric("Predicted risk with prescription", f"{result.risk_after:.1%}")
    actual.metric("Predicted risk with applied settings", f"{feedback.applied_risk:.1%}")
    passes = feedback.applied_tier_passes.values()
    st.caption(
        f"Applied settings passed {sum(passes)} of {len(passes)} checks · "
        f"{settings.adherence_label(feedback.adherence)} ({feedback.adherence:.0%} agreement)"
    )
    for name, score in feedback.action_adherence.items():
        st.progress(score, text=f"{labels[name]} · {score:.0%} agreement")


def _applied_inputs(
    decision: MachineDecision, result: MachineRecourseResult, labels: dict[str, str]
) -> tuple[ReportedChoice, str, dict[str, float]]:
    choice = st.radio("Reported follow-up", CHOICES, horizontal=True, key=f"choice:{result.run_id}")
    reason = (
        st.text_input("Reason (optional)", max_chars=500, key=f"reason:{result.run_id}").strip()
        if choice == "Not followed"
        else ""
    )
    limits = decision.control_bounds()
    applied = {}
    for name in result.action_features:
        recommendation = result.new_state[name]
        original = result.original_state[name]
        low, high = limits[name]
        starting = {
            "Followed as recommended": recommendation,
            "Followed partly": (original + recommendation) / 2,
            "Not followed": original,
        }[choice]
        applied[name] = st.slider(
            f"Applied {labels[name]}",
            min(low, original),
            max(high, original),
            starting,
            key=f"applied:{result.run_id}:{choice}:{name}",
        )
    return choice, reason, applied


def render_follow_up(
    decision: MachineDecision,
    window: pd.DataFrame,
    observations: pd.DataFrame,
    result: MachineRecourseResult | None,
    scope: ReplayFollowUp | None,
    settings: FollowUpSettings,
) -> tuple[FeedbackRecord, ReplayFollowUp] | None:
    """Preview applied values and store them only after an explicit recording action."""
    if (
        not decision.spec.confirmation.confirmed
        or result is None
        or scope is None
        or not result.action_features
    ):
        st.caption("A current prescription is needed to record applied settings.")
        return None
    labels = {feature.id: feature.label for feature in decision.spec.measurement_features}
    choice, reason, applied = _applied_inputs(decision, result, labels)
    try:
        feedback = decision.feedback(window, result, applied)
    except ValueError:
        st.warning("The applied settings could not be checked. Review the recorded values.")
        _feedback_log(decision, settings)
        return None
    _render_applied(feedback, result, labels, settings)
    if st.checkbox("Show later recorded replay", key=f"trend:{result.run_id}"):
        _trend_panel(decision, observations, scope, feedback, settings.trend_steps)
    details = ReplayFollowUp.model_validate(
        {**scope.model_dump(), "stated_choice": choice, "reason": reason or None}
    )
    active_key = (scope.input_hash, result.run_id, tuple(applied.items()), choice, reason)
    entry = (feedback, details)
    try:
        if st.button("Record this follow-up"):
            record_feedback_batch([entry])
            st.session_state["active_followup"] = (active_key, entry)
            st.success("Follow-up recorded locally.")
        if st.button("Simulate operators"):
            batch = [
                (record, scope.model_copy(update={"demo_seed": settings.demo_seed}))
                for record in decision.simulate_feedback(
                    window, result, settings.demo_seed, settings.demo_count
                )
            ]
            record_feedback_batch(batch)
            st.success(f"Recorded {len(batch)} rows labeled Simulated operator (demo).")
    except (OSError, ValueError, sqlite3.Error):
        st.warning("The requested follow-up could not be recorded.")
    _feedback_log(decision, settings)
    saved = st.session_state.get("active_followup")
    if saved is not None and saved[0] == active_key:
        return saved[1]  # type: ignore[no-any-return]
    return None
