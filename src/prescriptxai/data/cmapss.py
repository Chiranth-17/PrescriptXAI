"""Typed loaders and label helpers for NASA C-MAPSS turbofan telemetry."""

from __future__ import annotations

import logging
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal, cast

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
SUBSETS = ("FD001", "FD002", "FD003", "FD004")
CmapssSubset = Literal["FD001", "FD002", "FD003", "FD004"]
SENSOR_COLUMNS = tuple(f"s{index}" for index in range(1, 22))
SETTING_COLUMNS = ("op_setting_1", "op_setting_2", "op_setting_3")
CANONICAL_COLUMNS = ("unit_id", "cycle", *SETTING_COLUMNS, *SENSOR_COLUMNS)


@dataclass(frozen=True)
class CmapssData:
    """Canonical train/test telemetry and official per-engine test RUL labels."""

    train: pd.DataFrame
    test: pd.DataFrame
    test_rul: pd.DataFrame
    subset: str


def _read_table(data: bytes, source: str, expected_columns: int) -> pd.DataFrame:
    """Parse whitespace-delimited numeric data and reject malformed records."""
    if not data.strip():
        raise ValueError(f"{source} is empty")
    try:
        frame = pd.read_csv(BytesIO(data), sep=r"\s+", header=None, engine="python")
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        raise ValueError(f"could not parse {source}") from error
    if frame.shape[1] != expected_columns:
        raise ValueError(f"{source} has {frame.shape[1]} columns; expected {expected_columns}")
    numeric = cast(pd.DataFrame, frame.apply(pd.to_numeric, errors="coerce"))
    if numeric.isna().any().any():
        raise ValueError(f"{source} contains missing or non-numeric values")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError(f"{source} contains non-finite values")
    return numeric


