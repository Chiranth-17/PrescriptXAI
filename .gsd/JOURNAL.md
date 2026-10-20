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

## Session: 2026-10-17 — Phase 4 constrained recourse

### Objective

Implement sparse, physically bounded L-BFGS-B recourse with calibrated true-model validation,
then measure the requested FD001 held-out benchmark without hiding target failures.

### Decisions and changes

- Implemented smooth L1 as the default and p/n variable splitting as an alternative; both are
  compared by objective tests. Immutable variables are excluded from the decision vector.
- Intersected train-derived actuator bounds, per-step rate limits, and scaled movement intervals.
  Dependent sensors are propagated through the fitted Phase 3 torch coupling model.
- Used the differentiable surrogate in optimization and rescored candidate states using the true
  calibrated estimator. Added structured failure output, feasible nearest-point fallback, seeded
  restarts, alpha/L1 schedules, support search, and stage timing.
- Changed evaluation to count all high-risk inputs and identify non-actionable empty intervals
  before sampling the recourse benchmark. Added effective search configuration to saved reports.

### Empirical evidence

- The first default-search sample exposed 54 actuator and 54 rate-limit violations, including
  high-risk telemetry outside reachable physical/rate intervals. The candidate fallback and
  actionable-state prefilter were corrected and tested; no such violations occurred afterward.
- Real held-out FD001 benchmark: 378 eligible high-risk states; 70 infeasible one-step intervals;
  308 actionable; deterministic sample of 200 completed. Measured model-validity 0/200, overall
  physical-plausibility 0/200, Tier 2 95.5%, Tier 3 0%, Tier 4 100%, mean risk reduction 0.12047,
  mean returned diagnostic action size 2.595. There were zero frozen, bounds, or rate violations.
- Mean/P95 optimization latency 472.10/1,104.92 ms; mean pipeline latency 483.32 ms. The synopsis
  target ranges were not met. Direction-consistency was unmeasured because no sampled pairs were
  within the configured scaled-distance radius. Valid-candidate sparsity is unmeasured because no
  candidate reached the true risk threshold.
- The full configured search (500 iterations, 2 starts, 8 alpha steps, and 8 support candidates)
  was interrupted after one case exceeded 20 minutes. The completed 200-state evaluation therefore
  used an ignored temporary YAML config with 25 iterations, one restart, three alpha steps, one L1
  step, two support candidates, and eight line-search steps. It retains the same objective and
  true-model validity rule; this computational budget is reported as a limitation.

### Verification

- 2-query real-data smoke test with the benchmark search config: completed and showed zero frozen,
  bounds, and rate violations.
- `mingw32-make all-checks` → Ruff passed; mypy passed for 49 source files; 139 tests passed with
  77% total coverage; docs target passed. The only warnings came from deliberately short nonlinear
  coupling test fixtures.

### Remaining limitations

- The run did not achieve the required model validity or risk reduction. The feature proxies and
  statistical coupling are not validated control actions; no maintenance outcome or RUL extension
  can be claimed.
- The reduced search budget, absence of any valid candidate, and three below-target latency/risk
  outcomes require further optimizer/model investigation before operational use.

---

## Session: 2026-10-17 — Phase 4 validation and success-status correction

### Corrective findings

- Tier 3 applied percentile ranges for every feature, including dependent sensors and dropped
  sensors with unresolved bounds. It now checks configured actuator proxy bounds only; immutable
  features remain frozen, rates remain checked, and the distribution/coupling tiers remain separate.
- The previous 3%-of-range rate limit contradicted observed adjacent-cycle telemetry. Defaults now
  fit the configured p99 absolute within-engine changes on training engines only, persist raw-unit
  values in model artifacts, and reject non-contiguous training cycles.
- A larger search sample exposed risk-safe diagnostic candidates with four controls. Added explicit
  optimizer recourse feasibility; the calibrated risk check can remain true while a non-sparse
  failure is excluded from joint success and successful-action sparsity.

### Corrected FD001 benchmark

