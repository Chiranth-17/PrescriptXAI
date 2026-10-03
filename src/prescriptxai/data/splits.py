"""Deterministic, lifetime-stratified engine-level train/validation/test partitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass(frozen=True)
class EngineSplits:
    """Rows partitioned by disjoint engine identity."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    train_engine_ids: tuple[int, ...]
    validation_engine_ids: tuple[int, ...]
    test_engine_ids: tuple[int, ...]


def _target_counts(engine_count: int, fractions: NDArray[np.float64]) -> NDArray[np.int64]:
    """Allocate exact partition sizes while keeping every partition nonempty."""
    remaining = engine_count - 3
    proportional: NDArray[np.float64] = fractions * remaining
    extra: NDArray[np.int64] = np.floor(proportional).astype(np.int64)
    remainder = proportional - extra
    for index in np.argsort(-remainder, kind="stable")[: remaining - int(extra.sum())]:
        extra[index] += 1
    return cast(NDArray[np.int64], extra + 1)


def split_engines(
    frame: pd.DataFrame,
    train_fraction: float,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
    engine_column: str | None = None,
    lifetime_buckets: int = 6,
) -> EngineSplits:
    """Split complete trajectories, stratifying engine lifetimes and forbidding leakage.

    Lifetime buckets are quantile-sized groups ordered by each engine's maximum observed cycle.
    Their members are apportioned across the requested partition fractions, with exact overall
    partition sizes. Small datasets reduce the bucket count so each partition can be represented.
    """
    fractions = np.asarray([train_fraction, validation_fraction, test_fraction], dtype=float)
    if not np.isfinite(fractions).all() or (fractions <= 0).any():
        raise ValueError("split fractions must be finite and positive")
    if not np.isclose(fractions.sum(), 1.0):
        raise ValueError("split fractions must sum to 1")
    if seed < 0 or lifetime_buckets < 1:
        raise ValueError("seed must be non-negative and lifetime_buckets must be positive")
    if frame.empty:
        raise ValueError("cannot split an empty dataframe")
    if engine_column is None:
        engine_column = "unit_id" if "unit_id" in frame.columns else "engine_id"
    if engine_column not in frame.columns:
        raise ValueError(f"missing engine identifier column: {engine_column}")
    if frame[engine_column].isna().any():
        raise ValueError("engine identifiers must not be missing")
    if "cycle" not in frame.columns:
        raise ValueError("lifetime stratification requires a cycle column")
    engine_ids = np.asarray(pd.unique(frame[engine_column]))
    if len(engine_ids) < 3:
        raise ValueError(
            "at least three engines are required for nonempty train/validation/test splits"
        )
    if (frame["cycle"] < 1).any() or not np.isfinite(frame["cycle"].to_numpy(dtype=float)).all():
        raise ValueError("cycle values must be finite and positive")

    target_sizes = _target_counts(len(engine_ids), fractions)
    bucket_count = min(lifetime_buckets, int(target_sizes.min()), len(engine_ids) // 3)
    lifetimes = frame.groupby(engine_column, sort=False)["cycle"].max().sort_values()
    # Rank first makes qcut deterministic even when engines share the same lifetime.
    ranks = lifetimes.rank(method="first")
    bucket_ids = pd.qcut(ranks, q=bucket_count, labels=False, duplicates="drop")
    bucket_table = pd.DataFrame({engine_column: lifetimes.index, "bucket": bucket_ids.to_numpy()})

    rng = np.random.default_rng(seed)
    assigned: list[list[int]] = [[], [], []]
    capacity = target_sizes.copy()
    for _, bucket in bucket_table.groupby("bucket", sort=True):
        members = rng.permutation(bucket[engine_column].to_numpy())
        ideal = fractions * len(members)
        counts = np.minimum(np.floor(ideal).astype(int), capacity)
        remainders = ideal - np.floor(ideal)
        left = len(members) - int(counts.sum())
        for index in np.argsort(-remainders, kind="stable"):
            if left == 0:
                break
            if counts[index] < capacity[index]:
                counts[index] += 1
                left -= 1
        # If rounded quotas exhausted capacity, fill any remaining global slot deterministically.
        while left:
            available = np.flatnonzero(counts < capacity)
            if not len(available):
                raise RuntimeError("could not allocate lifetime bucket to split targets")
            index = int(available[np.argmax(remainders[available])])
            counts[index] += 1
            left -= 1
        offset = 0
        for index, count in enumerate(counts):
            assigned[index].extend(members[offset : offset + count].tolist())
            offset += int(count)
            capacity[index] -= int(count)

    train_ids, validation_ids, test_ids = tuple(
        tuple(sorted(int(value) for value in ids)) for ids in assigned
    )
    train_set, validation_set, test_set = map(set, (train_ids, validation_ids, test_ids))
    if (
        train_set & validation_set
        or train_set & test_set
        or validation_set & test_set
        or train_set | validation_set | test_set != set(int(value) for value in engine_ids)
    ):
        raise ValueError("engine leakage detected between train, validation, and test splits")
    return EngineSplits(
        train=frame.loc[frame[engine_column].isin(train_ids)].copy(),
        validation=frame.loc[frame[engine_column].isin(validation_ids)].copy(),
        test=frame.loc[frame[engine_column].isin(test_ids)].copy(),
        train_engine_ids=train_ids,
        validation_engine_ids=validation_ids,
        test_engine_ids=test_ids,
    )
