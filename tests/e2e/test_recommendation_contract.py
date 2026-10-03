"""End-to-end recourse and four-tier contract with an explicitly synthetic fixture."""

from pathlib import Path

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


def test_engine_returns_sparse_safe_and_physically_valid_fixture_candidate() -> None:
    """Exercise the same typed engine entrypoint used by CLI, API, and dashboard."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.recourse.max_scaled_distance = 3.0
    config.recourse.max_changed_features = 1
    config.recourse.max_iterations = 200
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    engine = PrescriptXAIEngine(config, taxonomy, bundle, validator)

    result = engine.recommend({"actuator": -2.0, "sensor": 2.0})

    assert result.outcome.model_valid
    assert result.outcome.tier2_plausible
    assert result.outcome.tier3_engineering_valid
    assert result.outcome.tier4_coupling_valid
    assert result.outcome.success
    assert len(result.outcome.deltas) <= config.recourse.max_changed_features
