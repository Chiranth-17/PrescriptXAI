"""Typed loading and validation of project YAML configuration."""

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class ExpectedRowCountsConfig(BaseModel):
    """Published C-MAPSS file row counts used for archive integrity checks."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    train: int = Field(gt=0)
    test: int = Field(gt=0)
    test_rul: int = Field(gt=0)


class DataConfig(BaseModel):
    """Dataset and engine split settings."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    root: Path
    processed_root: Path
    archive_name: str = Field(min_length=5)
    dataset: Literal["FD001", "FD002", "FD003", "FD004"]
    dataset_url: str = Field(min_length=1)
    dataset_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    expected_row_counts: dict[
        Literal["FD001", "FD002", "FD003", "FD004"], ExpectedRowCountsConfig
    ] = Field(default_factory=dict)
    download_timeout_seconds: int = Field(gt=0)
    rul_cap: int | None = Field(default=None, gt=0)
    failure_horizon: int = Field(gt=0)
    variance_threshold: float = Field(ge=0)
    regime_k: int = Field(ge=1)
    lifetime_buckets: int = Field(ge=1)
    rolling_features: bool
    rolling_window: int = Field(ge=1)
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


class ArtifactConfig(BaseModel):
    """Configured paths for model, validator, and evaluation artifacts."""

    model: Path
    mahalanobis: Path
    evaluation_report: Path
    coupling: Path | None = None


class ApiConfig(BaseModel):
    """Optional HTTP service bind settings."""

    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    cors_origins: list[str] = Field(default_factory=list)
    cors_methods: list[str] = Field(default_factory=lambda: ["GET", "POST"])
    cors_headers: list[str] = Field(
        default_factory=lambda: ["Content-Type", "X-API-Key", "X-Request-ID"]
    )
    api_key_env: str = "PRESCRIPTXAI_API_KEY"
    max_payload_bytes: int = Field(default=1048576, ge=1)


class ModelConfig(BaseModel):
    """Risk gate and probability calibration settings."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    danger_threshold: float = Field(ge=0, le=1)
    safe_threshold: float = Field(ge=0, le=1)
    calibration_method: str = Field(pattern=r"^(sigmoid|isotonic|temperature)$")
    calibration_folds: int = Field(default=5, ge=2)
    calibration_bins: int = Field(default=10, ge=2)
    risk_estimator: Literal["xgboost", "torch", "lstm"] = "xgboost"
    xgb_n_estimators: int = Field(default=250, ge=1)
    xgb_max_depth: int = Field(default=4, ge=1)
    xgb_learning_rate: float = Field(default=0.05, gt=0, le=1)
    xgb_subsample: float = Field(default=0.8, gt=0, le=1)
    xgb_colsample_bytree: float = Field(default=0.8, gt=0, le=1)
    xgb_reg_lambda: float = Field(default=1.0, ge=0)
    xgb_early_stopping_rounds: int = Field(default=20, ge=1)
    torch_hidden_dims: list[int] = Field(default_factory=lambda: [64, 32], min_length=1)
    torch_learning_rate: float = Field(default=0.001, gt=0)
    torch_epochs: int = Field(default=100, ge=1)
    torch_batch_size: int = Field(default=128, ge=1)
    torch_early_stopping_patience: int = Field(default=12, ge=1)
    torch_gradient_clip_norm: float = Field(default=1.0, gt=0)
    torch_deterministic: bool = True
    torch_device: Literal["cpu", "cuda"] = "cpu"
    lstm_window: int = Field(default=10, ge=1)

    @model_validator(mode="after")
    def safe_below_danger(self) -> "ModelConfig":
        """Ensure the safe target is stricter than the high-risk gate."""
        if self.safe_threshold >= self.danger_threshold:
            raise ValueError("safe_threshold must be lower than danger_threshold")
        if any(width <= 0 for width in self.torch_hidden_dims):
            raise ValueError("torch_hidden_dims values must be positive")
        return self


class RecourseConfig(BaseModel):
    """Optimization weights, numerical choices, and recourse complexity limits."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    max_changed_features: int = Field(
        ge=1, validation_alias=AliasChoices("k_max", "max_changed_features")
    )
    max_scaled_distance: float = Field(gt=0)
    rate_horizon_steps: int = Field(default=1, ge=1)
    prediction_weight: float = Field(
        gt=0, validation_alias=AliasChoices("alpha", "prediction_weight")
    )
    beta: float = Field(ge=0)
    gamma: float = Field(ge=0)
    max_iterations: int = Field(ge=1, validation_alias=AliasChoices("max_iter", "max_iterations"))
    solver_ftol: float = Field(gt=0)
    safety_margin: float = Field(default=0.005, ge=0, lt=1)
    l1_mode: Literal["smooth", "split"] = "smooth"
    l1_weight: float = Field(default=1.0, gt=0)
    l1_smoothing_epsilon: float = Field(default=1e-6, gt=0)
    prediction_loss: Literal["hinge", "squared_hinge"] = "squared_hinge"
    restarts: int = Field(default=2, ge=1)
    alpha_growth: float = Field(default=2.0, gt=1)
    alpha_steps: int = Field(default=4, ge=1)
    l1_growth: float = Field(default=2.0, gt=1)
    l1_escalation_steps: int = Field(default=3, ge=1)
    support_search_top_m: int = Field(default=5, ge=1)
    support_search_limit: int = Field(default=8, ge=1)
    true_model_grid_enabled: bool = True
    true_model_grid_points: int = Field(default=5, ge=2)
    search_mode: Literal["fast", "thorough"] = "thorough"
    record_candidate_trace: bool = False
    change_tolerance: float = Field(default=1e-7, ge=0)
    max_line_search_steps: int = Field(default=20, ge=1)

    @property
    def k_max(self) -> int:
        """Maximum number of changed controls in the phase-zero vocabulary."""
        return self.max_changed_features

    @property
    def alpha(self) -> float:
        """Prediction-flip loss weight in the phase-zero vocabulary."""
        return self.prediction_weight

    @property
    def max_iter(self) -> int:
        """Maximum optimizer iterations in the phase-zero vocabulary."""
        return self.max_iterations


