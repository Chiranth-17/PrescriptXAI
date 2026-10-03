"""Deterministic engine-level train/validation/test partitions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EngineSplits:
    """Rows partitioned by disjoint engine identity."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    train_engine_ids: tuple[int, ...]
    validation_engine_ids: tuple[int, ...]
    test_engine_ids: tuple[int, ...]


def split_engines(
    frame: pd.DataFrame,
    train_fraction: float,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
    engine_column: str = "engine_id",
) -> EngineSplits:
    """Split complete engine trajectories; no engine may cross a partition.

    The three fractions must sum to one. At least three unique engines are required so each split
    is nonempty. Remaining engines after assigning one per split use largest-remainder allocation.
    """
    fractions = np.asarray([train_fraction, validation_fraction, test_fraction], dtype=float)
    if not np.isfinite(fractions).all() or (fractions <= 0).any():
        raise ValueError("split fractions must be finite and positive")
    if not np.isclose(fractions.sum(), 1.0):
        raise ValueError("split fractions must sum to 1")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if frame.empty:
        raise ValueError("cannot split an empty dataframe")
    if engine_column not in frame.columns:
        raise ValueError(f"missing engine identifier column: {engine_column}")
    if frame[engine_column].isna().any():
        raise ValueError("engine identifiers must not be missing")
    engine_ids = np.asarray(pd.unique(frame[engine_column]))
    if len(engine_ids) < 3:
        raise ValueError(
            "at least three engines are required for nonempty train/validation/test splits"
        )
    remaining = len(engine_ids) - 3
    proportional = fractions * remaining
    extra = np.floor(proportional).astype(int)
    remainders = proportional - extra
    for index in np.argsort(-remainders, kind="stable")[: remaining - int(extra.sum())]:
        extra[index] += 1
    counts = extra + 1
    shuffled = np.random.default_rng(seed).permutation(engine_ids)
    train_end = int(counts[0])
    validation_end = train_end + int(counts[1])
    groups = (
        tuple(sorted(shuffled[:train_end].tolist())),
        tuple(sorted(shuffled[train_end:validation_end].tolist())),
        tuple(sorted(shuffled[validation_end:].tolist())),
    )
    train_ids, validation_ids, test_ids = groups
    return EngineSplits(
        train=frame.loc[frame[engine_column].isin(train_ids)].copy(),
        validation=frame.loc[frame[engine_column].isin(validation_ids)].copy(),
        test=frame.loc[frame[engine_column].isin(test_ids)].copy(),
        train_engine_ids=train_ids,
        validation_engine_ids=validation_ids,
        test_engine_ids=test_ids,
    )
