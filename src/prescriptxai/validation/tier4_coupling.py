"""Tier 4: learned sensor coupling and configured relationship checks."""

from collections.abc import Mapping

from prescriptxai.constraints.coupling import SensorCouplingModel, validate_couplings
from prescriptxai.constraints.taxonomy import FeatureTaxonomy
from prescriptxai.validation.base import TierResult


def validate_sensor_coupling(
    candidate: Mapping[str, float],
    taxonomy: FeatureTaxonomy,
    coupling: SensorCouplingModel | None = None,
) -> TierResult:
    """Evaluate learned residual bounds and configured coupling rules."""
    valid, diagnostics = validate_couplings(candidate, taxonomy, coupling)
    return TierResult(valid, diagnostics)
