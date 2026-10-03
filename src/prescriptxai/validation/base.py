"""Common typed validation-tier results."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TierResult:
    """Validity result and human-readable diagnostics for one independent check."""

    valid: bool
    diagnostics: tuple[str, ...]
    measurement: float | None = None
    limit: float | None = None
