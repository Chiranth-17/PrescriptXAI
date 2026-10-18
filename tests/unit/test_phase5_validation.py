"""Phase 5 statistical, evidence, feedback, and denominator contracts on test-only data."""

import itertools
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch
from scipy.linalg import solve
from scipy.stats import chi2

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import BoundsSpec, FeatureSpec, load_taxonomy
from prescriptxai.recourse.optimizer import optimize_recourse
from prescriptxai.schemas import ValidationReport as PublicReport
from prescriptxai.validation.base import TierResult
from prescriptxai.validation.feasibility import build_feasibility_penalty
from prescriptxai.validation.funnel import FunnelObservation, FunnelRun, build_funnel_report
from prescriptxai.validation.pipeline import (
    ValidationReport,
    fit_mahalanobis_validator,
    load_mahalanobis_validator,
    save_mahalanobis_validator,
    validate_candidate,
    verify_validator_compatibility,
)
from prescriptxai.validation.simulator import NullSimulator, run_simulator_validation
from prescriptxai.validation.tier1_model import validate_model_risk
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator
from prescriptxai.validation.tier3_engineering import validate_engineering
from prescriptxai.validation.tier4_coupling import calibrate_coupling_thresholds


def test_shrinkage_distance_matches_scipy_and_has_finite_torch_gradient(tmp_path: Path) -> None:
    """Cholesky distance agrees with a SciPy linear-system reference without an inverse."""
    rng = np.random.default_rng(1729)
    rows = rng.normal(size=(200, 4))
    validator = MahalanobisValidator.fit(
        rows, ("a", "b", "c", "d"), np.repeat([1, 2], 100), (1, 2), 5, 1e-6
    )
    difference = np.array([1.0, 2.0, 0.5, -1.0])
    factor = validator.covariance_cholesky
    covariance = factor @ factor.T
    expected = np.sqrt(difference @ solve(covariance, difference, assume_a="pos"))
    assert validator.distance(validator.mean) == pytest.approx(0.0, abs=1e-12)
    assert validator.distance(validator.mean + difference) == pytest.approx(expected)
    assert validator.distance(validator.mean + 2 * difference) == pytest.approx(2 * expected)
    tensor = torch.tensor((validator.mean + difference)[None, :], requires_grad=True)
    validator.torch_distance(tensor).sum().backward()
    assert tensor.grad is not None and torch.isfinite(tensor.grad).all()
    result = validator.validate(validator.mean + difference)
    assert result.margin == pytest.approx(5 - expected)
    assert result.evidence_level == "E2"
    restored = load_mahalanobis_validator(save_mahalanobis_validator(validator, tmp_path / "m.pkl"))
    assert restored.distance(validator.mean + difference) == validator.distance(
        validator.mean + difference
    )


def test_singular_covariance_threshold_methods_and_reference_masks() -> None:
    """Shrinkage handles duplicate/constant channels and cutoffs retain their exact methods."""
    x = np.linspace(-2, 2, 40)
    rows = np.column_stack([x, x, np.ones(40)])
    ids = np.repeat([1, 2], 20)
    methods = {}
    for method in ("fixed", "empirical_quantile", "chi_square_quantile"):
        validator = MahalanobisValidator.fit(
            rows,
            ("x", "duplicate", "constant"),
            ids,
            (1, 2),
            5,
            1e-6,
            threshold_method=method,
            threshold_quantile=0.95,
        )
        methods[method] = validator
        assert np.isfinite(validator.distance_batch(rows)).all()
        assert validator.regime_statistics[0].unregularized_rank == 1
    assert methods["fixed"].max_distance == 5
    assert methods["chi_square_quantile"].max_distance == pytest.approx(np.sqrt(chi2.ppf(0.95, 3)))
    assert methods["empirical_quantile"].max_distance == pytest.approx(
        np.quantile(methods["empirical_quantile"].distance_batch(rows), 0.95)
    )
    assert methods["empirical_quantile"].max_distance < methods["chi_square_quantile"].max_distance
    selected = MahalanobisValidator.fit(
        rows,
        ("x", "duplicate", "constant"),
        ids,
        (1, 2),
        5,
        1e-6,
        reference_distribution="healthy_to_moderate",
        reference_mask=np.arange(40) % 2 == 0,
    )
    assert selected.regime_statistics[0].row_count == 20
    with pytest.raises(ValueError, match="at least two"):
        MahalanobisValidator.fit(
            rows, ("a", "b", "c"), ids, (1, 2), 5, 1e-6, reference_mask=np.zeros(40, dtype=bool)
        )
    with pytest.raises(ValueError, match="quantile"):
        MahalanobisValidator.fit(
            rows,
            ("a", "b", "c"),
            ids,
            (1, 2),
            5,
            1e-6,
            threshold_method="chi_square_quantile",
            threshold_quantile=1,
        )


