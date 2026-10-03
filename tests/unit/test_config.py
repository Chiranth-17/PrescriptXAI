"""Configuration validation tests."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from prescriptxai.config import AppConfig, load_config


def test_default_yaml_loads_and_has_expected_thresholds() -> None:
    """The checked-in defaults load with the project's configured risk thresholds."""
    config = load_config(Path("configs/default.yaml"))

    assert config.model.danger_threshold == 0.80
    assert config.model.safe_threshold == 0.20
    assert config.data.failure_horizon == 30
    assert config.validation.simulator_enabled is False


@pytest.mark.parametrize("document", ["", "null", "[]", "3"])
def test_non_mapping_yaml_is_rejected(tmp_path: Path, document: str) -> None:
    """Empty and non-mapping YAML roots fail explicitly."""
    path = tmp_path / "bad.yaml"
    path.write_text(document, encoding="utf-8")

    with pytest.raises(ValueError, match="root must be a mapping"):
        load_config(path)


def test_invalid_threshold_order_is_rejected() -> None:
    """Safe threshold cannot be at or above the danger threshold."""
    values = {
        "seed": 1,
        "data": {
            "root": "raw",
            "processed_root": "processed",
            "dataset": "FD001",
            "rul_cap": 125,
            "failure_horizon": 30,
            "train_fraction": 0.7,
            "validation_fraction": 0.15,
            "test_fraction": 0.15,
        },
        "model": {
            "danger_threshold": 0.2,
            "safe_threshold": 0.2,
            "calibration_method": "sigmoid",
        },
        "recourse": {
            "max_changed_features": 3,
            "max_scaled_distance": 4,
            "prediction_weight": 10,
            "immutable_weight": 1_000_000,
            "max_iterations": 10,
        },
        "validation": {
            "mahalanobis_max": 5,
            "covariance_regularization": 1e-6,
            "simulator_enabled": False,
        },
        "evaluation": {"random_seed": 1},
    }

    with pytest.raises(ValidationError, match="safe_threshold must be lower"):
        AppConfig.model_validate(values)


def test_split_fraction_sum_is_enforced(tmp_path: Path) -> None:
    """Fractions that do not partition engines are rejected."""
    source = Path("configs/default.yaml").read_text(encoding="utf-8")
    path = tmp_path / "bad_split.yaml"
    path.write_text(source.replace("test_fraction: 0.15", "test_fraction: 0.20"), encoding="utf-8")

    with pytest.raises(ValidationError, match="fractions must sum to 1"):
        load_config(path)
