"""DiCE target enforcement and real fixed-prefix LSTM experiment execution."""

import random
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fixtures.experiments import fitted_experiment
from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.evaluation.runner import make_cases, observed_alert_cohort, run_experiment_case
from prescriptxai.models.registry import load_model_bundle, save_model_bundle
from prescriptxai.models.torch_models import LSTMFailureModel
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.recourse.baselines import dice_baseline


def test_dice_actual_target_determinism_and_no_candidate() -> None:
    """Use the installed library and true predictor, retaining context and global RNG state."""
    bundle, _, training = make_recourse_fixture()
    training["failure"] = (training.actuator < 0).astype(int)
    config = load_config(Path("configs/default.yaml"))
    original = {"actuator": -2.0, "sensor": 2.0, "engine_id": 6.0, "cycle": 2.0}
    numpy_state, random_state = np.random.get_state(), random.getstate()
    first = dice_baseline(original, bundle, training, config)
    second = dice_baseline(original, bundle, training, config)
    assert first is not None and second is not None
    assert first.state == second.state and first.final_risk <= config.tau_safe
    assert first.state["engine_id"] == 6 and first.state["cycle"] == 2
    assert random.getstate() == random_state
    np.testing.assert_array_equal(np.random.get_state()[1], numpy_state[1])
    with pytest.raises(ValueError, match="outcome column"):
        dice_baseline(original, bundle, training.drop(columns="failure"), config)
    config.tau_safe = config.model.safe_threshold = 1e-12
    failed = dice_baseline(original, bundle, training, config)
    assert failed is not None and failed.failure_reason == "dice_no_candidate"
    assert failed.state == original and not failed.model_valid


def test_observed_lstm_prefix_and_real_experiment(tmp_path: Path) -> None:
    """No prefixes are fabricated and earlier timesteps retain the supplied telemetry."""
    config, frame = fitted_experiment(tmp_path)
    bundle = load_model_bundle(config.artifacts.model)
    # Four distinct test-only two-cycle sequences; no sequence crosses engine boundaries.
    training = pd.DataFrame(
        {"sensor_1": [-2.0, -1.0, 0.0, 1.0, 2.0, 1.5, 0.5, -0.5], "sensor_2": [2.0] * 8}
    )
    scaled = bundle.scaler.transform(training)
    estimator = LSTMFailureModel(window=2, hidden_dims=(4,), epochs=2, seed=17)
    estimator.fit(scaled.reshape(4, 2, 2), np.asarray([1, 0, 0, 1]))
    bundle.estimator, bundle.model_type = estimator, "lstm"
    config.model_choice = config.model.risk_estimator = "lstm"
    # Test-specific low alert gate exercises the prefix path before fitting any study outcome.
    config.tau_safe = config.model.safe_threshold = 0.01
    config.tau_danger = config.model.danger_threshold = 0.02
    save_model_bundle(bundle, config.artifacts.model)
    pipeline = PrescriptXAI.from_config(config)
    alerts, contexts, counts = observed_alert_cohort(pipeline, frame)
    assert counts["scorable_rows"] == 2 and counts["insufficient_history_rows"] == 1
    assert len(alerts) == 2 and alerts.first_alert.tolist() == [True, False]
    assert contexts[(6, 2)].history == ((-2.0, 2.0),)
    case = next(
        make_cases(
            config,
            tmp_path / "config.yaml",
            alerts.iloc[:1],
            contexts,
            dataset="fixture",
            model="lstm",
            population="test",
            protocol="v1",
            variant="full",
            mode="fast",
            seeds=[17],
            free_rate_fraction=1,
        )
    )
    result = run_experiment_case(case)
    assert np.isfinite(result.risk_after) and result.engine_id == 6
    np.testing.assert_allclose(result.risk_before, pipeline.assess(case.state, case.context).risk)
    short, _, short_counts = observed_alert_cohort(pipeline, frame.iloc[:1])
    assert short.empty and short_counts["scorable_rows"] == 0
