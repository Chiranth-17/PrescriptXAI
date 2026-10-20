"""Persisted analytic test models and telemetry; never imported by real studies."""

from pathlib import Path

import pandas as pd
import yaml

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.taxonomy import BoundsSpec, FeatureGroup, FeatureSpec
from prescriptxai.data.preprocess import fit_feature_scaler
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, save_mahalanobis_validator


def fitted_experiment(tmp_path: Path) -> tuple[AppConfig, pd.DataFrame]:
    """Fit an actual scaler and covariance around the test-only sigmoid risk function."""
    bundle, taxonomy, training = make_recourse_fixture()
    rename = {"actuator": "sensor_1", "sensor": "sensor_2"}
    training = training.rename(columns=rename)
    training["cycle"] = training.groupby("engine_id").cumcount() + 1
    training["rul"] = 2 - training.cycle
    bundle.feature_names = ("sensor_1", "sensor_2")
    bundle.scaler = fit_feature_scaler(training, bundle.feature_names)
    bundle.model_type = "mlp"
    bundle.metrics = {
        "split_engines": {"train": [1, 2, 3, 4], "validation": [5], "test_holdout": [6]}
    }
    taxonomy.features = tuple(
        spec.model_copy(update={"name": rename[spec.name]}) for spec in taxonomy.features
    ) + tuple(
        FeatureSpec(
            name=n,
            label=n,
            unit="-",
            cmapss_column=n,
            group="context",
            bounds=BoundsSpec(minimum=1, maximum=1000),
        )
        for n in ("engine_id", "cycle")
    )
    taxonomy.feature_groups.controllable_actuators = FeatureGroup(features=["sensor_1"])
    taxonomy.feature_groups.dependent_sensors = FeatureGroup(features=["sensor_2"])
    taxonomy.feature_groups.context = FeatureGroup(features=["engine_id", "cycle"])
    taxonomy.actuator_constraints = {"sensor_1": taxonomy.actuator_constraints["actuator"]}
    taxonomy.coupling_rules = [
        rule.model_copy(update={"feature_a": "sensor_1", "feature_b": "sensor_2"})
        for rule in taxonomy.coupling_rules
    ]
    config = load_config(Path("configs/experiments/phase6-pipeline-v1.yaml"))
    config.model_choice = config.model.risk_estimator = "torch"
    config.recourse.max_iterations = 2
    config.recourse.restarts = config.recourse.alpha_steps = config.recourse.l1_escalation_steps = 1
    config.artifacts.model = config.paths.model = tmp_path / "model.joblib"
    config.artifacts.mahalanobis = config.paths.mahalanobis = tmp_path / "validator.joblib"
    config.artifacts.coupling = None
    config.pipeline.taxonomy_path = tmp_path / "features.yaml"
    config.pipeline.taxonomy_path.write_text(
        yaml.safe_dump(taxonomy.model_dump(mode="json")), encoding="utf-8"
    )
    save_model_bundle(bundle, config.artifacts.model)
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    save_mahalanobis_validator(validator, config.artifacts.mahalanobis)
    frame = pd.DataFrame(
        [
            {"engine_id": 6, "cycle": i, "sensor_1": -2.0, "sensor_2": 2.0, "rul": 3 - i}
            for i in range(1, 4)
        ]
    )
    return config, frame
