"""Tier 1: calibrated predictor target-risk check."""

from __future__ import annotations

import numpy as np

from prescriptxai.validation.base import TierResult


def validate_model_risk(risk: float, safe_threshold: float) -> TierResult:
    """Check whether a calibrated risk is no greater than the configured safe threshold."""
    if not np.isfinite(risk) or not 0 <= risk <= 1:
        raise ValueError("risk must be finite and within [0, 1]")
    if not 0 < safe_threshold < 1:
        raise ValueError("safe_threshold must be within (0, 1)")
    valid = risk <= safe_threshold
    diagnostic = () if valid else (f"predicted risk {risk:.6g} exceeds safe threshold",)
    return TierResult(valid, diagnostic, measurement=risk, limit=safe_threshold)
