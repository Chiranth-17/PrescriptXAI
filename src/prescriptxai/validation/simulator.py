"""Optional dynamic simulator integration contract, disabled by default."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SimulatorResult:
    """Result returned by an application-provided dynamic simulator adapter."""

    valid: bool
    diagnostics: tuple[str, ...]


class DynamicSimulator(Protocol):
    """Application contract for optional candidate trajectory validation."""

    def validate_candidate(self, state: Mapping[str, float]) -> SimulatorResult:
        """Simulate a proposed state and return simulator-specific evidence."""
        ...


def run_simulator_validation(
    state: Mapping[str, float], enabled: bool, simulator: DynamicSimulator | None
) -> SimulatorResult | None:
    """Run an injected simulator only when configuration explicitly enables it."""
    if not enabled:
        return None
    if simulator is None:
        raise RuntimeError("simulator validation is enabled but no simulator adapter was supplied")
    return simulator.validate_candidate(state)
