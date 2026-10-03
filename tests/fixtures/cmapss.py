"""Synthetic C-MAPSS-shaped data used exclusively in tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from prescriptxai.data.cmapss import CANONICAL_COLUMNS


def make_cmapss_frame(
    engine_count: int = 8,
    min_cycles: int = 60,
    max_cycles: int = 120,
    subset: str = "FD001",
) -> pd.DataFrame:
    """Return test-only telemetry with a degradation trend and one constant sensor."""
    if engine_count < 1 or min_cycles < 2 or max_cycles < min_cycles:
        raise ValueError("fixture engine and cycle dimensions are invalid")
    rows: list[dict[str, float | int]] = []
    for unit_id in range(1, engine_count + 1):
        lifetime = min_cycles + (unit_id - 1) % (max_cycles - min_cycles + 1)
        for cycle in range(1, lifetime + 1):
            row: dict[str, float | int] = {
                "unit_id": unit_id,
                "cycle": cycle,
                "op_setting_1": float((unit_id - 1) % 6) if subset in {"FD002", "FD004"} else 0.0,
                "op_setting_2": float(((unit_id - 1) % 6) * 0.1)
                if subset in {"FD002", "FD004"}
                else 0.0,
                "op_setting_3": 0.0,
            }
            for sensor in range(1, 22):
                if sensor == 2:
                    value = 5.0
                else:
                    slope = sensor / 100.0
                    value = sensor * 10.0 + unit_id * 0.25 + cycle * slope
                    if subset in {"FD002", "FD004"}:
                        value += ((unit_id - 1) % 6) * sensor * 0.4
                row[f"s{sensor}"] = value
            rows.append(row)
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def write_cmapss_archive(
    path: Path,
    subset: str = "FD001",
    train_engine_count: int = 8,
    test_engine_count: int = 3,
) -> Path:
    """Write a tiny syntactically valid C-MAPSS archive fixture for tests only."""
    training = make_cmapss_frame(train_engine_count, subset=subset)
    test = make_cmapss_frame(test_engine_count, min_cycles=30, max_cycles=30, subset=subset)

    def render(frame: pd.DataFrame) -> str:
        return "".join(
            " ".join(f"{float(value):.8f}" for value in row) + "\n"
            for row in frame.itertuples(index=False, name=None)
        )

    rul = "".join(f"{value}\n" for value in np.arange(6, 6 + test_engine_count * 5, 5))
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"CMAPSSData/train_{subset}.txt", render(training))
        archive.writestr(f"CMAPSSData/test_{subset}.txt", render(test))
        archive.writestr(f"CMAPSSData/RUL_{subset}.txt", rul)
    return path
