"""Orchestration for independent model and physical validity tiers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import joblib
import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray

from prescriptxai.artifacts import ArtifactLoadError, load_trusted_joblib
from prescriptxai.config import AppConfig
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.models.registry import ModelBundle
from prescriptxai.schemas import DeltaMapping, RecourseOutcome
from prescriptxai.validation.base import EvidenceLevel, TierResult
from prescriptxai.validation.simulator import DynamicSimulator, run_simulator_validation
from prescriptxai.validation.tier1_model import validate_model_risk
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator
from prescriptxai.validation.tier3_engineering import validate_engineering
from prescriptxai.validation.tier4_coupling import validate_sensor_coupling

if TYPE_CHECKING:
    from prescriptxai.schemas import ValidationReport as PublicValidationReport


def save_mahalanobis_validator(validator: MahalanobisValidator, path: Path) -> Path:
    """Persist fitted Tier 2 statistics and training-engine provenance."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(validator, path)
    return path


def load_coupling_model(path: Path) -> SensorCouplingModel:
    """Load a persisted sensor coupling model when the artifact exists."""
    return SensorCouplingModel.load(path)


def try_load_coupling_model(path: Path) -> SensorCouplingModel | None:
    """Return a coupling model when configured and present on disk."""
    if not path.is_file():
        return None
    return load_coupling_model(path)


def load_mahalanobis_validator(
    path: Path, *, expected_sha256: str | None = None
) -> MahalanobisValidator:
    """Load fitted Tier 2 statistics from a configured local artifact."""
    if not path.is_file():
        raise FileNotFoundError(path)
    loaded: object = load_trusted_joblib(path, expected_sha256)
    if not isinstance(loaded, MahalanobisValidator):
        raise ValueError("artifact does not contain a MahalanobisValidator")
    if not hasattr(loaded, "covariance_cholesky"):
        raise ValueError("legacy precision-only validator: refit on training engines for Phase 5")
    try:
        width = len(loaded.feature_names)
        if not width or width != len(set(loaded.feature_names)) or not loaded.regime_statistics:
            raise ArtifactLoadError("Mahalanobis artifact has invalid features/regimes")
        if len(loaded.regime_statistics) > 1:
            if loaded.clusterer is None or loaded.settings_scaler is None:
                raise ArtifactLoadError("multi-regime artifact requires its fitted regime assigner")
            centers = np.asarray(loaded.clusterer.cluster_centers_)
            scale = np.asarray(loaded.settings_scaler.scale_)
            mean = np.asarray(loaded.settings_scaler.mean_)
            if (
                centers.ndim != 2
                or centers.shape[0] != len(loaded.regime_statistics)
                or scale.shape != (centers.shape[1],)
                or mean.shape != scale.shape
                or not np.isfinite(centers).all()
                or not np.isfinite(scale).all()
                or not np.isfinite(mean).all()
                or (scale <= 0).any()
            ):
                raise ArtifactLoadError(
                    "multi-regime artifact has invalid regime assigner statistics"
                )
        factors = [(loaded.mean, loaded.covariance_cholesky, loaded.max_distance)] + [
            (stats.mean, stats.cholesky, stats.max_distance)
            for stats in loaded.regime_statistics.values()
        ]
        for center, factor, cutoff in factors:
            if (
                np.shape(center) != (width,)
                or np.shape(factor) != (width, width)
                or not np.isfinite(center).all()
                or not np.isfinite(factor).all()
                or not np.array_equal(factor, np.tril(factor))
                or (np.diag(factor) <= 0).any()
                or not np.isfinite(cutoff)
                or cutoff <= 0
            ):
                raise ArtifactLoadError("Mahalanobis artifact has invalid covariance factor/cutoff")
    except (AttributeError, TypeError, KeyError) as error:
        raise ArtifactLoadError(
            "Mahalanobis artifact contains malformed fitted metadata"
        ) from error
    return loaded


def verify_validator_compatibility(
    validator: MahalanobisValidator, bundle: ModelBundle, config: AppConfig
) -> None:
    """Reject persisted statistics whose effective protocol differs from runtime labels."""
    if validator.feature_names != bundle.feature_names:
        raise ValueError("model and Mahalanobis artifacts have different feature orders")
    if set(validator.training_engine_ids) != set(bundle.training_engine_ids):
        raise ValueError("Mahalanobis fitting engines differ from model fitting engines")
    expected = config.validation
    if (
        validator.threshold_method != expected.d_max_threshold_method
        or validator.reference_distribution != expected.reference_distribution
        or validator.regularization != expected.covariance_regularization
        or (
            validator.threshold_method == "fixed"
            and validator.max_distance != expected.mahalanobis_max
        )
        or (
            validator.threshold_method != "fixed"
            and validator.threshold_quantile != expected.d_max_quantile
        )
    ):
        raise ValueError(
            "Mahalanobis artifact protocol differs from config; refit matching validation artifacts"
        )
    regimes = expected.regime_k if config.data.dataset in {"FD002", "FD004"} else 1
    if len(validator.regime_statistics) != regimes:
        raise ValueError("Mahalanobis artifact regime count differs from config")


