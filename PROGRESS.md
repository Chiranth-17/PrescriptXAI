# PrescriptXAI Progress

## Phase status table

| Phase | Status | Notes |
|---|---|---|
| 0 — Scaffold and package foundation | Complete | Packaging, configuration, schemas, logging, CI, and checks |
| 1 — Data ingestion and preprocessing | Complete | Real FD001–FD004 loaded, split, filtered, scaled, and reported |
| 2 — Predictive models | Complete | XGBoost, differentiable MLP/LSTM, validation-only calibration, and real FD001 metrics |
| 3 — Feature taxonomy and sensor coupling | Complete | Proxy taxonomy, fitted physical bounds, coupling propagation and Tier 4 checks |
| 4 — Constrained recourse engine | Closed; synopsis targets measured honestly | Constrained search, final protocol audit, grouped uncertainty, historical errata |
| 5 — Multi-tier validation (current prompt) | Closed; measured gaps retained | Shared tiers, bounded feedback, real funnels, audits and phase5-closed |
| 6–11 — Remaining current phases | Not started | Source prompts / Part B changes table not supplied |

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
- Phase 4 closure metrics are in `docs/phase4_final.md`; the earlier contradictory summary has
  been superseded. The final report distinguishes model validity from Tiers 2–4 plausibility and
  reports v1 and frozen v2, all-alert, first-alert, grouped OOF, and official-test populations.

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

## Phase 4 — Constrained recourse engine and final closure

The constrained engine and the final evidence audit are closed. Closure means the implementation,
protocol comparison, diagnostics, and documentation are complete; it does not mean that every
synopsis target passed. The measured headline result remains below the true-risk target. All results
use the true calibrated predictor for Tier 1, and report plausibility independently for Tiers 2–4.

The authoritative report is `docs/phase4_final.md`; its complete saved evidence is
`docs/phase4_full_diagnosis_results.json`. The SVG K curve is `docs/phase4_k_curve.svg`. The report
uses the v1 protocol (`k_max=3`, `K=1`, `D_max=5`) and the precommitted v2 protocol (`k_max=3`,
`K=1`, `D_max=8`). Engine-cluster bootstrap intervals are used throughout. Headline status:

| Headline metric | Target | V1 | V2 | Result |
|---|---:|---:|---:|---|
| True calibrated model validity, all 200 queries | ≥0.95 | 0.560 [0.468, 0.636] | 0.560 [0.469, 0.637] | Fail both |
| Tier 2 plausibility, all 200 queries | ≥0.90 | 0.530 [0.432, 0.615] | 0.990 [0.975, 1.000] | V1 fail; V2 pass |
| Joint Tiers 2–4 plausibility, all 200 | reported separately | 0.435 [0.362, 0.498] | 0.525 [0.447, 0.592] | Low; not model validity |
| Mean risk reduction | ≥0.60 | 0.610 [0.551, 0.662] | 0.611 [0.553, 0.667] | Pass both |
| Mean changed features among joint successes | ≤3 | 2.816 [2.735, 2.879] | 2.781 [2.739, 2.829] | Pass both |
| Optimization p95 | ≤1,800 ms | 1,904.5 ms [1,648.9, 2,175.5] | 2,022.5 ms [1,679.7, 2,514.5] | Fail both |

Headline uses 200 sampled rows from 378 actionable alerts across 15 held-out engines. The all-alert
results, first alert per engine, grouped out-of-fold sample, and official NASA test sample are all
reported separately with engine-cluster intervals. The official test sample contains 159 alerts from
19 engines; grouped OOF contains 200 sampled queries from 78 engines across five folds. Protocol v2
Tier 2 rates were 0.989 for all alerts, 0.935 for grouped OOF, and 1.000 for official test; corresponding
joint Tiers 2–4 rates were 0.521, 0.575, and 0.881. These do not change the headline model-validity
result. First-alert summaries have only 15 engines and are not used to claim the headline target.

### Closure diagnostics and decisions

- **Oracle and failures:** 60 of 113 failed headline cases were replayed against the verified finite
  search superset: 59 had no safe candidate found within that set and one had a missed candidate.
  Every replay matched the production return. No case is classified as globally infeasible; finite
  candidate searches do not prove continuous-space infeasibility.
