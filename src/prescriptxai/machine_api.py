"""Machine-prefixed HTTP endpoints using the shared quality and decision boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.core.decision import MachineDecision
from prescriptxai.machine_schema import FeedbackRecord, MachineRecourseResult
from prescriptxai.machines import machine_summary, record_feedback, resolve_machine_decision
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import Assessment, _reject_nonreal_measurement


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


class MachineFeedbackRequest(MachineWindowRequest):
    """An applied control follow-up tied to a specific machine decision."""

    result: MachineRecourseResult
    applied: dict[str, float]
    source: Literal["operator", "simulated_operator"] = "operator"


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

    @router.post("/machines/{machine_id}/assess", response_model=Assessment)
    def assess(machine_id: str, request: MachineWindowRequest) -> Assessment:
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

    return router