def test_regime_statistics_are_selected_by_frozen_settings() -> None:
    """The same candidate is accepted in its original regime and rejected in a distant one."""
    rng = np.random.default_rng(52)
    rows = np.vstack([rng.normal(-20, 0.2, (100, 2)), rng.normal(20, 0.2, (100, 2))])
    settings = np.repeat([[-10.0, 0, 0], [10.0, 0, 0]], 100, axis=0)
    validator = MahalanobisValidator.fit(
        rows,
        ("a", "b"),
        np.repeat([1, 2], 100),
        (1, 2),
        5,
        1e-6,
        operating_settings=settings,
        regime_k=2,
    )
    assert validator.validate(np.array([-20.0, -20.0]), frozen_operating_settings=settings[0]).valid
    assert not validator.validate(
        np.array([-20.0, -20.0]), frozen_operating_settings=settings[-1]
    ).valid
    assert len(validator.regime_statistics) == 2
    labels = validator.assign_regimes(settings)
    assert np.array_equal(labels, validator.assign_regimes(settings))
    assert np.allclose(
        validator.distance_batch(rows, regime_ids=labels),
        validator.distance_batch(rows, frozen_operating_settings=settings),
    )
    with pytest.raises(ValueError, match="frozen operating"):
        validator.distance(rows[0])
    with pytest.raises(ValueError, match="regime labels"):
        validator.distance_batch(rows, regime_ids=np.array([4]))


def test_tier1_reports_true_risk_margin_and_surrogate_disagreement() -> None:
    """A falsely safe surrogate cannot change Tier 1; disagreement is explicitly warned."""
    result = validate_model_risk(0.9, 0.2, surrogate_risk=0.1, disagreement_threshold=0.1)
    assert not result.valid and result.margin == pytest.approx(-0.7)
    assert result.warnings and result.evidence_level == "E1"
    with pytest.raises(ValueError, match="surrogate risk"):
        validate_model_risk(0.1, 0.2, surrogate_risk=float("nan"), disagreement_threshold=0.1)


@pytest.mark.parametrize("bits", list(itertools.product([False, True], repeat=4)))
def test_verdict_truth_table_and_versioned_schema_round_trip(bits: tuple[bool, ...]) -> None:
    """All sixteen static verdict combinations preserve independent definitions and evidence."""
    levels = ("E1", "E2", "E3", "E3")
    tiers = [
        TierResult(value, (), evidence_level=level)
        for value, level in zip(bits, levels, strict=True)
    ]
    report = ValidationReport(*tiers)
    assert report.model_valid == bits[0]
    assert report.plausible == bits[1]
    assert report.constraints_ok == all(bits[2:])
    assert report.joint == all(bits)
    assert len(report.failing_tiers) == sum(not value for value in bits)
    encoded = report.to_schema().model_dump_json()
    restored = PublicReport.model_validate_json(encoded)
    assert restored.assumptions == report.assumptions
    assert restored.model_dump_json() == encoded
    assert json.loads(json.dumps(report.as_dict(), allow_nan=False))["joint"] == all(bits)


