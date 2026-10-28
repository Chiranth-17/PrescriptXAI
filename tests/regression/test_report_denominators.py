"""Reporting must preserve failed queries, engine clusters and conditional denominators."""

import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
import torch

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.evaluation.metrics import EvaluationRecord, calculate_metrics
from prescriptxai.evaluation.report import evaluation_metric_intervals, write_evaluation_report
from prescriptxai.evaluation.runner import EvaluationRun
from prescriptxai.models.xgb_model import XGBFailureModel
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


def test_report_retains_failed_queries_and_both_tier2_denominators(tmp_path: Path) -> None:
    """Two engines/three queries must not become three independent bootstrap units."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    engine = PrescriptXAIEngine(config, taxonomy, bundle, validator)
    original = pd.DataFrame(
        [
            {"engine_id": unit, "cycle": cycle, "actuator": -1.5, "sensor": 2.0}
            for unit, cycle in ((20, 1), (20, 2), (21, 1))
        ]
    )
    first = EvaluationRecord(
        20,
        1,
        0.9,
        0.1,
        True,
        True,
        True,
        True,
        1,
        10.0,
        1.0,
        True,
        "test-only",
        recourse_feasible=True,
        candidate_state={"actuator": -1.3, "sensor": 2.0},
        inference_ms=2.0,
        backend_pipeline_ms=13.0,
    )
    records = (
        first,
        replace(
            first,
            cycle=2,
            final_risk=0.9,
            model_valid=False,
            tier2_plausible=False,
            recourse_feasible=False,
            changed_features=0,
            optimization_ms=200.0,
            backend_pipeline_ms=203.0,
            candidate_state={"actuator": -1.5, "sensor": 2.0},
        ),
        replace(first, engine_id=21, final_risk=0.3, model_valid=False, recourse_feasible=False),
    )
    run = EvaluationRun(records, calculate_metrics(records, 3, None, None, config.evaluation))
    intervals = evaluation_metric_intervals(run, engine, original)
    assert intervals["validity"]["estimate"] == pytest.approx(1 / 3)
    assert intervals["plausibility_all"]["estimate"] == pytest.approx(2 / 3)
    assert intervals["plausibility_all"]["denominator"] == 3
    assert intervals["plausibility_returned"]["estimate"] == 1
    assert intervals["plausibility_returned"]["denominator"] == 2
    assert intervals["sparsity_success"]["denominator"] == 1
    assert intervals["plausibility_returned"]["engine_count"] == 2
    output = tmp_path / "measured.json"
    markdown = output.with_suffix(".md")
    write_evaluation_report(
        run,
        output,
        markdown,
        metric_intervals=intervals,
        provenance={"effective_configuration": config.model_dump(mode="json")},
    )
    saved = json.loads(output.read_text())
    text = markdown.read_text(encoding="utf-8")
    assert saved["whole_engine_metric_intervals"] == intervals
    assert saved["whole_engine_latency_intervals"]["optimization"]["engine_count"] == 2
    assert saved["whole_engine_latency_intervals"]["optimization"]["estimate"] > 180
    assert "denominator 3.0" in text and "denominator 2.0" in text
    assert "0.2333" in text  # Shortfall of Tier 2 over all queries against its own target.
    assert "measured; no target" in text and "documented proxy assumptions" in text
    assert "faster is a pass" in text


def test_unsupported_gradients_are_capability_errors() -> None:
    """Nondifferentiable predictors reject the operation as a type/capability mismatch."""
    bundle, _, training = make_recourse_fixture()
    bundle.estimator.supports_gradients = False
    with pytest.raises(TypeError, match="no differentiable predictor"):
        bundle.torch_forward(torch.zeros((1, 2)))
    with pytest.raises(TypeError, match="differentiable model path"):
        bundle.predict_risk_with_gradient(training)
    with pytest.raises(TypeError, match="does not support gradients"):
        config = load_config(Path("configs/default.yaml"))
        XGBFailureModel(config.seed, config.model).torch_forward(torch.zeros((1, 2)))


def test_publication_metadata_comes_from_the_measured_input() -> None:
    """Changed seed/count metadata must not silently inherit the old publication labels."""
    spec = importlib.util.spec_from_file_location("docs_results", "scripts/docs_results.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    study = {
        "bootstrap_confidence": 0.9,
        "bootstrap_replicates": 400,
        "solver_seeds": [7],
        "d_max_versions": {"new": 6.0},
    }
    group = {
        "seeds": [7],
        "labels": {"k_max": ["2"], "K": ["4"], "D_max": ["6.0"]},
        "metrics": {"validity": {"ci": {"seed": 42}}},
    }
    text = module.publication_context({"manifest": {"configuration": study}}, [group])
    assert "90%" in text and "400 requested draws" in text and "seeds [42]" in text
    assert "1 solver seeds [7]" in text and "assumed K=['4']" in text
    group["seeds"] = [8]
    with pytest.raises(ValueError, match="registered solver seeds"):
        module.publication_context({"manifest": {"configuration": study}}, [group])
