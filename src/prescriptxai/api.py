"""Optional FastAPI service over the shared recommendation engine."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from prescriptxai.logging_utils import configure_logging
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.schemas import RecommendationResponse, RecourseRequest, TierPayload


def create_app(engine: PrescriptXAIEngine) -> FastAPI:
    """Create an application bound to an already configured local engine."""
    configure_logging()
    app = FastAPI(
        title="PrescriptXAI",
        description=(
            "Maintenance decision support. Model validity and physical plausibility are separate. "
            "C-MAPSS does not support RUL-extension claims."
        ),
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report loaded model and dataset scope without claiming service safety."""
        return {
            "status": "ready",
            "model": engine.model.model_type,
            "dataset": engine.taxonomy.dataset,
        }

    @app.post("/recommend", response_model=RecommendationResponse)
    def recommend(request: RecourseRequest) -> RecommendationResponse:
        """Generate and validate a candidate from one raw-unit machine state."""
        try:
            result = engine.recommend(request.state)
        except (ValueError, FileNotFoundError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        report = result.validation
        tiers = report.tiers()
        return RecommendationResponse(
            evidence_level=report.evidence_level,
            plausible=report.plausible,
            constraints_ok=report.constraints_ok,
            joint=report.joint,
            failing_tiers=report.failing_tiers,
            assumptions=report.assumptions,
            original_state=request.state,
            new_state=result.optimization.state,
            outcome=result.outcome,
            solver_success=result.optimization.solver_success,
            optimizer_message=result.optimization.message,
            objective_value=result.optimization.objective_value,
            failure_reason=result.optimization.failure_reason,
            risk_reached=result.optimization.risk_reached,
            stage_timings_ms=result.optimization.stage_timings_ms,
            objective_terms=result.optimization.objective_terms,
            counterfactual_signs=result.optimization.counterfactual_signs,
            solver_calls=result.optimization.solver_calls,
            actuator_constraints_feasible=result.optimization.actuator_constraints_feasible,
            tiers={
                name: TierPayload.model_validate(tier.as_dict()) for name, tier in tiers.items()
            },
        )

    return app
