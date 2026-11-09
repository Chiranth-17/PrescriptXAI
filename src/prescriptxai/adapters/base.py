"""Canonical telemetry and unit-disjoint partitioning for dataset adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from prescriptxai.data.splits import split_engines
from prescriptxai.machine_spec import MachineSpec


@dataclass(frozen=True)
class UnitPartitions:
    """Canonical rows grouped into nonoverlapping unit partitions."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame

    @property
    def units(self) -> tuple[tuple[int | str, ...], ...]:
        """Return the observed units for each split in source order."""
        return tuple(
            tuple(frame["unit_id"].unique()) for frame in (self.train, self.validation, self.test)
        )


class DatasetAdapter(ABC):
    """Load canonical long rows and derive labels from the declared source."""

    def __init__(self, spec: MachineSpec, root: Path) -> None:
        self.spec = spec
        self.path = root / spec.dataset.path

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Return unit_id, time_index, features and the available label inputs."""

    def split(self, seed: int, *, frame: pd.DataFrame | None = None) -> UnitPartitions:
        """Reuse the lifetime-stratified splitter with an audited identifier mapping."""
        rows = self.load() if frame is None else frame
        codes, identities = pd.factorize(rows["unit_id"], sort=False)
        if np.any(codes < 0):
            raise ValueError("unit IDs must be present before splitting")
        translated = pd.DataFrame(
            {"unit_id": codes + 1, "cycle": rows["time_index"].to_numpy()},
            index=rows.index,
        )
        # The shared splitter uses positive cycle numbers. A uniform origin shift
        # keeps the ordering of trajectory endpoints intact for zero-based series.
        earliest = float(translated["cycle"].min())
        if earliest < 1:
            translated["cycle"] += 1 - earliest
        split = split_engines(
            translated,
            *self.spec.dataset.split_fractions,
            seed,
            lifetime_buckets=self.spec.dataset.lifetime_buckets,
        )
        ids = (split.train_engine_ids, split.validation_engine_ids, split.test_engine_ids)
        masks = tuple(rows["unit_id"].isin([identities[i - 1] for i in part]) for part in ids)
        if not np.all(sum(mask.to_numpy(dtype=int) for mask in masks) == 1):
            raise ValueError("unit partitions must cover every row exactly once")
        return UnitPartitions(*(rows.loc[mask].copy() for mask in masks))

    def failure_labels(self, horizon: int, *, frame: pd.DataFrame | None = None) -> pd.Series:
        """Compute one label per row without treating unknown outcomes as failures."""
        if horizon <= 0:
            raise ValueError("failure horizon must be positive")
        return (self.remaining_life(frame=frame) <= horizon).astype("int8").rename("failure_label")

    def remaining_life(self, *, frame: pd.DataFrame | None = None) -> pd.Series:
        """Return the declared or derived uncapped remaining life in source time units."""
        rows = self.load() if frame is None else frame
        if rows.empty:
            raise ValueError("failure labels require telemetry")
        source = self.spec.failure.label_source
        if source == "remaining_life":
            remaining = pd.to_numeric(rows["remaining_life"], errors="coerce")
        else:
            end = rows.groupby("unit_id", sort=False)["time_index"].transform("max")
            if source == "terminal_event":
                events = rows["event"]
                if not events.isin((0, 1)).all():
                    raise ValueError("event labels must be binary")
                counts = events.groupby(rows["unit_id"], sort=False).sum()
                if (
                    not (counts == 1).all()
                    or not (events.eq(1) == rows["time_index"].eq(end)).all()
                ):
                    raise ValueError(
                        "event-labeled training requires one terminal failure per unit"
                    )
            remaining = end - rows["time_index"]
        if not np.isfinite(remaining.to_numpy(dtype=float)).all() or (remaining < 0).any():
            raise ValueError("remaining life must be finite and nonnegative")
        return remaining.rename("remaining_life")
