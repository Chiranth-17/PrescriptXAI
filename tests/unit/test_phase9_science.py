"""Eleven explicit scientific failure-mode regressions requested for Phase 9."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from fixtures.hardening import PARTITIONS, raw_fixture
from fixtures.operator_artifacts import write_operator_fixture
from fixtures.recourse_models import make_recourse_fixture
from integration.test_phase8_backend import preview_service  # noqa: F401
from prescriptxai.config import load_config
from prescriptxai.constraints.bounds import allowed_interval
from prescriptxai.constraints.taxonomy import (
    ActuatorConstraint,
    BoundsSpec,
    FeatureGroup,
    FeatureSpec,
)
from prescriptxai.data.cmapss import add_test_labels
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.evaluation.latency import summarize_latency
from prescriptxai.evaluation.metrics import EvaluationRecord, calculate_metrics
from prescriptxai.evaluation.runner import validate_evaluation_provenance
from prescriptxai.models.train import train_risk_model
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.validation.base import TierResult
from prescriptxai.validation.pipeline import ValidationReport, validate_candidate
from prescriptxai.validation.tier1_model import validate_model_risk
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator


def test_science_leakage_heldout_perturbations_cannot_change_any_fitted_state(
    tmp_path: Path,
) -> None:
    """Holdout values affect measured metrics, never predictor/scaler/calibrator/solver settings."""
    raw, config, taxonomy = raw_fixture(tmp_path)
    first = train_risk_model(raw, config, taxonomy, "mlp", engine_partitions=PARTITIONS)
    altered = raw.copy()
    altered.loc[altered.unit_id.isin(PARTITIONS[2]), "s3"] += 10_000
    second = train_risk_model(altered, config, taxonomy, "mlp", engine_partitions=PARTITIONS)
    np.testing.assert_array_equal(
        first.bundle.scaler.scaler.mean_, second.bundle.scaler.scaler.mean_
    )
    np.testing.assert_array_equal(
        first.bundle.scaler.scaler.scale_, second.bundle.scaler.scaler.scale_
    )
    assert first.bundle.config_hash == second.bundle.config_hash
    assert first.bundle.calibrator is not None and second.bundle.calibrator is not None
    probes = np.asarray([0.01, 0.2, 0.8, 0.99])
    np.testing.assert_array_equal(
        first.bundle.calibrator.transform(probes), second.bundle.calibrator.transform(probes)
    )
    for name, tensor in first.bundle.estimator.network_.state_dict().items():
        assert torch.equal(tensor, second.bundle.estimator.network_.state_dict()[name])
    assert first.metrics["calibration"]["fit_engine_ids"] == list(PARTITIONS[1])


def test_science_declared_solver_tuning_on_evaluation_engines_is_rejected(tmp_path: Path) -> None:
    """Persisted solver-tuning provenance is a fitting component, even with an unchanged seed."""
    write_operator_fixture(tmp_path)
    service = PrescriptXAI.from_config(tmp_path / "pipeline.yaml")
    service.engine.model.metrics["solver_tuning"] = {"fit_engine_ids": [7]}
    with pytest.raises(ValueError, match="solver_tuning"):
        validate_evaluation_provenance(
            service.engine, pd.DataFrame({"engine_id": [7], "cycle": [1]})
        )


@pytest.mark.parametrize("ids", [(1.5,), (True,), (1, 1), (float("nan"),)])
@pytest.mark.parametrize("component", ["model", "scaler", "mahalanobis"])
def test_all_primary_fitting_provenance_rejects_invalid_engine_ids(
    preview_service: PrescriptXAI,  # noqa: F811
    component: str,
    ids: tuple[object, ...],
) -> None:
    """No fitting component may silently truncate, deduplicate or boolean-cast engine IDs."""
    engine = preview_service.engine
    if component == "model":
        engine.model.training_engine_ids = ids
    elif component == "scaler":
        engine.model.scaler = replace(engine.model.scaler, training_engine_ids=ids)
    else:
        engine.mahalanobis = replace(engine.mahalanobis, training_engine_ids=ids)
    with pytest.raises(ValueError, match="provenance.*invalid engine IDs"):
        validate_evaluation_provenance(engine, pd.DataFrame({"engine_id": [7], "cycle": [1]}))


def test_science_scaling_divides_by_training_scale_and_preserves_raw_delta() -> None:
    """A non-unit scaler detects reversed multiply/divide and raw/scaled delta confusion."""
    bundle, _, _ = make_recourse_fixture()
    scaler = bundle.scaler.scaler
    raw = scaler.mean_ + scaler.scale_ * np.asarray([1.25, -0.75])
    scaled = bundle.scaler.transform(pd.DataFrame([raw], columns=bundle.feature_names))
    np.testing.assert_allclose(scaled[0], [1.25, -0.75], atol=1e-14)
    np.testing.assert_allclose(scaler.inverse_transform(scaled)[0], raw, atol=1e-14)


def test_science_threshold_comparisons_include_exact_safe_boundary() -> None:
    """True risk equal to tau_safe passes; the immediate representable value above fails."""
    assert validate_model_risk(0.2, 0.2).valid
    assert validate_model_risk(np.nextafter(0.2, 0), 0.2).valid
    assert not validate_model_risk(np.nextafter(0.2, 1), 0.2).valid


def test_science_rul_training_and_official_test_boundaries_are_not_off_by_one() -> None:
    """Terminal training RUL is zero; official prefix RUL adds unobserved terminal remainder."""
    training = pd.DataFrame({"unit_id": [1] * 33, "cycle": np.arange(1, 34)})
    labeled = add_training_labels(training, 10, 30)
    assert labeled.y.iloc[[0, 1, 2, -1]].tolist() == [0, 0, 1, 1]
    assert labeled.rul.iloc[0] == 10 and labeled.rul.iloc[-1] == 0
    test = pd.DataFrame({"unit_id": [1] * 17, "cycle": np.arange(1, 18)})
    labeled_test = add_test_labels(test, pd.DataFrame({"unit_id": [1], "rul": [5]}), 20)
    assert labeled_test.rul.iloc[[0, 1, -1]].tolist() == [21, 20, 5]
    assert labeled_test.y.iloc[[0, 1, -1]].tolist() == [0, 1, 1]


def test_science_mahalanobis_candidate_cannot_choose_a_more_favorable_regime() -> None:
    """Frozen original operating settings determine the reference distribution."""
    values = np.asarray([[-10.1], [-10], [-9.9], [9.9], [10], [10.1]])
    settings = np.asarray([[-1.0, 0, 0]] * 3 + [[1.0, 0, 0]] * 3)
    validator = MahalanobisValidator.fit(
        values,
        ("sensor",),
        np.asarray([1] * 3 + [2] * 3),
        (1, 2),
        5,
        1e-6,
        operating_settings=settings,
        regime_k=2,
        seed=17,
    )
    frozen = validator.validate(np.asarray([10.0]), frozen_operating_settings=settings[:1])
    changed = validator.validate(np.asarray([10.0]), frozen_operating_settings=settings[3:4])
    assert not frozen.valid and changed.valid
    assert frozen.measurement > changed.measurement
    bundle, taxonomy, _ = make_recourse_fixture()
    setting_names = tuple(f"op_setting_{index}" for index in range(1, 4))
    taxonomy.features += tuple(
        FeatureSpec(
            name=name,
            label=name,
            unit="-",
            cmapss_column=name,
            group="immutable_operational",
            bounds=BoundsSpec(minimum=-2, maximum=2),
        )
        for name in setting_names
    )
    taxonomy.feature_groups.immutable_operational = FeatureGroup(features=list(setting_names))
    matrix = np.column_stack([values[:, 0], np.zeros(len(values))])
    actual = MahalanobisValidator.fit(
        matrix,
        bundle.feature_names,
        np.asarray([1] * 3 + [2] * 3),
        (1, 2),
        5,
        1e-6,
        operating_settings=settings,
        regime_k=2,
        seed=17,
    )
    scaler = bundle.scaler.scaler
    raw = scaler.inverse_transform(np.asarray([[10.0, 0.0]]))[0]
    candidate = {
        **dict(zip(bundle.feature_names, raw, strict=True)),
        **dict(zip(setting_names, settings[3], strict=True)),
    }
    original = {**candidate, **dict(zip(setting_names, settings[0], strict=True))}
    report = validate_candidate(
        original,
        candidate,
        bundle,
        taxonomy,
        actual,
        load_config(Path("configs/default.yaml")),
    )
    assert not report.tier2_plausibility.valid and not report.tier3_engineering.valid
    assert report.tier2_plausibility.measurement == pytest.approx(
        actual.validate(np.asarray([10.0, 0.0]), frozen_operating_settings=settings[:1]).measurement
    )


def test_science_surrogate_risk_cannot_override_true_model_safety() -> None:
    """A favorable surrogate is diagnostic only; true calibrated risk controls validity."""
    unsafe = validate_model_risk(0.8, 0.2, surrogate_risk=0.01, disagreement_threshold=0.1)
    safe = validate_model_risk(0.1, 0.2, surrogate_risk=0.9, disagreement_threshold=0.1)
    assert not unsafe.valid and safe.valid and unsafe.warnings and safe.warnings


def test_science_calibration_is_applied_exactly_once_to_actual_estimator_probabilities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observe the real calibrator without replacing its computed results."""
    write_operator_fixture(tmp_path)
    bundle = PrescriptXAI.from_config(tmp_path / "pipeline.yaml").engine.model
    frame = pd.DataFrame({"actuator": [-2.0, 0.5, 2.0], "sensor": [2.0] * 3})
    raw = bundle.estimator.predict_proba(bundle.scaler.transform(frame))
    original = bundle.calibrator.transform
    expected = original(raw)
    inputs = []

    def observed_transform(values: np.ndarray) -> np.ndarray:
        """Record call inputs while invoking the unchanged fitted calibration method."""
        inputs.append(np.array(values, copy=True))
        return original(values)

    monkeypatch.setattr(bundle.calibrator, "transform", observed_transform)
    np.testing.assert_array_equal(bundle.predict_risk(frame), expected)
    assert len(inputs) == 1
    np.testing.assert_array_equal(inputs[0], raw[:, 1] if raw.ndim == 2 else raw)