- **Sparsity and settings:** headline policy is `k_max≤3`. `k_max=5` is one-factor sensitivity only.
  On a 60-query/14-engine sample, k3 baseline Tier 1/Tier 2/joint rates were 0.533/0.517/0.383;
  changing only k to 5 gave 0.833/0.733/0.717. Successful headline candidates passed recorded
  support, bound, and rate checks.
- **Movement distance and Dmax:** `max_scaled_distance=6` in the old expanded run meant a per-feature
  scaled movement radius; it was not Mahalanobis `D_max`, which remained 5. Fresh one-factor radius
  2 and 6 runs both measured 0.533/0.517/0.383 for Tier 1/Tier 2/joint, with latency differences.
  Dmax v1=5 and v2=8 are separately frozen and reported; the v2 setting improves Tier 2 and does not
  produce the Tier 1 target.
- **Historical count discrepancy:** an old diagnosis table reported 112/200, 106/200, and 87/200
  against expanded settings (`k_max=5`, movement radius 6, 3 restarts, 100 iterations, grid 10).
  The saved k3 run instead records 135/158/127 and the saved k5 run 174/161/156; the old table has
  no matching per-query artifact. Its cause cannot be determined. Fresh k5-only sensitivity changes
  outcomes, so the settings are honored in the current implementation. The old report is marked
  superseded in `docs/phase4_diagnosis.md`.
- **K sensitivity:** the one-factor K={1,2,3,5,10} measurements and confidence intervals are in the
  final report. K>1 multiplies adjacent-cycle sensor-proxy rates and is an assumed intervention
  horizon, not observed actuator dynamics.
- **Tier 2 and fallbacks:** Tier 2 is constraint-first. Any fallback that does not pass all physical
  tiers is flagged as engineering-only and excluded from successful recourse. Distances for queries
  and returns are both reported. Validation-alert Mahalanobis p95 was 7.959; low-risk p95 was 5.342
  (secondary diagnostic only).
- **FAST mode:** among 32 shared successes, FAST and thorough returned exactly the same candidate
  and risk. FAST optimization p95 was 2,435.7 ms, above the 1,800 ms target.
- **End-of-life concentration:** among headline queries with RUL≤10 (83 rows across 15 engines),
  joint success was 0.096 [0.025, 0.190]. Risk-reduction histograms and RECOVERABLE/PARTIAL/ESCALATE
  triage appear by population and life stage in the final report.
- **Coupling quality:** engine-grouped held-out R² and residual standard deviation are reported for
  every dependent sensor. `sensor_3` (R²=0.3469) and `sensor_6` (R²=0.0304) fall below the configured
  0.35 fit floor and remain explicitly flagged.
- **Evidence boundary:** the work is E1 dataset/model and software evidence only. C-MAPSS has sensor
  telemetry, no commanded actuator interventions or validated counterfactual simulator. The proxy
  rate limits are adjacent-cycle sensor movement. Do not infer physical control efficacy, maintenance
  benefit, or RUL extension.

### Phase 4 verification

The final run/oracle used source commit `d1a6945fa9671beb6c48ebbbf89f0a2c72221488`;
holdout/sensitivity metrics came from `7860fed5a99b6c94eefc2ffd2c8327052ea56b24`, and grouped
OOF/official-test metrics came from `4a8275a788c9998d80acf07f3e7e9dfe2fcbe179`. Protocol v2 was
frozen at `5f88d27b329a3ff673f841e525b154bfc853432c`. Exact run/config hashes, model and data hashes,
thresholds, populations, and timings are preserved in the JSON evidence.

- Real-data closure command: `uv run python scripts/diagnostics/run_full_diagnosis.py`.
- Main implementation checks: `uv run ruff check src/prescriptxai tests scripts/diagnostics/run_full_diagnosis.py`,
  `uv run mypy src/prescriptxai`, and `uv run pytest --cov=prescriptxai`.
- Closure verification on Python 3.13.9: `mingw32-make all-checks` passed; Ruff passed, mypy passed
  for 49 source files, 188 tests passed at 79% total coverage, and the documentation target passed.
  The 24 convergence warnings are from deliberately short nonlinear-backend fixtures.
