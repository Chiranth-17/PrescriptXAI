"""Observed telemetry and saved evidence loading; no training/evaluation runtime imports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
import streamlit as st

from prescriptxai.dashboard.backend import Backend, OperatorError
from prescriptxai.dashboard.state import DashboardSettings
from prescriptxai.data.cmapss import load_cmapss_archive, to_model_frame
from prescriptxai.schemas import Assessment, InputContext


def file_identity(path: Path) -> str:
    """Detect changed local data/evidence bytes without retaining a mutable dataframe."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise OperatorError(f"Data source unavailable: {path.name}") from error


@st.cache_data(show_spinner=False, max_entries=8)
def telemetry(path: str, subset: str, population: str, identity: str) -> pd.DataFrame:
    """Read real observed rows, with canonical names and unique increasing unit/cycle pairs."""
    del identity
    source = Path(path)
    try:
        if source.suffix.lower() == ".csv":
            frame = pd.read_csv(source)
        else:
            dataset = load_cmapss_archive(source, subset)
            frame = dataset.train if population == "train" else dataset.test
        frame = to_model_frame(frame)
        if not {"engine_id", "cycle"}.issubset(frame.columns) or frame.empty:
            raise ValueError("Telemetry must contain observed engine_id/cycle rows")
        if frame[["engine_id", "cycle"]].duplicated().any():
            raise ValueError("Duplicate engine/cycle telemetry rows")
        ids = frame[["engine_id", "cycle"]].to_numpy(dtype=float)
        if not np.isfinite(ids).all() or (ids < 1).any() or (ids != np.floor(ids)).any():
            raise ValueError("Engine IDs and cycles must be positive integers")
        return frame.sort_values(["engine_id", "cycle"]).reset_index(drop=True)
    except (OSError, ValueError, KeyError) as error:
        raise OperatorError(f"Cannot load observed telemetry: {error}") from error


def observed_state(
    frame: pd.DataFrame,
    engine_id: int,
    cycle: int,
    info: dict[str, Any],
) -> tuple[dict[str, float], InputContext]:
    """Select known telemetry only and genuine prior same-unit LSTM history in saved order."""
    rows = frame.loc[frame.engine_id == engine_id].sort_values("cycle")
    current = rows.loc[rows.cycle == cycle]
    if len(current) != 1:
        raise OperatorError("Selected engine has no observed telemetry at this cycle")
    features = list(info["feature_names"])
    required = set(features)
    for group in info["feature_groups"].values():
        required.update(group["features"])
    if required - set(current.columns):
        raise OperatorError(
            f"Telemetry missing features: {sorted(required - set(current.columns))}"
        )
    try:
        if any(
            isinstance(v, (bool, np.bool_))
            for v in current[list(required)].to_numpy().ravel().tolist()
        ):
            raise OperatorError("Boolean telemetry is not a physical measurement")
        state = {name: float(current.iloc[0][name]) for name in sorted(required)}
        count = int(info["history_rows"])
        prior = rows.loc[rows.cycle < cycle].tail(count) if count else rows.iloc[:0]
        if len(prior) != count or (
            count and prior.cycle.tolist() != list(range(cycle - count, cycle))
        ):
            raise OperatorError(
                "Genuine contiguous prior LSTM history is unavailable at this cycle"
            )
        history = tuple(tuple(float(v) for v in row) for row in prior[features].to_numpy())
        if any(
            isinstance(v, (bool, np.bool_)) for v in prior[features].to_numpy().ravel().tolist()
        ):
            raise OperatorError("Boolean history is not a physical measurement")
        if not np.isfinite(list(state.values())).all() or not np.isfinite(history).all():
            raise OperatorError("Telemetry/history must contain finite measurements")
        return state, InputContext(
            engine_id=engine_id,
            cycle=cycle,
            feature_names=tuple(features),
            history=history if count else None,
        )
    except (TypeError, ValueError, OverflowError) as error:
        raise OperatorError(str(error)) from error


@st.cache_data(show_spinner=False, max_entries=16)
def saved_json(path: str, identity: str) -> dict[str, Any]:
    """Load copied saved JSON evidence, explicitly rejecting malformed or absent sources."""
    del identity
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("expected an evidence object")
        return value
    except (OSError, ValueError) as error:
        raise OperatorError(f"Saved evidence unavailable: {Path(path).name}: {error}") from error


@st.cache_data(show_spinner=False, max_entries=32)
def score_observations(
    frame: pd.DataFrame,
    path: str,
    identity: str,
    settings_json: str,
    info_json: str,
    mode: Literal["fast", "thorough"],
    target_cycle: int | None = None,
) -> pd.DataFrame:
    """Score supplied actual rows, retaining early/missing-history failures in ranking/trace."""
    backend = Backend(Path(path), identity, DashboardSettings.model_validate_json(settings_json))
    info = json.loads(info_json)
    rows = []
    targets = frame if target_cycle is None else frame.loc[frame.cycle == target_cycle]
    for engine_id, cycle in targets[["engine_id", "cycle"]].itertuples(index=False, name=None):
        engine_id, cycle = int(engine_id), int(cycle)
        try:
            state, context = observed_state(frame, engine_id, cycle, info)
            result = backend.call("assess", state, context, mode)
            assert isinstance(result, Assessment)
            rows.append(
                {
                    "engine_id": engine_id,
                    "cycle": cycle,
                    "risk": result.risk,
                    "triage": "Not assessed",
                    "availability": "Observed",
                }
            )
        except OperatorError as error:
            rows.append(
                {
                    "engine_id": engine_id,
                    "cycle": cycle,
                    "risk": None,
                    "triage": "Unavailable",
                    "availability": str(error),
                }
            )
    return pd.DataFrame(rows, columns=["engine_id", "cycle", "risk", "triage", "availability"])
