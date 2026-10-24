"""Fleet and evidence pages consume observed telemetry and unchanged saved Phase 7 results."""

from __future__ import annotations

import json
from typing import Any, Literal

import pandas as pd
import streamlit as st

from prescriptxai.dashboard.backend import Backend, OperatorError, computation_pool
from prescriptxai.dashboard.data import file_identity, saved_json, score_observations
from prescriptxai.dashboard.plots import calibration_chart, evidence_bars
from prescriptxai.schemas import RecourseResult

PAGES = (
    "Operator Console",
    "Fleet Overview",
    "Model and Validation Diagnostics",
    "Evaluation Results",
    "About and Limitations",
)


def fleet_page(
    backend: Backend,
    frame: pd.DataFrame,
    cycle: int,
    info: dict[str, Any],
    mode: Literal["fast", "thorough"],
) -> int | None:
    """Rank every observed engine, retaining engines unavailable at the exact chosen cycle."""
    st.header("Fleet Overview")
    st.caption(
        "Risk ranking is not a validated recommendation. Triage is unassessed until a solve."
    )
    with st.spinner("Scoring the observed fleet in a background worker…"):
        scored = (
            computation_pool()
            .submit(
                score_observations,
                frame,
                str(backend.path),
                backend.identity,
                backend.settings.model_dump_json(),
                json.dumps(info),
                mode,
                cycle,
            )
            .result()
        )
    engines = pd.DataFrame({"engine_id": sorted(frame.engine_id.unique())})
    ranking = engines.merge(scored, how="left", on="engine_id")
    ranking["availability"] = ranking["availability"].fillna("No observation at chosen cycle")
    ranking["triage"] = ranking["triage"].fillna("Unavailable")
    raw = st.session_state.get("preview_result")
    if raw:
        result = RecourseResult.model_validate_json(raw)
        selection = st.session_state.get("selected_observation")
        if selection and selection[1] == cycle:
            ranking.loc[ranking.engine_id == selection[0], "triage"] = result.status
    st.dataframe(
        ranking.sort_values("risk", ascending=False, na_position="last"),
        hide_index=True,
        width="stretch",
    )
    candidates = [int(v) for v in ranking.loc[ranking.risk.notna(), "engine_id"]]
    if not candidates:
        st.info("No assessable engines at this cycle, including required genuine history.")
        return None
    selected = st.selectbox("Fleet engine to recommend", candidates, key="fleet_engine")
    return (
        int(selected)
        if st.button("Recommend selected fleet engine", key="fleet_recommend")
        else None
    )


def metric_rows(summary: dict[str, Any], subset: str, model: str) -> pd.DataFrame:
    """Flatten real group measurements with full denominators and engine-bootstrap CIs."""
    manifest = summary["manifest"]
    targets = manifest["configuration"]["targets"]
    rows = []
    for group, data in summary["groups"].items():
        if not group.startswith(f"{subset}/{model}/"):
            continue
        labels = data["labels"]
        for metric, value in data["metrics"].items():
            ci = value["ci"]
            estimate, target = ci["estimate"], targets.get(metric)
            higher = metric != "sparsity_all"
            gap = (
                None
                if target is None or estimate is None
                else max(0, target - estimate if higher else estimate - target)
            )
            rows.append(
                {
                    "group": group,
                    "metric": metric,
                    "design_target": target,
                    "comparison": ">=" if higher else "<=",
                    "measured": estimate,
                    "gap_to_target": gap,
                    "CI_lower": ci["lower"],
                    "CI_upper": ci["upper"],
                    "engines": ci["engine_count"],
                    "denominator": ci.get("denominator"),
                    "observations": ci["observation_count"],
                    "run_id": manifest["run_id"],
                    "source": manifest["git_hash"],
                    "evidence_levels_observed": "; ".join(
                        labels.get("evidence_level", ["unrecorded"])
                    ),
                    **{
                        k: "; ".join(map(str, labels[k]))
                        for k in (
                            "config_path",
                            "config_hash",
                            "protocol",
                            "k_max",
                            "K",
                            "D_max",
                            "population",
                        )
                    },
                }
            )
    return pd.DataFrame(rows)


