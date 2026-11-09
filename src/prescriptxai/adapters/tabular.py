"""Local CSV and Parquet telemetry adapter."""

from __future__ import annotations

import numpy as np
import pandas as pd

from prescriptxai.adapters.base import DatasetAdapter


class TabularAdapter(DatasetAdapter):
    """Read named telemetry columns from the machine specification."""

    def load(self) -> pd.DataFrame:
        """Read a stable canonical table without filling missing measurements."""
        mapping = self.spec.dataset
        if self.path.suffix.lower() == ".csv":
            frame = pd.read_csv(self.path, dtype={mapping.unit_column: "string"})
        elif self.path.suffix.lower() == ".parquet":
            frame = pd.read_parquet(self.path)
        else:
            raise ValueError("tabular telemetry must be a local CSV or Parquet file")
        columns = {feature.column: feature.id for feature in self.spec.measurement_features}
        columns.update({mapping.unit_column: "unit_id", mapping.time_column: "time_index"})
        if mapping.remaining_life_column is not None:
            columns[mapping.remaining_life_column] = "remaining_life"
        if mapping.event_column is not None:
            columns[mapping.event_column] = "event"
        missing = columns.keys() - set(frame.columns)
        if missing or frame.empty:
            raise ValueError(f"telemetry is empty or missing mapped columns: {sorted(missing)}")
        result = frame.loc[:, list(columns)].rename(columns=columns)
        result["unit_id"] = result["unit_id"].astype("string").str.strip()
        result["time_index"] = pd.to_numeric(result["time_index"], errors="coerce")
        if (
            result["unit_id"].isna().any()
            or result["unit_id"].eq("").any()
            or not np.isfinite(result["time_index"].to_numpy(dtype=float)).all()
        ):
            raise ValueError("unit IDs must be present and time indices must be finite")
        if result.duplicated(["unit_id", "time_index"]).any():
            raise ValueError("telemetry contains duplicate unit/time rows")
        return result.sort_values(["unit_id", "time_index"], kind="stable", ignore_index=True)
