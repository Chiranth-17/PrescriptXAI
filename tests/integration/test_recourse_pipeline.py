"""Integration test from optimizer output through all independent validation tiers."""

from pathlib import Path

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.recourse.optimizer import optimize_recourse
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, validate_candidate


def test_candidate_flows_through_recourse_and_four_tier_validation() -> None:
    """Synthetic fixture verifies API wiring only; it is not benchmark evidence."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_scaled_distance = 3.0
    config.recourse.max_changed_features = 1
    config.recourse.max_iterations = 200
    initial = {"actuator": -2.0, "sensor": 2.0}

    recourse = optimize_recourse(initial, bundle, taxonomy, config)
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    validation = validate_candidate(initial, recourse.state, bundle, taxonomy, validator, config)
    outcome = validation.as_outcome(recourse.initial_risk, recourse.final_risk, recourse.deltas)

    assert recourse.model_valid
    assert validation.tier1_model.valid
    assert validation.tier2_plausibility.valid
    assert validation.tier3_engineering.valid
    assert validation.tier4_coupling.valid
    assert outcome.success