class ValidationConfig(BaseModel):
    """Plausibility and optional simulator settings."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    mahalanobis_max: float = Field(gt=0, validation_alias=AliasChoices("D_max", "mahalanobis_max"))
    covariance_regularization: float = Field(gt=0)
    simulator_enabled: bool
    d_max_method: Literal["mahalanobis"]
    d_max_threshold_method: Literal["fixed", "empirical_quantile", "chi_square_quantile"] = "fixed"
    d_max_quantile: float = Field(gt=0, le=1)
    rate_limits: dict[str, float]
    reference_distribution: Literal["all_cycles", "healthy_to_moderate"] = "all_cycles"
    healthy_min_rul: int = Field(default=30, ge=0)
    regime_k: int = Field(default=6, ge=1)
    mode: Literal["collect_all", "fail_fast"] = "collect_all"
    surrogate_disagreement_threshold: float = Field(default=0.1, ge=0, le=1)
    feedback_max_refinements: int = Field(default=2, ge=0)
    feedback_penalty_weight: float = Field(default=10.0, gt=0)
    feedback_penalty_growth: float = Field(default=10.0, gt=1)
    coupling_calibration_reference: Literal["all_cycles", "healthy_to_moderate"] = (
        "healthy_to_moderate"
    )

    @model_validator(mode="after")
    def valid_rate_limits(self) -> "ValidationConfig":
        """Ensure configured per-feature rate limits are positive and finite."""
        if any(not name.strip() or value <= 0 for name, value in self.rate_limits.items()):
            raise ValueError("rate_limits must map non-empty feature names to positive values")
        if self.d_max_threshold_method == "chi_square_quantile" and self.d_max_quantile == 1:
            raise ValueError("chi-square quantile must be less than one")
        return self


class EvaluationConfig(BaseModel):
    """Reproducible evaluation settings."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    bootstrap_replicates: int = Field(default=2000, ge=1)
    development_max_queries: int = Field(default=60, ge=1)

    random_seed: int = Field(ge=0)
    max_queries: int = Field(ge=1)
    direction_similarity_radius: float = Field(default=1.0, ge=0)
    recourse_validity_rate: float = Field(ge=0, le=1)
    physical_plausibility_rate: float = Field(ge=0, le=1)
    average_sparsity_max: int = Field(ge=0)
    mean_risk_drop_min: float = Field(ge=0, le=1)
    ingestion_max_ms: float = Field(gt=0)
    inference_max_ms: float = Field(gt=0)
    optimization_min_ms: float = Field(gt=0)
    optimization_max_ms: float = Field(gt=0)
    validation_max_ms: float = Field(gt=0)
    dashboard_max_ms: float = Field(gt=0)
    pipeline_min_ms: float = Field(gt=0)
    pipeline_max_ms: float = Field(gt=0)

    @model_validator(mode="after")
    def latency_bounds_ordered(self) -> "EvaluationConfig":
        """Require an ordered optimization latency target range."""
        if self.optimization_min_ms > self.optimization_max_ms:
            raise ValueError("optimization_min_ms must not exceed optimization_max_ms")
        if self.pipeline_min_ms > self.pipeline_max_ms:
            raise ValueError("pipeline_min_ms must not exceed pipeline_max_ms")
        return self