@dataclass(frozen=True)
class ValidationReport:
    """Four separate tier results and aggregate outcome."""

    tier1_model: TierResult
    tier2_plausibility: TierResult
    tier3_engineering: TierResult
    tier4_coupling: TierResult
    simulator: TierResult = field(default_factory=lambda: TierResult.skipped("no simulator"))
    schema_version: str = "2.0.0"
    assumptions: tuple[str, ...] = (
        "C-MAPSS controllables and their bounds/rate limits are documented telemetry proxies.",
        "The intervention horizon K is an assumption, not validated actuator dynamics.",
    )

    @property
    def model_valid(self) -> bool:
        """Whether the predictor target-risk check passed."""
        return self.tier1_model.valid

    @property
    def physical_valid(self) -> bool:
        """Whether the three independent physical plausibility checks passed."""
        return all(
            tier.valid
            for tier in (self.tier2_plausibility, self.tier3_engineering, self.tier4_coupling)
        )

    @property
    def plausible(self) -> bool:
        """Whether Tier 2 alone passed (the distributional plausibility definition)."""
        return self.tier2_plausibility.valid

    @property
    def constraints_ok(self) -> bool:
        """Whether both proxy engineering and sensor-relationship checks passed."""
        return self.tier3_engineering.valid and self.tier4_coupling.valid

    @property
    def joint(self) -> bool:
        """Whether all four static tiers passed, independently of optimizer feasibility."""
        return self.model_valid and self.plausible and self.constraints_ok

    @property
    def failing_tiers(self) -> tuple[str, ...]:
        """Name failed checks without misclassifying unrun/skipped checks as passed."""
        return tuple(name for name, tier in self.tiers().items() if tier.status == "fail")

    @property
    def evidence_level(self) -> EvidenceLevel:
        """Report the highest contiguous evidence level actually reached."""
        if not self.model_valid:
            return "none"
        if not self.plausible:
            return "E1"
        if not self.constraints_ok:
            return "E2"
        if self.simulator.valid and self.simulator.evidence_level in {"E4", "E5"}:
            return self.simulator.evidence_level
        return "E3"

    def tiers(self) -> dict[str, TierResult]:
        """Return ordered tier names and complete diagnostics for adapters/reporting."""
        return {
            "tier1_model": self.tier1_model,
            "tier2_plausibility": self.tier2_plausibility,
            "tier3_engineering": self.tier3_engineering,
            "tier4_coupling": self.tier4_coupling,
            "simulator": self.simulator,
        }

    def as_dict(self) -> dict[str, object]:
        """Serialize independent verdicts, skipped checks, margins, and evidence."""
        return {
            "schema_version": self.schema_version,
            "tiers": {name: tier.as_dict() for name, tier in self.tiers().items()},
            "model_valid": self.model_valid,
            "plausible": self.plausible,
            "constraints_ok": self.constraints_ok,
            "joint": self.joint,
            "failing_tiers": list(self.failing_tiers),
            "evidence_level": self.evidence_level,
            "assumptions": list(self.assumptions),
        }

    def to_schema(self) -> PublicValidationReport:
        """Adapt the runtime report to the versioned public schema without dropping evidence."""
        from prescriptxai.schemas import ValidationReport as PublicValidationReport

        fields = (
            "tier1_model_safety",
            "tier2_distributional",
            "tier3_engineering",
            "tier4_sensor_coupling",
            "simulator",
        )
        return PublicValidationReport.model_validate(
            {
                "schema_version": self.schema_version,
                "assumptions": self.assumptions,
                **{
                    field: {
                        "passed": tier.valid,
                        **{key: value for key, value in tier.as_dict().items() if key != "valid"},
                    }
                    for field, tier in zip(fields, self.tiers().values(), strict=True)
                },
            }
        )

    @property
    def success(self) -> bool:
        """Whether model safety and all required physical checks passed."""
        return self.model_valid and self.physical_valid

    def as_outcome(
        self,
        initial_risk: float,
        final_risk: float,
        deltas: tuple[DeltaMapping, ...],
        *,
        recourse_feasible: bool,
    ) -> RecourseOutcome:
        """Add optimizer feasibility to the independently measured model/tier statuses."""
        return RecourseOutcome(
            initial_risk=initial_risk,
            final_risk=final_risk,
            model_valid=self.model_valid,
            recourse_feasible=recourse_feasible,
            tier2_plausible=self.tier2_plausibility.valid,
            tier3_engineering_valid=self.tier3_engineering.valid,
            tier4_coupling_valid=self.tier4_coupling.valid,
            deltas=deltas,
            success=self.success and recourse_feasible,
        )