def _validate_telemetry(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    """Enforce canonical dtypes and contiguous one-based unit cycles."""
    if tuple(frame.columns) != CANONICAL_COLUMNS:
        raise ValueError(f"{source} does not match the canonical C-MAPSS column schema")
    for column in ("unit_id", "cycle"):
        values = frame[column].to_numpy(dtype=float)
        if not np.equal(values, np.floor(values)).all():
            raise ValueError(f"{source} {column} values must be integers")
        if (values < 1).any():
            raise ValueError(f"{source} unit IDs and cycles must be positive")
        frame[column] = frame[column].astype("int64")
    for column in (*SETTING_COLUMNS, *SENSOR_COLUMNS):
        frame[column] = frame[column].astype("float64")
    if frame.isna().any().any():
        raise ValueError(f"{source} contains missing values")
    if frame.duplicated(["unit_id", "cycle"]).any():
        raise ValueError(f"{source} contains duplicate unit/cycle rows")
    frame.sort_values(["unit_id", "cycle"], inplace=True, ignore_index=True)
    for unit_id, group in frame.groupby("unit_id", sort=False):
        cycles = group["cycle"].to_numpy(dtype=np.int64)
        if cycles[0] != 1 or (len(cycles) > 1 and not np.all(np.diff(cycles) == 1)):
            raise ValueError(f"{source} cycles must be contiguous from 1 for unit {unit_id}")
    return frame


def _parse_subset(archive: zipfile.ZipFile, subset: str) -> CmapssData:
    """Parse train, test, and RUL members for one subset without extracting files."""
    members = set(archive.namelist())
    suffix = f"{subset}.txt"
    train_name = next((name for name in members if name.endswith(f"train_{suffix}")), None)
    test_name = next((name for name in members if name.endswith(f"test_{suffix}")), None)
    rul_name = next((name for name in members if name.endswith(f"RUL_{suffix}")), None)
    if train_name is None or test_name is None or rul_name is None:
        raise ValueError(f"archive does not contain complete {subset} train/test/RUL files")
    train = _read_table(archive.read(train_name), train_name, len(CANONICAL_COLUMNS))
    test = _read_table(archive.read(test_name), test_name, len(CANONICAL_COLUMNS))
    test_rul = _read_table(archive.read(rul_name), rul_name, 1)
    train.columns = CANONICAL_COLUMNS
    test.columns = CANONICAL_COLUMNS
    test_rul.columns = ["rul"]
    train = _validate_telemetry(train, train_name)
    test = _validate_telemetry(test, test_name)

    test_rul_values = test_rul["rul"].to_numpy(dtype=float)
    if not np.equal(test_rul_values, np.floor(test_rul_values)).all():
        raise ValueError(f"{rul_name} RUL values must be integers")
    if (test_rul_values < 0).any():
        raise ValueError(f"{rul_name} RUL values must not be negative")
    test_rul["rul"] = test_rul["rul"].astype("int64")
    test_ids = test["unit_id"].drop_duplicates().tolist()
    if len(test_ids) != len(test_rul):
        raise ValueError("test RUL row count does not match the number of test engines")
    test_rul.insert(0, "unit_id", test_ids)
    LOGGER.info(
        "Parsed %s: %d train engines, %d test engines, %d/%d rows",
        subset,
        train["unit_id"].nunique(),
        test["unit_id"].nunique(),
        len(train),
        len(test),
    )
    return CmapssData(train=train, test=test, test_rul=test_rul, subset=subset)


def load_cmapss_archive(path: Path, subset: str) -> CmapssData:
    """Read a subset from either the direct data ZIP or NASA's nested ZIP archive.

    No members are extracted to disk. The returned telemetry uses the public canonical names
    ``unit_id``, ``cycle``, ``op_setting_1..3``, and ``s1..s21``.
    """
    if subset not in SUBSETS:
        raise ValueError(f"subset must be one of {', '.join(SUBSETS)}")
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        with zipfile.ZipFile(path) as outer_archive:
            nested_name = next(
                (name for name in outer_archive.namelist() if Path(name).name == "CMAPSSData.zip"),
                None,
            )
            if nested_name is None:
                return _parse_subset(outer_archive, subset)
            nested_bytes = outer_archive.read(nested_name)
        with zipfile.ZipFile(BytesIO(nested_bytes)) as data_archive:
            return _parse_subset(data_archive, subset)
    except zipfile.BadZipFile as error:
        raise ValueError(f"{path} is not a valid C-MAPSS ZIP archive") from error


def verify_row_counts(dataset: CmapssData, expected: Mapping[str, int] | None) -> dict[str, object]:
    """Compare parsed file row counts with optional published subset metadata."""
    observed = {
        "train": len(dataset.train),
        "test": len(dataset.test),
        "test_rul": len(dataset.test_rul),
    }
    if expected is None:
        return {"expected": None, "observed": observed, "passed": None}
    if set(expected) != set(observed):
        raise ValueError("expected row counts must declare train, test, and test_rul")
    expected_counts = {key: int(value) for key, value in expected.items()}
    if observed != expected_counts:
        raise ValueError(
            f"{dataset.subset} row counts do not match configured integrity metadata: "
            f"expected {expected_counts}, observed {observed}"
        )
    return {"expected": expected_counts, "observed": observed, "passed": True}


def add_test_labels(
    test_frame: pd.DataFrame,
    test_rul: pd.DataFrame,
    failure_horizon: int,
    rul_cap: int | None = None,
) -> pd.DataFrame:
    """Attach NASA test RUL to every observed cycle and create ``y = 1[RUL <= H]``.

    The RUL file provides remaining cycles after the final observed test cycle. Earlier test rows
    add the number of observed cycles since that final row. An optional cap applies to the
    reported RUL only; failure labels always use the exact uncapped value.
    """
    if failure_horizon <= 0 or (rul_cap is not None and rul_cap <= 0):
        raise ValueError("failure_horizon and an enabled rul_cap must be positive")
    if test_frame.empty or test_rul.empty:
        raise ValueError("test telemetry and test RUL must not be empty")
    required = {"unit_id", "cycle"}
    if not required.issubset(test_frame.columns) or not {"unit_id", "rul"}.issubset(
        test_rul.columns
    ):
        raise ValueError("test telemetry and RUL must contain unit_id and their required values")
    if test_rul["unit_id"].duplicated().any():
        raise ValueError("test RUL must contain one row per unit")
    if set(test_frame["unit_id"].unique()) != set(test_rul["unit_id"].unique()):
        raise ValueError("test RUL unit IDs do not match test telemetry")
    result = test_frame.copy()
    final_cycles = result.groupby("unit_id", sort=False)["cycle"].transform("max")
    remaining_after_final = result["unit_id"].map(test_rul.set_index("unit_id")["rul"])
    exact_rul = remaining_after_final + final_cycles - result["cycle"]
    if exact_rul.isna().any() or (exact_rul < 0).any():
        raise ValueError("test RUL values do not produce valid row-level RUL")
    result["rul"] = exact_rul if rul_cap is None else exact_rul.clip(upper=rul_cap)
    result["y"] = (exact_rul <= failure_horizon).astype("int8")
    return result


def to_model_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Adapt canonical C-MAPSS columns to the existing model taxonomy vocabulary.

    This explicit adapter keeps the ingestion contract canonical while preserving downstream
    model bundles trained against ``engine_id`` and ``sensor_1..sensor_21`` names.
    """
    rename = {"unit_id": "engine_id", **{f"s{i}": f"sensor_{i}" for i in range(1, 22)}}
    return frame.rename(columns=rename).copy()