class FollowUpSettings(BaseModel):
    """Presentation and demo settings for locally replayed operator feedback."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    followed_at: float = Field(default=0.80, gt=0, le=1)
    partial_at: float = Field(default=0.40, ge=0, lt=1)
    trend_steps: int = Field(default=30, ge=1, le=30)
    demo_seed: int = Field(default=1729, ge=0)
    demo_count: int = Field(default=5, ge=1, le=30)

    @model_validator(mode="after")
    def ordered_labels(self) -> "FollowUpSettings":
        """Keep adherence categories disjoint and ordered."""
        if self.partial_at >= self.followed_at:
            raise ValueError("partial_at must be below followed_at")
        return self

    def adherence_label(self, score: float) -> str:
        """Describe the measured agreement with the recommended settings."""
        if score >= self.followed_at:
            return "Followed as recommended"
        return "Followed partly" if score >= self.partial_at else "Not followed"


class LatencyBudgetConfig(BaseModel):
    """Synopsis latency targets, in milliseconds, mapped to measured stages."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    ingestion_max_ms: float = Field(gt=0)
    inference_max_ms: float = Field(gt=0)
    optimization_min_ms: float = Field(gt=0)
    optimization_max_ms: float = Field(gt=0)
    validation_max_ms: float = Field(gt=0)
    dashboard_max_ms: float = Field(gt=0)
    pipeline_min_ms: float = Field(gt=0)
    pipeline_max_ms: float = Field(gt=0)

    @model_validator(mode="after")
    def ordered_ranges(self) -> "LatencyBudgetConfig":
        """Reject inverted optimization and full-pipeline target intervals."""
        if self.optimization_min_ms > self.optimization_max_ms:
            raise ValueError("optimization latency minimum must not exceed its maximum")
        if self.pipeline_min_ms > self.pipeline_max_ms:
            raise ValueError("pipeline latency minimum must not exceed its maximum")
        return self