def evidence_page(
    backend: Backend, subset: str, model: str, info: dict[str, Any], diagnostics: bool
) -> None:
    """Show saved diagnostics/evaluation with explicit unavailable data and historical scope."""
    st.header(PAGES[2] if diagnostics else PAGES[3])
    directory = backend.settings.report_directory
    summary_path = directory / "summary.json"
    try:
        summary = saved_json(str(summary_path), file_identity(summary_path))
    except OperatorError as error:
        st.warning(str(error))
        return
    manifest = summary["manifest"]
    st.caption(
        f"Run {manifest['run_id']} · measured source {manifest['git_hash']} · "
        f"study {manifest['study_path']} · complete={summary.get('complete')}"
    )
    st.info(
        "Historical populations are not fresh independent generalization. Every interval "
        "bootstraps whole engines; failed queries remain in reported denominators."
    )
    rows = metric_rows(summary, subset, model)
    if rows.empty:
        st.warning("No saved evaluation groups for the selected dataset/model.")
        return
    if not diagnostics:
        st.subheader("Design target / measured / gap · all populations and protocols")
        st.dataframe(
            rows.loc[
                rows.design_target.notna()
                | rows.metric.isin(["tier3", "tier4", "joint", "joint_tiers"])
            ],
            hide_index=True,
            width="stretch",
        )
        with st.expander("All metrics, sensitivity runs and paired ablations"):
            st.dataframe(rows, hide_index=True, width="stretch")
        st.download_button(
            "Download measured results CSV",
            rows.to_csv(index=False),
            "phase7-measured-results.csv",
            "text/csv",
        )
        st.subheader("Serial latency · p95 versus upper budgets")
        st.json(summary.get("latency", {}))
        return
    model_diagnostics = info.get("model_diagnostics", {})
    calibration_source = model_diagnostics.get("calibration", {})
    calibration = calibration_source.get(
        "test_after", calibration_source.get("validation_after", {})
    )
    if calibration.get("reliability_curve"):
        st.plotly_chart(calibration_chart(calibration["reliability_curve"]), width="stretch")
        st.caption(
            "Saved held-out test bins; calibrator fitted on separate validation engines."
            if "test_after" in calibration_source
            else "Saved calibrator-fit validation bins; these are in-sample calibration "
            "diagnostics, not independent test evidence."
        )
    else:
        st.info("Saved calibration bins unavailable for this artifact.")
    st.subheader("Learned coupling fit and residual evidence")
    if info.get("coupling_diagnostics"):
        st.json(info["coupling_diagnostics"])
    else:
        st.info("Learned coupling diagnostics unavailable; YAML rules are not a physics simulator.")
    available = [
        k for k in summary["groups"] if k.startswith(f"{subset}/{model}/") and k.endswith("/full")
    ]
    group = st.selectbox(
        "Diagnostic population / protocol / mode", available, key="diagnostic_group"
    )
    data = summary["groups"][group]
    st.json(data["labels"])
    st.caption(
        f"Engines {data['engines']} · query/seed observations {data['query_seed_observations']}"
    )
    quantiles = data["D_M_quantiles"]
    st.plotly_chart(
        evidence_bars(
            list(quantiles), list(quantiles.values()), "Saved Mahalanobis distribution quantiles"
        ),
        width="stretch",
    )
    funnel = data["funnel"]
    st.plotly_chart(
        evidence_bars(
            list(funnel),
            [v["count"] for v in funnel.values()],
            "Acceptance funnel · retained failed queries",
        ),
        width="stretch",
    )
    st.dataframe(
        pd.DataFrame([{"stage": k, "count": v["count"], **v["ci"]} for k, v in funnel.items()]),
        hide_index=True,
        width="stretch",
    )
    protocol = data["labels"]["protocol"][0]
    st.subheader(f"Constraint ladder · saved paired diagnostic population · {protocol}")
    ladder = rows.loc[
        rows["group"].map(lambda name: name.rsplit("/", 1)[-1].startswith("L"))
        & (rows.protocol == protocol)
    ].copy()
    if ladder.empty:
        st.info("No saved constraint-ladder runs for this model/protocol; none are inferred.")
    else:
        ladder["step"] = ladder["group"].str.rsplit("/", n=1).str[-1]
        ladder_metric = st.selectbox(
            "Ladder metric", sorted(ladder.metric.unique()), key="ladder_metric"
        )
        selected_ladder = ladder.loc[ladder.metric == ladder_metric].sort_values("step")
        st.plotly_chart(
            evidence_bars(
                selected_ladder.step.tolist(),
                selected_ladder.measured.tolist(),
                f"Constraint ladder · {ladder_metric} · {protocol}",
            ),
            width="stretch",
        )
        st.dataframe(selected_ladder, hide_index=True, width="stretch")
    k_rows = []
    for name, item in summary["groups"].items():
        if name.startswith(f"{subset}/{model}/{protocol}/") and "sensitivity-horizon-K-" in name:
            k_rows.append(
                {
                    "group": name,
                    "K": int(item["labels"]["K"][0]),
                    "protocol": protocol,
                    "population": "; ".join(item["labels"]["population"]),
                    "config_hash": "; ".join(item["labels"]["config_hash"]),
                    "D_max": "; ".join(item["labels"]["D_max"]),
                    **item["metrics"]["validity"]["ci"],
                }
            )
    if k_rows:
        curve = pd.DataFrame(k_rows).sort_values("K")
        st.subheader(f"Validity versus assumed intervention horizon K · {protocol} · includes K=1")
        st.line_chart(curve, x="K", y="estimate")
        st.dataframe(curve, hide_index=True, width="stretch")
    else:
        st.info("No saved K sensitivity data for this model; no curve is inferred.")


def about_page() -> None:
    """Keep the evidence limits and reproducible source of dashboard values visible."""
    st.header("About and Limitations")
    st.markdown("""
PrescriptXAI generates sparse proxy-control candidates and checks true calibrated model risk,
statistical plausibility, engineering bounds/rates and learned sensor relationships separately.

- **E1:** model-based validity; **E2:** statistical plausibility; **E3:** proxy engineering checks.
- **E4/E5:** no validated emulator or physics simulator is available in this dashboard.
- C-MAPSS is static. Sensor channels are actuator proxies; limits and intervention horizon K
  are documented assumptions. Plausibility is not physical proof, and validity is model-based.
- No RUL extension, causal machine response or deployment safety is established.
- Predictor selection uses predictive/calibration metrics, never recourse outcomes.
- Historical measurements retain their source, protocol, engine counts and denominators.

See `docs/assumptions.md`, `docs/evidence_levels.md`, `docs/limitations.md`,
`docs/evaluation_protocol.md` and `docs/phase7_changes.md`. Exports carry the current result's
complete validation and provenance; an ESCALATE candidate is diagnostic, not an instruction.
""")
