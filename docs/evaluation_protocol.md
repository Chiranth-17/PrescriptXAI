# Evaluation protocol — Phase 5 validation revision

Status: frozen by committing this document and `configs/experiments/phase5-validation-v{1,2}.yaml`
before any Phase 5 real-data measurement. The run records that commit and both config hashes.
This revision consolidates validation; it does not select or retrain a predictor using recourse.

## Immutable experiment choices

- Predictor: the existing FD001 calibrated XGBoost bundle and its unchanged scaler and surrogate.
  The original engine split is 69 fitting / 16 validation / 15 internal test engines. Verify IDs
  against saved metadata rather than relying on these counts. Fold-specific artifacts retain their
  own fitting/validation/test IDs. Official test unit IDs use the existing +10000 namespace.
- Risk gates: `tau_danger=0.80`, `tau_safe=0.20`. Headline support `k_max=3`; assumed horizon `K=1`.
  Physical bounds, fitted p99 one-step proxy rate limits, masks, and direction restrictions are
  copied unchanged from the predictor/coupling artifacts. Sensor channels remain proxies.
- Tier 2 validator revision: Ledoit–Wolf shrinkage plus the existing diagonal regularization
  `1e-6`, Cholesky factorization and triangular solves. Reference = **all cycles of fitting engines**.
  For FD002/FD004 only, fit setting-standardization/KMeans on fitting engines with seed 1729 and
  k=6; select each candidate's statistics using its original frozen operating settings.
- D_max v1 remains fixed **5.0**; v2 remains fixed **8.0**, reported beside v1. Configured quantile
  is 0.99, unused for the fixed headline methods. Chi-square (`sqrt(chi2.ppf(q,d))`) and empirical
  training-distance quantiles are implemented and unit-tested, not substituted into this headline.
  Healthy-to-moderate reference is supported but is evaluated against all-cycle reference only in
  the future Phase 7 ablation. No thresholds are derived from Phase 5 evaluation outcomes.
- Tier 4: retain the training-fitted propagation regressors and fixed YAML sigma multiplier.
  Calibrate residual standard deviations on **validation engines only**, restricted to
  RUL > max(H, configured coupling min_rul_cycles). Preserve predictor weights, bounds and rates.
  Persist calibration IDs, rows, residual mean/std, R² and threshold-exceedance rates. Propagation
  remains residual-preserving; an initial absolute residual violation cannot be repaired by
  erasing that residual. Such a candidate remains a structured failure.
- In-loop feedback: 2 maximum refinements, initial normalized feasibility penalty 10, growth 10;
  reuse frozen solver settings (25 iterations, 1 restart, 3 alpha steps, 1 L1 step, 2 local supports,
  five-point true-model grid). No tuning after test replay. All effective settings are logged.
- Modes: collect-all for reporting; fail-fast marks unrun tiers **skipped**, never passing. The
  disabled/unavailable simulator is skipped and supplies no E4/E5 evidence.

## Populations and comparisons

1. Development: validation-engine alerts, deterministic seeded sample of at most 60 all-alert
   states, plus the true first alert of each validation engine. Development is not unbiased test
   evidence; these engines also calibrate probabilities and coupling thresholds. No solver outcome
   is used to select a predictor or change settings.
2. Paired replay: exact saved Phase 4 candidates on internal test engines, grouped out-of-fold
   engines, and official test engines, using their original input states. Preserve every query,
   including missing candidates. Before = saved per-tier Phase 4 results; after = Phase 5 validator
   checks on the identical candidate, with a stricter successful-return flag. This is previously
   evaluated data and **not fresh generalization evidence**.
3. All-alert and first-alert-per-engine populations are separate. Reconstruct first alerts from
   raw telemetry and true calibrated probabilities, not the first sampled alert. Report candidate
   coverage and unavailable before results explicitly. The grouped OOF saved sample contains 200
   queries and 189 records; retain the 11 missing candidates in denominators.
4. Integrated validation-in-loop: run the frozen Phase 5 solver on the saved 200-state internal
   headline sample and development sample, with maximum feedback iterations enforced. Any extra
   first-alert queries needed for population coverage are named separately. Run v1/v2 side by side.
5. The existing Phase 4 K={1,2,3,5,10} saved sensitivity is revalidated when its candidates exist.
   Show its validity curve beside K=1, labeled saved-state sensitivity; K>1 is an assumption,
   not measured actuator dynamics. Do not claim new optimization measurements from replay timings.

## Metrics, denominators, and evidence

- Validity = true calibrated risk <= tau_safe (Tier 1); plausibility = Tier 2 only. Report Tier 3,
  Tier 4, their physical conjunction, and all-four joint separately. The 90% target applies only
  to Tier 2, never joint. Missing candidates count as no pass over all queries and remain visible.
- Funnel: alerts → candidate returned → cumulative Tier 1 → Tier 2 → Tier 3 → Tier 4 → joint.
  Independent tier pass rates accompany the cumulative counts. Report Tier 2 over all queries and
  over returned counterfactuals with explicit returned definitions, including diagnostic candidates.
- Every interval is 95% percentile bootstrap over whole engines, 2000 replicates, seed 1729 plus
  deterministic stage offsets. Show engine count and denominator beside every interval. Empty
  denominators produce unavailable intervals, never an invented rate.
- Each table carries run ID, committed config path/hash, source git hash, protocol v1/v2, k_max,
  K, D_max version/value, and population. Preserve dataset, predictor, checkpoint and validator hashes.
- Evidence uses current AGENTS taxonomy: E1 true-model validity, E2 statistical plausibility,
  E3 proxy engineering/coupling constraints, E4 held-out validated emulator, E5 validated physics
  simulator. A failed or skipped tier grants no level; later tiers do not erase earlier failures.
  No RUL-extension or validated actuator/control efficacy is claimed.
- Latency budgets pass at p95 <= the upper figure; faster is a pass. Record actual wall times;
  saved Phase 4 optimization timing is historical and not a Phase 5 optimization measurement.

## Guardrails and scope

Phase 4 measurements and artifacts remain unchanged. Replacing its sample-covariance validator
with Ledoit–Wolf changes distances and must be shown as a validator revision even though D_max is
unchanged. Phase 4 summary labels that conflate physical conjunction with all-four joint are
corrected in the new paired report; the historical report is retained with an explicit erratum.
Unavailable saved candidates or unavailable dynamic evidence are labeled Partial/Not met in
`docs/traceability.md`, never replaced with synthetic benchmark data. Synthetic fixtures are tests only.
