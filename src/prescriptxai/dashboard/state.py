"""Parsing and validation of uploaded raw-unit machine state documents."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

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
        request = RecourseRequest(state={str(name): float(value) for name, value in raw.items()})
    except (TypeError, ValueError) as error:
        raise ValueError("state values must be finite numbers") from error
    return request.state
