"""Genuinely fitted deterministic tiny artifacts for operator tests, never benchmark claims."""

from pathlib import Path

import pandas as pd
import yaml

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.models.calibration import ProbabilityCalibrator, calibration_diagnostics
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.models.torch_models import MLPFailureModel
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, save_mahalanobis_validator


def write_operator_fixture(directory: Path) -> Path:
    """Fit train-only scaler/predictor/covariance and calibrate separate fixture engines."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.model_choice = config.model.risk_estimator = "torch"
    config.recourse.max_iterations = 15
    config.recourse.restarts = config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = config.recourse.support_search_limit = 1
    bundle.estimator = MLPFailureModel(hidden_dims=(8,), epochs=150, learning_rate=0.03, seed=17)
    matrix = bundle.scaler.transform(training[list(bundle.feature_names)])
    bundle.estimator.fit(matrix, (training.actuator < 0).astype(int).to_numpy())
    calibration = pd.DataFrame(
        [
            {"engine_id": engine, "actuator": value, "sensor": 2.0}
            for engine in (5, 6)
            for value in (-1.8, -1.2, -0.6, 0.6, 1.2, 1.8)
        ]
    )
    probabilities = bundle.predict_risk(calibration)
    bundle.calibrator = ProbabilityCalibrator("sigmoid").fit(
        probabilities, (calibration.actuator < 0).astype(int).to_numpy()
    )
    bundle.model_type = "mlp"
    bundle.metrics = {
        "dataset": "FD001",
        "horizon_H": config.horizon_H,
        "calibration": {
            "fit_engine_ids": sorted(calibration.engine_id.unique().tolist()),
            "validation_after": calibration_diagnostics(
                (calibration.actuator < 0).astype(int).to_numpy(), bundle.predict_risk(calibration)
            ),
        },
    }
    config.artifacts.model = config.paths.model = directory / "model.joblib"
    config.artifacts.mahalanobis = config.paths.mahalanobis = directory / "validator.joblib"
    config.artifacts.coupling = None
    config.pipeline.taxonomy_path = directory / "features.yaml"
    config.pipeline.taxonomy_path.write_text(
        yaml.safe_dump(taxonomy.model_dump(mode="json")), encoding="utf-8"
    )
    save_model_bundle(bundle, config.artifacts.model)
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    save_mahalanobis_validator(validator, config.artifacts.mahalanobis)
    profile = directory / "pipeline.yaml"
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    observed = pd.DataFrame(
        [
            {
                "engine_id": engine,
                "cycle": cycle,
                "actuator": value,
                "sensor": 2.0,
                "rul": 99,
                "y": 1,
            }
            for engine, values in ((7, (-2.0, -1.0, 2.0)), (8, (2.0, 0.5, -2.0)))
            for cycle, value in enumerate(values, 1)
        ]
    )
    observed.to_csv(directory / "observed.csv", index=False)
    settings = directory / "dashboard.yaml"
    settings.write_text(
        yaml.safe_dump(
            {
                "profiles": {"FD001": {"Fixture MLP / v1": str(profile)}},
                "telemetry_path": str(directory / "observed.csv"),
                "report_directory": str(directory / "no_saved_evidence"),
            }
        ),
        encoding="utf-8",
    )
    return settings