- Report target misses remain visible and are not corrected by redefining metrics or changing the
  frozen headline protocol.

## Phases 5–11 orchestration preflight — 2026-10-18

**Not started: required source instructions are missing.** The requested
`docs/prompts/remaining_phases_5_to_11.md` and `docs/prompts/phase_changes.md` both returned `False`
from `Test-Path`; no `docs/prompts/` directory or Part B change table is present. The known pasted
attachment contains Phase 4 closure tasks only. Numbered rules 12–21 were subsequently supplied by
the user and added verbatim to `AGENTS.md`, preserving the original instructions and rules 22–29.

The requested Phase 5–11 tasks and gates cannot be inferred from the older roadmap. Existing
Phase 5/6 completion rows above describe that earlier delivery and do not certify execution of the
new prompts. All seven requested phases remain unstarted; zero phase gates have run and no new
`phase<N>-closed` tags have been created for this request. Evidence and missing-input requirements
are recorded in `docs/traceability.md`.

The remaining inputs are the Phase 5–11 prompt file and Part B table. Copy the actual Part B table
into the changes file before executing Phase 5; then run the per-phase gates, record measurements,
commit, tag, and proceed in order.


## Phase 5 validation revision — active

The user subsequently supplied the complete Phase 5 prompt directly; it supersedes the Phase 5
missing-prompt preflight above. Phase 6–11 prompts and the Part B table remain unavailable.
Rules 12–29 are preserved in AGENTS.md. No later phase is inferred from an older roadmap.

The Phase 5 protocol/configs were committed at `d64826c` before real-data measurements. The
implementation consolidates train-only shrinkage/Cholesky distances, regime-aware scoring,
validation-only residual calibration, independent tier verdicts, explicit skipped dynamics and
bounded in-loop feedback. Read-only independent audits identified provenance and adapter gaps;
these are being addressed before the measurement run. Gate results and measured funnels will
be added after execution; this section does not claim closure.


Preflight: 213 tests passed, coverage 79.6811% (displayed 80%), Ruff and mypy clean. A final
read-only audit caught two additional negative-input/integration cases before the completed
measurement: NaN in the original Tier 3 state, and persisted validator/config mismatches.
The first real run was interrupted without publishing a report; its cache is not reused by the
new source revision. Both cases have explicit regression tests. Config thresholds, bounds, rates,
predictor and solver settings are unchanged. Historical config mirrors now load successfully.


## Phase 5 multi-tier validation — closed

Real FD001 run `phase5-20261018T092602Z`; measured source `8b1a206fc1800a0674019b6e0527c2a31a5159df`; preregistration `d64826c5c1bd69dc6310c7c2d11506a7add11822`.

Implemented: shared true-predictor Tier 1, train-only Ledoit–Wolf/Cholesky Tier 2 with regime/reference/quantile options, reused bound/rate Tier 3, validation-only residual-calibrated Tier 4, explicit skipped simulator, schema 1.1.0, and bounded in-loop feedback. API/dashboard preserve margins, rules, evidence and assumptions.

### Headline measurements and gaps

Phase5 integrated solver: run `phase5-20261018T092602Z`; config `configs\experiments\phase5-validation-v1.yaml` SHA-256 `a9a32d9d0623db1038a58389b4624c5255c939b4a9ad32f38ef92293c65bd661`; git `8b1a206fc1800a0674019b6e0527c2a31a5159df`; protocol `v1`; k_max=3; K=1; D_max version `v1`=5.0; population `internal_headline_integrated`.

| Metric | Observed (engine bootstrap) |
|---|---:|
| tier1_all_queries | 112/200 = 0.560 [0.473, 0.638]; 15 engines |
| tier2_all_queries | 106/200 = 0.530 [0.437, 0.616]; 15 engines |
| tier3_all_queries | 200/200 = 1.000 [1.000, 1.000]; 15 engines |
| tier4_all_queries | 190/200 = 0.950 [0.923, 0.979]; 15 engines |
| joint_tiers1_to4_all_queries | 87/200 = 0.435 [0.364, 0.502]; 15 engines |

