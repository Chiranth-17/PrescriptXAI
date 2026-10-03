"""Configuration validation tests."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from prescriptxai.config import AppConfig, load_config


def test_default_yaml_loads_and_has_expected_thresholds() -> None:
    """The checked-in defaults load with the project's configured risk thresholds."""
    config = load_config(Path("configs/default.yaml"))

    assert config.model.danger_threshold == 0.80
    assert config.model.safe_threshold == 0.20
    assert config.data.failure_horizon == 30
    assert config.horizon_H == 30
    assert config.tau_danger == 0.8
    assert config.tau_safe == 0.2
    assert config.dataset_subsets == ("FD001", "FD002", "FD003", "FD004")
    assert config.recourse.k_max == 3
    assert config.validation.d_max_method == "mahalanobis"
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
    values = yaml.safe_load(Path("configs/default.yaml").read_text(encoding="utf-8"))
    values["tau_danger"] = 0.2
    values["tau_safe"] = 0.2

    with pytest.raises(ValidationError, match="safe_threshold must be lower"):
        AppConfig.model_validate(values)


def test_negative_failure_horizon_is_rejected() -> None:
    """The configurable RUL failure horizon must be strictly positive."""
    values = yaml.safe_load(Path("configs/default.yaml").read_text(encoding="utf-8"))
    values["horizon_H"] = -1

    with pytest.raises(ValidationError, match="greater than 0"):
        AppConfig.model_validate(values)


def test_environment_overrides_are_typed_and_synchronized(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prefixed environment variables override YAML at root and nested paths."""
    monkeypatch.setenv("PRESCRIPTXAI_TAU_SAFE", "0.15")
    monkeypatch.setenv("PRESCRIPTXAI_RECOURSE__K_MAX", "2")
    monkeypatch.setenv("PRESCRIPTXAI_PATHS__RAW_DATA", "data/test-raw")

    config = load_config(Path("configs/default.yaml"))

    assert config.tau_safe == config.model.safe_threshold == 0.15
    assert config.recourse.k_max == 2
    assert config.data.root == Path("data/test-raw")


def test_split_fraction_sum_is_enforced(tmp_path: Path) -> None:
    """Fractions that do not partition engines are rejected."""
    source = Path("configs/default.yaml").read_text(encoding="utf-8")
    path = tmp_path / "bad_split.yaml"
    path.write_text(source.replace("test_fraction: 0.15", "test_fraction: 0.20"), encoding="utf-8")

    with pytest.raises(ValidationError, match="fractions must sum to 1"):
        load_config(path)
