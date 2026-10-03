"""Tier 4: configured sensor relationship checks."""

from collections.abc import Mapping

from prescriptxai.constraints.coupling import validate_couplings
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.validation.base import TierResult


def validate_sensor_coupling(
    candidate: Mapping[str, float], taxonomy: FeatureTaxonomy
) -> TierResult:
    """Evaluate every configured coupling rule; missing rules cannot pass vacuously."""
    valid, diagnostics = validate_couplings(candidate, taxonomy)
    return TierResult(valid, diagnostics)