def fit_mahalanobis_validator(
    training_frame: pd.DataFrame,
    bundle: ModelBundle,
    expected_training_engine_ids: tuple[int, ...],
    config: AppConfig,
) -> MahalanobisValidator:
    """Fit Tier 2 only from rows of declared training engines using the model's scaler."""
    if set(expected_training_engine_ids) != set(bundle.training_engine_ids):
        raise ValueError("Tier 2 fitting IDs must match the model's training engines")
    if "engine_id" not in training_frame.columns:
        raise ValueError("training frame must contain engine_id provenance")
    observed_ids = tuple(sorted(int(value) for value in training_frame["engine_id"].unique()))
    if observed_ids != tuple(sorted(expected_training_engine_ids)):
        raise ValueError("Tier 2 rows must contain exactly the model's training engines")
    raw_features = training_frame[list(bundle.feature_names)]
    scaled = bundle.scaler.transform(raw_features)
    reference_mask: NDArray[np.bool_] = np.ones(len(training_frame), dtype=bool)
    if config.validation.reference_distribution == "healthy_to_moderate":
        if "rul" not in training_frame:
            raise ValueError("healthy-to-moderate covariance reference requires RUL")
        reference_mask = training_frame.rul.to_numpy() > config.validation.healthy_min_rul
    setting_names = ("op_setting_1", "op_setting_2", "op_setting_3")
    multi_regime = config.data.dataset in {"FD002", "FD004"}
    return MahalanobisValidator.fit(
        scaled,
        bundle.feature_names,
        training_frame["engine_id"].to_numpy(dtype=np.int64),
        expected_training_engine_ids,
        config.validation.mahalanobis_max,
        config.validation.covariance_regularization,
        threshold_method=config.validation.d_max_threshold_method,
        threshold_quantile=config.validation.d_max_quantile,
        reference_distribution=config.validation.reference_distribution,
        reference_mask=reference_mask,
        operating_settings=(
            training_frame.loc[:, setting_names].to_numpy(dtype=float) if multi_regime else None
        ),
        regime_k=config.validation.regime_k if multi_regime else 1,
        seed=config.seed,
    )


def validate_candidate(
    initial_state: Mapping[str, float],
    candidate_state: Mapping[str, float],
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    mahalanobis: MahalanobisValidator,
    config: AppConfig,
    coupling: SensorCouplingModel | None = None,
    *,
    mode: Literal["collect_all", "fail_fast"] | None = None,
    simulator: DynamicSimulator | None = None,
) -> ValidationReport:
    """Run ordered static tiers, with explicit skipped results in fail-fast mode."""
    candidate_frame = pd.DataFrame([dict(candidate_state)])
    final_risk = float(bundle.predict_risk(candidate_frame)[0])
    raw_features = candidate_frame[list(bundle.feature_names)]
    scaled_candidate = bundle.scaler.transform(raw_features)[0]
    if mahalanobis.feature_names != bundle.feature_names:
        raise ValueError("Mahalanobis and model feature orders do not match")
    surrogate_risk: float | None = None
    if bundle.supports_gradients:
        estimator = (
            bundle.estimator
            if getattr(bundle.estimator, "supports_gradients", False)
            else bundle.surrogate
        )
        device = torch.device(getattr(estimator, "device", "cpu"))
        with torch.no_grad():
            surrogate_risk = float(
                bundle.torch_forward(
                    torch.as_tensor(scaled_candidate[None, :], dtype=torch.float32, device=device)
                ).reshape(-1)[0]
            )
    frozen_settings = (
        np.asarray([[initial_state[f"op_setting_{index}"] for index in range(1, 4)]])
        if mahalanobis.clusterer is not None
        else None
    )
    checks: tuple[Callable[[], TierResult], ...] = (
        lambda: validate_model_risk(
            final_risk,
            config.model.safe_threshold,
            surrogate_risk=surrogate_risk,
            disagreement_threshold=config.validation.surrogate_disagreement_threshold,
        ),
        lambda: mahalanobis.validate(
            np.asarray(scaled_candidate, dtype=float),
            frozen_operating_settings=frozen_settings,
        ),
        lambda: validate_engineering(
            initial_state,
            candidate_state,
            taxonomy,
            horizon_steps=config.recourse.rate_horizon_steps,
        ),
        lambda: validate_sensor_coupling(candidate_state, taxonomy, coupling),
    )
    selected_mode = mode or config.validation.mode
    if selected_mode not in {"collect_all", "fail_fast"}:
        raise ValueError("unknown validation mode")
    results: list[TierResult] = []
    stopped = False
    for check in checks:
        result = (
            TierResult.skipped("previous tier failed in fail-fast mode") if stopped else check()
        )
        results.append(result)
        stopped = stopped or (selected_mode == "fail_fast" and not result.valid)
    dynamic = (
        TierResult.skipped("previous tier failed in fail-fast mode")
        if stopped
        else run_simulator_validation(
            candidate_state, config.validation.simulator_enabled, simulator
        )
    )
    return ValidationReport(results[0], results[1], results[2], results[3], dynamic)
