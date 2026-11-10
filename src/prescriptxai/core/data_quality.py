"""Quality gates for canonical observed telemetry windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from prescriptxai.machine_spec import MachineSpec

QualityCode = Literal[
    "missing_value", "nonfinite_value", "out_of_range", "stuck_sensor", "time_gap"
]


@dataclass(frozen=True)
class QualityIssue:
    """A stable issue code and the affected field."""

    code: QualityCode
    field: str


class RecommendationWithheld(ValueError):
    """A machine policy or data check blocked publication of a recommendation."""

    def __init__(self, reason: str) -> None:
        prefix = "Recommendation withheld: "
        super().__init__(prefix + reason.removeprefix(prefix))


def check_window(rows: pd.DataFrame, spec: MachineSpec) -> tuple[QualityIssue, ...]:
    """Report missing, nonfinite, out-of-range, stuck or irregular observations."""
    if rows.empty:
        return (QualityIssue("missing_value", "window"),)
    if rows.columns.has_duplicates:
        return (QualityIssue("missing_value", "ambiguous column names"),)
    if "unit_id" in rows and (rows["unit_id"].isna().any() or rows["unit_id"].nunique() != 1):
        return (QualityIssue("missing_value", "one unit_id required per window"),)
    issues: list[QualityIssue] = []
    if "time_index" not in rows or rows["time_index"].isna().any():
        issues.append(QualityIssue("missing_value", "time_index"))
    else:
        times = pd.to_numeric(rows["time_index"], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(times).all():
            issues.append(QualityIssue("nonfinite_value", "time_index"))
        else:
            steps = np.diff(times)
            if np.any(steps <= 0) or np.any(steps > spec.quality.max_time_gap):
                issues.append(QualityIssue("time_gap", "time_index"))
    for feature in spec.measurement_features:
        name = feature.id
        if name not in rows or rows[name].isna().any():
            issues.append(QualityIssue("missing_value", name))
            continue
        if rows[name].map(lambda value: isinstance(value, (bool, np.bool_, complex))).any():
            issues.append(QualityIssue("nonfinite_value", name))
            continue
        values = pd.to_numeric(rows[name], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(values).all():
            issues.append(QualityIssue("nonfinite_value", name))
            continue
        lower, upper = feature.bounds.minimum, feature.bounds.maximum
        if (
            lower is not None
            and upper is not None
            and (np.any(values < lower) or np.any(values > upper))
        ):
            issues.append(QualityIssue("out_of_range", name))
        window = spec.quality.stuck_window
        if (
            name in spec.quality.stuck_features
            and len(values) >= window
            and np.ptp(values[-window:]) <= spec.quality.stuck_tolerance
        ):
            issues.append(QualityIssue("stuck_sensor", name))
    return tuple(issues)


def require_clean_window(rows: pd.DataFrame, spec: MachineSpec) -> None:
    """Fail closed before prediction or recommendation on invalid observations."""
    issues = check_window(rows, spec)
    if issues:
        raise RecommendationWithheld(", ".join(f"{issue.code} ({issue.field})" for issue in issues))
