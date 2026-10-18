"""Common typed validation-tier results."""

from dataclasses import asdict, dataclass
from typing import Literal

EvidenceLevel = Literal["none", "E1", "E2", "E3", "E4", "E5"]
TierStatus = Literal["pass", "fail", "skipped"]


@dataclass(frozen=True)
class CheckResult:
    """One rule with a signed compliance margin (negative means violation)."""

    name: str
    passed: bool
    margin: float | None
    explanation: str
    feature: str | None = None


@dataclass(frozen=True)
class TierResult:
    """Validity result and human-readable diagnostics for one independent check."""

    valid: bool
    diagnostics: tuple[str, ...]
    measurement: float | None = None
    limit: float | None = None
    margin: float | None = None
    evidence_level: EvidenceLevel = "none"
    status: TierStatus | None = None
    checks: tuple[CheckResult, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Resolve boolean calls and ensure skipped checks cannot pass."""
        if self.status is None:
            object.__setattr__(self, "status", "pass" if self.valid else "fail")
        if self.valid != (self.status == "pass"):
            raise ValueError("only a passing tier may have valid=True")

    @classmethod
    def skipped(cls, reason: str) -> "TierResult":
        """Create an unrun check without granting evidence or a pass."""
        return cls(False, (f"skipped: {reason}",), status="skipped")

    def as_dict(self) -> dict[str, object]:
        """Serialize all measurements, margins, status, and evidence."""
        return asdict(self)
