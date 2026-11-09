"""Display machine-scoped historical objectives and independent serial timings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from prescriptxai.adapters.registry import DEFAULT_MACHINE
from prescriptxai.dashboard.backend import OperatorError
from prescriptxai.dashboard.data import file_identity, saved_json
from prescriptxai.machine_spec import MachineSpec

METRICS = {
    "validity": "Calibrated model validity",
    "plausibility_all": "Statistical plausibility, all queries",
    "plausibility_returned": "Statistical plausibility, returned candidates",
    "tier3": "Proxy control limits",
    "tier4": "Sensor consistency",
    "joint": "Joint success",
    "sparsity_all": "Mean number of changed parameters, all queries",
    "sparsity_returned": "Mean number of changed parameters, returned candidates",
    "risk_reduction": "Mean predicted risk drop",
    "NO_INTERVENTION": "No action needed",
    "RECOVERABLE": "Fixable now",
    "PARTIAL": "Partly fixable",
    "ESCALATE": "Needs maintenance",
}


def objective_rows(summary: dict[str, Any], group: str) -> pd.DataFrame:
    """Use saved all-alert and same-mode first-alert estimates and their engine intervals."""
    data = summary["groups"][group]
    targets = summary["manifest"]["configuration"]["targets"]
    first = data["strata"]["first_alert_versus_all_same_mode"]["first_alert"]
    all_alerts = {name: value["ci"] for name, value in data["metrics"].items()}
    rows = []
    for population, measurements in (("All alerts", all_alerts), ("First alert", first)):
        for name, label in METRICS.items():
            ci = measurements.get(name)
            if ci is None:
                continue
            value, target = ci["estimate"], targets.get(name)
            upper = name == "sparsity_all"
            status = "No saved target"
            if target is not None:
                if value is None:
                    status = "Unavailable for this denominator"
                elif upper:
                    status = "Met" if value <= target else "Mean action count exceeds target"
                else:
                    status = "Met" if value >= target else "Measured result is below target"
            rows.append(
                {
                    "Population": population,
                    "Objective": label,
                    "Measured": value,
                    "Target": target,
                    "CI lower": ci["lower"],
                    "CI upper": ci["upper"],
                    "Engines": ci["engine_count"],
                    "Denominator": ci["denominator"],
                    "Finding": status,
                }
            )
    return pd.DataFrame(rows)


def _latency(summary: dict[str, Any]) -> None:
    st.subheader("Historical serial latency")
    latency = summary.get("latency")
    if not latency:
        st.info("This archive has no saved serial measurements.")
        return
    st.caption(f"{latency['scope']} · separate benchmark population")
    st.json(latency["labels"], expanded=False)
    for mode, stages in latency["modes"].items():
        rows = []
        for stage, value in stages.items():
            interval = value["p95_engine_ci"] or {}
            measured = value["p95_ms"]
            status = (
                "Unmeasured"
                if measured is None
                else ("Within budget" if value["passed"] else "Measured p95 exceeds budget")
            )
            rows.append(
                {
                    "Stage": stage,
                    "p95 (ms)": measured,
                    "Upper budget (ms)": value["upper_budget_ms"],
                    "CI lower": interval.get("lower"),
                    "CI upper": interval.get("upper"),
                    "Engines": value["engine_count"],
                    "Finding": status,
                }
            )
        st.write(mode)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def objectives_page(spec: MachineSpec, directory: Path) -> None:
    """Expose only evidence attributable to this machine's historical archive."""
    st.header("Objectives scorecard")
    st.caption(f"{spec.display_name} · {spec.machine_id} · active spec {spec.spec_hash}")
    if spec.machine_id != DEFAULT_MACHINE or not spec.dataset.subset:
        st.info("There is no registered historical scorecard for this machine.")
        return
    try:
        path = directory / "summary.json"
        summary = saved_json(str(path), file_identity(path))
        choices = [
            name
            for name in summary["groups"]
            if name.startswith(f"{spec.dataset.subset}/")
            and name.split("/")[2] in spec.validation.plausibility
            and name.endswith("_all_alerts/fast/full")
            and "/development_" not in name
        ]
        if not choices:
            st.info("No saved held-out FAST alert groups match this machine.")
            return
        official = next((idx for idx, name in enumerate(choices) if "/official_test_" in name), 0)
        group = st.selectbox("Saved benchmark group", choices, index=official)
        manifest = summary["manifest"]
        st.caption(f"Run {manifest['run_id']} · measured source {manifest['git_hash']}")
        st.json(summary["groups"][group]["labels"], expanded=False)
        st.info(
            "The saved study predates machine specs. Its intervals resample whole engines. "
            "First-alert results use the same FAST mode; only saved first-alert metrics are shown. "
            "Model validity and plausibility are separate. The archive supports proxy evidence."
        )
        st.dataframe(objective_rows(summary, group), hide_index=True, width="stretch")
        _latency(summary)
    except (OperatorError, TypeError, ValueError, KeyError) as error:
        st.warning(f"Saved objective evidence unavailable or invalid: {error}")
