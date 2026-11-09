"""Machine-prefixed HTTP endpoints using the shared quality and decision boundary."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from statistics import mean
from typing import Literal

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.core.decision import MachineDecision
from prescriptxai.machine_schema import (
    FeedbackRecord,
    MachineAssessment,
    MachineRecourseResult,
    SimulatedRisk,
)
from prescriptxai.machines import (
    machine_summary,
    read_feedback,
    record_feedback,
    resolve_machine_decision,
)
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.scenarios import Scenario, scenario_presets
from prescriptxai.schemas import _reject_nonreal_measurement


class MachineWindowRequest(BaseModel):
    """Canonical observed rows in chronological order."""

    model_config = ConfigDict(extra="forbid")

    rows: list[dict[str, object]] = Field(min_length=1)
    protocol_version: str = "v1"
    mode: Literal["fast", "thorough"] | None = None

    @field_validator("controls", "applied", mode="before", check_fields=False)
    @classmethod
    def require_real_controls(cls, value: object) -> object:
        """Reject control booleans before numeric coercion."""
        if isinstance(value, dict):
            for item in value.values():
                _reject_nonreal_measurement(item, "controls")
        return value


class MachineControlsRequest(MachineWindowRequest):
    """An observed window and the controls to validate."""

    controls: dict[str, float]


class SimulatorRiskRequest(MachineWindowRequest):
    """A local what-if risk request for one named machine."""

    machine_id: str
    controls: dict[str, float] = Field(default_factory=dict)


class SimulatorPrescriptionRequest(MachineWindowRequest):
    """A request to publish a result for the currently shown recorded state."""

    machine_id: str
    input_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class SimulatorPrescription(BaseModel):
    """A named decision with the hash of the observation that produced it."""

    input_hash: str
    decision: MachineRecourseResult


class MachineFeedbackRequest(MachineWindowRequest):
    """An applied control follow-up tied to a specific machine decision."""

    result: MachineRecourseResult
    applied: dict[str, float]
    source: Literal["operator", "simulated_operator"] = "operator"


class SimulatorFeedbackRequest(MachineFeedbackRequest):
    """Machine-selected feedback through the simulator endpoint."""

    machine_id: str


def machine_router(
    registry: MachineRegistry,
    legacy: PrescriptXAI | None,
    artifact_root: Path,
    max_rows: int,
) -> APIRouter:
    """Build named-machine routes with local trusted model loading."""
    router = APIRouter()

    def selected(machine_id: str, request: MachineWindowRequest) -> MachineDecision:
        if len(request.rows) > max_rows:
            raise HTTPException(422, "observed window exceeds the configured row limit")
        try:
            return resolve_machine_decision(
                registry, machine_id, request.protocol_version, artifact_root, legacy
            )
        except KeyError as error:
            raise HTTPException(404, "unknown machine") from error
        except (OSError, ValueError) as error:
            raise HTTPException(503, "machine or protocol runtime unavailable") from error

    @router.get("/machines")
    def machines() -> list[dict[str, object]]:
        return [machine_summary(spec) for spec in registry.list()]

    @router.get("/machines/{machine_id}/spec")
    def machine_spec(machine_id: str) -> dict[str, object]:
        try:
            return registry.get(machine_id).model_dump(mode="json")
        except KeyError as error:
            raise HTTPException(404, "unknown machine") from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @router.get("/machines/{machine_id}/scenarios", response_model=list[Scenario])
    def machine_scenarios(machine_id: str) -> list[Scenario]:
        try:
            spec = registry.get(machine_id)
            return scenario_presets(registry, machine_id, "test", spec.spec_hash)
        except KeyError as error:
            raise HTTPException(404, "unknown machine") from error
        except (OSError, ValueError) as error:
            raise HTTPException(422, str(error)) from error

    @router.post("/simulate/risk", response_model=SimulatedRisk)
    def simulate_risk(request: SimulatorRiskRequest) -> SimulatedRisk:
        service = selected(request.machine_id, request)
        try:
            return service.simulate_risk(pd.DataFrame(request.rows), request.controls)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @router.post("/simulate/prescribe", response_model=SimulatorPrescription)
    def simulate_prescribe(request: SimulatorPrescriptionRequest) -> SimulatorPrescription:
        service = selected(request.machine_id, request)
        rows = pd.DataFrame(request.rows)
        try:
            input_hash = service.input_hash(rows, {})
            if input_hash != request.input_hash:
                raise HTTPException(409, "Recorded conditions have changed")
            result = service.recommend(rows, "fast")
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        return SimulatorPrescription(input_hash=input_hash, decision=result)

    @router.post("/machines/{machine_id}/assess", response_model=MachineAssessment)
    def assess(machine_id: str, request: MachineWindowRequest) -> MachineAssessment:
        service = selected(machine_id, request)
        try:
            return service.assess(pd.DataFrame(request.rows), request.mode)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @router.post("/machines/{machine_id}/recommend", response_model=MachineRecourseResult)
    def recommend(machine_id: str, request: MachineWindowRequest) -> MachineRecourseResult:
        service = selected(machine_id, request)
        try:
            return service.recommend(pd.DataFrame(request.rows), request.mode)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @router.post("/machines/{machine_id}/validate-controls", response_model=MachineRecourseResult)
    def validate_controls(
        machine_id: str, request: MachineControlsRequest
    ) -> MachineRecourseResult:
        service = selected(machine_id, request)
        try:
            return service.validate_controls(
                pd.DataFrame(request.rows), request.controls, request.mode
            )
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @router.post("/machines/{machine_id}/feedback", response_model=FeedbackRecord)
    def feedback(machine_id: str, request: MachineFeedbackRequest) -> FeedbackRecord:
        service = selected(machine_id, request)
        try:
            record = service.feedback(
                pd.DataFrame(request.rows), request.result, request.applied, request.source
            )
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        record_feedback(record, artifact_root / "feedback.sqlite3")
        return record

    @router.post("/feedback", response_model=FeedbackRecord)
    def simulator_feedback(request: SimulatorFeedbackRequest) -> FeedbackRecord:
        return feedback(request.machine_id, request)

    @router.get("/feedback/summary")
    def feedback_summary(
        machine_id: str, protocol_version: str = "v1", include_simulated: bool = False
    ) -> dict[str, object]:
        try:
            spec = registry.get(machine_id)
            records = read_feedback(
                spec,
                protocol_version,
                artifact_root / "feedback.sqlite3",
                include_simulated=include_simulated,
            )
        except KeyError as error:
            raise HTTPException(404, "unknown machine") from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except (OSError, sqlite3.Error) as error:
            raise HTTPException(503, "local feedback log unavailable") from error
        groups = []
        for source, label in (
            ("operator", "Operator (this session)"),
            ("simulated_operator", "Simulated operator (demo)"),
        ):
            if source == "simulated_operator" and not include_simulated:
                continue
            selected_records = [record for record in records if record.source == source]
            groups.append(
                {
                    "source": source,
                    "label": label,
                    "count": len(selected_records),
                    "mean_adherence": (
                        mean(record.adherence for record in selected_records)
                        if selected_records
                        else None
                    ),
                }
            )
        return {
            "machine_id": spec.machine_id,
            "spec_hash": spec.spec_hash,
            "protocol_version": protocol_version,
            "synthetic": spec.synthetic,
            "groups": groups,
        }

    return router
