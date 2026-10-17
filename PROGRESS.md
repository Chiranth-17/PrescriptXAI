# PrescriptXAI Progress

## Phase status table

| Phase | Status | Notes |
|---|---|---|
| 0 — Scaffold and package foundation | Complete | Packaging, configuration, schemas, logging, CI, and checks |
| 1 — Data ingestion and preprocessing | Complete | Real FD001–FD004 loaded, split, filtered, scaled, and reported |
| 2 — Predictive models | Complete | XGBoost, differentiable MLP/LSTM, validation-only calibration, and real FD001 metrics |
| 3 — Feature taxonomy and sensor coupling | Complete | Proxy taxonomy, fitted physical bounds, coupling propagation and Tier 4 checks |
| 4 — Constrained recourse engine | Complete with target failures | L-BFGS-B, hard constraints, sparse support search, true-model scoring |
| 5 — Product surfaces and evaluation | Complete | CLI, optional API, dashboard, reports |
| 6 — End-to-end verification and documentation | Complete | Current measured limits in docs and artifacts |

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
- Fit predictors on train engines, use validation engines for early stopping and calibration, and
  reserve the internal holdout engines for metrics and reliability diagnostics.
- Give XGBoost a distilled MLP gradient path and report measured fidelity for the surrogate.
- Keep C-MAPSS operating settings immutable and expose measured sensor channels used as controllable
  proxies only through `configs/features.yaml`, with a visible proxy warning.
- Estimate physical bounds from the 1st–99th train-engine percentiles plus the configured margin;
  persist fitted ranges with trained model and coupling artifacts.
- Score coupling fit quality with engine-grouped cross-validation and report below-floor sensors
  directly; do not use in-sample fit scores for the quality gate.
- Use L-BFGS-B with a smooth L1 objective by default and exact p/n variable splitting as an
  alternative. Immutable variables are excluded/fixed, dependent sensors are propagated, and
  only true calibrated predictor scores determine success.
- A recommendation is actionable only if physical, rate, and scaled trust intervals intersect.
  Evaluation reports these infeasible high-risk inputs separately instead of treating them as
  optimizer violations or returning them as actions.
- Default proxy rate limits use the configurable p99 of adjacent-cycle absolute changes, fitted
  within train engines only and persisted with the model. They are telemetry envelopes, not
  actuator slew rates.
- Model validity records the true calibrated-risk threshold independently. Joint success also
  requires a sparse optimizer-feasible action and passing Tiers 2–4; a safe-risk diagnostic that
  fails the sparse search cannot count as a successful action.

## Assumptions

- Python 3.11 and 3.12 are the supported CI interpreter versions.
- C-MAPSS is static run-to-failure data and does not support RUL-extension claims.
- Configured C-MAPSS controllable channels are measured telemetry proxies, not verified actuator
  commands. They are suitable for research recourse only until a domain-reviewed mapping exists.
- Configured beta and gamma weights are scaffold settings; current hard masks and actuator bounds
  enforce the corresponding immutability and bound requirements directly.
- `data.expected_row_counts` describes the published NASA files; it is an integrity check, not a
  model result. The configured mirror did not provide an expected digest, so the archive's local
  digest is recorded without asserting it against an external checksum.

## Open issues

- The C-MAPSS proxy mapping and statistical coupling rules are configurable, but none proves a real
  actuator mapping or causal thermodynamics. A domain-reviewed control mapping is required before
  any operational use.
- The measured FD001 coupling fit falls below the configured R² floor for `sensor_3` and `sensor_6`;
  those relations remain flagged and need better predictors or additional validated measurements.
- The optional simulator remains an interface only and is disabled by default.
- The LSTM supports sequence scoring and gradients, but the current snapshot recourse request does
  not carry the history window. LSTM training/evaluation works; current interactive LSTM recourse
  remains unsupported until that request interface accepts history.
- The corrected Phase 4 200-state FD001 sample met the sparsity target but missed true model
  validity (12.5%), sparse recourse feasibility (11.5%), joint success (11%), physical plausibility
  (68%), risk reduction (0.52495), and mean latency targets. These measured outcomes must not be
  presented as demonstrated operational recourse.

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
uv run prescriptxai train --subset FD001 --model xgb
uv run prescriptxai train --subset FD001 --model mlp
uv run prescriptxai train --subset FD001 --model lstm
uv run prescriptxai constraints fit-coupling --subset FD001
uv run prescriptxai evaluate
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

