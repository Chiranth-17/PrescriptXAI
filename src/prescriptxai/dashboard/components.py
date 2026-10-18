"""Streamlit result display components with separate validity statuses."""

from __future__ import annotations

import streamlit as st

from prescriptxai.dashboard.charts import delta_chart, risk_comparison_chart
from prescriptxai.pipeline import RecommendationResult


def show_recommendation(
    result: RecommendationResult, danger_threshold: float, safe_threshold: float
) -> None:
    """Render risk safety, sparse-action feasibility, physical checks, and raw deltas."""
    if result.outcome.success:
        st.success("Model target, sparse-action, and all configured physical checks passed.")
    else:
        st.warning("No fully validated recommendation is available for this state.")
    st.caption(f"Highest evidence reached: {result.validation.evidence_level}")
    for assumption in result.validation.assumptions:
        st.caption(f"Assumption: {assumption}")
    first, second, third = st.columns(3)
    first.metric("Model validity", "Pass" if result.outcome.model_valid else "Fail")
    second.metric(
        "Sparse-action feasibility", "Pass" if result.outcome.recourse_feasible else "Fail"
    )
    third.metric("Tier 2 plausibility", "Pass" if result.validation.plausible else "Fail")
    st.plotly_chart(
        risk_comparison_chart(result, danger_threshold, safe_threshold), use_container_width=True
    )
    delta_figure = delta_chart(result)
    if delta_figure is None:
        st.info("No actuator changes were generated.")
    else:
        st.plotly_chart(delta_figure, use_container_width=True)
    tiers = {
        "Tier 1 · model risk": result.validation.tier1_model,
        "Tier 2 · Mahalanobis plausibility": result.validation.tier2_plausibility,
        "Tier 3 · engineering limits": result.validation.tier3_engineering,
        "Tier 4 · sensor coupling": result.validation.tier4_coupling,
        "Dynamic simulator": result.validation.simulator,
    }
    for label, tier in tiers.items():
        with st.expander(f"{label}: {str(tier.status).capitalize()}"):
            st.caption(f"Evidence: {tier.evidence_level}")
            for diagnostic in tier.diagnostics:
                st.write(diagnostic)
            if tier.measurement is not None:
                st.write(f"Measured: {tier.measurement:.6g}")
            if tier.limit is not None:
                st.write(f"Configured limit: {tier.limit:.6g}")
            if tier.margin is not None:
                st.write(f"Compliance margin: {tier.margin:.6g}")
            for check in tier.checks:
                st.write(f"{check.name}: {check.explanation}; margin={check.margin}")
            for warning in tier.warnings:
                st.warning(warning)
    if result.optimization.message:
        st.caption(result.optimization.message)
    st.caption(
        f"Measured optimization: {result.optimization_ms:.2f} ms · "
        f"validation: {result.validation_ms:.2f} ms"
    )