def test_science_rate_limit_direction_signs_and_assumed_horizon() -> None:
    """Increasing and decreasing controls have oppositely signed cumulative intervals."""
    common = {"minimum": -2, "maximum": 2, "max_change_per_step": 0.25}
    increasing = ActuatorConstraint(**common, direction="increase_only")
    decreasing = ActuatorConstraint(**common, direction="decrease_only")
    assert allowed_interval(0, increasing, horizon_steps=2) == (0, 0.5)
    assert allowed_interval(0, decreasing, horizon_steps=2) == (-0.5, 0)
    assert allowed_interval(0, increasing) == (0, 0.25)


def test_science_failed_queries_remain_in_validity_and_tier_denominators() -> None:
    """One success plus one solver failure is a half rate, never a success-only full rate."""
    records = tuple(
        EvaluationRecord(
            engine_id=engine,
            cycle=1,
            initial_risk=0.9,
            final_risk=0.1 if passed else 0.9,
            model_valid=passed,
            tier2_plausible=passed,
            tier3_engineering_valid=passed,
            tier4_coupling_valid=passed,
            changed_features=int(passed),
            optimization_ms=1,
            validation_ms=1,
            solver_success=passed,
            recourse_feasible=passed,
            message="fixture",
        )
        for engine, passed in ((7, True), (8, False))
    )
    result = calculate_metrics(
        records, 2, None, None, load_config(Path("configs/default.yaml")).evaluation
    )
    assert result.evaluated_states == 2 and result.model_valid_count == 1
    assert result.recourse_validity_rate.value == result.tier2_plausibility_rate.value == 0.5


def test_science_physical_valid_plausibility_and_model_validity_are_independent() -> None:
    """Tier 2 alone is plausibility; physical_valid is Tiers 2-4; joint also requires Tier 1."""
    passed, failed = TierResult(True, ()), TierResult(False, ("fixture rejection",))
    report = ValidationReport(passed, passed, failed, passed)
    assert report.plausible and not report.physical_valid and not report.joint
    assert report.evidence_level == "E2"
    unsafe = ValidationReport(failed, passed, passed, passed)
    assert unsafe.physical_valid and unsafe.plausible and not unsafe.joint
    assert unsafe.evidence_level == "none"


def test_science_latency_lower_band_is_not_a_minimum_or_failure_condition() -> None:
    """Faster is a pass; only the upper p95 figure is a budget, and absent data is unknown."""
    fast = summarize_latency([0.01, 0.02, 0.05], 1200, 1800)
    assert fast.passed and fast.below_target_range
    assert summarize_latency([1800], 1200, 1800).passed
    assert not summarize_latency([1800.001], 1200, 1800).passed
    assert summarize_latency([], 1200, 1800).passed is None