def test_healthy_fixture_collect_all_fail_fast_simulator_and_ood_tiers() -> None:
    """Known satisfying fixtures pass, immutable ambient/cycle attacks fail Tier 3."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    healthy = {"actuator": 1.0, "sensor": 2.0}
    report = validate_candidate(healthy, healthy, bundle, taxonomy, validator, config)
    assert report.joint and report.evidence_level == "E3"
    assert report.simulator.status == "skipped" and not report.simulator.valid
    unsafe = {"actuator": -2.0, "sensor": 2.0}
    fast = validate_candidate(unsafe, unsafe, bundle, taxonomy, validator, config, mode="fail_fast")
    assert fast.failing_tiers == ("tier1_model",)
    assert fast.tier2_plausibility.status == fast.tier4_coupling.status == "skipped"
    for enabled in (False, True):
        dynamic = run_simulator_validation(healthy, enabled, None)
        assert dynamic.status == "skipped" and dynamic.evidence_level == "none"
    assert not NullSimulator().validate_candidate(healthy).valid
    taxonomy.feature_groups.immutable_environmental.features = ["ambient"]
    taxonomy.feature_groups.context.features = ["cycle"]
    taxonomy.features += (
        FeatureSpec(
            name="ambient",
            label="Test ambient",
            unit="degC",
            cmapss_column="ambient",
            group="immutable_environmental",
            bounds=BoundsSpec(minimum=280, maximum=320),
        ),
        FeatureSpec(
            name="cycle",
            label="Cycle",
            unit="cycle",
            cmapss_column="cycle",
            group="context",
            bounds=BoundsSpec(minimum=1, maximum=10000),
        ),
    )
    initial = {**healthy, "ambient": 300.0, "cycle": 1.0}
    for candidate in ({**initial, "ambient": 285.0}, {**initial, "cycle": 0.0}):
        tier3 = validate_engineering(initial, candidate, taxonomy)
        assert not tier3.valid and any(
            check.margin < 0 for check in tier3.checks if check.margin is not None
        )
    extreme = {**initial, "actuator": 100.0, "sensor": -100.0}
    attacked = validate_candidate(initial, extreme, bundle, taxonomy, validator, config)
    assert not attacked.plausible and not attacked.constraints_ok
    assert not validate_engineering(
        {**initial, "cycle": 0.0}, {**initial, "cycle": 0.0}, taxonomy
    ).valid


def test_validation_only_coupling_calibration_preserves_regressors_and_provenance() -> None:
    """No fitting/evaluation engine can supply calibration residuals."""
    bundle, taxonomy, training = make_recourse_fixture()
    defaults = load_taxonomy(Path("configs/features.yaml"))
    taxonomy.coupling = defaults.coupling
    taxonomy.bound_estimation = defaults.bound_estimation
    taxonomy.features = tuple(
        spec.model_copy(
            update={
                "bounds": BoundsSpec(
                    minimum=None,
                    maximum=None,
                    source="training_percentiles",
                )
            }
        )
        for spec in taxonomy.features
    )
    rng = np.random.default_rng(1729)
    frame = pd.DataFrame(
        {
            "engine_id": np.repeat(np.arange(1, 7), 15),
            "actuator": rng.uniform(-1, 1, 90),
            "rul": 100,
        }
    )
    frame["sensor"] = 2 + 0.2 * frame.actuator + rng.normal(0, 0.02, 90)
    fitted = SensorCouplingModel.fit(
        frame, taxonomy, training_engine_ids=(1, 2, 3, 4), failure_horizon=30
    )
    validation = frame.loc[frame.engine_id.isin([5, 6])]
    calibrated = calibrate_coupling_thresholds(
        fitted,
        validation,
        (5, 6),
        reference_distribution="healthy_to_moderate",
        min_rul=30,
        evaluation_engine_ids=(7, 8),
    )
    assert calibrated is not fitted and fitted.calibration_engine_ids == ()
    assert calibrated.calibration_engine_ids == (5, 6)
    assert np.array_equal(calibrated.models["sensor"].coef_, fitted.models["sensor"].coef_)
    assert calibrated.calibration_report["row_count"] == 30
    residual = validation.sensor - fitted.models["sensor"].predict(
        validation[["actuator"]].to_numpy()
    )
    assert calibrated.residual_std["sensor"] == pytest.approx(np.std(residual, ddof=1))
    config = load_config(Path("configs/default.yaml"))
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    penalty = build_feasibility_penalty(
        bundle, taxonomy, validator, calibrated, {"actuator": 0.0, "sensor": 2.0}
    )
    outlier = torch.tensor([[0.0, 10.0]], dtype=torch.float64, requires_grad=True)
    value = penalty(outlier)
    value.backward()
    assert value.item() > 0
    assert outlier.grad is not None and torch.isfinite(outlier.grad).all()
    with pytest.raises(ValueError, match="overlap"):
        calibrate_coupling_thresholds(
            fitted,
            validation,
            (5, 6),
            reference_distribution="all_cycles",
            min_rul=30,
            evaluation_engine_ids=(6,),
        )
    with pytest.raises(ValueError, match="exactly"):
        calibrate_coupling_thresholds(
            fitted, validation, (6,), reference_distribution="all_cycles", min_rul=30
        )


def test_nonfinite_original_and_persisted_protocol_mismatch_fail_closed() -> None:
    """Invalid origins and mislabeled D_max artifacts cannot pass engineering/loading checks."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    verify_validator_compatibility(validator, bundle, config)
    for value in (float("nan"), float("inf"), float("-inf")):
        report = validate_engineering(
            {"actuator": value, "sensor": 2.0}, {"actuator": 1.0, "sensor": 2.0}, taxonomy
        )
        assert not report.valid and "non-finite" in report.diagnostics[0]
    with pytest.raises(ValueError, match="protocol differs"):
        verify_validator_compatibility(replace(validator, max_distance=8.0), bundle, config)
    with pytest.raises(ValueError, match="fitting engines"):
        verify_validator_compatibility(
            replace(validator, training_engine_ids=(999,)), bundle, config
        )
    with pytest.raises(ValueError, match="regime count"):
        verify_validator_compatibility(replace(validator, regime_statistics={}), bundle, config)


