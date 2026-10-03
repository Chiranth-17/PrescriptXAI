"""Optional FastAPI service over the shared recommendation engine."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.schemas import RecommendationResponse, RecourseRequest, TierPayload


def create_app(engine: PrescriptXAIEngine) -> FastAPI:
    """Create an application bound to an already configured local engine."""
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
        tiers = {
            "tier1_model": report.tier1_model,
            "tier2_plausibility": report.tier2_plausibility,
            "tier3_engineering": report.tier3_engineering,
            "tier4_coupling": report.tier4_coupling,
        }
        return RecommendationResponse(
            outcome=result.outcome,
            solver_success=result.optimization.solver_success,
            optimizer_message=result.optimization.message,
            objective_value=result.optimization.objective_value,
            tiers={
                name: TierPayload(
                    valid=tier.valid,
                    diagnostics=tier.diagnostics,
                    measurement=tier.measurement,
                    limit=tier.limit,
                )
                for name, tier in tiers.items()
            },
        )

    return app