## Phase 2 — Predictive models and calibrated risk

Trained all three model choices on the real FD001 C-MAPSS training file with seed `1729`, failure
horizon `30`, and thresholds `tau_danger=0.80`, `tau_safe=0.20`. The 100 run-to-failure engines
were split as 69 train, 16 validation, and 15 held-out test engines. Engine-ID checks found zero
overlap. Feature filtering and scaling fit on train engines; early stopping and sigmoid calibration
used validation engines. The held-out partition contains 3,281 cycle rows and 465 positive labels.
NASA's official truncated test file was not used for these metrics.

All three models used this exact ordered input list:
`op_setting_1, op_setting_2, sensor_2, sensor_3, sensor_4, sensor_6, sensor_7, sensor_8, sensor_9,
sensor_11, sensor_12, sensor_13, sensor_14, sensor_15, sensor_17, sensor_20, sensor_21,
op_setting_3`. This corresponds to the Phase 1 FD001 retained sensor set (`s2,s3,s4,s6,s7,s8,s9,
s11,s12,s13,s14,s15,s17,s20,s21`); the train-only variance filter dropped `s1,s5,s10,s16,s18,s19`.

Held-out classification and calibration results came from the generated JSON artifacts. Confusion
matrix values below are `TN/FP/FN/TP`, with labels ordered `0,1`.

| Model | AUROC | AUPRC | F1 at 0.80 | Brier before → after | ECE before → after | High-risk recall | TN/FP/FN/TP |
|---|---:|---:|---:|---:|---:|---:|---:|
| XGBoost | 0.99105 | 0.95674 | 0.85612 | 0.03485 → 0.02552 | 0.03654 → 0.00909 | 0.77419 | 2800/16/105/360 |
| MLP | 0.99126 | 0.95717 | 0.85511 | 0.02509 → 0.02527 | 0.00723 → 0.00748 | 0.77419 | 2799/17/105/360 |
| LSTM | 0.99299 | 0.96543 | 0.83436 | 0.02251 → 0.02204 | 0.01364 → 0.01070 | 0.73118 | 2806/10/125/340 |

The FD001 XGBoost AUROC exceeded the investigation trigger of `0.90`. Its distilled MLP had test
MAE `0.01321`, Spearman rank correlation `0.96763`, agreement `0.98659` at `tau_safe=0.20`, and
agreement `0.99025` at `tau_danger=0.80`. The MLP calibrator's held-out Brier score and ECE rose
slightly after calibration; the measured values are retained in the report.

Artifacts are `artifacts/FD001-{xgboost,mlp,lstm}-metrics.json`, model bundles, separate
Mahalanobis artifacts, and held-out reliability plots in PNG and HTML. The metrics JSON includes
reliability bins, validation calibration diagnostics, split engine IDs, feature order, and
surrogate fidelity when applicable.

### Phase 2 verification

- Real-data CLI runs for `--model xgb`, `--model mlp`, and `--model lstm`: passed.
- Unit/integration checks cover output shape/range, seeded determinism, save/load equality,
  calibration monotonicity, finite gradients, NaN/shape rejection, surrogate metrics, feature-order
  mismatch, engine-level leakage, and late-vs-early risk on the test-only degradation fixture.
- `uv sync --all-groups --locked`: passed.
- `mingw32-make all-checks` with Python 3.13.9: Ruff passed, mypy passed for 49 source files,
  105 tests passed with 77% total coverage, and the documentation target passed.

## Phase 3 — Feature taxonomy, physical bounds, and sensor coupling

`configs/features.yaml` now maps all three C-MAPSS operating settings and all 21 sensor channels
to their standard columns and meanings. Operating settings are immutable. The configured proxies
are measured fan speed (`s8`), core speed (`s9`), fuel-flow ratio (`s12`), bypass ratio (`s15`),
bleed enthalpy (`s17`), and coolant bleed (`s20`, `s21`). Each proxy has a rate limit and an
explicit note that it is not a direct actuator command. The statistical taxonomy includes all
channels; the active model feature list is subset-specific after train-only constant filtering.

