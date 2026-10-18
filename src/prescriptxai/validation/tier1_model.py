"""Tier 1: calibrated predictor target-risk check."""

from __future__ import annotations

import logging

import numpy as np

from prescriptxai.validation.base import TierResult


def validate_model_risk(
    risk: float,
    safe_threshold: float,
    *,
    surrogate_risk: float | None = None,
    disagreement_threshold: float | None = None,
) -> TierResult:
    """Check whether a calibrated risk is no greater than the configured safe threshold."""
    if not np.isfinite(risk) or not 0 <= risk <= 1:
        raise ValueError("risk must be finite and within [0, 1]")
    if not 0 < safe_threshold < 1:
        raise ValueError("safe_threshold must be within (0, 1)")
    valid = risk <= safe_threshold
    diagnostic = () if valid else (f"predicted risk {risk:.6g} exceeds safe threshold",)
    warnings: tuple[str, ...] = ()
    if surrogate_risk is not None:
        if not np.isfinite(surrogate_risk) or not 0 <= surrogate_risk <= 1:
            raise ValueError("surrogate risk must be finite and within [0, 1]")
        if disagreement_threshold is None or not 0 <= disagreement_threshold <= 1:
            raise ValueError("a surrogate disagreement threshold in [0, 1] is required")
        error = abs(risk - surrogate_risk)
        if error > disagreement_threshold:
            warnings = (
                f"surrogate/true risk disagreement {error:.6g} exceeds "
                f"{disagreement_threshold:.6g}; true risk determines validity",
            )
            logging.getLogger(__name__).warning(warnings[0])
    return TierResult(
        valid,
        diagnostic,
        measurement=risk,
        limit=safe_threshold,
        margin=safe_threshold - risk,
        evidence_level="E1",
        warnings=warnings,
    )