- Seeded sample: 200 of 378 actionable high-risk internal held-out states, with zero frozen-feature,
  actuator-bound, or rate-limit violations.
- Model validity: 25/200 (12.5%); sparse recourse feasibility: 23/200 (11.5%); joint success:
  22/200 (11%); physical plausibility: 136/200 (68%); Tier 2 68%, Tier 3 100%, Tier 4 100%.
- Mean risk reduction: 0.52495; mean successful-action sparsity: 2.27273; mean/P95 optimization:
  701.71/1,148.80 ms; mean/P95 pipeline: 709.54/1,158.01 ms. Synopsis validity, plausibility,
  risk-reduction, and latency targets remain unmet.
- A separate 40-state larger-budget diagnostic reached 20/40 model-valid and 16/40 joint-success
  cases but averaged 4,655.82 ms optimization latency. This does not justify the longer search as
  the default.

### Verification

- Focused tests: 48 passed for schemas, evaluation metrics, recourse validation, training artifact
  persistence, and taxonomy rate fitting.
- `mingw32-make all-checks` on Python 3.13.9: Ruff passed, mypy passed for 49 source files, 143
  tests passed with 77% total coverage, and the documentation target passed. The 24 warnings came
  from deliberately short nonlinear coupling fixtures.


---

## Session: 2026-10-17 — True-model sparse-grid fallback and final benchmark

- Added configurable true-model grid fallback on sparse supports and candidate preference using the
  existing independent Tier 2–4 validators. The five-point grid obeys physical bounds, per-cycle rate
  limits, scaled trust intervals, immutable freezes, coupling propagation, and the configured action
  cap. Out-of-range current controls are treated as mandatory projected moves within the sparsity cap.
- Final real-data command: `uv run prescriptxai evaluate --queries 200 --config
  data/processed/phase4-grid-final.yaml`. It evaluated 200/378 actionable FD001 high-risk states.
  Observed model validity 131/200 (65.5%), physical plausibility 152/200 (76%), sparse feasibility
  129/200 (64.5%), joint success 127/200 (63.5%), mean risk drop 0.66151, and mean joint-success
  sparsity 2.59055. Optimization mean/P95 was 705.04/1,171.68 ms; pipeline mean/P95 was
  712.74/1,179.41 ms. Frozen/bound/rate violations were 0/0/0.
- Fallback execution: 178/200 states, average 3,103 true-model candidates and 39.77 ms per evaluated
  state. The 9-point diagnostic did not improve validity or joint-success count versus 5 points and
  increased mean optimization latency.
- A real-state audit uncovered candidates that omitted a mandatory move for a currently out-of-range
  actuator proxy; the grid now includes those features in every support and the corrected full run
  observed zero bound/rate violations.
- Synopsis validity (95%), plausibility (90%), and minimum latency targets remain unmet. Risk-drop
  (0.60) and sparsity (3) targets pass. These are reported as actual results, not tuned thresholds.

- Final `mingw32-make all-checks` after the follow-up: Ruff passed; mypy passed for 49 source files;
  146 tests passed with 77% total coverage; documentation target passed. The 24 convergence warnings
  came from deliberately short nonlinear coupling fixtures.

## Session: 2026-10-17 — Phase 4 sparsity and reachability diagnostic

- Reconstructed the same seeded 200-state held-out evaluation sample and examined its first 40 cases.
- Holding physical bounds, fitted per-step rates, scaled trust intervals, coupling propagation, the
  calibrated predictor, and Mahalanobis threshold fixed, an all-seven-proxy three-point grid found
  safe and Tier 2-plausible candidates for 36/40 states. The accepted `k_max=3` run had 29/40
  model-valid and joint-success cases in that same slice.
- A five-point all-seven-proxy refinement of the remaining four states found no safe candidate.
  Lowest sampled true risks were 0.9044, 0.8865, 0.4812, and 0.9622. These finite grids do not prove
  global infeasibility; they show that relaxing sparsity alone still does not meet the 95% target.
