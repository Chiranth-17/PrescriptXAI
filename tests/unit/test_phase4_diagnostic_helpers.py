"""Regression checks for Phase 4 diagnostic denominators and effective settings."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from prescriptxai.evaluation.metrics import EvaluationRecord

_SCRIPT_PATH = Path(__file__).parents[2] / "scripts/diagnostics/run_full_diagnosis.py"
_SPEC = importlib.util.spec_from_file_location("phase4_diagnostic_helpers", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_DIAGNOSTICS = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _DIAGNOSTICS
_SPEC.loader.exec_module(_DIAGNOSTICS)


@dataclass
class _RiskModel:
    feature_names: tuple[str, ...] = ("x",)

    @staticmethod
    def predict_risk(frame: pd.DataFrame) -> np.ndarray:
        return np.full(len(frame), 0.33, dtype=np.float64)


def _record(engine_id: int, cycle: int, *, returned: bool) -> EvaluationRecord:
    return EvaluationRecord(
        engine_id=engine_id,
        cycle=cycle,
        initial_risk=0.9,
        final_risk=0.15 if returned else 0.9,
        model_valid=returned,
        tier2_plausible=returned,
        tier3_engineering_valid=returned,
        tier4_coupling_valid=returned,
        changed_features=1 if returned else 0,
        optimization_ms=10.0,
        validation_ms=1.0,
        solver_success=returned,
        message="test",
        recourse_feasible=returned,
    )


def test_population_outcomes_uses_query_risk_and_returned_engine_denominator() -> None:
    """OOF risks stay fold-specific and returned CIs use only returned engines."""
    engine = SimpleNamespace(
        model=_RiskModel(),
        config=SimpleNamespace(
            model=SimpleNamespace(safe_threshold=0.2),
            recourse=SimpleNamespace(max_changed_features=3),
        ),
    )
    rows = pd.DataFrame(
        {
            "engine_id": [1, 1, 2, 3],
            "cycle": [10, 11, 10, 10],
            "rul": [20, 19, 30, 40],
            "x": [0.0, 0.1, 0.2, 0.3],
            "_risk_before": [0.9, 0.85, 0.95, 0.8],
        }
    )
    records = (_record(1, 10, returned=True), _record(2, 10, returned=False))

    outcome = _DIAGNOSTICS._population_outcomes(
        engine, rows, records, seed=8, include_frame=True
    )
    metrics = outcome["metrics"]

    assert outcome["query_count"] == 4
    assert metrics["mean_risk_drop_all_queries"]["estimate"] == pytest.approx(0.2)
    assert metrics["tier2_plausible_returned_counterfactuals"]["n"] == 1
    assert metrics["tier2_plausible_returned_counterfactuals"]["engine_count"] == 1
    assert metrics["tier2_plausible_all_queries"]["n"] == 4
    assert outcome["_raw_outcomes"].initial_risk.tolist() == [0.9, 0.85, 0.95, 0.8]


def test_effective_solver_settings_do_not_treat_missing_grid_checks_as_pass() -> None:
    """Runtime grid enforcement counters distinguish false from unreported values."""
    grid_run = _record(1, 1, returned=True).__class__(
        **{
            **_record(1, 1, returned=True).__dict__,
            "effective_solver_settings": {
                "grid_ran": True,
                "grid_k_limit_honored": True,
                "grid_scaled_distance_honored": False,
            },
        }
    )
    missing = _record(2, 1, returned=False)

    summary = _DIAGNOSTICS._effective_solver_settings((grid_run, missing))

    assert summary["grid_run_count"] == 1
    assert summary["k_max_enforcement"] == {"true": 1, "false": 0, "unreported": 0}
    assert summary["max_scaled_distance_enforcement"] == {
        "true": 0,
        "false": 1,
        "unreported": 0,
    }
    assert summary["all_grid_runs_honored_k_max"] is True
    assert summary["all_grid_runs_honored_max_scaled_distance"] is False


def test_legacy_report_count_parser_preserves_numerator_and_denominator() -> None:
    """The historical mismatch audit reads counts as pairs, not flattened digits."""
    report = """| Recourse Validity | 112 | 200 | 56.0% |
| Distributional Plausibility | 106 | 200 | 53.0% |
| Joint success | 87 | 200 | 43.5% |
"""

    counts = _DIAGNOSTICS._parse_legacy_d1_counts(report)

    assert counts == {
        "tier1": [[112, 200]],
        "tier2": [[106, 200]],
        "joint": [[87, 200]],
    }
