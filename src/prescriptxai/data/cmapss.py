"""Parsing helpers for NASA C-MAPSS turbofan degradation files."""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
_SENSOR_COLUMNS = [f"sensor_{index}" for index in range(1, 22)]
_COLUMNS = ["engine_id", "cycle", "op_setting_1", "op_setting_2", "op_setting_3", *_SENSOR_COLUMNS]


@dataclass(frozen=True)
class CmapssData:
    """Parsed train and test telemetry with official test RUL labels."""

    train: pd.DataFrame
    test: pd.DataFrame
    test_rul: pd.DataFrame
    subset: str


def _read_table(data: bytes, source: str, expected_columns: int) -> pd.DataFrame:
    """Parse whitespace-delimited numeric records and check the schema."""
    if not data.strip():
        raise ValueError(f"{source} is empty")
    try:
        frame = pd.read_csv(BytesIO(data), sep=r"\s+", header=None, engine="python")
    except pd.errors.ParserError as error:
        raise ValueError(f"could not parse {source}") from error
    if frame.shape[1] != expected_columns:
        raise ValueError(f"{source} has {frame.shape[1]} columns; expected {expected_columns}")
    numeric = cast(pd.DataFrame, frame.apply(pd.to_numeric, errors="coerce"))
    if numeric.isna().any().any():
        raise ValueError(f"{source} contains missing or non-numeric values")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError(f"{source} contains non-finite values")
    return numeric


def _parse_subset(archive: zipfile.ZipFile, subset: str) -> CmapssData:
    """Parse the expected train, test, and RUL members without extracting files."""
    members = set(archive.namelist())
    suffix = f"{subset}.txt"
    train_name = next((name for name in members if name.endswith(f"train_{suffix}")), None)
    test_name = next((name for name in members if name.endswith(f"test_{suffix}")), None)
    rul_name = next((name for name in members if name.endswith(f"RUL_{suffix}")), None)
    if train_name is None or test_name is None or rul_name is None:
        raise ValueError(f"archive does not contain complete {subset} train/test/RUL files")
    train_raw = _read_table(archive.read(train_name), train_name, len(_COLUMNS))
    test_raw = _read_table(archive.read(test_name), test_name, len(_COLUMNS))
    rul_raw = _read_table(archive.read(rul_name), rul_name, 1)
    train_raw.columns = _COLUMNS
    test_raw.columns = _COLUMNS
    rul_raw.columns = ["rul"]
    for label, frame in (("train", train_raw), ("test", test_raw)):
        if (frame[["engine_id", "cycle"]] < 1).any().any():
            raise ValueError(f"{label} engine IDs and cycles must be positive")
        if frame.duplicated(["engine_id", "cycle"]).any():
            raise ValueError(f"{label} contains duplicate engine/cycle rows")
        frame.sort_values(["engine_id", "cycle"], inplace=True, ignore_index=True)
    test_ids = test_raw["engine_id"].drop_duplicates().tolist()
    if len(test_ids) != len(rul_raw):
        raise ValueError("test RUL row count does not match the number of test engines")
    if (rul_raw["rul"] < 0).any():
        raise ValueError("test RUL values must not be negative")
    if not pd.api.types.is_numeric_dtype(rul_raw["rul"]):
        raise ValueError("test RUL values must be numeric")
    rul_raw.insert(0, "engine_id", test_ids)
    LOGGER.info(
        "Parsed %s: %d train engines, %d test engines",
        subset,
        train_raw["engine_id"].nunique(),
        test_raw["engine_id"].nunique(),
    )
    return CmapssData(train=train_raw, test=test_raw, test_rul=rul_raw, subset=subset)


def load_cmapss_archive(path: Path, subset: str) -> CmapssData:
    """Read one FD subset from a direct or NASA-wrapped C-MAPSS ZIP archive.

    NASA's downloadable outer archive contains a nested ``CMAPSSData.zip``. No archive members
    are extracted to the filesystem; only the expected data tables are read, avoiding ZIP path
    traversal during ingestion.
    """
    if subset not in {"FD001", "FD002", "FD003", "FD004"}:
        raise ValueError("subset must be one of FD001, FD002, FD003, or FD004")
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
