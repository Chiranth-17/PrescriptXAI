"""Raw-format synthetic telemetry for genuine temp-directory system tests, never efficacy claims."""

import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from fixtures.cmapss import make_cmapss_frame
from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import FeatureTaxonomy, load_taxonomy
from prescriptxai.data.cmapss import load_cmapss_archive
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.models.train import TrainingResult, train_risk_model
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, save_mahalanobis_validator
from prescriptxai.validation.tier4_coupling import calibrate_coupling_thresholds

PARTITIONS = ((1, 2, 3, 4), (5, 6), (7, 8))


def raw_fixture(directory: Path) -> tuple[pd.DataFrame, AppConfig, FeatureTaxonomy]:
    """Write and parse actual whitespace archive members with a fixed synthetic progression."""
    frame = make_cmapss_frame(8, 80, 80)
    rng = np.random.default_rng(17)
    for sensor in range(1, 22):
        # Remove fixture engine-ID trend: held-out engines follow the same synthetic law.
        frame[f"s{sensor}"] = (
            sensor * 10 + frame.cycle * sensor / 100 + rng.normal(0, 0.002, len(frame))
        )
    archive_path = directory / "raw.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("train_FD001.txt", frame.to_csv(sep=" ", header=False, index=False))
        observed = frame.loc[(frame.unit_id <= 2) & (frame.cycle <= 40)]
        archive.writestr("test_FD001.txt", observed.to_csv(sep=" ", header=False, index=False))
        archive.writestr("RUL_FD001.txt", "40\n40\n")
    loaded = load_cmapss_archive(archive_path, "FD001")
    config = load_config(Path("configs/default.yaml"))
    config.seed = 17
    config.evaluation.random_seed = 17
    config.model_choice = config.model.risk_estimator = "torch"
    config.model.torch_hidden_dims = [8]
    config.model.torch_epochs = 40
    config.model.torch_learning_rate = 0.03
    config.model.torch_early_stopping_patience = 8
    config.recourse.max_iterations = 3
    config.recourse.restarts = config.recourse.alpha_steps = 1
    config.recourse.l1_escalation_steps = config.recourse.support_search_limit = 1
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    return loaded.train, config, taxonomy


@dataclass
class FittedSystem:
    """Paths and actual fit products shared by the system regression assertions."""

    training: TrainingResult
    profile: Path
    dashboard: Path


def fit_system(directory: Path) -> FittedSystem:
    """Execute real train/calibration/coupling/covariance fits with disjoint engine IDs."""
    raw, config, taxonomy = raw_fixture(directory)
    trained = train_risk_model(raw, config, taxonomy, "mlp", engine_partitions=PARTITIONS)
    train = trained.splits.train
    coupling = SensorCouplingModel.fit(
        train,
        taxonomy,
        training_engine_ids=PARTITIONS[0],
        failure_horizon=config.horizon_H,
        seed=17,
    )
    coupling = calibrate_coupling_thresholds(
        coupling,
        trained.splits.validation,
        PARTITIONS[1],
        reference_distribution="all_cycles",
        min_rul=0,
        evaluation_engine_ids=PARTITIONS[2],
    )
    config.artifacts.model = config.paths.model = directory / "model.joblib"
    config.artifacts.mahalanobis = config.paths.mahalanobis = directory / "validator.joblib"
    config.artifacts.coupling = directory / "coupling.joblib"
    config.pipeline.taxonomy_path = directory / "features.yaml"
    config.pipeline.taxonomy_path.write_text(
        yaml.safe_dump(taxonomy.model_dump(mode="json")), encoding="utf-8"
    )
    save_model_bundle(trained.bundle, config.artifacts.model)
    coupling.save(config.artifacts.coupling)
    save_mahalanobis_validator(
        fit_mahalanobis_validator(train, trained.bundle, PARTITIONS[0], config),
        config.artifacts.mahalanobis,
    )
    profile = directory / "pipeline.yaml"
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    telemetry = directory / "observed.csv"
    trained.splits.test.to_csv(telemetry, index=False)
    dashboard = directory / "dashboard.yaml"
    dashboard.write_text(
        yaml.safe_dump(
            {
                "profiles": {"FD001": {"Synthetic temp E2E MLP / v1": str(profile)}},
                "telemetry_path": str(telemetry),
                "report_directory": str(directory / "absent_reports"),
            }
        ),
        encoding="utf-8",
    )
    return FittedSystem(trained, profile, dashboard)
