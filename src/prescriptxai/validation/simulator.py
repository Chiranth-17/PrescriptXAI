"""Optional validated-emulator/physics-simulator adapter; no dynamic evidence is fabricated."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from prescriptxai.validation.base import TierResult


@dataclass(frozen=True)
class SimulatorResult(TierResult):
    """An adapter result declaring E4 emulator or E5 validated physics evidence."""


class DynamicSimulator(Protocol):
    """Abstract application hook; adapters must document held-out validation and provenance."""

    def validate_candidate(self, state: Mapping[str, float]) -> SimulatorResult:
        """Validate a trajectory without asserting RUL extension from static telemetry."""
        ...


class NullSimulator:
    """Unavailable simulator that always reports skipped, never pass."""

    def validate_candidate(self, state: Mapping[str, float]) -> SimulatorResult:
        """Grant no dynamic evidence for an arbitrary candidate state."""
        del state
        return SimulatorResult(False, ("skipped: no simulator",), status="skipped")


def run_simulator_validation(
    state: Mapping[str, float],
    enabled: bool,
    simulator: DynamicSimulator | None,
) -> SimulatorResult:
    """Invoke only an explicitly enabled adapter; otherwise return an explicit skipped tier."""
    if not enabled or simulator is None:
        return NullSimulator().validate_candidate(state)
    result = simulator.validate_candidate(state)
    if result.valid and result.evidence_level not in {"E4", "E5"}:
        raise ValueError("a passing dynamic adapter must declare validated E4 or E5 evidence")
    return result
