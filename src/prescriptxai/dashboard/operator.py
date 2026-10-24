"""Operator widgets render only authoritative library results and live manual previews."""

from __future__ import annotations

import json
import math
from collections.abc import MutableMapping
from time import perf_counter
from typing import Any, Literal, cast

import pandas as pd
import streamlit as st

from prescriptxai.config import AppConfig
from prescriptxai.dashboard.backend import (
    Backend,
    computation_pool,
    contribution_data,
)
from prescriptxai.dashboard.data import score_observations
from prescriptxai.dashboard.plots import (
    comparison_chart,
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
from prescriptxai.dashboard.state import save_result
from prescriptxai.schemas import Assessment, InputContext, RecourseResult


def triage_banner(result: RecourseResult) -> None:
    """Present shared triage without implying accepted physical intervention for failures."""
    if result.status == "RECOVERABLE":
        st.success("RECOVERABLE · all configured static checks passed under proxy assumptions.")
    elif result.status == "PARTIAL":
        st.warning(
            f"PARTIAL · risk reduction {result.risk_before - result.risk_after:.2%}; "
            "risk remains above the safe target. Schedule inspection."
        )
    elif result.status == "ESCALATE":
        st.error("ESCALATE · no accepted action. Schedule maintenance and obtain domain review.")
    else:
        st.info("NO_INTERVENTION · below the alert gate; this does not establish physical safety.")
    st.caption(
        f"Highest evidence reached: {result.evidence_level} · "
        f"True candidate risk: {result.risk_after:.6f}"
    )


def result_panels(result: RecourseResult, info: dict[str, Any], config: AppConfig) -> None:
    """Show independent tiers, raw actions, frozen-feature comparison, timings and exports."""
    triage_banner(result)
    st.subheader("Closest diagnostic candidate" if result.status == "ESCALATE" else "Proxy actions")
    table = action_table(result, info)
    if table.empty:
        st.info("No changed controllable proxies in this result.")
    else:
        st.dataframe(table, hide_index=True, width="stretch")
    if result.failure is not None:
        with st.expander(
            "Structured failure and closest candidate", expanded=result.status == "ESCALATE"
        ):
            st.json(result.failure.model_dump(mode="json"))
    report = result.validation_report
    tiers = [
        ("Model Safety", report.tier1_model_safety),
        ("Distributional Plausibility", report.tier2_distributional),
        ("Engineering Constraints", report.tier3_engineering),
        ("Sensor Relationships", report.tier4_sensor_coupling),
    ]
    st.subheader("Independent validation tiers")
    for column, (label, tier) in zip(st.columns(len(tiers)), tiers, strict=True):
        with column:
            st.markdown(f"**{label} · {str(tier.status).upper()}**")
            st.caption(f"Margin: {tier.margin if tier.margin is not None else 'unavailable'}")
            for reason in tier.diagnostics:
                st.write(reason)
            if not tier.diagnostics:
                st.caption(
                    "Configured checks passed."
                    if tier.passed
                    else "No additional diagnostic text was supplied; inspect the tier checks."
                )
            for check in tier.checks:
                st.caption(f"{check.name}: {check.explanation}; margin={check.margin}")
    if report.simulator is None or report.simulator.status == "skipped":
        st.markdown(":gray[Dynamic Simulator: not available]")
    else:
        st.write("Dynamic Simulator", report.simulator.model_dump(mode="json"))
    st.plotly_chart(
        mahalanobis_gauge(
            report.tier2_distributional.measurement, report.tier2_distributional.limit
        ),
        width="stretch",
    )
    st.plotly_chart(comparison_chart(scaled_comparison(result, info)), width="stretch")
    for warning in (*result.warnings, *result.assumptions):
        st.caption(warning)
    st.caption(
        f"Model {result.model_version} · config {result.config_hash} · {result.mode} · "
        f"run {result.run_id}"
    )
    budget = config.latency_budget
    budgets = {
        "ingestion_ms": budget.ingestion_max_ms,
        "inference_ms": budget.inference_max_ms,
        "optimization_ms": budget.optimization_max_ms,
        "validation_ms": budget.validation_max_ms,
        "pipeline_ms": budget.pipeline_max_ms,
    }
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "stage": stage,
                    "measured_call_ms": value,
                    "upper_budget_ms": budgets[stage],
                    "single_call_within_budget": value <= budgets[stage]
                    if value is not None
                    else None,
                }
                for stage, value in result.timings.model_dump().items()
                if stage in budgets
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption("Single call timings; budget certification requires p95 over a declared population.")
    first, second, third = st.columns(3)
    first.download_button(
        "Export JSON", result.model_dump_json(indent=2), "recommendation.json", "application/json"
    )
    second.download_button("Export CSV", result_csv(result, info), "recommendation.csv", "text/csv")
    third.download_button(
        "Printable summary", printable_summary(result, info), "summary.html", "text/html"
    )