- This is diagnostic evidence only. No production policy, metric, target, or constraint was changed.
  Phase 4 remains in progress because the accepted `k_max=3` benchmark is below the synopsis
  validity/plausibility targets and the required physical limits are proxy-derived rather than
  verified actuator constraints.

## Session: 2026-10-20 — Phase 6 closure

- Population measurement `phase6-20261018T114827Z` completed on source `a72832c` with 600 saved
  results; configs and protocol were committed before execution. The immutable raw SHA-256 is
  `7b2b8d5719c9848bc5504f5277967a3d9d75526718fdbf208f5f6ad7fca1f0b6`.
- Real CLI/API RECOVERABLE and ESCALATE delivery checks passed for both D_max versions on source
  `1e41d77`. Both-mode CLI latency-bench completed; output and JSON file matched.
- `mingw32-make all-checks` exited 0 on final runtime `d177460`: Ruff clean, mypy clean for
  51 source files, `260 passed, 66 warnings in 98.16s`; branch coverage 81.0170359933393%, above
  Phase 5's 79.7752808988764%. Focused new-path verification separately passed 45 tests.
- Read-only independent audit reproduced true risks exactly and D_M within 1.78e-15 for every
  saved record; checked 16 cohorts/12 split partitions/36 artifact hashes/16 committed configs;
  zero leakage or acceptance errors. Audit counts are 558 RECOVERABLE, 2 PARTIAL, 40 ESCALATE
  across overlapping protocols/modes. Detailed evidence is ignored under artifacts/phase6/.
- Budget gaps are retained: FAST grouped-OOF optimization p95 6.84 s (v1) and 6.28 s (v2),
  above 1.80 s. Report every tier independently with engine-bootstrap CIs; do not compare this
  first-alert population as an improvement over older mixed-cycle evaluations. Execution outliers
  remain; controlled steady-state latency is not established.
- Schema 2.0.0 snapshots are frozen; report, migration notes, task traceability and PROGRESS.md
  record the evidence and assumptions. Closure tag: phase6-closed. Phases 7–11 await actual prompts
  and the missing Part B table.
# Phase 7 preparation evidence — 2026-10-20

- Preregistered source `0c0b6e1`; initial asset source `4ffb038`. Real preparation completed with
  28 model entries / 112 files. Independent audit verified every saved hash, complete OOF engine
  coverage (100 FD001, 260 FD002), disjoint fit/calibration/test partitions and artifact features.
- Source archive SHA-256:
  `c9c5dec12a945a82e8bb4446589d7fb3cc057b5e5d81fa1a12e25ee9912ad3b2`.
  Canonical asset-index hash:
  `32d2a5ba1fe00efb0ab214d2a520050115be6ae7cf7f80b19de2e4fb58a77269`.
- Legacy model migration preserved all 6 MLP and 10 LSTM tensors exactly, scaler arrays and
  calibrator parameters. Historical XGBoost fold seeds 1730–1734 remain unchanged; actual source,
  seed, training config and metrics are recorded per bundle.
- `artifacts/phase7-gate.log`: 276 passed, 66 warnings, 376.36 s. Coverage JSON totals:
  7196 statements, 915 missing, 2322 branches, 517 partial; 83.33683546963648% overall.
  Source metadata additions followed this run; a new stable-source all-checks gate is running.
- Phase 7 full recourse measurements have not started. No target claim follows from these tests.
  The completed-source protocol clarifications and implementation will be committed first.
- Stable-source verification: `mingw32-make all-checks` exited 0; Ruff passed, strict mypy
  passed for 55 source files; 276 passed, 70 warnings in 368.59 s; docs checks passed.
  `artifacts/phase7-stable-coverage.json`: 7246 statements, 921 missing, 2340 branches,
  521 partial; 83.3507197997079%, above the enforced Phase 6 floor. `uv lock --check` passed.
  The independent final source recheck found no remaining correctness blocker and no public
  schema change. Real recourse measurements remain pending at this commit.
