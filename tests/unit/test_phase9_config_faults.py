"""Malformed and contradictory configurations cannot silently alter effective limits."""

from pathlib import Path

import pytest
import yaml

from prescriptxai.config import AppConfig, load_config


@pytest.mark.parametrize("section", ["model", "data", "artifacts", "evaluation", "api"])
def test_null_configuration_section_is_a_clear_value_error(tmp_path: Path, section: str) -> None:
    """Configuration errors cannot escape as raw dict(None) or None.get tracebacks."""
    values = load_config(Path("configs/default.yaml")).model_dump(mode="json")
    values[section] = None
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(values), encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_config(path)


@pytest.mark.parametrize(
    ("section", "field", "conflict"),
    [
        ("model", "safe_threshold", 0.9),
        ("data", "failure_horizon", 99),
        ("evaluation", "dashboard_max_ms", 999),
    ],
)
def test_duplicate_config_aliases_cannot_disagree(
    section: str, field: str, conflict: float
) -> None:
    """An explicit contradictory duplicate is rejected rather than overwritten."""
    values = load_config(Path("configs/default.yaml")).model_dump(mode="json")
    values[section][field] = conflict
    with pytest.raises(ValueError, match="conflict|match"):
        AppConfig.model_validate(values)


def test_conflicting_explicit_environment_aliases_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two explicitly supplied environment values cannot silently select one risk gate."""
    monkeypatch.setenv("PRESCRIPTXAI_TAU_SAFE", "0.15")
    monkeypatch.setenv("PRESCRIPTXAI_MODEL__SAFE_THRESHOLD", "0.3")
    with pytest.raises(ValueError, match="conflict"):
        load_config(Path("configs/default.yaml"))
