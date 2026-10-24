"""Train-only, regime-aware Ledoit-Wolf Mahalanobis validation without inverses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, cast

import numpy as np
import torch
from numpy.typing import NDArray
from scipy.linalg import solve_triangular
from scipy.stats import chi2
from sklearn.cluster import KMeans
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import StandardScaler

from prescriptxai.validation.base import TierResult

ThresholdMethod = Literal["fixed", "empirical_quantile", "chi_square_quantile"]
ReferenceDistribution = Literal["all_cycles", "healthy_to_moderate"]


@dataclass(frozen=True)
class RegimeStatistics:
    """One training regime's covariance factor and frozen cutoff."""

    mean: NDArray[np.float64]
    cholesky: NDArray[np.float64]
    max_distance: float
    row_count: int
    engine_ids: tuple[int, ...]
    shrinkage: float
    condition_number: float
    unregularized_rank: int


@dataclass(frozen=True)
class MahalanobisValidator:
    r"""Compute D_M = ||L^{-1}(x-mu)||, where LL^T = Sigma.

    Shrinkage and a configured diagonal floor handle singular/constant channels. Regimes are
    selected by original frozen operating settings. Precision-only legacy artifacts need refitting.
    """

    feature_names: tuple[str, ...]
    training_engine_ids: tuple[int, ...]
    mean: NDArray[np.float64]
    covariance_cholesky: NDArray[np.float64]
    max_distance: float
    regularization: float
    threshold_method: ThresholdMethod = "fixed"
    threshold_quantile: float | None = None
    reference_distribution: ReferenceDistribution = "all_cycles"
    regime_statistics: dict[int, RegimeStatistics] = field(default_factory=dict)
    settings_scaler: StandardScaler | None = None
    clusterer: KMeans | None = None
    artifact_version: str = "2.0.0"

    @classmethod
    def fit(
        cls,
        training_features: NDArray[np.float64],
        feature_names: tuple[str, ...],
        row_engine_ids: NDArray[np.int64],
        expected_training_engine_ids: tuple[int, ...],
        max_distance: float,
        regularization: float,
        *,
        threshold_method: ThresholdMethod = "fixed",
        threshold_quantile: float | None = None,
        reference_distribution: ReferenceDistribution = "all_cycles",
        reference_mask: NDArray[np.bool_] | None = None,
        operating_settings: NDArray[np.float64] | None = None,
        regime_k: int = 1,
        seed: int = 1729,
    ) -> MahalanobisValidator:
        """Fit shrinkage statistics after verifying the declared fitting-engine partition."""
        matrix = np.asarray(training_features, dtype=np.float64)
        ids = np.asarray(row_engine_ids)
        if matrix.ndim != 2 or matrix.shape[0] < 2:
            raise ValueError("training_features must be a 2-D matrix with at least two rows")
        if matrix.shape[1] != len(feature_names) or not feature_names:
            raise ValueError("feature_names must match the nonempty feature matrix width")
        if len(feature_names) != len(set(feature_names)):
            raise ValueError("feature_names must be unique")
        if not np.isfinite(matrix).all():
            raise ValueError("training features must be finite")
        if ids.ndim != 1 or len(ids) != len(matrix) or not np.isfinite(ids).all():
            raise ValueError("row_engine_ids must match finite training feature rows")
        if not np.equal(ids, np.floor(ids)).all():
            raise ValueError("row_engine_ids must be integers")
        observed = tuple(sorted(int(value) for value in np.unique(ids)))
        if not expected_training_engine_ids or observed != tuple(
            sorted(expected_training_engine_ids)
        ):
            raise ValueError("covariance rows must contain exactly the declared training engines")
        if (
            not np.isfinite([max_distance, regularization]).all()
            or min(max_distance, regularization) <= 0
        ):
            raise ValueError("max_distance and regularization must be finite and positive")
        if threshold_method not in {"fixed", "empirical_quantile", "chi_square_quantile"}:
            raise ValueError("unknown Mahalanobis threshold method")
        if threshold_method != "fixed" and (
            threshold_quantile is None
            or not np.isfinite(threshold_quantile)
            or not 0 < threshold_quantile <= 1
            or (threshold_method == "chi_square_quantile" and threshold_quantile == 1)
        ):
            raise ValueError("threshold quantile must be in (0, 1), or (0, 1] for empirical")
        if reference_distribution not in {"all_cycles", "healthy_to_moderate"}:
            raise ValueError("unknown reference distribution")
        mask = np.ones(len(matrix), dtype=bool) if reference_mask is None else reference_mask
        if mask.shape != (len(matrix),) or mask.dtype != np.bool_ or mask.sum() < 2:
            raise ValueError("reference mask must select at least two training rows")
        if regime_k < 1 or seed < 0:
            raise ValueError("regime_k and seed must be valid")
        settings_scaler: StandardScaler | None = None
        clusterer: KMeans | None = None
        labels: NDArray[np.int64] = np.zeros(len(matrix), dtype=np.int64)
        if regime_k > 1:
            if operating_settings is None or operating_settings.ndim != 2:
                raise ValueError("multi-regime fitting requires operating settings")
            if len(operating_settings) != len(matrix) or not np.isfinite(operating_settings).all():
                raise ValueError("operating settings must match finite training rows")
            settings_scaler = StandardScaler().fit(operating_settings)
            clusterer = KMeans(n_clusters=regime_k, random_state=seed, n_init="auto")
            labels = clusterer.fit_predict(settings_scaler.transform(operating_settings))
        statistics: dict[int, RegimeStatistics] = {}
        for regime in range(regime_k):
            selected = mask & (labels == regime)
            rows = matrix[selected]
            if len(rows) < 2:
                raise ValueError(f"regime {regime} has fewer than two reference rows")
            estimator = LedoitWolf(store_precision=False).fit(rows)
            covariance = np.asarray(estimator.covariance_, dtype=float)
            covariance = covariance + np.eye(matrix.shape[1]) * regularization
            factor = np.linalg.cholesky(covariance)
            mean = np.asarray(estimator.location_, dtype=float)
            distances = np.linalg.norm(
                solve_triangular(factor, (rows - mean).T, lower=True), axis=0
            )
            cutoff = max_distance
            if threshold_method == "empirical_quantile":
                cutoff = float(np.quantile(distances, threshold_quantile))
            elif threshold_method == "chi_square_quantile":
                cutoff = float(np.sqrt(chi2.ppf(threshold_quantile, matrix.shape[1])))
            statistics[regime] = RegimeStatistics(
                mean,
                factor,
                cutoff,
                len(rows),
                tuple(sorted(int(value) for value in np.unique(ids[selected]))),
                float(estimator.shrinkage_),
                float(np.linalg.cond(covariance)),
                int(np.linalg.matrix_rank(rows - mean)),
            )
        first = statistics[0]
        return cls(
            feature_names,
            observed,
            first.mean,
            first.cholesky,
            first.max_distance,
            regularization,
            threshold_method,
            threshold_quantile if threshold_method != "fixed" else None,
            reference_distribution,
            statistics,
            settings_scaler,
            clusterer,
        )

    def assign_regimes(self, frozen_operating_settings: NDArray[np.float64]) -> NDArray[np.int64]:
        """Assign regimes from original settings using training-only KMeans."""
        values = np.atleast_2d(frozen_operating_settings)
        if not np.isfinite(values).all() or not len(values):
            raise ValueError("frozen operating settings must be finite and nonempty")
        if self.clusterer is None or self.settings_scaler is None:
            return np.zeros(len(values), dtype=np.int64)
        return np.asarray(
            self.clusterer.predict(self.settings_scaler.transform(values)), dtype=np.int64
        )

    def _labels(
        self,
        count: int,
        frozen_operating_settings: NDArray[np.float64] | None,
        regime_ids: NDArray[np.int64] | None = None,
    ) -> NDArray[np.int64]:
        if not hasattr(self, "covariance_cholesky"):
            raise ValueError(
                "legacy precision-only validator: refit on training engines for Phase 5"
            )
        if regime_ids is not None:
            supplied = np.asarray(regime_ids)
            if (
                supplied.dtype.kind not in "iuf"
                or not np.isfinite(supplied).all()
                or not np.equal(supplied, np.floor(supplied)).all()
            ):
                raise ValueError("regime labels must be finite integers")
            labels = supplied.astype(np.int64)
        elif frozen_operating_settings is not None:
            labels = self.assign_regimes(frozen_operating_settings)
            if len(labels) == 1:
                labels = np.repeat(labels, count)
        elif self.clusterer is not None:
            raise ValueError("multi-regime scoring requires frozen operating settings")
        else:
            labels = np.zeros(count, dtype=np.int64)
        if labels.shape != (count,) or any(
            int(label) not in self.regime_statistics for label in labels
        ):
            raise ValueError("regime labels must align with candidates and fitted regimes")
        return labels

    def distance_batch(
        self,
        candidates: NDArray[np.float64],
        *,
        frozen_operating_settings: NDArray[np.float64] | None = None,
        regime_ids: NDArray[np.int64] | None = None,
    ) -> NDArray[np.float64]:
        """Score finite rows with triangular solves, never a precision matrix."""
        matrix = np.asarray(candidates, dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] != len(self.feature_names) or not len(matrix):
            raise ValueError("candidate matrix shape does not match fitted feature names")
        if not np.isfinite(matrix).all():
            raise ValueError("candidate matrix must be finite")
        labels = self._labels(len(matrix), frozen_operating_settings, regime_ids)
        output: NDArray[np.float64] = np.empty(len(matrix), dtype=float)
        for regime in np.unique(labels):
            selected = labels == regime
            stats = self.regime_statistics[int(regime)]
            whitened = solve_triangular(
                stats.cholesky, (matrix[selected] - stats.mean).T, lower=True
            )
            output[selected] = np.linalg.norm(whitened, axis=0)
        if not np.isfinite(output).all():
            raise ValueError("Mahalanobis distance overflowed for candidate values")
        return output

    def distance(
        self,
        candidate: NDArray[np.float64],
        *,
        frozen_operating_settings: NDArray[np.float64] | None = None,
    ) -> float:
        """Calculate one candidate's distance under its frozen regime."""
        if candidate.ndim != 1:
            raise ValueError("candidate vector shape does not match fitted feature names")
        return float(
            self.distance_batch(
                candidate[None, :], frozen_operating_settings=frozen_operating_settings
            )[0]
        )

    def threshold_for(self, frozen_operating_settings: NDArray[np.float64] | None = None) -> float:
        """Return the pre-fitted cutoff for one original operating regime."""
        label = int(self._labels(1, frozen_operating_settings)[0])
        return (
            self.max_distance
            if self.threshold_method == "fixed"
            else (self.regime_statistics[label].max_distance)
        )

    def validate(
        self,
        candidate: NDArray[np.float64],
        *,
        frozen_operating_settings: NDArray[np.float64] | None = None,
    ) -> TierResult:
        """Return D_M, D_max and signed margin independently of model safety."""
        value = self.distance(candidate, frozen_operating_settings=frozen_operating_settings)
        limit = self.threshold_for(frozen_operating_settings)
        diagnostic = (
            () if value <= limit else (f"Mahalanobis distance {value:.6g} exceeds {limit:.6g}",)
        )
        return TierResult(value <= limit, diagnostic, value, limit, limit - value, "E2")

    def torch_distance(
        self,
        candidates: torch.Tensor,
        *,
        frozen_operating_settings: NDArray[np.float64] | None = None,
    ) -> torch.Tensor:
        """Differentiate a batch in one frozen regime through a Cholesky solve."""
        label = int(self._labels(1, frozen_operating_settings)[0])
        stats = self.regime_statistics[label]
        mean = torch.as_tensor(stats.mean, dtype=candidates.dtype, device=candidates.device)
        factor = torch.as_tensor(stats.cholesky, dtype=candidates.dtype, device=candidates.device)
        whitened = torch.linalg.solve_triangular(factor, (candidates - mean).T, upper=False)
        return cast(torch.Tensor, torch.linalg.vector_norm(whitened, dim=0))
