"""Hand-computed experimental metrics, whole-engine resampling and atomic evidence tests."""

from pathlib import Path

import numpy as np
import pytest

from prescriptxai.evaluation.experiments import (
    ExperimentObservation,
    ExperimentStore,
    content_hash,
    load_study,
)
from prescriptxai.evaluation.metrics import (
    action_sparsity,
    clustered_ratio_interval,
    cumulative_funnel,
    experiment_metric_values,
    state_proximity,
)


def observation() -> ExperimentObservation:
    """Create one test-only serialization observation, never an experiment input."""
    return ExperimentObservation(
        case_id="fixture",
        group="fixture",
        dataset="fixture",
        model="fixture",
        population="fixture",
        protocol="v1",
        variant="full",
        mode="FAST",
        seed=1,
        engine_id=10,
        cycle=3,
        risk_before=0.9,
        risk_after=0.1,
        surrogate_after=0.11,
        original={"a": 1},
        candidate={"a": 2},
        changed_features=["a"],
        sparsity=1,
        raw_l1=1,
        scaled_l1=0.5,
        returned=True,
        action_feasible=True,
        tier2=True,
        tier3=True,
        tier4=True,
        joint=True,
        status="RECOVERABLE",
        reason=None,
        evidence_level="E3",
        mahalanobis_before=2,
        mahalanobis_after=1,
        tier4_margin=0.2,
        immutable_violations=0,
        bound_violations=0,
        rate_violations=0,
        rul=20,
        life_fraction=0.5,
        first_alert=True,
        timings={"optimization_ms": 1},
        config_hash="fixture",
        config_path="fixture",
        k_max=3,
        K=1,
        D_max=5,
        solver_tau_safe=0.2,
        solver_tau_danger=0.8,
        solver_settings={},
        validation={},
    )


def test_metrics_hand_counts_and_distances() -> None:
    """Keep failure/return denominators separate and count true rather than surrogate safety."""
    first = observation().model_dump()
    second = {
        **first,
        "risk_after": 0.4,
        "returned": False,
        "joint": False,
        "tier2": False,
        "status": "ESCALATE",
        "sparsity": 0,
    }
    values = experiment_metric_values([first, second], 0.2)
    assert values["validity"] == ([1, 0], [1, 1])
    assert values["plausibility_returned"] == ([1, 0], [1, 0])
    np.testing.assert_allclose(values["risk_reduction"][0], [0.8, 0.5])
    assert cumulative_funnel([first, second], 0.2) == {
        "alerts": 2,
        "candidate_returned": 1,
        "tier1": 1,
        "tier2": 1,
        "tier3": 1,
        "tier4": 1,
        "joint": 1,
    }
    assert state_proximity({"a": 1, "b": 3}, {"a": 3, "b": 2}, {"a": 2, "b": 0.5}) == (3, 3)
    assert action_sparsity({"a": 1}, {"a": 1.1}, ["a"], {"a": 2}, 0.1) == 0
    with pytest.raises(ValueError, match="scales"):
        action_sparsity({"a": 1}, {"a": 2}, ["a"], {"a": 0}, 0.1)
    with pytest.raises(ValueError, match="probabilities"):
        experiment_metric_values([{**first, "risk_after": float("nan")}], 0.2)


def test_bootstrap_keeps_whole_engines_and_zero_return_engines() -> None:
    """Compare exact cluster sampling and preserve engines without returned candidates."""
    result = clustered_ratio_interval(
        [1, 1, 2], [1, 1, 0], [1, 1, 1], seed=7, replicates=1000, confidence=0.95
    )
    assert result["estimate"] == pytest.approx(2 / 3)
    assert result["lower"] == 0 and result["upper"] == 1 and result["engine_count"] == 2
    conditional = clustered_ratio_interval(
        [1, 1, 2, 2], [1, 1, 0, 0], [1, 1, 0, 0], seed=7, replicates=1000, confidence=0.95
    )
    assert conditional["engine_count"] == 2
    assert conditional["estimate"] == 1 and conditional["zero_denominator_replicates"] > 0
    assert conditional == clustered_ratio_interval(
        [1, 1, 2, 2], [1, 1, 0, 0], [1, 1, 0, 0], seed=7, replicates=1000, confidence=0.95
    )
    empty = clustered_ratio_interval([], [], [], seed=7, replicates=100, confidence=0.95)
    assert empty["estimate"] is None and empty["engine_count"] == 0
    for n, d in (([float("nan")], [1]), ([1], [0]), ([0], [-1])):
        with pytest.raises(ValueError):
            clustered_ratio_interval([1], n, d, seed=7, replicates=100, confidence=0.95)


def test_atomic_resume_and_manifest_rejection(tmp_path: Path) -> None:
    """A completed query survives reconnect; incompatible evidence is never overwritten."""
    manifest = {"config_hash": content_hash({"frozen": True}), "git_hash": "fixture"}
    store = ExperimentStore(tmp_path, manifest)
    record = observation()
    store.save(record)
    store.save(record)
    store.close()
    resumed = ExperimentStore(tmp_path, manifest)
    assert resumed.completed() == {"fixture"} and resumed.records() == [record]
    with pytest.raises(ValueError, match="replaced"):
        resumed.save(record.model_copy(update={"risk_after": 0.2}))
    resumed.close()
    with pytest.raises(ValueError, match="manifest mismatch"):
        ExperimentStore(tmp_path, {**manifest, "config_hash": "different"})


def test_study_configuration_is_explicit_and_rejects_invalid_design() -> None:
    """Load precommitted real-run design; validate seeds, quantiles and bin order."""
    study = load_study(Path("configs/experiments/phase7-study.yaml"))
    assert len(study.solver_seeds) == 5 and study.latency_runs_per_mode >= 1000
    for change in (
        {"solver_seeds": [1, 1]},
        {"tau_safe_grid": [1.1]},
        {"risk_band_edges": [1, 0]},
        {"K_grid": [0]},
    ):
        with pytest.raises(ValueError):
            type(study).model_validate({**study.model_dump(), **change})
