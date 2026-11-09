"""Adapter for the existing NASA C-MAPSS archive loader."""

from __future__ import annotations

import pandas as pd

from prescriptxai.adapters.base import DatasetAdapter
from prescriptxai.data.cmapss import add_test_labels, load_cmapss_archive


class CmapssAdapter(DatasetAdapter):
    """Expose archive rows without changing the legacy parser or label arithmetic."""

    def _canonical(self, frame: pd.DataFrame) -> pd.DataFrame:
        columns = {feature.column: feature.id for feature in self.spec.measurement_features}
        columns.update(
            {self.spec.dataset.unit_column: "unit_id", self.spec.dataset.time_column: "time_index"}
        )
        return frame.loc[:, list(columns)].rename(columns=columns)

    def load(self) -> pd.DataFrame:
        """Return complete run-to-failure trajectories for training and internal splits."""
        subset = self.spec.dataset.subset
        if subset is None:
            raise ValueError("archive subset is required")
        return self._canonical(load_cmapss_archive(self.path, subset).train)

    def load_official(self) -> pd.DataFrame:
        """Return official truncated trajectories with archive-derived row-level RUL."""
        subset = self.spec.dataset.subset
        if subset is None:
            raise ValueError("archive subset is required")
        dataset = load_cmapss_archive(self.path, subset)
        labeled = add_test_labels(dataset.test, dataset.test_rul, self.spec.failure.horizon)
        return self._canonical(labeled).assign(
            remaining_life=labeled["rul"], failure_label=labeled["y"]
        )
