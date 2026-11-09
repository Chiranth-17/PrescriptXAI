"""Version 3 machine-scoped recourse and feedback records."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from prescriptxai.machine_spec import MACHINE_ID_PATTERN
from prescriptxai.schemas import Assessment, RecourseResult, _RecourseFields

LEGACY_MACHINE_ID = "cmapss_fd001"
HASH_PATTERN = r"^[0-9a-f]{64}$"


class MachineAssessment(Assessment):
    """Observed risk with the provenance needed to label the score."""

    machine_id: str = Field(pattern=MACHINE_ID_PATTERN)
    spec_hash: str = Field(pattern=HASH_PATTERN)
    protocol_version: str
    synthetic: bool


class SimulatedRisk(BaseModel):
    """Input-bound prediction and a statistical context flag for simulated settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment: MachineAssessment
    input_hash: str = Field(pattern=HASH_PATTERN)
    unusual: bool


class MachineRecourseResult(_RecourseFields):
    """A decision with explicit machine, spec and protocol provenance."""

    schema_version: Literal["3.0.0"] = "3.0.0"
    machine_id: str = Field(pattern=MACHINE_ID_PATTERN)
    spec_hash: str | None = Field(pattern=HASH_PATTERN)
    protocol_version: str | None = None
    synthetic: bool

    @classmethod
    def from_decision(
        cls,
        decision: RecourseResult,
        *,
        machine_id: str,
        spec_hash: str | None,
        protocol_version: str | None,
        synthetic: bool,
    ) -> MachineRecourseResult:
        """Preserve the recorded decision and attach versioned machine provenance."""
        return cls.model_validate(
            {
                **decision.model_dump(mode="json", exclude={"schema_version"}),
                "machine_id": machine_id,
                "spec_hash": spec_hash,
                "protocol_version": protocol_version,
                "synthetic": synthetic,
            }
        )


def migrate_recourse_result(record: dict[str, object]) -> MachineRecourseResult:
    """Migrate a v2 row without assigning an unrecorded spec or protocol."""
    if record.get("schema_version") == "3.0.0":
        return MachineRecourseResult.model_validate(record)
    return MachineRecourseResult.from_decision(
        RecourseResult.model_validate(record),
        machine_id=LEGACY_MACHINE_ID,
        spec_hash=None,
        protocol_version=None,
        synthetic=True,
    )


class FeedbackRecord(BaseModel):
    """Versioned advisory follow-up with source and applied-state evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    schema_version: Literal[1] = 1
    machine_id: str = Field(pattern=MACHINE_ID_PATTERN)
    spec_hash: str = Field(pattern=HASH_PATTERN)
    protocol_version: str = Field(min_length=1)
    result_run_id: str = Field(min_length=1)
    recorded_at: datetime
    synthetic: bool
    source: Literal["operator", "simulated_operator"]
    applied: dict[str, float]
    adherence: float = Field(ge=0, le=1)
    action_adherence: dict[str, float]
    applied_risk: float = Field(ge=0, le=1)
    applied_tier_passes: dict[str, bool]
