"""Pure Plotly builders; plotted measurements come from live or saved evidence."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import plotly.graph_objects as go

PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00"]


def risk_gauge(risk: float, danger: float, safe: float) -> go.Figure:
    """Display a calibrated probability with both configured threshold markers."""
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=risk,
            title={"text": "True calibrated failure risk"},
            gauge={
                "axis": {"range": [0, 1]},
                "bar": {"color": PALETTE[0]},
                "threshold": {"value": danger, "line": {"color": PALETTE[1], "width": 4}},
                "steps": [
                    {"range": [0, safe], "color": "#d9f0e8"},
                    {"range": [safe, danger], "color": "#f5f5f5"},
                ],
            },
        )
    ).update_layout(height=240, margin={"t": 45, "b": 20})


def history_chart(frame: pd.DataFrame, danger: float, safe: float) -> go.Figure:
    """Plot only observed cycle risks; empty histories remain empty and labeled."""
    figure = go.Figure()
    if not frame.empty:
        figure.add_trace(
            go.Scatter(
                x=frame.cycle,
                y=frame.risk,
                mode="lines",
                name="True risk",
                line={"color": PALETTE[0]},
            )
        )
    figure.add_hline(y=danger, line_dash="dash", annotation_text="Alert threshold")
    figure.add_hline(y=safe, line_dash="dot", annotation_text="Safe target")
    return figure.update_layout(
        title="Observed risk over cycles",
        xaxis_title="Observed cycle",
        yaxis_title="Calibrated probability",
        yaxis_range=[0, 1],
    )


def mahalanobis_gauge(distance: float | None, limit: float | None) -> go.Figure:
    """Show actual Tier 2 distance; missing measurements are explicitly unavailable."""
    figure = go.Figure()
    if distance is not None and limit is not None:
        figure.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=distance,
                title={"text": "Mahalanobis D_M / D_max"},
                gauge={
                    "axis": {"range": [0, max(distance, limit) * 1.2 or 1]},
                    "threshold": {"value": limit, "line": {"color": PALETTE[1], "width": 4}},
                    "bar": {"color": PALETTE[0]},
                },
            )
        )
    return figure.update_layout(
        title=None if distance is not None else "D_M unavailable", height=240
    )


def comparison_chart(frame: pd.DataFrame) -> go.Figure:
    """Compare training-scaled coordinates and visibly lock immutable features."""
    figure = go.Figure()
    if not frame.empty:
        labels = [f"{r.feature} [LOCKED]" if r.locked else r.feature for r in frame.itertuples()]
        for name, color in zip(("before", "after"), PALETTE, strict=False):
            figure.add_trace(go.Bar(x=labels, y=frame[name], name=name, marker_color=color))
    return figure.update_layout(
        title="Before / after in saved scaled coordinates",
        barmode="group",
        yaxis_title="Training standard deviations",
    )


def waterfall_chart(
    names: Sequence[str], contributions: Sequence[float], before: float, after: float, method: str
) -> go.Figure:
    """Display additive true-risk changes in a documented sequential or averaged order."""
    return go.Figure(
        go.Waterfall(
            x=["Observed", *names, "Candidate"],
            y=[before, *contributions, after],
            measure=["absolute", *["relative"] * len(names), "total"],
            decreasing={"marker": {"color": PALETTE[0]}},
            increasing={"marker": {"color": PALETTE[1]}},
        )
    ).update_layout(title=f"True-risk contributions · {method}", yaxis_title="Risk change")


def evidence_bars(labels: Sequence[str], values: Sequence[float | None], title: str) -> go.Figure:
    """Plot supplied saved counts/quantiles only; unavailable values remain gaps."""
    return go.Figure(go.Bar(x=list(labels), y=list(values), marker_color=PALETTE[0])).update_layout(
        title=title
    )


def calibration_chart(rows: list[dict[str, float]]) -> go.Figure:
    """Plot saved held-out reliability bins against the ideal calibration diagonal."""
    figure = go.Figure(go.Scatter(x=[0, 1], y=[0, 1], name="Ideal", line={"dash": "dot"}))
    if rows:
        figure.add_trace(
            go.Scatter(
                x=[r["mean_probability"] for r in rows],
                y=[r["fraction_positive"] for r in rows],
                name="Saved held-out calibration",
                mode="lines+markers",
            )
        )
    return figure.update_layout(
        title="Saved calibration reliability",
        xaxis_title="Mean prediction",
        yaxis_title="Observed failure fraction",
    )
