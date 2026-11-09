"""Versioned metadata for replay presets selected from archived results."""

from __future__ import annotations

import yaml
from pydantic import BaseModel, ConfigDict, Field

from prescriptxai.adapters.registry import MachineRegistry


class Scenario(BaseModel):
    """An observed preset with a saved observation identifier."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    time: float
    case_id: str = Field(pattern=r"^[0-9a-f]{64}$")


def scenario_presets(
    registry: MachineRegistry, machine_id: str, population: str, spec_hash: str
) -> list[Scenario]:
    """Read the registered, machine-bound preset manifest when available."""
    path = registry.root / machine_id / "scenarios.yaml"
    if not path.is_file():
        return []
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != 1
        or document.get("machine_id") != machine_id
        or document.get("spec_hash") != spec_hash
        or document.get("population") != population
    ):
        raise ValueError("Saved examples do not match this machine and data source")
    records = document.get("scenarios")
    if not isinstance(records, list):
        raise ValueError("Saved examples are unavailable for this machine")
    return [Scenario.model_validate(row) for row in records]