class PathsConfig(BaseModel):
    """Configured filesystem locations for data and fitted artifacts."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    raw_data: Path
    processed_data: Path
    model: Path
    mahalanobis: Path
    evaluation_report: Path


class PipelineConfig(BaseModel):
    """Public input, concurrency, triage and artifact policies."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    taxonomy_path: Path = Path("configs/features.yaml")
    delta_min: float = Field(default=0.30, ge=0, le=1)
    default_mode: Literal["fast", "thorough"] = "fast"
    max_batch_rows: int = Field(default=1024, ge=1)
    batch_workers: int = Field(default=1, ge=1)
    max_workers: int = Field(default=4, ge=1)
    artifact_cache_size: int = Field(default=4, ge=1)
    benchmark_warmups: int = Field(default=1, ge=0)
    benchmark_repeats: int = Field(default=1, ge=1)
    escalation_message: str = "Schedule maintenance and obtain domain review before intervention."
    model_artifacts: dict[str, ArtifactConfig] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """Complete PrescriptXAI configuration."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    seed: int = Field(ge=0)
    horizon_H: int = Field(gt=0)
    tau_danger: float = Field(ge=0, le=1)
    tau_safe: float = Field(ge=0, le=1)
    dataset_subsets: tuple[Literal["FD001", "FD002", "FD003", "FD004"], ...] = Field(min_length=1)
    model_choice: Literal["xgboost", "torch", "lstm"]
    paths: PathsConfig
    latency_budget: LatencyBudgetConfig
    artifacts: ArtifactConfig
    api: ApiConfig
    data: DataConfig
    model: ModelConfig
    recourse: RecourseConfig
    validation: ValidationConfig
    evaluation: EvaluationConfig

    @model_validator(mode="before")
    @classmethod
    def sync_phase_zero_configuration(cls, value: object) -> object:
        """Map phase-zero top-level keys onto the established runtime config models."""
        if not isinstance(value, dict):
            return value
        raw = dict(value)
        for section in ("model", "data", "artifacts", "paths", "evaluation", "api"):
            if section in raw and not isinstance(raw[section], dict):
                if isinstance(raw[section], BaseModel):
                    raw[section] = raw[section].model_dump()
                else:
                    raise ValueError(f"configuration section {section} must be a mapping")
        for root, section, key in (
            ("tau_safe", "model", "safe_threshold"),
            ("tau_danger", "model", "danger_threshold"),
            ("horizon_H", "data", "failure_horizon"),
            ("model_choice", "model", "risk_estimator"),
        ):
            if root in raw and key in raw.get(section, {}):
                left, right = raw[root], raw[section][key]
                if root == "model_choice":
                    aliases = {"xgb": "xgboost", "mlp": "torch"}
                    left = aliases.get(left, left) if isinstance(left, str) else left
                    right = aliases.get(right, right) if isinstance(right, str) else right
                if left != right:
                    raise ValueError(f"conflicting {root} and {section}.{key} must match")
        model = dict(raw.get("model", {}))
        data = dict(raw.get("data", {}))
        artifacts = dict(raw.get("artifacts", {}))
        paths = raw.get("paths", {})
        if isinstance(paths, dict):
            for root_key, runtime_values, nested_key in (
                ("raw_data", data, "root"),
                ("processed_data", data, "processed_root"),
                ("model", artifacts, "model"),
                ("mahalanobis", artifacts, "mahalanobis"),
                ("evaluation_report", artifacts, "evaluation_report"),
            ):
                if root_key in paths and nested_key in runtime_values:
                    left, right = paths[root_key], runtime_values[nested_key]
                    if isinstance(left, (str, Path)) and isinstance(right, (str, Path)):
                        left, right = Path(left), Path(right)
                    if left != right:
                        raise ValueError(
                            f"conflicting paths.{root_key} and runtime paths must match"
                        )
            data["root"] = paths.get("raw_data", data.get("root"))
            data["processed_root"] = paths.get("processed_data", data.get("processed_root"))
            for name in ("model", "mahalanobis", "evaluation_report"):
                artifacts[name] = paths.get(name, artifacts.get(name))
        if "horizon_H" in raw:
            data["failure_horizon"] = raw["horizon_H"]
        if "tau_danger" in raw:
            model["danger_threshold"] = raw["tau_danger"]
        if "tau_safe" in raw:
            model["safe_threshold"] = raw["tau_safe"]
        if "model_choice" in raw:
            if isinstance(raw["model_choice"], str):
                raw["model_choice"] = {"xgb": "xgboost", "mlp": "torch"}.get(
                    raw["model_choice"], raw["model_choice"]
                )
            model["risk_estimator"] = raw["model_choice"]
        raw["model"] = model
        raw["data"] = data
        raw["artifacts"] = artifacts
        budget = raw.get("latency_budget")
        if isinstance(budget, dict):
            evaluation = dict(raw.get("evaluation", {}))
            if any(key in evaluation and evaluation[key] != item for key, item in budget.items()):
                raise ValueError("conflicting latency_budget and evaluation settings must match")
            evaluation.update(budget)
            raw["evaluation"] = evaluation
        return raw

    @model_validator(mode="after")
    def recourse_margin_below_safe_target(self) -> "AppConfig":
        """Keep the optimizer's conservative numerical margin below the target risk."""
        if self.recourse.safety_margin >= self.model.safe_threshold:
            raise ValueError("recourse safety_margin must be below model safe_threshold")
        if self.tau_safe >= self.tau_danger:
            raise ValueError("tau_safe must be lower than tau_danger")
        if (
            self.model.safe_threshold != self.tau_safe
            or self.model.danger_threshold != self.tau_danger
        ):
            raise ValueError("top-level thresholds and model thresholds must match")
        if self.data.failure_horizon != self.horizon_H:
            raise ValueError("horizon_H must match data.failure_horizon")
        if self.data.dataset not in self.dataset_subsets:
            raise ValueError("selected dataset must be listed in dataset_subsets")
        if len(set(self.dataset_subsets)) != len(self.dataset_subsets):
            raise ValueError("dataset_subsets must not contain duplicates")
        if self.model.risk_estimator != self.model_choice:
            raise ValueError("model_choice must match model.risk_estimator")
        if self.seed != self.evaluation.random_seed:
            raise ValueError("seed must match evaluation.random_seed")
        if (
            self.paths.raw_data != self.data.root
            or self.paths.processed_data != self.data.processed_root
        ):
            raise ValueError("paths data directories must match data settings")
        if (
            self.paths.model != self.artifacts.model
            or self.paths.mahalanobis != self.artifacts.mahalanobis
            or self.paths.evaluation_report != self.artifacts.evaluation_report
        ):
            raise ValueError("paths artifact locations must match artifacts settings")
        if self.evaluation.model_fields_set and any(
            getattr(self.evaluation, key) != getattr(self.latency_budget, key)
            for key in (
                "ingestion_max_ms",
                "inference_max_ms",
                "optimization_min_ms",
                "optimization_max_ms",
                "validation_max_ms",
                "dashboard_max_ms",
                "pipeline_min_ms",
                "pipeline_max_ms",
            )
        ):
            raise ValueError("latency_budget and evaluation latency settings must match")
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
    raw = _apply_environment_overrides(raw)
    return AppConfig.model_validate(raw)


