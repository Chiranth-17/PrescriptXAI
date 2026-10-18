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


## Phase 6 preregistration — public pipeline and modes

Committed before Phase 6 real measurements. This adds no new D_max version: v1=5 and v2=8
remain unchanged, as do risk gates, bounds, proxy rates, K=1, k=3, predictor and calibrator.
The Phase 5 frozen solver settings are retained. FAST uses the existing support-ordered certified
true-model grid; THOROUGH evaluates the full existing grid. Semantics-preserving batched checks
may remove repeated computation; no setting is tuned on reported outcomes. Development is the
validation-engine population; no predictor is selected based on recourse.

- Public triage: RECOVERABLE requires Tiers 1–4 and sparse action feasibility. PARTIAL requires
  Tiers 2–4 and sparse feasibility, true risk reduction >= configured delta_min=0.30, and final
  risk > tau_safe. Otherwise ESCALATE. Below tau_danger returns NO_INTERVENTION, triage=null,
  unchanged state; it does not imply risk <= tau_safe. Exactly tau_danger enters recourse.
- Bench populations: true first alert per engine for development validation engines, internal
  held-out engines, each of the five frozen grouped OOF models across all 100 engines, and
  official test engines (namespaced IDs and derived cycle-level RUL). Both modes/protocols use
  identical queries. Include failures and infeasible queries. These are previously evaluated
  engines; no fresh generalization claim. A new high-risk CLI/API demo also selects the first
  chronological failing/partial result from the declared population if present.
- Warm cache after artifact loading; one validation-engine warmup per mode/protocol, excluded
  and disclosed. One timed repetition of each query. All settings/selection are YAML governed;
  no post-result tuning. Timing benchmarks run serially with no concurrent test workloads.
- Stage boundaries: ingestion normalizes/validates raw input; inference measures the true gate
  probability; optimization includes all search/in-loop checks and true rescoring; validation
  measures final checks. Backend total is measured directly around the public request including
  lock wait and serialization setup. Startup and UI rendering remain separate/unmeasured.
- p50/p95/p99 are measured per stage and total. p95 <= the upper budget is a pass; faster is a
  pass. UI is null, never inferred from backend latency. Whole-engine bootstrap intervals and
  engine counts accompany p95. Every mode/protocol/population table includes run/config/git,
  k_max, K and D_max version. Validity/Tier2/Tier3/Tier4/joint/evidence accompany latency.
- Snapshot vectors use the saved model feature order; dict/Series inputs use named columns.
  Context may provide actual omitted telemetry/context plus units and an LSTM history. No missing
  measured sensors or past timesteps are fabricated. Missing history is an explicit input error
  for LSTM. Earlier history stays fixed; recourse changes only the latest timestep.
- Optional multiprocessing is a throughput mode and is not used for serial latency claims.
  Artifact caching is bounded and keyed by config/taxonomy/artifact fingerprints; per-engine
  access is locked. Modes use request-local copied configuration.
- Schema 2.0.0 is frozen at closure with JSON-schema snapshots and a migration/changelog entry.
  Future changes require a version bump, changelog and agreement from library/CLI/API/dashboard
  owners under rule19. Existing Phase 5 K sensitivity remains linked as historical assumed-K
  sensitivity; it is not relabeled as a newly measured Phase 6 mode curve.

Phase 6 denominator clarification (before measurement): a returned counterfactual/diagnostic
candidate is a nonzero sparse feasible returned state, regardless of Tier 1-4 outcomes; its
Tier 2 numerator counts only those passing Tier 2. Failed returned candidates remain in this
denominator. All-query Tier 2 also includes unchanged/infeasible diagnostics. Neither ratio is
joint success. Every table includes per-base/per-fold config and artifact hashes. First-alert
results are not compared as an improvement over the different Phase 5 mixed-cycle sample.

Warmup clarification: one validation-engine warmup per population/model/mode/protocol report.
The three base populations and five folds therefore exclude 32 warmup calls overall.
