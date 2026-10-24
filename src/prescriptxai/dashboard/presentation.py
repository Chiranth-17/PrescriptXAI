"""Pure result tables and escaped exports for the frozen public schema."""

from __future__ import annotations

import html
import json
from typing import Any

import pandas as pd

from prescriptxai.schemas import RecourseResult


def action_table(result: RecourseResult, info: dict[str, Any]) -> pd.DataFrame:
    """Show action features only; dependent sensor responses are not prescribed controls."""
    rows = []
    for name in result.action_features:
        delta = result.delta_per_feature[name]
        spec = info["feature_metadata"][name]
        rows.append(
            {
                "feature": name,
                "label": spec["label"],
                "unit": spec["unit"],
                "current": result.original_state[name],
                "candidate": result.new_state[name],
                "raw_change": delta.raw_delta,
                "percent_change": delta.percent_change,
                "scaled_change": delta.scaled_delta,
                "lower_bound": spec["bounds"]["minimum"],
                "upper_bound": spec["bounds"]["maximum"],
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "feature",
            "label",
            "unit",
            "current",
            "candidate",
            "raw_change",
            "percent_change",
            "scaled_change",
            "lower_bound",
            "upper_bound",
        ],
    )


def scaled_comparison(result: RecourseResult, info: dict[str, Any]) -> pd.DataFrame:
    """Map both raw states through saved training means/scales and label frozen features."""
    scaling = info["scaling"]
    groups = info["feature_groups"]
    locked = {
        name
        for key, group in groups.items()
        if key.startswith("immutable")
        for name in group["features"]
    }
    rows = []
    for name, mean, scale in zip(
        scaling["feature_names"], scaling["mean"], scaling["scale"], strict=True
    ):
        rows.append(
            {
                "feature": name,
                "locked": name in locked,
                "before": (result.original_state[name] - mean) / scale,
                "after": (result.new_state[name] - mean) / scale,
            }
        )
    return pd.DataFrame(rows)


def result_csv(result: RecourseResult, info: dict[str, Any]) -> str:
    """Keep failure status, evidence and provenance beside every exported action/empty row."""
    table = action_table(result, info)
    if table.empty:
        table = pd.DataFrame([{"feature": None}])
    for name, value in {
        "status": result.status,
        "risk_before": result.risk_before,
        "risk_after": result.risk_after,
        "evidence_level": result.evidence_level,
        "config_hash": result.config_hash,
        "model_version": result.model_version,
        "mode": result.mode,
        "run_id": result.run_id,
        "candidate_kind": "diagnostic" if result.status == "ESCALATE" else "proxy preview",
        "model_valid": result.validation_report.model_valid,
        "plausible": result.plausible,
        "action_feasible": result.action_feasible,
    }.items():
        table[name] = value
    return table.to_csv(index=False)


def printable_summary(result: RecourseResult, info: dict[str, Any]) -> str:
    """Export exactly the displayed result and escape every telemetry/metadata string."""
    heading = (
        "Closest diagnostic candidate" if result.status == "ESCALATE" else "Proxy action preview"
    )
    payload = html.escape(json.dumps(result.model_dump(mode="json"), indent=2))
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>PrescriptXAI summary</title>"
        "<style>body{font:14px sans-serif;margin:3em}table{border-collapse:collapse}"
        "td,th{padding:.5em;border:1px solid #aaa}pre{white-space:pre-wrap}</style></head><body>"
        f"<h1>{heading}: {html.escape(result.status)}</h1>"
        "<p>Model-based validity is not physical validity. No RUL extension is claimed on "
        "static datasets. Actuator limits are proxy assumptions on C-MAPSS.</p>"
        f"<p>Evidence: {html.escape(result.evidence_level)}; "
        f"model: {html.escape(result.model_version)}; mode: {result.mode}; "
        f"config: {result.config_hash}</p>"
        + action_table(result, info).to_html(index=False, escape=True)
        + f"<h2>Complete validation and provenance</h2><pre>{payload}</pre></body></html>"
    )
