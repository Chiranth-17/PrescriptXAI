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

## Phase 7 additive preregistration — 2026-10-20

Study version `phase7-20261020`, controlled by committed `configs/experiments/phase7-study.yaml`
and explicit `phase7-<subset>-<model>-v{1,2}.yaml` inputs. This expansion is committed before
new fitting or measurement. Earlier protocol sections/results remain historical and unchanged.
D_max versions remain v1=5 and v2=8; neither is replaced. All existing public FD001 engines have
previous exposure, so this is a reproducible expanded evaluation, not fresh-engine generalization.

- Required datasets/models: FD001 XGBoost, MLP and LSTM; FD002 XGBoost (the already designated
  primary predictor family, without selection on recourse). FD003/FD004 are optional and not
  scheduled in this required run. They remain explicitly not evaluated.
- Preserve existing FD001 predictor/scaler/calibrator artifacts and partitions. Train missing
  FD002 and grouped-fold artifacts using model seed 1729. Base splits use fixed split seed 1729,
  lifetime-stratified by engine. Outer five folds cover every training-file engine exactly once;
  each outer fold fits on the other engines and uses a fixed validation-engine subset for stopping,
  calibration and residual thresholds. No outer test engine enters any fit or calibration.
- Five seeds 1729–1733 vary only the solver randomness on persisted fixed predictors/partitions.
  They do not represent five independent training datasets or model initializations. Report mean
  and sample standard deviation across these five solver seeds, including legitimate zero variance.
  Engine bootstrap keeps each engine's repeated-seed rows together; never count seeds as engines.
- FAST headline: every true alert in internal held-out, grouped OOF and official truncated-test
  populations, including empty actuator intersections and all failures. Development is validation
  engines only (at most 60 seeded all-alert queries). THOROUGH is the true first alert per engine
  in those populations. Also report first-alert summaries derived from full FAST records and
  clearly distinguish them from all-alert headlines. No cap applies to FAST test populations.
- Official cycle-level RUL is terminal RUL plus terminal observed cycle minus current cycle;
  official IDs use +10000 within each dataset. Life fraction uses cycle/(cycle+observed RUL).
  It is retrospective stratification, never a model input or RUL-extension estimate.
- LSTM assessment/recourse uses exactly window-1 actual previous rows from that same engine;
  only the latest row is changed. Earlier cycles lacking an observed prefix are counted as
  insufficient-history/unscorable, not padded or silently discarded. Training retains its earlier
  documented left-padding convention; no training padding is described as observed history.
- Frozen search settings remain Phase 6's 25 iterations, one restart, three alpha levels,
  one L1 level, two support searches, five-point teacher grid and two feedback refinements;
  k_max=3, K=1, tau_danger=.80, tau_safe=.20, bounds/rates unchanged. CPU runtime uses one torch/
  BLAS thread per worker and at most four quality workers; log effective settings and hardware.
  FD002 predictor retains global feature scaling; its Tier 2 statistics are regime-conditioned.
- Primary metrics use all queries, with all-query/returned/success sparsity separately exposed.
  Returned means a nonzero sparse-feasible diagnostic/CF, regardless of tier outcome; failure is
  not a filter. Tier 2 returned-ratio CIs resample engines from the complete cohort and aggregate
  numerator and denominator together; zero-denominator replicates are disclosed, never invented.
  Mean risk reduction and raw/scaled proximity include failures. Each tier and joint/evidence
  are separate. Simulator/emulator trajectory health is **not evaluated**.
- Diagnostic/baseline/ablation/sensitivity queries: the seeded, ordered first at most 12 alerts
  from internal holdout for each primary XGBoost subset, fixed before outcomes; solver seed 1729,
  both D_max versions. Every component-removal variant actually reruns search and is validated
  afterward against the unmodified reporting taxonomy. An omitted search check never becomes a
  passing validation result. No claim about the Model Realism Fallacy is made without observed
  immutable/bound/Tier 2 violations. DiCE runs if its optional pinned dependency is compatible;
  otherwise its install/error evidence is reported, with no substitute result.