Feature bounds default to the configured 1st and 99th percentiles on training engines, expanded by
2% of that percentile span. Constant features use the configured `degenerate_half_width`. YAML can
instead provide manual minima and maxima. The loader checks that manual or fitted bounds remain
within the observed training envelope plus its configured margin. Trained model and coupling
artifacts persist effective raw-unit bounds. `bound_vectors` converts them to and from scaled model
space using the fitted train-only scaler.

`SensorCouplingModel` fits one target model per active dependent sensor on training engines with
RUL above the configured healthy-to-moderate cutoff. The default Ridge backend has an exact torch
representation; configured gradient-boosting and sklearn MLP backends are distilled to a
differentiable torch MLP. Tier 4 reports out-of-fold residual bounds and YAML engineering rules.
The optimizer's torch gradient path propagates changes through dependent sensors before predictor
inference. Coupling fit R² and residual standard deviation are measured with deterministic,
engine-grouped cross-validation.

The real FD001 coupling fit used seed `1729`, five grouped folds, 47 training engines, and 8,072
healthy-to-moderate rows. Its configured floor is R² `0.35`; two relations are below that floor and
remain flagged:

| Dependent sensor | Engine-grouped out-of-fold R² | Residual standard deviation (raw units) | Floor status |
|---|---:|---:|---|
| `sensor_11` | 0.67856 | 0.11326 | pass |
| `sensor_13` | 0.66789 | 0.03371 | pass |
| `sensor_14` | 0.83837 | 4.49841 | pass |
| `sensor_2` | 0.42010 | 0.31002 | pass |
| `sensor_3` | 0.33057 | 4.12348 | below floor |
| `sensor_4` | 0.59260 | 4.36157 | pass |
| `sensor_6` | 0.03053 | 0.00154 | below floor |
| `sensor_7` | 0.59312 | 0.43846 | pass |

The fit artifact and its HTML/PNG diagnostics are written under ignored `artifacts/` as
`FD001-coupling.joblib` and `FD001-coupling-diagnostics.{html,png}`. A real FD001 healthy row
(engine 3, cycle 1, RUL 178) passes the configured pressure and temperature ordering rules; a
deliberately inconsistent temperature state fails. These empirical relations describe observed
co-variation and do not establish causal physics or real-machine safety. The proxy assumption is
documented in `docs/limitations.md`.

### Phase 3 verification

- The real retained feature lists for FD001–FD004 each passed taxonomy coverage and train-derived
  bounds validation: 18, 24, 19, and 24 model inputs respectively.
- The real FD001 coupling model and HTML/PNG diagnostics were fitted and persisted. R² floor
  failures for `sensor_3` and `sensor_6` are reported without tuning or suppression.
- Tests cover duplicate/missing/invalid bounds, masks, percentile margin behavior, bounds projection
  idempotence, raw/scaled conversion, rate-limit boundary checks, NaN rejection, real healthy-state
  rules, inconsistent-state failure, dependent-only propagation, torch gradients for all coupling
  backends, persistence, and diagnostics.
- One real high-risk held-out query (engine 2, cycle 261) was exercised through the updated engine:
  risk moved from 0.88002 to 0.48425 with three changed proxies (`sensor_17`, `sensor_20`,
  `sensor_15`), respecting `k_max=3`. It did not meet `tau_safe`; Tier 2 and Tier 4 passed while
  Tier 3 failed, so the outcome remained unsuccessful. This is a single diagnostic query, not an
  evaluation rate.
- Final `mingw32-make all-checks` on Python 3.13.9: Ruff passed; mypy passed for 49 source files;
  129 tests passed with 77% total coverage; the documentation target passed. Unit tests emitted
  convergence warnings only for deliberately short (8-iteration) nonlinear-backend fixtures.

## Phase 4 — Constrained recourse engine

Implemented constrained recourse with L-BFGS-B, hard-frozen immutable inputs, physical/rate/trust
intersections, coupling propagation, calibrated true-model rescoring, sparse support re-optimization,
structured failures, raw/scaled deltas, and per-stage timings. The objective and its L1 parameterizations
are documented in `docs/math.md`. A configurable bounded grid fallback now searches sparse actuator
supports against the true calibrated model when gradient/support search finds no physically valid
candidate. It prefers candidates passing Tiers 2–4. Initial controls outside their allowed intervals
are mandatory grid changes and count toward `k_max`; the grid does not relax any limits. It is finite
resolution and does not claim continuous/global optimality.

