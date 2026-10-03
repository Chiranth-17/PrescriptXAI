# C-MAPSS ingestion and preprocessing

PrescriptXAI reads the NASA C-MAPSS FD001–FD004 subsets as whitespace-delimited telemetry with
canonical columns `unit_id`, `cycle`, `op_setting_1..3`, and `s1..s21`. IDs and cycles are positive
integers, cycles must start at one and be contiguous within each unit, and the loader rejects
missing, non-numeric, non-finite, duplicate, or malformed rows.

## Acquire and prepare

```powershell
uv run prescriptxai data download --subset FD001
uv run prescriptxai data prepare --subset FD001
```

Acquisition uses `data.dataset_url` from `configs/default.yaml`. An optional `data.dataset_sha256`
pins an expected archive digest. ZIP CRCs are checked and the computed SHA-256 is recorded. If the
source cannot be reached, the CLI returns `DATASET_DOWNLOAD_UNAVAILABLE` with instructions to save
the original NASA archive as `data/raw/CMAPSSData.zip`; it never substitutes generated telemetry.
Published per-subset row counts in `data.expected_row_counts` are compared to the parsed train, test,
and test-RUL files when configured.

Preparation writes four CSV partitions and `data/processed/<subset>_report.json`. The report
contains source digest, row and engine counts, class balance, exact retained/dropped sensors,
feature names, and operating-regime counts. Fitted KMeans/scaler state and the explicit sensor-drop
list are persisted under `artifacts/`. Re-running with the same input, configuration, and seed
reproduces the report and processed CSV files.

## Labels and splits

For run-to-failure training rows, exact RUL is `max_cycle(unit_id) - cycle`. The binary target is
`y = 1[RUL <= H]`, including the boundary `RUL == H`. `data.rul_cap` is optional and defaults to
`null` (off); if set, it caps the reported RUL only, while the target still uses uncapped RUL. This
cap is a piecewise-capped RUL target convention and does not imply a dynamic RUL trajectory.

The official test RUL file gives remaining cycles after each truncated engine's final observed row.
Earlier test rows add the cycle difference from that final row. Train, validation, and internal
holdout partitions are disjoint by engine ID. Lifetime quantile buckets are apportioned across the
partitions with the configured seed. Scalers, variance filters, and regime clustering are fitted
only on the training-engine partition.

## Sensor mapping

Sensors with training variance at or below `data.variance_threshold` are dropped for that subset.
The report and `artifacts/<subset>_dropped_sensors.json` record the exact change. Raw sensor columns
remain in physical units; scaled values are added as `sN_scaled` columns and can be inverted using
the persisted, regime-aware preprocessor. FD002/FD004 cluster the three operating settings with
the configured `data.regime_k` (default six) and use per-regime sensor means and scales. FD001/FD003
use one sensor-statistics regime. Optional grouped rolling means are controlled by
`data.rolling_features` and are disabled by default.

C-MAPSS is static run-to-failure data. These labels and transformations do not demonstrate
intervention effects, closed-loop behavior, or RUL extension on a physical engine.