- Constraint ladder is genuine re-optimization: L0 all model inputs free, L1 +immutable freezing,
  L2 +physical bounds, L3 +rate limits, L4 +dependent propagation, L5 +k sparsity, L6 +Tier 2,
  L7 +Tier 4. Earlier dependent-free stages and unsafe baselines are research diagnostics only.
- One-component ablations: no immutable freezing, no physical bounds (retain rates), no Tier 2,
  no dependent propagation (dependents stay fixed), no sparsity, no in-loop validation;
  D_max empirical/chi-square methods and healthy-to-moderate reference are labeled changes.
- Sensitivities are one factor at a time using YAML grids: tau_safe .1/.2/.3, k 1/2/3/5,
  H 15/30/50, K 1/2/3/5/10, alpha 1/10/100, beta and gamma 0/1/100, quantiles .95/.99/.999.
  H requires newly labeled/retrained/recalibrated XGBoost on the same base engine partitions.
  Beta/gamma do not soften hard freezing/boxes; zero effect is an expected valid result.
  Quantile sensitivity uses empirical and chi-square baselines (fixed D_max ignores quantile).
  Always retain f(x')<=.20 as headline validity, with variant-target-relative success separate.
- Oracle: at most 12 failed production states per primary population/protocol. Replay exact
  production seed/mode/config and preserve its exact candidate. Search the union of its traced
  terminal candidates, exact returned candidate and the configured seven-point sparse grid.
  Verify reproduction and record scope before classifying a miss. A found safe/plausible point is
  a search failure; finite absence is unresolved, not continuous global infeasibility. A truly
  infeasible label requires a verified superset plus an exact empty physical/rate interval proof.
- Leverage probes change each control to its allowed interval endpoints with dependent propagation;
  report true risk slopes, distances, residual margins and feasible interval widths, not causal effects.
  Risk/RUL/life-fraction strata and the full risk-reduction histogram use committed YAML bin edges.
- Latency is a separate serial warm-cache experiment: 10 warmups excluded and 1000 actual high-risk
  public calls per FAST/THOROUGH mode. Cycle through validation-engine alerts in fixed engine/cycle
  order using the primary FD001 model/v1 config. No competing tests/training/quality jobs run during
  timing. Include every failure/outlier. Stage p50/p95/p99 and engine-bootstrap p95 CIs use measured
  calls; missing stages stay unmeasured. Pass means p95<=upper budget. This is the named development
  latency workload, not a claim of latency for every model/dataset or UI/startup performance.
- Manifests record the committed study/base config hashes, runtime config hash, source, protocol
  snapshot, artifact/cohort hashes, seeds, versions and hardware. Atomic per-query checkpoints
  reject incompatible resume inputs. No completed query is silently rerun or removed. Markdown/
  HTML reports are generated from saved files with targets, gaps, diagnosis, engine CIs and seed
  variation. Record unmet tasks in traceability; do not hide a target miss or redefine a metric.
# Phase 7 implementation clarification — 2026-10-20, before recourse measurements

The L0–L4 ladder and no-sparsity ablation retain dense gradient search. Their finite fallback
grid keeps the frozen configuration's support cap (k_max) as a computational search budget;
it does not constrain the dense candidate's allowed support. The cap and full effective policy
are logged. This avoids exponential materialization when all model inputs are freed. These
diagnostics are finite searches and never continuous infeasibility certificates.

Development FAST selection keeps its preregistered seeded cap. Development THOROUGH uses
true first alerts selected before that cap, so each eligible engine retains its first alert.
The reported test populations remain uncapped. Successful-action sparsity and directly
optimized-input sparsity are reported alongside original controllable-proxy sparsity. In
tau_safe sensitivity, triage and evidence are labeled target-relative; the fixed .20 validity
and joint metrics remain separately reported. "Returned counterfactual" means a nonzero,
action-feasible candidate; saved closest diagnostics are available for every query.

Preparation source is retained per asset. A post-preparation completion seal verifies the raw
archive and source predictor identities against the audited historical assets on every resume;
this is explicitly not a retroactive pre-fitting signature. Existing v1 fold coupling artifacts
are reused for both D_max versions; their validation calibration reports match the historical
v2 calibration, although the serialized v2 bytes differ. Predictor weights and cutoffs are unchanged.

Alert selection uses authoritative singleton snapshot or genuine-window scoring, matching the
public gate numerically; predictor scores can be reused across D_max versions. Historical FD001
XGBoost outer-fold seeds remain as saved (1730–1734); newly fitted models use 1729. The actual
training seed/source/config hash is reported per artifact. Solver seed repetitions do not estimate
training-seed uncertainty. H sensitivity retains its paired source population and reports the
new model's risk-gate eligibility and NO_INTERVENTION share; it never substitutes this population
for the fixed headline. The post-preparation seal anchors independently audited source predictor
identities; its automatic historical checksum comparison applies to the raw archive.

## Phase 8 UI rendering protocol — registered before timing callbacks, 2026-10-24

Configuration: `configs/experiments/phase8-ui-render.yaml`; measurement code source
`52affd06d39b03f76a0dd70417c3a75bd76f55c4`. This separate UI study preserves all Phase 7
measurements and scientific settings. It is not a new recourse quality/generalization run.

The declared population is four serial, actual-browser sidebar Recompute callbacks on each
of eight official FD001 test engines at their final observed cycle:1/31,2/49,3/126,4/106,
5/98,6/105,20/184,76/205. Raw NASA test IDs are used; historical Phase7 official IDs have a
10000 namespace offset. All32 callback records, failures and outliers are retained; no warmups
are discarded. Preparatory navigation/assessment frames are outside this declared callback population.

Use the existing direct-backend dashboard and frozen FD001 XGBoost v1 profile in FAST mode.
Predictors, calibration, validators, thresholds, bounds, rates, K and k_max are unchanged.
The registered statistic is p95 complete Operator-page Python UI construction, including the
sidebar/header/result panels. Explicitly timed loading/scoring/solve/attribution computation
is subtracted by the instrumented application. Browser paint/network/startup and other pages
are outside this statistic and must not be described as measured. Desktop load is not isolated.

Compare p95 with the profile's UI upper budget (faster is a pass). The interval is a percentile
bootstrap over whole engines, retaining all four repeats within each draw:2000 replicates,
seed1729,95% confidence; report32 observations and8 engines. Missing callbacks are a software
failure, not passing zero latency. Do not replace a failure or discard a slow callback.

## Phase 9 fixture performance and memory protocol — before baseline

Configuration `configs/experiments/phase9-performance.yaml` and helper
`scripts/diagnostics/phase9_performance.py` must be committed before preparation or measurement.
This is a development software microbenchmark, not a new C-MAPSS efficacy estimate or a
replacement for Phase7 timings. The actual synthetic fixture fits predictor/scaler/covariance
on engines1–4 and calibrates on5–6; observed engines7–8 each have three saved cycles.
Predictor fit and bootstrap use seed17; covariance and solver configuration retain seed1729.
Protocol fixture-only-v1 uses configured k_max3,K1,D_max5,tau_danger.80,tau_safe.20, unchanged.

Each before/after segment runs in a fresh process with one native CPU thread, six warmup calls,
twelve separate cProfile calls, then twenty repeats of all six observations in saved order:
120 complete public recommend calls per segment. Loaded-artifact inference, gating, optimization,
validation and result construction are timed; fitting/loading, warmups, profiling and recording
are outside timed samples. Retain every duration, decision, error and outlier. Attempt/result
records flush as execution proceeds; incomplete segments stay incomplete and cannot be overwritten.
The summary shows p50/p95/p99 and a95% whole-engine bootstrap p95 interval,2000 draws, seed17,
two synthetic engines with all cycles/repeats retained. Two clusters give limited resolution.
Compare every after decision and the independent stored goldens using the documented tolerances.
Only implementation may change between segments; all settings, inputs, goldens, helpers and
dependency lock bytes are checked against preparation and baseline, and again at segment end.

The memory population is explicitly engines7/cycle3 and8/cycle1, both already-safe synthetic
observations. After100 warmups, alternate them for exactly10000 complete public recommend calls.
This checks the no-intervention path, not optimizer memory stress. Record every attempted/result
call, initial manifest and post-GC baseline/1000-call checkpoints; measure tracemalloc live/peak
Python bytes and psutil process RSS. Predeclared final-growth software regression budgets are
5MiB Python live allocations and50MiB RSS. These are regression limits, not a deployment memory
guarantee; platform allocators and native allocations are disclosed. Never infer physics, real
actuator response or RUL extension from this fixture. No competing tests/training/quality workload
runs during timing or memory stages. The full repository must be clean before each stage.
# Phase 10 reproducibility workflow preregistration

The install/demo workflow uses `configs/experiments/phase10-reproduce-v1.yaml`,
packaged byte-for-byte as the initialization template. It is a separately labeled
**reused-engine reproducibility demonstration**, not fresh generalization or a
replacement for Phase 7. FD001, seed1729, engine split70/15/15, XGBoost predictive
selection, validation-engine sigmoid calibration, training-only scaling/covariance/
coupling fitting and validation-only coupling calibration remain unchanged.

Evaluation uses the existing runner's seeded uniform sample of at most20 high-risk
states with feasible actuator intervals from the internal held-out engines. Report
the realized query and engine counts, all failures, and whole-engine bootstrap intervals
(2000 replicates,seed1729). Disclose the complete high-risk count and number excluded by
the interval pre-screen; sampled query rates are not rates over all alert states.
This small demo population does not alter any prior declared
population. Protocolv1, D_max fixed5, K1, k_max3, tau_danger.8/tau_safe.2; all other
scientific settings match the default configuration. No solver tuning or outcome-based
model selection occurs. The reproduction manifest records effective settings, hashes,
engine partitions, package/build identity and stage durations. Timings are workflow
runtime observations, not a new serial latency-budget experiment.

Prepare, train/calibrate, fit learned coupling and covariance, evaluate and write the
report in order. Existing output directories are refused, including incomplete runs;
retain failures and their stage manifest. Individual demo engine/cycle choices can be
selected from completed outputs and are explicitly illustrative examples, not rate
estimates. Neither this protocol nor the outputs imply physical safety or RUL extension.

Implementation clarification before the first real run: the registered evaluation mode
is THOROUGH (`recourse.search_mode`); UI/API defaults are FAST and are separate demo calls.
`measured_metrics.json` is the authoritative Phase10 metric table. Its returned denominator
requires a nonzero retained-model-feature change and a bounded, rate-compliant, frozen-feature-
preserving action with proxy sparsity <=k_max, independent of the model-safety verdict.
Whole-engine ratios use the existing clustered bootstrap with2000 draws/seed1729 and95% CIs;
zero-returned replicates/counts remain explicit. Selected query rows and each completed record
are persisted before subsequent work. A failed workflow is incomplete, never a new pass.

## Phase 11 independent replay audit — registered before execution, 2026-10-28

The user requested a final audit after Phase 10. Independent reviewers inspect code they did
not implement; the original implementer fixes verified gaps and reviewers recheck those fixes.
This audit does not change scientific settings or add product features.

Committed audit settings: `configs/experiments/phase11-audit.yaml`; complete replay study:
`configs/experiments/phase11-seed1730-replay.yaml`. The latter differs from the Phase7 study
only in run label, a new output directory and solver_seeds=[1730]. It retains all 34,298 quality
queries for this seed:32,116 main FAST alerts,1,526 test THOROUGH first alerts,480 development
FAST and176 development THOROUGH. All64 quality groups remain, with no added cap. All four
dataset/model profiles, v1/v2, internal/OOF/official populations and original failure states
remain. The separate required `reproduce` command uses the existing Phase10 20-query profile;
it does not substitute for this complete replay.

Execute the existing quality runner in an isolated clean checkout of historical measured source
`63c2ed445fba16c73a2771e184f635abf76b4405`, with its locked environment and byte-verified copies
of original raw data, fitted assets and all diagnostic validators. Do not refit or modify the
original files. Pass the absolute path to the newly committed study in the main checkout;
do not add an untracked scientific config to the frozen checkout. Record both the historical
execution commit and the new audit-preregistration commit/config hash. They are different
identities: this audit registration necessarily postdates the original experiment.

Before launch verify the imported module path, package/core dependency versions, clean source,
all copied hashes and absence of a duplicate run. Use a new run ID; per-query checkpoints are
preserved and an interrupted run resumes only after compatibility and process checks. No
completed query, failure or duration is replaced. Quality replay timings are not a new isolated
latency study; no latency budget is certified from them.

First compare new1730 against historical1730 for the exact expected query population and all
scientific records. Require discrete fields, identities, feature roles and threshold verdicts
to match exactly. Numerical values use absolute tolerance1e-6 plus relative tolerance1e-5.
Then separately compare new1730 with historical1729: rates must match exactly; scientific
means use the same numeric tolerance, and any per-query difference is reported. These are
NEW audit tolerances, registered before this replay; Phase7 originally reported five-seed
variation but did not preregister cross-seed acceptance tolerances. The numerical magnitude
is borrowed from documented software-golden tolerances, not a claim of statistical equivalence.
Never let numeric tolerance turn a failed tier into a pass. Keep timings and execution metadata
separate from scientific comparisons. Recompute aggregate metrics and95% whole-engine CIs
(2000replicates,seed1729), retaining all failures and the actual engine count per population.

The reused public engines cannot demonstrate fresh-engine generalization or strict once-ever
test use. Record that protocol limitation as Partial, without changing the populations or
claiming historical preregistration for a newly chosen audit threshold. Target misses remain
valid findings; neither model selection nor solver/threshold tuning is permitted.

## Post-audit development profiling, remediation-development-profile-v1

Preregistration: configs/experiments/remediation-development-profile-v1.yaml and
scripts/diagnostics/remediation_profile.py are committed before the first run. This is a
new, separately labeled development profile; original Phase7 and Phase11 records are immutable.

Population: all60 saved FD001/XGB/v1/development_all_alerts/fast/full queries, solverseed1729,
14validation engines, ordered byengine/cycle. These are the original QUALITY-development
sample, not the original full serial-latency population. Overlap with saved serial identities
is recorded without falsely asserting equal populations. BothFAST andTHOROUGH use exactly
those same60 observations. Each mode receives
two warmups and one measured call per observation (120total); one separate cProfile call
permode occurs after timing. Loading, profiling and bootstrap computation are excluded.
No test/training/quality/render job may overlap the serial stage; one native CPU thread is used.

K=1, k_max=3, D_max v1=5, tau_safe=.20 and tau_danger=.80, every model/calibrator/covariance/
coupling artifact, all masks/bounds/rates and all solver settings come from the unchanged
saved effective configuration. No fitting or search-setting tuning is performed in this profile.
The prior scientific metric definitions and all-query failure denominators remain unchanged.
Each timed public outcome is transactionally checkpointed, including failures and outliers.
Unexpected exceptions retain their latency and error type; they cannot produce an accepted run.

p95 stage intervals bootstrap whole engines, 2000draws/seed1729/95%; engine counts and actual
observations accompany every interval. The benchmark records source/config/input hashes and
full outcomes. Before/after comparisons require exact query/discrete/tier verdict identities and
numeric atol1e-6/rtol1e-5; operational timings/source metadata are separately labeled, not erased.
Development p95s do not close a design target. A final implementation/config must be committed
before the full serial1000calls/mode plus10warmups/mode gate on the unchanged full workload.
No new engine generalization or physical/causal/SDG/RUL evidence is inferred from timing.
