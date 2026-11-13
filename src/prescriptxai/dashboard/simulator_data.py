"""Machine-scoped inputs for the local replay simulator."""

from __future__ import annotations

import json
from collections.abc import Mapping
from concurrent.futures import CancelledError, ProcessPoolExecutor, wait
from hashlib import sha256
from inspect import getfile
from math import isclose
from multiprocessing import get_context
from pathlib import Path
from threading import Event

import pandas as pd
import streamlit as st

from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.core.data_quality import RecommendationWithheld
from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.backend import direct_service, profile_identity
from prescriptxai.dashboard.state import DashboardSettings, load_settings
from prescriptxai.evaluation.runner import _worker_threads
from prescriptxai.machine_schema import MachineRecourseResult
from prescriptxai.machine_spec import MachineSpec
from prescriptxai.machines import resolve_machine_decision
from prescriptxai.pipeline import PrescriptXAI


@st.cache_data(show_spinner=False, max_entries=16)
def _parsed_spec(machine_id: str, contents: bytes) -> MachineSpec:
    return MachineRegistry.parse_spec(machine_id, contents)


class SimulatorRegistry(MachineRegistry):
    """Cache parsed specs by their authoritative bytes."""

    def get(self, machine_id: str) -> MachineSpec:
        """Load the current bytes and reuse their validated representation."""
        return _parsed_spec(machine_id, self.spec_bytes(machine_id))


@st.cache_data(show_spinner=False, max_entries=8)
def simulator_settings(path: Path, identity: str) -> DashboardSettings:
    """Cache parsed dashboard settings under the file content hash."""
    del identity
    return load_settings(path)


@st.cache_data(show_spinner=False, max_entries=8)
def observed_rows(machine_id: str, spec_hash: str, population: str, identity: str) -> pd.DataFrame:
    """Load canonical observed rows for the selected trusted data snapshot."""
    adapter = SimulatorRegistry().open(machine_id)
    if adapter.spec.spec_hash != spec_hash:
        raise ValueError("The machine configuration changed while loading observations")
    del identity  # Content identity participates in the cache key.
    if isinstance(adapter, CmapssAdapter) and population == "test":
        return adapter.load_official()
    return adapter.load()


def simulator_decision(
    registry: MachineRegistry,
    machine_id: str,
    settings: DashboardSettings,
    *,
    isolated: bool = False,
) -> MachineDecision:
    """Load the named fit or the first compatible configured archive profile."""
    spec = registry.get(machine_id)
    protocol = next(iter(spec.validation.plausibility))
    profiles = settings.profiles.get(spec.dataset.subset or "", {})
    profile = next(
        (path for label, path in profiles.items() if label.rsplit("/", 1)[-1].strip() == protocol),
        None,
    )
    if profile is None:
        return resolve_machine_decision(registry, machine_id, protocol)

    def legacy() -> PrescriptXAI:
        identity = profile_identity(profile)
        if isolated:
            return direct_service(str(profile), identity, isolated=True)
        return direct_service(str(profile), identity)

    return resolve_machine_decision(registry, machine_id, protocol, legacy=legacy)


@st.cache_resource(show_spinner=False)
def prescription_pool(code_identity: str) -> ProcessPoolExecutor:
    """Keep native FAST search and its numerical thread pool outside Streamlit."""
    del code_identity  # Reloading application code must not reuse an older worker interpreter.
    return ProcessPoolExecutor(
        max_workers=1, mp_context=get_context("spawn"), initializer=_worker_threads, initargs=(1,)
    )


def _solve_prescription(
    registry: MachineRegistry,
    machine_id: str,
    settings: DashboardSettings,
    window: pd.DataFrame,
    input_hash: str,
    controls: Mapping[str, float] | None = None,
) -> MachineRecourseResult:
    decision = simulator_decision(registry, machine_id, settings, isolated=True)
    current = dict(controls or {})
    if decision.input_hash(window, current) != input_hash:
        raise RecommendationWithheld("The model or recorded conditions changed")
    starting = decision.simulation_window(window, current) if current else window
    result = decision.recommend(starting, "fast")
    if current and not isclose(
        result.risk_before,
        decision.simulate_risk(window, current).assessment.risk,
        rel_tol=0,
        abs_tol=1e-9,
    ):
        raise RecommendationWithheld("The prescription does not match the current risk preview")
    return result


def solve_prescription(
    registry: MachineRegistry,
    machine_id: str,
    settings: DashboardSettings,
    window: pd.DataFrame,
    input_hash: str,
    cancelled: Event,
    controls: Mapping[str, float] | None = None,
) -> MachineRecourseResult:
    """Submit the bound snapshot and drop stale work without blocking a new session edit."""
    if cancelled.is_set():
        raise CancelledError()
    code_identity = sha256(
        b"".join(
            path.read_bytes()
            for path in (
                Path(__file__),
                Path(getfile(MachineDecision)),
                Path(getfile(PrescriptXAI)),
            )
        )
    ).hexdigest()
    future = prescription_pool(code_identity).submit(
        _solve_prescription,
        MachineRegistry(registry.root, registry.workspace),
        machine_id,
        settings,
        window,
        input_hash,
        dict(controls or {}),
    )
    while not cancelled.is_set():
        if wait((future,), timeout=0.05).done:
            return future.result()
    future.cancel()
    raise CancelledError()


def parse_settings(serialized: str, limits: Mapping[str, tuple[float, float]]) -> dict[str, float]:
    """Restore only finite settings for controls in the current fitted model."""
    if not serialized:
        return {}
    document = json.loads(serialized)
    if not isinstance(document, dict) or set(document) - limits.keys():
        raise ValueError("The link includes settings for a different machine")
    values: dict[str, float] = {}
    for name, value in document.items():
        lower, upper = limits[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not lower <= value <= upper
        ):
            raise ValueError("The link includes a setting outside its allowed range")
        values[name] = float(value)
    return values


def sequential_risks(
    decision: MachineDecision, window: pd.DataFrame, ordered_controls: Mapping[str, float]
) -> tuple[float, ...]:
    """Score successive prefixes from the same observed window and coupling reference."""
    risks = [decision.simulate_risk(window, {}).assessment.risk]
    applied = {}
    for name, value in ordered_controls.items():
        applied[name] = value
        risks.append(decision.simulate_risk(window, applied).assessment.risk)
    return tuple(risks)


def replay_trend(
    decision: MachineDecision,
    observations: pd.DataFrame,
    unit: str,
    time: float,
    applied: Mapping[str, float],
    steps: int,
) -> pd.DataFrame:
    """Re-score recorded future inputs, keeping observations separate from predicted risk."""
    rows = observations.loc[observations["unit_id"].map(str) == unit].sort_values("time_index")
    future = rows.loc[rows["time_index"] > time].head(steps)
    records = []
    for _, row in future.iterrows():
        cycle = float(row["time_index"])
        window = rows.loc[rows["time_index"] <= cycle]
        before = decision.simulate_risk(window, {}).assessment
        after = decision.simulate_risk(window, applied).assessment
        records.append(
            {
                "Recorded time": cycle,
                "Recorded settings (model prediction)": before.risk,
                "Applied settings (model prediction)": after.risk,
                "Safe level": before.tau_safe,
                "Alert level": before.tau_danger,
                "Recorded remaining life": row.get("remaining_life"),
                "Recorded event": row.get("event"),
            }
        )
    return pd.DataFrame(records)
