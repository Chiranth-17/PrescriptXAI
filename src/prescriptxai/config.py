"""Typed loading and validation of project YAML configuration."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataConfig(BaseModel):
    """Dataset and engine split settings."""

    model_config = ConfigDict(extra="forbid")

    root: Path
    processed_root: Path
    dataset: str = Field(pattern=r"^FD00[1-4]$")
    rul_cap: int = Field(gt=0)
    failure_horizon: int = Field(gt=0)
    train_fraction: float = Field(gt=0, lt=1)
    validation_fraction: float = Field(gt=0, lt=1)
    test_fraction: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def fractions_sum_to_one(self) -> "DataConfig":
        """Require the three engine split fractions to partition the dataset."""
        total = self.train_fraction + self.validation_fraction + self.test_fraction
        if abs(total - 1.0) > 1e-9:
            raise ValueError("train, validation, and test fractions must sum to 1")
        return self


class ModelConfig(BaseModel):
    """Risk gate and probability calibration settings."""

    model_config = ConfigDict(extra="forbid")

    danger_threshold: float = Field(gt=0, le=1)
    safe_threshold: float = Field(gt=0, le=1)
    calibration_method: str = Field(pattern=r"^(sigmoid|isotonic)$")

    @model_validator(mode="after")
    def safe_below_danger(self) -> "ModelConfig":
        """Ensure the safe target is stricter than the high-risk gate."""
        if self.safe_threshold >= self.danger_threshold:
            raise ValueError("safe_threshold must be lower than danger_threshold")
        return self


class RecourseConfig(BaseModel):
    """Optimization weights and recourse complexity limits."""

    model_config = ConfigDict(extra="forbid")

    max_changed_features: int = Field(ge=1)
    max_scaled_distance: float = Field(gt=0)
    prediction_weight: float = Field(gt=0)
    immutable_weight: float = Field(gt=0)
    max_iterations: int = Field(ge=1)


class ValidationConfig(BaseModel):
    """Plausibility and optional simulator settings."""

    model_config = ConfigDict(extra="forbid")

    mahalanobis_max: float = Field(gt=0)
    covariance_regularization: float = Field(gt=0)
    simulator_enabled: bool


class EvaluationConfig(BaseModel):
    """Reproducible evaluation settings."""

    model_config = ConfigDict(extra="forbid")

    random_seed: int = Field(ge=0)


class AppConfig(BaseModel):
    """Complete PrescriptXAI configuration."""

    model_config = ConfigDict(extra="forbid")

    seed: int = Field(ge=0)
    data: DataConfig
    model: ModelConfig
    recourse: RecourseConfig
    validation: ValidationConfig
    evaluation: EvaluationConfig


def load_config(path: Path) -> AppConfig:
    """Load and validate an application config from a YAML file.

    Parameters
    ----------
    path:
        Path to a UTF-8 YAML configuration.

    Returns
    -------
    AppConfig
        Validated immutable-by-convention settings object.

    Raises
    ------
    ValueError
        If the YAML root is not a mapping.
    pydantic.ValidationError
        If fields are missing, unexpected, or out of range.
    yaml.YAMLError
        If the file contains invalid YAML syntax.
    OSError
        If the path cannot be read.
    """
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a mapping")
    return AppConfig.model_validate(raw)
