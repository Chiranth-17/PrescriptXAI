"""Machine-readable and human-readable reports from measured evaluation objects."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from prescriptxai.evaluation.metrics import EvaluationSummary
from prescriptxai.evaluation.runner import DirectionConsistency, EvaluationRun


def write_evaluation_report(
    run: EvaluationRun,
    json_path: Path,
    markdown_path: Path,
    run_configuration: Mapping[str, Any] | None = None,
) -> None:
    """Write records and computed metrics to JSON and Markdown files."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_document = {
        "summary": run.summary.to_dict(),
        "counterfactual_direction_consistency": run.direction_consistency.__dict__,
        "infeasible_high_risk_states": run.infeasible_high_risk_states,
        "actionable_high_risk_states": (
            run.summary.eligible_high_risk_states - run.infeasible_high_risk_states
        ),
        "recourse_search_configuration": dict(run_configuration or {}),
        "records": [record.__dict__ for record in run.records],
    }
    json_path.write_text(json.dumps(json_document, indent=2, allow_nan=False), encoding="utf-8")
    markdown_path.write_text(
        render_markdown(
            run.summary,
            run.direction_consistency,
            (
                sum(record.changed_features for record in run.records) / len(run.records)
                if run.records
                else None
            ),
            run.infeasible_high_risk_states,
            run_configuration,
        ),
        encoding="utf-8",
    )


def _format_metric(value: float | None) -> str:
    """Display missing values as unmeasured and numeric outcomes to four places."""
    return "Unmeasured" if value is None else f"{value:.4f}"


def render_markdown(
    summary: EvaluationSummary,
    direction: DirectionConsistency | None = None,
    mean_returned_action_sparsity: float | None = None,
    infeasible_high_risk_states: int | None = None,
    run_configuration: Mapping[str, Any] | None = None,
) -> str:
    """Render dynamically computed measurements and target statuses."""
    lines = [
        "# PrescriptXAI Evaluation",
        "",
        f"Eligible high-risk held-out states: {summary.eligible_high_risk_states}",
        f"Evaluated states: {summary.evaluated_states}",
        f"Model-valid candidates: {summary.model_valid_count}",
        f"Physically plausible candidates: {summary.physically_plausible_count}",
        f"Successful sparse recourses: {summary.successful_recourse_count}",
        "",
        "| Metric | Measured | Target | Status |",
        "|---|---:|---:|---|",
    ]
    metrics: dict[str, Any] = {
        "Model validity rate": summary.recourse_validity_rate,
        "Optimizer sparse-action feasibility rate": summary.recourse_feasibility_rate,
        "Joint successful recourse rate": summary.successful_recourse_rate,
        "Physical plausibility rate": summary.physical_plausibility_rate,
        "Tier 2 plausibility rate": summary.tier2_plausibility_rate,
        "Tier 3 engineering rate": summary.tier3_engineering_rate,
        "Tier 4 coupling rate": summary.tier4_coupling_rate,
        "Average sparsity": summary.average_sparsity,
        "Mean risk reduction": summary.mean_risk_reduction,
    }
    for name, metric in metrics.items():
        status = "unmeasured" if metric.passed is None else ("pass" if metric.passed else "fail")
        lines.append(f"| {name} | {_format_metric(metric.value)} | {metric.target} | {status} |")
    if direction is not None:
        lines.extend(
            (
                "",
                "## Counterfactual direction consistency",
                "",
                f"Similar state pairs (scaled distance ≤ {direction.similarity_radius:g}): "
                f"{direction.similar_pair_count}",
                "Pairwise sign agreement: "
                f"{_format_metric(direction.pairwise_sign_agreement)}",
            )
        )
    if mean_returned_action_sparsity is not None:
        lines.extend(
            (
                "Mean changed features across all returned candidates: "
                f"{mean_returned_action_sparsity:.4f}",
                "The target average sparsity metric above is computed over successful recourses.",
            )
        )
    if infeasible_high_risk_states is not None:
        lines.append(
            "High-risk inputs with no feasible physical/rate-limited one-step interval: "
            f"{infeasible_high_risk_states}"
        )
        lines.append(
            "Actionable high-risk states: "
            f"{summary.eligible_high_risk_states - infeasible_high_risk_states}"
        )
    if run_configuration:
        lines.extend(("", "## Recourse search configuration", ""))
        lines.extend(
            f"- `{name}`: `{value}`" for name, value in sorted(run_configuration.items())
        )
    lines.extend(
        ("", "## Latency", "", "| Stage | Mean ms | P95 ms | Status |", "|---|---:|---:|---|")
    )
    for name, metric in summary.latency.items():
        status = "unmeasured" if metric.passed is None else ("pass" if metric.passed else "fail")
        lines.append(
            f"| {name} | {_format_metric(metric.mean_ms)} | "
            f"{_format_metric(metric.p95_ms)} | {status} |"
        )
    lines.extend(
        (
            "",
            "Model validity and physical plausibility are reported separately; "
            "sparse-action feasibility is shown independently.",
            "C-MAPSS is static run-to-failure data and does not establish RUL extension.",
            "",
        )
    )
    return "\n".join(lines)
