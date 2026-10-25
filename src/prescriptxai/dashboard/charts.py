"""Plotly figures built only from measured recommendation outputs."""

from __future__ import annotations

import plotly.graph_objects as go

from prescriptxai.pipeline import RecommendationResult


def risk_comparison_chart(
    result: RecommendationResult, danger_threshold: float, safe_threshold: float
) -> go.Figure:
    """Plot actual pre/post model risks with configured danger and safe thresholds."""
    values = [result.optimization.initial_risk, result.optimization.final_risk]
    figure = go.Figure(
        data=[
            go.Bar(
                x=["Initial", "Candidate"],
                y=values,
                marker_color=["#b45309", "#2563eb"],
                text=[f"{value:.3f}" for value in values],
                textposition="auto",
            )
        ]
    )
    figure.add_hline(y=danger_threshold, line_dash="dash", annotation_text="Danger threshold")
    figure.add_hline(y=safe_threshold, line_dash="dot", annotation_text="Safe target")
    figure.update_yaxes(range=[0, 1], title="Calibrated model risk")
    figure.update_layout(title="Model risk before and after candidate", showlegend=False)
    return figure


def delta_chart(result: RecommendationResult) -> go.Figure | None:
    """Plot measured raw-unit deltas, or return no chart when no controls changed."""
    if not result.optimization.deltas:
        return None
    figure = go.Figure(
        data=[
            go.Bar(
                x=[delta.feature for delta in result.optimization.deltas],
                y=[delta.raw_delta for delta in result.optimization.deltas],
                text=[f"{delta.raw_delta:.4g}" for delta in result.optimization.deltas],
                textposition="auto",
            )
        ]
    )
    title = (
        "Prescribed changes in raw proxy units"
        if result.outcome.success
        else "Diagnostic candidate changes in raw proxy units — not an accepted action"
    )
    figure.update_layout(title=title, yaxis_title="Raw delta")
    return figure
