# PrescriptXAI Progress

## Phase status table

| Phase | Status | Notes |
|---|---|---|
| 0 — Scaffold and package foundation | Complete | Packaging, configuration, schemas, logging, CI, and checks |
| 1 — Data ingestion and preprocessing | Complete | Real FD001–FD004 loaded, split, filtered, scaled, and reported |
| 2 — Predictive models | Complete | Engine-level model training and training-only fitting |
| 3 — Constrained recourse and validation | Complete | Optimizer and validation tiers |
| 4 — Product surfaces and evaluation | Complete | CLI, optional API, dashboard, reports |
| 5 — End-to-end verification and documentation | Complete | Current measured limits in docs and artifacts |

## Decisions

- Preserve the user-provided synopsis as the source of truth; its numeric case study is illustrative.
- Keep model validity and physical plausibility as separate outcomes.
- Keep every threshold, budget, path, and algorithm parameter in validated YAML.
- Use the PRESCRIPTXAI_ environment variable prefix for runtime overrides; double underscores
  separate nested keys.
- Use PEP 735 dependency groups (core, dev, dashboard, api) with exact pins in pyproject.toml and
  complete transitive pins in uv.lock.
- Keep canonical ingestion columns (`unit_id`, `cycle`, `op_setting_1..3`, `s1..s21`) and adapt to
  the existing model vocabulary only at the model boundary.
- Default the optional RUL cap and rolling features off. Validate published subset row counts from
  YAML and record a computed archive SHA-256 when no expected digest is configured.

## Assumptions

- Python 3.11 and 3.12 are the supported CI interpreter versions.
- C-MAPSS is static run-to-failure data and does not support RUL-extension claims.
- No C-MAPSS telemetry feature is treated as a controllable actuator without a verified mapping.
- Configured beta and gamma weights are scaffold settings; current hard masks and actuator bounds
  enforce the corresponding immutability and bound requirements directly.
- `data.expected_row_counts` describes the published NASA files; it is an integrity check, not a
  model result. The configured mirror did not provide an expected digest, so the archive's local
  digest is recorded without asserting it against an external checksum.

## Open issues

- The default C-MAPSS taxonomy intentionally contains no verified actuator mapping or coupling rules.
  A domain-reviewed taxonomy and operating envelope are required to demonstrate physical recourse.
- The optional simulator remains an interface only and is disabled by default.

Phase 0 scaffold verification is complete. GNU Make's Windows executable is named mingw32-make in
this environment; its all-checks target passed using Python 3.11.17. The same target also passed in
the primary Python 3.13.9 environment. The fresh Python 3.11 environment installed all groups from
the lock, and the package wheel includes its py.typed marker.

## How to run

Install all pinned dependency groups and run checks:

~~~powershell
uv sync --all-groups --locked
make all-checks
~~~

Run individual workflows:

~~~powershell
uv run prescriptxai data download --subset FD001
uv run prescriptxai data prepare --subset FD001
make data
make train
make evaluate
make dashboard
make api
~~~

Use make clean to remove generated build, test, coverage, and type-check caches. It does not remove
downloaded datasets or trained artifacts.

## Phase 0 verification

- Ruff: passed.
- Mypy: passed for 47 package source files.
- Pytest: 79 passed with coverage enabled (79% overall coverage).
- CI workflow parsed as YAML and includes Python 3.11 and 3.12.
- Fresh Python 3.11.17 sync from pyproject.toml and uv.lock: passed.
- Wheel build and py.typed marker inclusion: passed.

## Phase 1 — Data ingestion and preprocessing

The cached NASA archive was CRC-checked and parsed from the real files. Its computed SHA-256 is
`c9c5dec12a945a82e8bb4446589d7fb3cc057b5e5d81fa1a12e25ee9912ad3b2`; no expected checksum was
configured. Published row-count checks passed for train, test, and test-RUL files in every subset:

| Subset | Train rows | Test rows | Test-RUL rows | Train engines |
|---|---:|---:|---:|---:|
| FD001 | 20,631 | 13,096 | 100 | 100 |
| FD002 | 53,759 | 33,991 | 259 | 260 |
| FD003 | 24,720 | 16,596 | 100 | 100 |
| FD004 | 61,249 | 41,214 | 248 | 249 |

Retained model feature lists were measured with `variance_threshold: 1e-8`, fitting the variance
filter on training engines only. All subsets retain `op_setting_1`, `op_setting_2`, and
`op_setting_3`:

- **FD001:** `s2, s3, s4, s6, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21`. Dropped:
  `s1, s5, s10, s16, s18, s19`.
- **FD002:** `s1` through `s21`. No sensors dropped.
- **FD003:** `s2, s3, s4, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s17, s20, s21`.
  Dropped: `s1, s5, s16, s18, s19`.
- **FD004:** `s1` through `s21`. No sensors dropped.

The CLI wrote train, validation, internal holdout, and NASA official-test CSVs plus one quality
report and fitted preprocessor per subset under ignored `data/processed/` and `artifacts/` paths.
The report records RUL class balance, row/engine counts, regime counts, exact feature lists, and
actual split-overlap checks. FD002/FD004 use deterministic six-cluster operating-setting regimes;
FD001/FD003 use one regime. Raw retained sensors and reversible `*_scaled` sensor columns are
both present; dropped sensors are absent from prepared CSVs and listed in the JSON artifact.

### Phase 1 verification

- `prescriptxai data download --subset FD001`: passed against the valid local archive; printed the
  computed digest. The live network transfer path was not exercised because the archive was already
  present; failed-transfer handling is covered by a test and emits manual instructions with exit 2.
- `prescriptxai data prepare --subset FD001` and the same command for FD002–FD004: passed on real
  NASA data with configured row-count checks.
- Fixture preparation idempotency, loader schema/corruption, exact RUL boundary, engine disjointness,
  deterministic regimes, train-only scaling, dropped sensors, and inverse round-trip: passed.
- `mingw32-make all-checks` with Python 3.11.17: Ruff passed, mypy passed for 48 source files,
  95 tests passed, 80% total coverage, and the docs target passed.