Phase5 integrated solver: run `phase5-20261018T092602Z`; config `configs\experiments\phase5-validation-v2.yaml` SHA-256 `7c74cabf0f2b8347c116a29cf03dfae16184f39066a46e441c42479f985b8bae`; git `8b1a206fc1800a0674019b6e0527c2a31a5159df`; protocol `v2`; k_max=3; K=1; D_max version `v2`=8.0; population `internal_headline_integrated`.

| Metric | Observed (engine bootstrap) |
|---|---:|
| tier1_all_queries | 112/200 = 0.560 [0.473, 0.638]; 15 engines |
| tier2_all_queries | 198/200 = 0.990 [0.977, 1.000]; 15 engines |
| tier3_all_queries | 200/200 = 1.000 [1.000, 1.000]; 15 engines |
| tier4_all_queries | 190/200 = 0.950 [0.923, 0.979]; 15 engines |
| joint_tiers1_to4_all_queries | 106/200 = 0.530 [0.452, 0.600]; 15 engines |

The 95% true-model target is missed under both protocols. Tier 2 meets its 90% all-query target only under v2. Joint is reported separately and is not compared with 90%. Final-validation p95 is 10.92/16.46 ms (pass); optimization p95 is 4618.75/6735.16 ms (fail). The report supplies engine-bootstrap intervals and population labels for every latency table.

### Coverage, audits and evidence limits

- Produced 42 labeled funnels and 752 integrated population rows; 456 accepted recommendations. These named populations overlap, so the combined counts are an audit total, not an unbiased pooled success rate.
- Two independent read-only audits found zero accepted unsafe, frozen-feature, support, bound, rate or coupling violations. Frozen-predictor risks reproduced exactly; maximum D_M difference was 1.78e-15. All 12 partition sets and 51 input/artifact hashes were checked. Feedback never exceeded the configured two refinements.
- 20 rejected development rows contain 24 bound and 24 rate-interval violations, covering 10 engine/cycle queries across both protocols. All have `infeasible_actuator_interval`, infeasible actuator constraints, and acceptance=False. These original/diagnostic states are not recommended actions.
- All 11 missing OOF candidates per protocol remain in the 200-query denominator. The OOF first-alert run covers all 100 engines; full 2378-alert paired coverage remains Partial because Phase 4 did not save all candidates. Official replay covers 159 alerts / 19 engines. The K curve carries 60 queries / 14 engines beside its bootstrap intervals.
- Reused saved states are explicitly not fresh independent generalization. Proxy mapping, raw bounds/rates and assumed K are unchanged. Only the required covariance estimator and validation-only residual calibration were revised; risk gates and D_max stay frozen.
- sensor_6 calibration R² is 0.031962, residual std 0.001653, and threshold-exceedance share 0.029068 on 2649 healthy-to-moderate rows from 16 validation engines. Historical grouped fit warnings remain. Available checks reach E3 at most; no E4/E5 or RUL-extension claim.

### Verification and reproduction

- `mingw32-make all-checks`: Ruff clean; mypy clean for 51 source files; 215 tests passed; coverage 79.7753% (80% displayed), above Phase 4’s reported 79%; docs check passed. The 24 convergence warnings come from deliberately short test-only nonlinear-backend fits.
- Run: `uv run python scripts/diagnostics/phase5_validate.py`. Measurement inputs/configs were committed before the run. Presentation additions were rendered offline from the saved JSON without rerunning or tuning the solver.
- Main report: `docs/phase5_changes.md`; curve: `docs/phase5_k_curve.svg`; detailed ignored evidence: `artifacts/phase5/funnel.json`; diagnostics/validators: `artifacts/phase5/`.
- Detailed evidence SHA-256: `8cefe8e69091369e4db1d4935e7b57fd9bc1fbaec16dac646790e0e1564e7e13`.
- Independent audits and the final gate passed; closure tag: `phase5-closed`.

### Open issues / next phase

- The validity and optimization-latency targets remain missed. Any tuning or performance changes must be developed on validation engines and frozen before a future test run; no targets were adjusted for this closure.
- Full OOF all-alert paired coverage and new unseen-engine generalization are Partial/Not met as recorded in `docs/traceability.md`. No dynamic simulator or validated emulator is available; NullSimulator correctly skips.
- Phase 6–11 prompts and the Part B changes table remain unavailable. The directly supplied Phase 5 prompt is complete; later phases have not been inferred or started.
