"""Typed loading and validation of project YAML configuration."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataConfig(BaseModel):
    """Dataset and engine split settings."""

    model_config = ConfigDict(extra="forbid")

    root: Path
    processed_root: Path
    dataset: str = Field(pattern=r"^FD00[1-4]$")
    dataset_url: str = Field(min_length=1)
    download_timeout_seconds: int = Field(gt=0)
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
    calibration_folds: int = Field(default=5, ge=2)
    risk_estimator: Literal["xgboost", "torch"] = "xgboost"
    xgb_n_estimators: int = Field(default=250, ge=1)
    xgb_max_depth: int = Field(default=4, ge=1)
    xgb_learning_rate: float = Field(default=0.05, gt=0, le=1)
    xgb_subsample: float = Field(default=0.8, gt=0, le=1)
    xgb_colsample_bytree: float = Field(default=0.8, gt=0, le=1)
    xgb_reg_lambda: float = Field(default=1.0, ge=0)
    torch_hidden_dims: list[int] = Field(default_factory=lambda: [64, 32], min_length=1)
    torch_learning_rate: float = Field(default=0.001, gt=0)
    torch_epochs: int = Field(default=100, ge=1)
    torch_batch_size: int = Field(default=128, ge=1)
    torch_device: Literal["cpu", "cuda"] = "cpu"

    @model_validator(mode="after")
    def safe_below_danger(self) -> "ModelConfig":
        """Ensure the safe target is stricter than the high-risk gate."""
        if self.safe_threshold >= self.danger_threshold:
            raise ValueError("safe_threshold must be lower than danger_threshold")
        if any(width <= 0 for width in self.torch_hidden_dims):
            raise ValueError("torch_hidden_dims values must be positive")
        return self


class RecourseConfig(BaseModel):
    """Optimization weights and recourse complexity limits."""

    model_config = ConfigDict(extra="forbid")

    max_changed_features: int = Field(ge=1)
    max_scaled_distance: float = Field(gt=0)
    prediction_weight: float = Field(gt=0)
    max_iterations: int = Field(ge=1)
    solver_ftol: float = Field(gt=0)
    safety_margin: float = Field(default=0.005, ge=0, lt=1)


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

    @model_validator(mode="after")
    def recourse_margin_below_safe_target(self) -> "AppConfig":
        """Keep the optimizer's conservative numerical margin below the target risk."""
        if self.recourse.safety_margin >= self.model.safe_threshold:
            raise ValueError("recourse safety_margin must be below model safe_threshold")
        return self


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