def _apply_environment_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply ``PRESCRIPTXAI_`` variables using ``__`` for nested YAML keys."""
    result = dict(raw)
    env_prefix = "PRESCRIPTXAI_"
    service_variables = {
        "PRESCRIPTXAI_DASHBOARD_CONFIG",
        "PRESCRIPTXAI_API_KEY",
        "PRESCRIPTXAI_API_TOKEN",
        "PRESCRIPTXAI_AUTH_ORIGIN",
        "PRESCRIPTXAI_OPERATOR_PASSWORD_HASH",
        "PRESCRIPTXAI_ADMIN_PASSWORD_HASH",
        "PRESCRIPTXAI_TLS_CERTFILE",
        "PRESCRIPTXAI_TLS_KEYFILE",
        "PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS",
        "PRESCRIPTXAI_ARTIFACT_MANIFEST",
    }
    api_settings = raw.get("api", {})
    if not isinstance(api_settings, dict):
        raise ValueError("configuration section api must be a mapping")
    configured_key = api_settings.get("api_key_env")
    if isinstance(configured_key, str):
        service_variables.add(configured_key)
    changed: set[tuple[str, ...]] = set()
    for env_name, env_value in os.environ.items():
        if not env_name.startswith(env_prefix) or env_name in service_variables:
            continue
        path_parts = tuple(part.lower() for part in env_name[len(env_prefix) :].split("__"))
        path = tuple("horizon_H" if part == "horizon_h" else part for part in path_parts)
        if not path or any(not part for part in path):
            raise ValueError(f"invalid environment override name: {env_name}")
        cursor = result
        for part in path[:-1]:
            child = cursor.setdefault(part, {})
            if not isinstance(child, dict):
                raise ValueError(f"environment override {env_name} conflicts with a scalar setting")
            cursor = child
        try:
            cursor[path[-1]] = yaml.safe_load(env_value)
        except yaml.YAMLError as error:
            raise ValueError(f"invalid YAML value in environment override {env_name}") from error
        changed.add(path)

    alias_paths = (
        (("seed",), ("evaluation", "random_seed")),
        (("tau_danger",), ("model", "danger_threshold")),
        (("tau_safe",), ("model", "safe_threshold")),
        (("horizon_H",), ("data", "failure_horizon")),
        (("model_choice",), ("model", "risk_estimator")),
        (("paths", "raw_data"), ("data", "root")),
        (("paths", "processed_data"), ("data", "processed_root")),
        (("paths", "model"), ("artifacts", "model")),
        (("paths", "mahalanobis"), ("artifacts", "mahalanobis")),
        (("paths", "evaluation_report"), ("artifacts", "evaluation_report")),
        (("validation", "d_max"), ("validation", "D_max")),
    )
    for root_path, runtime_path in alias_paths:
        if (
            root_path in changed
            and runtime_path in changed
            and _nested_get(result, root_path) != _nested_get(result, runtime_path)
        ):
            raise ValueError("conflicting explicit environment aliases")
        source, target = (
            (root_path, runtime_path) if root_path in changed else (runtime_path, root_path)
        )
        if source in changed:
            value = _nested_get(result, source)
            _nested_set(result, target, value)
    return result


def _nested_get(document: dict[str, Any], path: tuple[str, ...]) -> object:
    """Read one nested configuration value."""
    value: object = document
    for part in path:
        if not isinstance(value, dict):
            raise ValueError(f"configuration path {'.'.join(path)} is not a mapping")
        value = value[part]
    return value


def _nested_set(document: dict[str, Any], path: tuple[str, ...], value: object) -> None:
    """Set one nested configuration value, creating intermediate mappings."""
    cursor = document
    for part in path[:-1]:
        child = cursor.setdefault(part, {})
        if not isinstance(child, dict):
            raise ValueError(f"cannot override nested configuration key {'.'.join(path)}")
        cursor = child
    cursor[path[-1]] = value
