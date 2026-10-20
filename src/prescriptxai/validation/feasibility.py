"""Differentiable penalties for the same Tier 2/4 checks used after search."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import cast

import numpy as np
import torch
from numpy.typing import NDArray

from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.models.registry import ModelBundle
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator


def frozen_settings(
    validator: MahalanobisValidator,
    initial: Mapping[str, float],
) -> NDArray[np.float64] | None:
    """Select regimes using immutable original settings, including during optimization."""
    if validator.clusterer is None:
        return None
    return cast(
        NDArray[np.float64],
        np.asarray(
            [[initial[f"op_setting_{index}"] for index in range(1, 4)]],
            dtype=float,
        ),
    )


def build_feasibility_penalty(
    bundle: ModelBundle,
    taxonomy: FeatureTaxonomy,
    validator: MahalanobisValidator,
    coupling: SensorCouplingModel | None,
    initial: Mapping[str, float],
    *,
    check_distribution: bool = True,
    check_coupling: bool = True,
) -> Callable[[torch.Tensor], torch.Tensor]:
    """Penalize normalized Tier 2 distance and Tier 4 relationship excess.

    Input rows already contain propagated dependents. Hard actuator/rate limits remain in the
    optimizer bounds. Nonlinear coupling teachers may use their existing differentiable surrogate;
    final acceptance always checks the true coupling regressors and true failure predictor.
    """
    names = bundle.feature_names
    positions = {name: index for index, name in enumerate(names)}
    regime_settings = frozen_settings(validator, initial)
    cutoff = validator.threshold_for(regime_settings)
    scaler = bundle.scaler.scaler

    def penalty(scaled_rows: torch.Tensor) -> torch.Tensor:
        """Return a scalar autograd penalty while leaving every cutoff fixed."""
        epsilon = torch.finfo(scaled_rows.dtype).eps
        value = torch.zeros((), dtype=scaled_rows.dtype, device=scaled_rows.device)
        if check_distribution:
            distance = validator.torch_distance(
                scaled_rows, frozen_operating_settings=regime_settings
            )
            value = torch.relu(distance - cutoff).square().sum() / max(cutoff**2, epsilon)
        mean = torch.as_tensor(scaler.mean_, dtype=scaled_rows.dtype, device=scaled_rows.device)
        scale = torch.as_tensor(scaler.scale_, dtype=scaled_rows.dtype, device=scaled_rows.device)
        raw = scaled_rows * scale + mean
        if check_coupling and coupling is not None:
            inputs = raw[:, [positions[name] for name in coupling.predictor_features]]
            for target in coupling.dependent_features:
                if target not in positions:
                    continue
                teacher = coupling.torch_models[target].to(raw.device)
                predicted = teacher(inputs.to(torch.float64)).reshape(-1).to(raw.dtype)
                residual = torch.abs(raw[:, positions[target]] - predicted)
                sigma = coupling.residual_std[target]
                excess = torch.relu(residual - coupling.residual_sigma_k * sigma)
                value = value + (excess / max(sigma, epsilon)).square().sum()
        for rule in taxonomy.coupling_rules if check_coupling else ():
            if rule.feature_a not in positions or rule.feature_b not in positions:
                continue
            a, b = raw[:, positions[rule.feature_a]], raw[:, positions[rule.feature_b]]
            if rule.relation == "greater_than":
                excess = torch.relu(b - a - rule.tolerance)
            elif rule.relation == "less_than":
                excess = torch.relu(a - b - rule.tolerance)
            else:
                assert rule.slope is not None and rule.intercept is not None
                excess = torch.relu(
                    torch.abs(b - (rule.slope * a + rule.intercept)) - rule.tolerance
                )
            denominator = max(float(scaler.scale_[positions[rule.feature_b]]), epsilon)
            value = value + (excess / denominator).square().sum()
        return value

    return penalty
