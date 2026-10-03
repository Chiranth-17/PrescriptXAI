"""Ablation acceptance rates computed from actual validation records."""

from prescriptxai.evaluation.metrics import EvaluationRecord


def ablation_acceptance_rates(records: tuple[EvaluationRecord, ...]) -> dict[str, float | None]:
    """Measure how many model-valid candidates pass if a physical tier is omitted.

    These are counterfactual acceptance rates, not physical-validity claims. Each key names the
    omitted check; the full validation metrics remain unchanged.
    """
    count = len(records)
    if count == 0:
        return {"omit_tier2": None, "omit_tier3": None, "omit_tier4": None, "model_only": None}
    return {
        "omit_tier2": sum(
            r.model_valid and r.tier3_engineering_valid and r.tier4_coupling_valid for r in records
        )
        / count,
        "omit_tier3": sum(
            r.model_valid and r.tier2_plausible and r.tier4_coupling_valid for r in records
        )
        / count,
        "omit_tier4": sum(
            r.model_valid and r.tier2_plausible and r.tier3_engineering_valid for r in records
        )
        / count,
        "model_only": sum(r.model_valid for r in records) / count,
    }
