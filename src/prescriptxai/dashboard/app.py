"""Five-page operator dashboard using frozen library decisions and real saved evidence."""

from __future__ import annotations

import os
from collections.abc import MutableMapping
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, cast

import streamlit as st

from prescriptxai.config import load_config
from prescriptxai.dashboard.backend import (
    Backend,
    OperatorError,
    computation_pool,
    profile_identity,
)
from prescriptxai.dashboard.data import file_identity, observed_state, telemetry
from prescriptxai.dashboard.objectives import objectives_page
from prescriptxai.dashboard.operator import operator_console
from prescriptxai.dashboard.pages import PAGES, about_page, evidence_page, fleet_page
from prescriptxai.dashboard.state import load_settings, select_session
from prescriptxai.machine_spec import MachineSpec


def main(*, advanced: bool = False, spec: MachineSpec | None = None) -> None:
    """Run the local operator workflow without training, mutable thresholds or sample results."""
    started = perf_counter()
    loading_seconds = 0.0
    if not advanced:
        st.set_page_config(page_title="PrescriptXAI", page_icon="⚙", layout="wide")
    st.title("PrescriptXAI · Maintenance Decision Support")
    st.warning(
        "Model-based validity is not physical validity. No RUL extension is claimed on "
        "static datasets. Actuator limits are proxy assumptions on C-MAPSS. This tool "
        "does not establish real-machine safety or RUL extension."
    )
    st.info(
        "Configured controllable channels are C-MAPSS telemetry proxies, not verified "
        "actuator commands. Bounds, rates and intervention horizon K are assumptions."
    )
    if not advanced and "pending_fleet_engine" in st.session_state:
        st.session_state["page"] = PAGES[0]
    pages = PAGES[1:] if advanced else PAGES
    if spec is not None:
        pages = (*pages, "Objectives scorecard")
    page = st.sidebar.radio("Page", pages, key="advanced-page" if advanced else "page")
    if page == PAGES[4]:
        about_page()
        if spec is not None:
            st.write(spec.limits_label)
        return
    try:
        settings = load_settings(
            Path(os.environ.get("PRESCRIPTXAI_DASHBOARD_CONFIG", "configs/dashboard.yaml"))
        )
        if page == "Objectives scorecard" and spec is not None:
            objectives_page(spec, settings.report_directory)
            return
        subset = st.sidebar.selectbox("Subset", list(settings.profiles), key="subset")
        profile = st.sidebar.selectbox(
            "Model / protocol", list(settings.profiles[subset]), key="profile"
        )
        path = settings.profiles[subset][profile]
        loading_started = perf_counter()
        identity = profile_identity(path)
        backend = Backend(path, identity, settings)
        with st.spinner("Loading the selected trusted artifacts…"):
            info = computation_pool().submit(backend.info).result()
        config = load_config(path)
        loading_seconds += perf_counter() - loading_started
        mode = cast(
            Literal["fast", "thorough"],
            st.sidebar.radio("Mode", ["fast", "thorough"], format_func=str.upper, key="mode"),
        )
        st.sidebar.caption(f"Backend: {settings.backend} · thresholds are read-only")
        st.sidebar.write(f"Alert τ = {info['tau_danger']} · Safe τ = {info['tau_safe']}")
        st.sidebar.write(
            f"D_max = {info['D_max']} · k_max = {config.recourse.k_max} · "
            f"assumed K = {config.recourse.rate_horizon_steps}"
        )
        st.sidebar.caption(
            "Protocol/model selection loads prior committed settings; no tuning occurs."
        )
        loading_started = perf_counter()
        data_identity = file_identity(settings.telemetry_path)
        with st.spinner("Loading observed telemetry…"):
            frame = (
                computation_pool()
                .submit(
                    telemetry,
                    str(settings.telemetry_path),
                    subset,
                    settings.telemetry_population,
                    data_identity,
                )
                .result()
            )
        loading_seconds += perf_counter() - loading_started
        st.caption(
            f"Replay source: {settings.telemetry_path.name} · {settings.telemetry_population} "
            "observations · no new generalization claim"
        )
        engines = sorted(int(v) for v in frame.engine_id.unique())
        if "pending_fleet_engine" in st.session_state:
            st.session_state["engine"] = st.session_state.pop("pending_fleet_engine")
        engine_id = st.sidebar.selectbox("Engine", engines, key="engine")
        available = frame.loc[frame.engine_id == engine_id, "cycle"]
        lo, hi = int(available.min()), int(available.max())
        pending_cycle = st.session_state.pop("pending_fleet_cycle", None)
        if pending_cycle is not None:
            st.session_state["cycle"] = pending_cycle
        if "cycle" not in st.session_state:
            st.session_state["cycle"] = hi
        if "cycle" in st.session_state and not lo <= st.session_state["cycle"] <= hi:
            st.session_state["cycle"] = hi
        cycle = st.sidebar.slider("Cycle", lo, hi, key="cycle") if lo < hi else lo
        recompute = st.sidebar.button("Recompute", key="recompute")
        st.sidebar.caption(f"Model: {info['model_version']} · profile: {path}")
        st.sidebar.caption(f"Profile config hash: {info['config_hash']}")
        st.sidebar.caption(f"Predictor training source: {info['model_git_hash'] or 'unrecorded'}")
        session = cast(MutableMapping[str, Any], st.session_state)
        select_session(
            session,
            (
                identity,
                data_identity,
                subset,
                profile,
                engine_id,
                cycle,
                mode,
                settings.backend,
                settings.api_url,
            ),
        )
        st.session_state["selected_observation"] = (engine_id, cycle)
        model = {"xgboost": "xgb", "torch": "mlp", "lstm": "lstm"}[str(info["model_choice"])]
        if page == PAGES[1]:
            selected = fleet_page(
                backend, frame, cycle, info, mode, allow_recommendation=not advanced
            )
            if selected is not None:
                st.session_state["pending_fleet_engine"] = selected
                st.session_state["pending_fleet_cycle"] = cycle
                st.session_state["pending_fleet_recommend"] = True
                st.rerun()
            return
        if page in (PAGES[2], PAGES[3]):
            evidence_page(backend, subset, model, info, page == PAGES[2])
            return
        st.header(PAGES[0])
        state, context = observed_state(frame, engine_id, cycle, info)
        history = frame.loc[(frame.engine_id == engine_id) & (frame.cycle <= cycle)]
        excluded = operator_console(
            backend,
            history,
            state,
            context,
            info,
            config,
            mode,
            recompute or st.session_state.pop("pending_fleet_recommend", False),
        )
        render_ms = max(0, (perf_counter() - started - excluded - loading_seconds) * 1000)
        upper = config.latency_budget.dashboard_max_ms
        st.caption(
            f"Server UI build: {render_ms:.2f} ms · upper budget {upper:g} ms · "
            f"{'within' if render_ms <= upper else 'over'} this call. "
            "Excludes loading/scoring/solve/attribution, browser paint and network; "
            "not a browser p95 certification."
        )
    except (OperatorError, ValueError, OSError, KeyError) as error:
        st.error(f"Operator request unavailable: {error}")
        st.info(
            "No action is accepted from this failed request. Check the selected observed "
            "history and trusted artifact/config files, or schedule maintenance review."
        )


if __name__ == "__main__":
    main()
