"""Machine-scoped inputs for the local replay simulator."""

from __future__ import annotations

import json
from collections.abc import Mapping
from random import Random

import pandas as pd
import streamlit as st

from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.core.decision import MachineDecision
from prescriptxai.dashboard.backend import direct_service, profile_identity
from prescriptxai.dashboard.state import DashboardSettings
from prescriptxai.machines import resolve_machine_decision
from prescriptxai.pipeline import PrescriptXAI


@st.cache_data(show_spinner=False, max_entries=8)
def observed_rows(machine_id: str, spec_hash: str, population: str, identity: str) -> pd.DataFrame:
    """Load canonical observed rows for the selected trusted data snapshot."""
    adapter = MachineRegistry().open(machine_id)
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


def simulated_settings(
    original: Mapping[str, float],
    prescription: Mapping[str, float],
    seed: int,
    count: int,
) -> list[dict[str, float]]:
    """Draw reproducible compliance fractions and interpolate named applied settings."""
    generator = Random(seed)
    return [
        {
            name: original[name] + fraction * (value - original[name])
            for name, value in prescription.items()
        }
        for fraction in (generator.random() for _ in range(count))
    ]


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