The final benchmark uses real FD001 data, a deterministic engine-level holdout and a seeded sample of
200 actionable high-risk rows from 378 eligible rows. The selected model and validator remain fit on
training engines only. The ignored benchmark config is `data/processed/phase4-grid-final.yaml`; its
report and per-row records are in `artifacts/FD001-evaluation-grid-final.json` and `.md`.
The search config used `max_iterations=25`, one restart, three alpha steps, one L1 step, a two-support
local search, and the five-point true-model grid. The separate 9-point 40-state diagnostic produced
no more model-valid or joint-success cases than the 5-point run, and increased mean optimization
time from about 660 ms to 888 ms, so five points remain the default.

| Measured outcome | Final FD001 result | Synopsis target/status |
|---|---:|---|
| Actionable high-risk states evaluated | 200 / 378 | At least 200: pass |
| True model-valid (`f(x') <= tau_safe`) | 131 / 200 = 65.5% | ≥95%: fail |
| Sparse recourse feasibility | 129 / 200 = 64.5% | Reported separately |
| Joint successful recourse | 127 / 200 = 63.5% | Model-safe, sparse, and Tiers 2–4 pass |
| Physical plausibility (Tiers 2–4) | 152 / 200 = 76% | ≥90%: fail |
| Tier 2 Mahalanobis plausibility | 76% | No separate target |
| Tier 3 engineering validity | 100% | No separate target |
| Tier 4 coupling validity | 100% | No separate target |
| Mean risk reduction | 0.66151 | ≥0.60: pass |
| Mean changed features among joint successes | 2.59055 | ≤3: pass |
| Mean returned diagnostic action size | 2.79 | Diagnostic only |
| Mean / P95 optimization time | 705.04 / 1,171.68 ms | Mean target 1,200–1,800 ms: fail |
| Mean / P95 pipeline time | 712.74 / 1,179.41 ms | Mean target 1,500–2,200 ms: fail |
| Frozen / actuator-bound / rate violations | 0 / 0 / 0 | Zero observed |
| Grid fallback usage | 178 / 200; mean 3,103 candidates | Diagnostic |
| Mean grid-search time per evaluated state | 39.77 ms | Included in optimization time |

A search that runs faster than the synopsis latency minimum is reported as measured; the code does not
add delay to manufacture a latency pass. Direction consistency remains unmeasured because the sampled
states had no nearby pairs inside the configured scaled-space radius. The C-MAPSS proxy, fitted p99
adjacent-cycle rates, one-step recourse, `k_max=3`, calibrated predictor, and configured `D_max` do not
produce the synopsis validity and plausibility targets on this holdout. The 40-state grid experiment
and a finer-grid check did not remove that gap. The feature channels are sensor proxies, not verified
actuators; this evaluation cannot establish physical control efficacy, RUL extension, or maintenance
benefit.

### Phase 4 verification

- Real benchmark command: `uv run prescriptxai evaluate --queries 200 --config data/processed/phase4-grid-final.yaml`.
- The final 200-record report confirms zero frozen-feature, actuator-bound, and rate-limit violations.
- Unit/integration tests cover finite-difference objective gradients, smooth/split L1 comparison,
  frozen controls, bounds and rate checks, bounded-grid support enumeration including mandatory
  projections, surrogate/true-model mismatch, true-model-safe recovery, structured closest-candidate
  failure, Tiers 2–4 selection, determinism, and recorded grid timing/evaluation counts.
- `mingw32-make all-checks`: Ruff passed; mypy passed for 49 source files; 146 tests passed with
  77% total coverage; documentation target passed. The 24 convergence warnings came from deliberately
  short nonlinear coupling fixtures.

### Open issue / acceptance blocker

Phase 4's constrained algorithm and tests are implemented, but its full synopsis acceptance gate is not
met: model validity is 65.5% (target 95%), physical plausibility is 76% (target 90%), and the mean
optimization/pipeline measurements are below their specified minimum latency bands. These failures
are not hidden or redefined. Reaching the risk/plausibility rates may require a reviewed multi-step
action horizon, real actuator/control telemetry and limits, a different validated risk model, or
additional intervention/physics evidence. Do not widen telemetry-derived rates, change `D_max`, or
relax thresholds merely to force a pass; those choices need domain evidence and must be evaluated as a
new experiment.
