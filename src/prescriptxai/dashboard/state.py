"""Parsing and validation of uploaded raw-unit machine state documents."""

from __future__ import annotations

import json
from collections.abc import MutableMapping
from io import StringIO
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field

from prescriptxai.config import FollowUpSettings
from prescriptxai.schemas import RecourseRequest


def parse_state_document(text: str, filename: str, required_features: set[str]) -> dict[str, float]:
    """Parse the first CSV row or one flat JSON object and validate required features."""
    suffix = Path(filename).suffix.casefold()
    if suffix == ".json":
        raw: Any = json.loads(text)
    elif suffix == ".csv":
        frame = pd.read_csv(StringIO(text))
        if len(frame) != 1:
            raise ValueError("CSV upload must contain exactly one state row")
        raw = frame.iloc[0].to_dict()
    else:
        raise ValueError("state file must be JSON or CSV")
    if not isinstance(raw, dict):
        raise ValueError("state document must contain one flat object")
    missing = required_features - set(raw)
    if missing:
        raise ValueError(f"state is missing configured fields: {sorted(missing)}")
    try:
        request = RecourseRequest.model_validate({"state": raw})
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("state values must be finite numbers") from error
    return request.state


class DashboardSettings(BaseModel):
    """Trusted local source configuration; thresholds remain in committed study profiles."""

    model_config = ConfigDict(extra="forbid")
    backend: Literal["direct", "api"] = "direct"
    api_url: str = "http://127.0.0.1:8000"
    api_key_env: str = "PRESCRIPTXAI_API_KEY"
    timeout_seconds: float = Field(default=120, gt=0)
    telemetry_path: Path = Path("data/raw/CMAPSSData.zip")
    telemetry_population: Literal["train", "test"] = "test"
    report_directory: Path = Path("artifacts/experiments/phase7-20261020T102540Z")
    profiles: dict[str, dict[str, Path]]
    follow_up: FollowUpSettings = Field(default_factory=FollowUpSettings)


def load_settings(path: Path) -> DashboardSettings:
    """Read local dashboard configuration without fitting or modifying scientific settings."""
    return DashboardSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def select_session(session: MutableMapping[str, Any], identity: tuple[object, ...]) -> bool:
    """Discard result/preview/control widgets whenever any authoritative selection changes."""
    if session.get("selection_identity") == identity:
        return False
    for key in list(session):
        if key in {
            "solver_result",
            "preview_result",
            "preview_controls",
            "contributions",
        } or key.startswith("control:"):
            del session[key]
    session["selection_identity"] = identity
    return True


def save_result(session: MutableMapping[str, Any], result: str) -> None:
    """Keep solved and edited results separate, resetting sliders on explicit recompute."""
    for key in list(session):
        if key.startswith("control:") or key in {"contributions", "preview_controls"}:
            del session[key]
    session["solver_result"] = result
    session["preview_result"] = result