def operator_console(
    backend: Backend,
    frame: pd.DataFrame,
    state: dict[str, float],
    context: InputContext,
    info: dict[str, Any],
    config: AppConfig,
    mode: Literal["fast", "thorough"],
    recompute: bool,
) -> float:
    """Score observed risk, solve on request and revalidate edited controls with shared logic."""
    excluded = 0.0
    work = perf_counter()
    assessment = backend.call("assess", state, context, mode)
    assert isinstance(assessment, Assessment)
    with st.spinner("Scoring observed history with the selected calibrated model…"):
        trace = (
            computation_pool()
            .submit(
                score_observations,
                frame,
                str(backend.path),
                backend.identity,
                backend.settings.model_dump_json(),
                json.dumps(info),
                mode,
            )
            .result()
        )
    excluded += perf_counter() - work
    first, second = st.columns([1, 2])
    first.plotly_chart(
        risk_gauge(assessment.risk, assessment.tau_danger, assessment.tau_safe), width="stretch"
    )
    first.metric("Observed calibrated risk", f"{assessment.risk:.6f}")
    if assessment.alert:
        first.warning("ALERT · calibrated risk is at or above the configured alert threshold.")
    second.plotly_chart(
        history_chart(trace, assessment.tau_danger, assessment.tau_safe), width="stretch"
    )
    if recompute or st.button("Recommend for selected state", type="primary", key="recommend"):
        work = perf_counter()
        with st.spinner("Solving the frozen proxy recourse problem…"):
            solved = backend.call("recommend", state, context, mode)
            assert isinstance(solved, RecourseResult)
            save_result(cast(MutableMapping[str, Any], st.session_state), solved.model_dump_json())
        excluded += perf_counter() - work
    if "solver_result" not in st.session_state:
        st.info("Request a recommendation to inspect action candidates and all validation tiers.")
        return excluded
    solved = RecourseResult.model_validate_json(st.session_state["solver_result"])
    controls = {}
    if solved.action_features:
        st.subheader("Manual proxy preview · every edit re-runs all static tiers")
        st.caption(
            "Closest-candidate edits are diagnostic until all checks pass. Exact nonzero "
            "edits count toward sparsity; solver search radius is not a physical bound."
        )
    for name in solved.action_features:
        spec = info["feature_metadata"][name]
        current, target = state[name], solved.new_state[name]
        lower = min(float(spec["bounds"]["minimum"]), current, target)
        upper = max(float(spec["bounds"]["maximum"]), current, target)
        if lower == upper:
            continue
        controls[name] = st.slider(
            f"{spec['label']} ({spec['unit']})",
            min_value=lower,
            max_value=upper,
            value=float(target),
            step=(upper - lower) / 1000,
            key=f"control:{name}",
            format="%.6f",
        )
    changed = any(value != solved.new_state[name] for name, value in controls.items())
    signature = json.dumps(controls, sort_keys=True)
    work = perf_counter()
    if changed:
        if st.session_state.get("preview_controls") != signature:
            with st.spinner("Re-scoring manual controls and all validation tiers…"):
                preview = backend.call("validate-controls", state, context, mode, controls)
                st.session_state["preview_result"] = preview.model_dump_json()
                st.session_state["preview_controls"] = signature
        st.caption("Displaying manually edited candidate; original solver result is retained.")
    else:
        st.session_state["preview_result"] = solved.model_dump_json()
        st.session_state.pop("preview_controls", None)
    excluded += perf_counter() - work
    result = RecourseResult.model_validate_json(st.session_state["preview_result"])
    result_panels(result, info, config)
    if controls and result.alert:
        work = perf_counter()
        with st.spinner("Computing true-risk contributions from the original observed state…"):
            contributions = (
                computation_pool()
                .submit(
                    contribution_data,
                    str(backend.path),
                    backend.identity,
                    backend.settings.model_dump_json(),
                    json.dumps(state),
                    context.model_dump_json(),
                    signature,
                    mode,
                )
                .result()
            )
        excluded += perf_counter() - work
        if not (
            math.isclose(contributions["before"], result.risk_before, abs_tol=1e-9)
            and math.isclose(contributions["after"], result.risk_after, abs_tol=1e-9)
        ):
            st.warning(
                "Attribution endpoints differ from the displayed candidate; chart unavailable."
            )
            return excluded
        for name, values in (
            ("Sequential · alphabetical feature order", contributions["sequential"]),
            ("Exact permutation average (Shapley-style)", contributions["averaged"]),
        ):
            if values is not None:
                st.plotly_chart(
                    waterfall_chart(
                        contributions["names"],
                        values,
                        contributions["before"],
                        contributions["after"],
                        name,
                    ),
                    width="stretch",
                )
        st.caption(
            "Attribution explains this calibrated model with residual-preserving proxy "
            "propagation; it does not estimate a causal machine response."
        )
    return excluded
