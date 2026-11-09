"""Discover and open locally configured machines."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

from prescriptxai.adapters.base import DatasetAdapter
from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.tabular import TabularAdapter
from prescriptxai.machine_spec import MACHINE_ID_PATTERN, MachineSpec, load_machine_spec

DEFAULT_MACHINE = "cmapss_fd001"


class MachineRegistry:
    """Resolve machines by validated ID with a packaged default fallback."""

    def __init__(self, root: Path = Path("configs/machines"), workspace: Path = Path(".")) -> None:
        self.root = root
        self.workspace = workspace

    def get(self, machine_id: str) -> MachineSpec:
        """Read one spec and verify that its internal ID matches its directory."""
        if re.fullmatch(MACHINE_ID_PATTERN, machine_id) is None:
            raise ValueError(f"invalid machine ID: {machine_id!r}")
        path = self.root / machine_id / "machine.yaml"
        if path.is_file():
            spec = load_machine_spec(path)
        elif machine_id == DEFAULT_MACHINE:
            import yaml

            resource = files("prescriptxai").joinpath(
                "resources/machines/cmapss_fd001/machine.yaml"
            )
            spec = MachineSpec.model_validate(yaml.safe_load(resource.read_text(encoding="utf-8")))
        else:
            raise KeyError(machine_id)
        if spec.machine_id != machine_id:
            raise ValueError(f"registered machine ID differs from spec ID: {machine_id}")
        return spec

    def list(self) -> tuple[MachineSpec, ...]:
        """List local machines and the packaged default in stable order."""
        names = {path.parent.name for path in self.root.glob("*/machine.yaml")}
        return tuple(self.get(name) for name in sorted(names | {DEFAULT_MACHINE}))

    def open(self, machine_id: str) -> DatasetAdapter:
        """Build the declared data adapter for a registered machine."""
        spec = self.get(machine_id)
        adapter = CmapssAdapter if spec.dataset.adapter == "cmapss" else TabularAdapter
        return adapter(spec, self.workspace)