def test_manifold_penalty_gradient_and_feedback_termination() -> None:
    """An unreachable tiny manifold terminates at the configured refinement limit."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.validation.mahalanobis_max = 0.001
    config.validation.feedback_max_refinements = 2
    config.recourse.max_iterations = 10
    config.recourse.restarts = config.recourse.alpha_steps = config.recourse.l1_escalation_steps = 1
    config.recourse.support_search_limit = config.recourse.max_changed_features = 1
    config.recourse.true_model_grid_enabled = False
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    initial = {"actuator": -2.0, "sensor": 2.0}
    penalty = build_feasibility_penalty(bundle, taxonomy, validator, None, initial)
    tensor = torch.tensor([[-1.0, 0.0]], dtype=torch.float64, requires_grad=True)
    penalty(tensor).backward()
    assert tensor.grad is not None and torch.isfinite(tensor.grad).all()
    result = optimize_recourse(initial, bundle, taxonomy, config, mahalanobis=validator)
    assert result.failure_reason is not None and not result.solver_success
    assert result.effective_solver_settings["feedback_refinements_executed"] == 2
    assert result.stage_timings_ms["validation_feedback"] >= 0
    assert len(result.deltas) <= 1


def test_funnel_retains_failed_queries_and_matches_hand_counts() -> None:
    """Cluster bootstrap denominators match exact fixture counts, including a missing candidate."""
    metadata = FunnelRun(
        "test-only", "test.yaml", "hash", "commit", "v1", 3, 1, "v1", 5, "fixture", "test"
    )
    rows = [
        FunnelObservation(1, 1, True, True, True, True, True, True, "E3"),
        FunnelObservation(1, 2, True, False, True, False, True, True),
        FunnelObservation(2, 1, True, False, False, True, False, True),
        FunnelObservation(2, 2, False, False, False, False, False, False),
    ]
    report = build_funnel_report(rows, metadata, bootstrap_replicates=100, seed=1729)
    assert report["missing_candidates"] == 1
    assert report["independent"]["tier2_all_queries"]["count"] == 2
    assert report["independent"]["tier2_all_queries"]["denominator"] == 4
    assert report["independent"]["tier2_returned_counterfactuals"]["denominator"] == 1
    assert report["funnel"]["joint_success"]["count"] == 1
    assert report["independent"]["tier1_all_queries"]["ci"]["engine_count"] == 2
    json.dumps(report, allow_nan=False)
    empty = build_funnel_report([], metadata, bootstrap_replicates=100, seed=1729)
    assert empty["independent"]["tier2_all_queries"]["rate"] is None
    with pytest.raises(ValueError, match="unique"):
        build_funnel_report(rows + rows[:1], metadata, bootstrap_replicates=10, seed=1)
    with pytest.raises(ValueError, match="must have a candidate"):
        build_funnel_report(
            [replace(rows[-1], counterfactual_returned=True)],
            metadata,
            bootstrap_replicates=10,
            seed=1,
        )
