"""Discover and open locally configured machines."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import yaml

from prescriptxai.adapters.base import DatasetAdapter
from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.tabular import TabularAdapter
from prescriptxai.machine_spec import MACHINE_ID_PATTERN, MachineSpec

DEFAULT_MACHINE = "cmapss_fd001"


class MachineRegistry:
    """Resolve machines by validated ID with a packaged default fallback."""

    def __init__(self, root: Path = Path("configs/machines"), workspace: Path = Path(".")) -> None:
        self.root = root
        self.workspace = workspace

    def spec_bytes(self, machine_id: str) -> bytes:
        """Read the authoritative local or packaged spec bytes."""
        if re.fullmatch(MACHINE_ID_PATTERN, machine_id) is None:
            raise ValueError(f"invalid machine ID: {machine_id!r}")
        path = self.root / machine_id / "machine.yaml"
        if path.is_file():
            return path.read_bytes()
        if machine_id == DEFAULT_MACHINE:
            return files("prescriptxai").joinpath(
                "resources/machines/cmapss_fd001/machine.yaml"
            ).read_bytes()
        raise KeyError(machine_id)

    @staticmethod
    def parse_spec(machine_id: str, contents: bytes) -> MachineSpec:
        """Validate the configuration and its registered identity."""
        spec = MachineSpec.model_validate(yaml.safe_load(contents.decode("utf-8")))
        if spec.machine_id != machine_id:
            raise ValueError(f"registered machine ID differs from spec ID: {machine_id}")
        return spec

    def get(self, machine_id: str) -> MachineSpec:
        """Read and validate the current registered spec."""
        return self.parse_spec(machine_id, self.spec_bytes(machine_id))

    def list(self) -> tuple[MachineSpec, ...]:
        """List local machines and the packaged default in stable order."""
        names = {path.parent.name for path in self.root.glob("*/machine.yaml")}
        return tuple(self.get(name) for name in sorted(names | {DEFAULT_MACHINE}))

    def open(self, machine_id: str) -> DatasetAdapter:
        """Build the declared data adapter for a registered machine."""
        spec = self.get(machine_id)
        adapter = CmapssAdapter if spec.dataset.adapter == "cmapss" else TabularAdapter
        return adapter(spec, self.workspace)
