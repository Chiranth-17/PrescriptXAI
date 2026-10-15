# JOURNAL.md — Session Log

## Session: 2026-10-03 06:40 UTC

### Objective

Complete the requested C-MAPSS ingestion and preprocessing phase using real NASA data where
available, and record measured retained feature sets.

### Accomplished

- Added canonical loader schema, integrity validation, optional RUL capping, and inclusive failure
  labels.
- Added train-only variance filtering, deterministic FD002/FD004 regime clustering, reversible
  regime-aware scaling, engine lifetime splits, processed partitions, reports, and CLI commands.
- Prepared real FD001–FD004 files and recorded the feature lists and checks in `PROGRESS.md`.

### Verification

- [x] `prescriptxai data download --subset FD001` validated the local archive, CRC, and FD001 row
  counts. Computed archive SHA-256: `c9c5dec12a945a82e8bb4446589d7fb3cc057b5e5d81fa1a12e25ee9912ad3b2`.
- [x] `prescriptxai data prepare --subset FD001` and FD002–FD004 passed against the real archive.
- [x] `mingw32-make all-checks`: Ruff and mypy passed, 95 tests passed with 80% coverage, docs check
  passed.

### Blockers Encountered

- The first full `uv run pytest` collection could not import the new fixture as `tests.fixtures`
  because pytest is configured with `pythonpath = ["tests"]`. Imports were corrected to
  `fixtures.cmapss`; the full suite then passed.
- Live network transfer was not exercised because the valid archive was already present. Both
  successful and failed transfer behavior are covered with mocked responses; failed retrieval
  provides manual instructions and does not generate substitute data.

### Handoff Notes

- `PROGRESS.md` has the exact retained features per subset and measured file counts.
- Generated CSVs, JSON reports, and fitted preprocessing artifacts are ignored under `data/` and
  `artifacts/`.

---

*Last updated: 2026-10-03*

## Phase 3 — Feature taxonomy, physical bounds, and sensor coupling (2026-10-15)

### Accomplished

- Added configurable group mappings for all three immutable operating settings and all 21 C-MAPSS
  sensor channels. Seven measured telemetry channels are explicitly designated proxy controls; the
  config and limitations documentation say they are not verified actuator commands.
- Added YAML taxonomy validation, train-percentile bounds with margin and manual overrides, raw and
  scaled bound transforms, idempotent projection, and actuator rate checks.
- Added train-engine-only, healthy-to-moderate sensor coupling fits, grouped out-of-fold metrics,
  learned residual constraints, configurable engineering rules, differentiable torch propagation,
  artifact persistence, and HTML/PNG diagnostics.
- Connected fitted bounds and coupling to the predictor registry and recourse path. Sparse fallback
  remains within the configured feature cap even when no safe candidate is found.
- Corrected README and technical docs that still claimed the default feature map had no proxies.

### Verification evidence

- `uv run pytest tests/unit/test_constraints_phase3.py tests/unit/test_taxonomy.py tests/unit/test_recourse_validation.py -q`
  → `40 passed`.
- `uv run prescriptxai constraints fit-coupling --subset FD001 --train-csv data/processed/FD001_train.csv --output artifacts/FD001-coupling.joblib --report artifacts/FD001-coupling-diagnostics`
  → persisted the model and HTML/PNG reports. Engine-grouped out-of-fold R² was 0.330574 for
  `sensor_3` and 0.030526 for `sensor_6`, below the configured floor 0.35; both remain flagged.
- Reloaded the persisted coupling artifact and confirmed the diagnostic files exist. Refit and
  validated taxonomy bounds on real train rows for all subsets: model feature counts were FD001 18,
  FD002 24, FD003 19, FD004 24, with seven active proxy channels in each.
- Real high-risk holdout diagnostic (engine 2, cycle 261): risk 0.88002 → 0.48425, 3 proxy changes
  (cap 3); model safety failed, Tier 2 passed, Tier 3 failed, Tier 4 passed. The recommendation was
  correctly reported unsuccessful.
- `mingw32-make all-checks` → Ruff passed; mypy passed for 49 source files; `129 passed`, 77% total
  coverage; documentation target passed.

### Remaining limitations

- The configured channels and learned statistical relationships are research proxies and are not
  evidence of causal physics. Two FD001 coupling relations fall below the configured quality floor.
- The observed diagnostic recourse did not achieve the safe-risk threshold and failed Tier 3.
  These rates and outcomes must be evaluated over a saved benchmark run before operational claims.

---

*Last updated: 2026-10-15*
