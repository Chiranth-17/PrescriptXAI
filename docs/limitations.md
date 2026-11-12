# Limitations and intended use

## Native Linux reproducibility remains unmet (13 November 2026 IST)

The Windows saved-result replay passes in its registered numerical environment.
Native Linux completes the fixed 15,525-case computation but does not reproduce
that reference: 1,547 cases have non-identity fields beyond the existing tolerance,
including 52 Tier 2 and 14 triage changes outside the borderline band. Do not
claim cross-platform numerical invariance, relabel these as noise, change the
known-difference policy, or substitute Linux outputs for historical results.
See the [complete diagnostic scope](linux_portability.md). The Linux demonstration
passes API scoring and dashboard HTTP readiness; complete Linux UI/software,
scientific verification and final release are still pending.


- **Controllable channels are telemetry proxies, not actuators.** C-MAPSS reports measured
  sensor outputs and operating settings. The configurable mapping in `configs/features.yaml`
  treats fuel-flow ratio (phi), bypass ratio (BPR), fan/core speed, and bleed-related channels as
  *controllable proxies* for synopsis-style experiments. These are not verified actuator commands
  and must not be interpreted as direct engine control inputs without domain review.
- **Coupling models describe observed co-variation, not causal physics.** Learned propagation and
  Tier 4 propagation captures statistical coupling on training engines in a healthy-to-moderate
  degradation regime. Passing a coupling check is not proof of a physically realizable intervention.
- **Rate limits are telemetry proxies.** The default per-step limits are the configured 99th
  percentile of absolute adjacent-cycle changes within training engines, fit on training engines
  only and saved with the model artifact. They describe observed sensor movement, not verified
  actuator slew rates; C-MAPSS does not record actuator commands.
- **Static run-to-failure data.** C-MAPSS has no counterfactual intervention trajectories. Do not
  claim that PrescriptXAI extends RUL or establishes real engine safety. The simulator is only an
  optional interface and is disabled by default.
- **Model validity is not physical plausibility.** Tier 1 checks the predictor's target risk. Tiers
  2–4 independently check operating-distribution distance, engineering constraints, and coupling.
- **LSTM recourse history input.** LSTM recommendations require the genuine observed history
  through the public input context. Only the latest timestep is mutable. Missing early histories
  are counted as unavailable rather than padded with duplicated telemetry. The frozen Phase 7
  setup did not find a model-safe LSTM intervention; this is not a global infeasibility proof.
- **Mahalanobis model assumptions.** Training-fitted shrinkage covariances remain a coarse
  description of an operating distribution. FD002 uses regime-specific validators with the
  regime fixed by original operating settings. A passing distance is not a physics proof.
- **Out-of-range starting telemetry.** A high-risk input can lie outside the train-derived actuator
  proxy bounds by more than its configured one-step rate limit. No adjustment can satisfy both
  constraints in that case; the engine returns an explicit infeasible-interval failure and the
  evaluation reports such inputs separately from actionable recourse cases.
- **Evaluation scope.** Metrics are for the configured model, seed, engine split, taxonomy, and
  sampled held-out rows. Synopsis case-study values are illustrative and never substituted for
  measured results.
- **Phase 4 FD001 outcome.** The reproducible closure report at `docs/phase4_final.md` records the
  200-state headline sample and all 378 actionable high-risk states from 15 held-out engines.
  Under protocol v1 (`k_max=3`, `K=1`, `D_max=5`), headline true model validity was 56.0%, Tier 2
  plausibility was 53.0%, and joint Tiers 2–4 plausibility was 43.5%. Protocol v2 changes only
  `D_max` to 8: Tier 2 rose to 99.0%, while true model validity remained 56.0% and joint
  plausibility was 52.5%. Optimization p95 was 1,904.5 ms (v1) and 2,022.5 ms (v2), above the
  1,800 ms target. The full report includes engine-cluster bootstrap intervals, all-alert and
  first-alert results, grouped OOF and official-test strata, risk-reduction histograms, triage,
  sensitivity, and saved JSON evidence. No synopsis pass is inferred from a subgroup result.
  These are E1 dataset/model measurements using sensor telemetry proxies; they do not establish
  actuator efficacy, physical safety, maintenance benefit, or RUL extension.
- **Latency scope.** Phase 7 measures request normalization, inference, optimization, validation
  and backend total in an isolated warm serial workload. Bulk telemetry download, network, cold
  startup and dashboard rendering are outside that benchmark; its results cannot establish
  deployment-wide latency on other machines, datasets or predictors.
- **Operator review.** The current package is research/decision-support software, not an autonomous
  control system. Recommendations require qualified engineering review and independent safety
  controls before any deployment.


## Phase 5 validation revision and evidence interpretation

Phase 4 tables are historical. Their old E1-only label uses a different vocabulary; the current
rules define E1 true-model validity, E2 statistical plausibility, E3 proxy engineering/coupling,
E4 held-out validated emulator and E5 validated physics simulator. The highest available static
check level is E3, conditional on sensor-proxy assumptions; it is not evidence of real actuator
control efficacy. Dynamic validation always reports `skipped: no simulator` in this project.

Phase 5 uses Ledoit–Wolf shrinkage and Cholesky solves rather than the old sample-covariance
precision artifact. This changes distances even at the same fixed D_max. Its residual thresholds
are calibrated on disjoint validation engines, while propagation regressors remain train-fitted.
Neither the fixed risk gates nor bounds, rate limits or D_max were changed. The before/after
comparison is paired replay of previously evaluated states, not fresh independent evidence.
Independent Tier 2 and Tiers 3/4 rates accompany every model-validity report; all-four joint
success is stricter and is never compared with the Tier 2 90% target.

Legacy precision-only artifacts are rejected with a refit instruction. Refit on the original
training engines; do not convert an old inverse into purported new shrinkage statistics. Regime
statistics and threshold provenance are persisted. Historical experiment profiles retain their original artifact paths. A fresh installation uses
`prescriptxai init` and `prescriptxai reproduce` to create its own compatible artifacts; it must
not assume ignored historical files are present.

## Phase 7 measured gaps

The complete frozen experiment and engine-bootstrap target/gap tables are in
`docs/phase7_changes.md`, with raw records and complete machine-readable summaries under the
ignored run directory. Both D_max versions and all internal, grouped OOF and official-test
populations remain visible. Statistical plausibility, proxy coupling and true-model validity
can disagree sharply. FD002's high model-validity rate does not imply an accepted intervention;
distribution and coupling failures remain in all-query denominators. Its input features,
calibration/test partitions and artifact hashes are independently audited for leakage.

The LSTM findings are conditional on the frozen observed prefix, latest-state-only intervention
and production search. Reference search covers failed paired XGBoost cases; finite-search
absence remains unresolved and does not certify continuous or real-engine infeasibility.
Optimization exceeds the design latency budget in both measured modes. No measured miss is
repaired by changing historical thresholds, limits, populations or timings. Evidence remains
at most E3 under proxy assumptions; dynamic simulator/emulator evidence is unavailable.

## Phase 9 software assurance scope

The fixture profiling/memory study in `phase9_changes.md` uses two synthetic engines and a small
MLP. Its warm-call improvement does not change historical C-MAPSS latency verdicts. Two engine
clusters limit bootstrap resolution. The10000-call memory population covers two identical safe
measurement vectors, so optimizer memory stress and unbounded service uptime are not established.
Explicit5MiB Python/50MiB RSS final-growth budgets are software regression assumptions.

Retained legacy pickle/joblib objects are restricted to resolved, operator-controlled roots with
byte-identity checks. This does not make downloaded objects safe or provide a pickle sandbox;
no API/upload can grant trust. Dependency audits cover known public advisories, while the local
project is checked by source/regression tests. Credential scans use disclosed high-confidence
patterns and do not claim to recognize every possible credential format. See `artifact_security.md`.
Hosted CI/GPU execution is separate from the local CPU gate; unavailable GPU results are not passes.

## Surrogate fidelity and incomplete search

The global distilled gradient surrogate approximates the original calibrated predictor. Its
errors can direct search away from feasible recourse or toward candidates that fail true-model
rescoring. Final acceptance always uses the original calibrated model, preventing surrogate-only
acceptance; this does not certify that search found every feasible candidate. See surrogate
error and false-safe metrics in the [Phase 7 report](phase7_changes.md). Finite reference
searches remain unresolved unless the required production-superset test is met.

## Phase 12 reality-check limitations

The complete [open-item ledger](phase12_open_items.md) retains every earlier exception plus
the new verification obligations. The initial 540-test software gate passed with unchanged
coverage; the complete new regression and clean-clone check are still pending. Historical
closure tags1-3 are absent and will not be manufactured. Later closure tags are verified.

The headline fixed D_max=5/8, fitted from the existing training distribution, is not the
strict empirical95th-percentile distance threshold of real low-risk states. Separate old
quantile and healthy-reference ablations do not establish their combination. A new diagnostic
must be preregistered and reported separately, without redefining either historical protocol.

Historical constraint-first fallback rates are available in the Phase4 diagnosis. The Phase7
observation schema did not persist its internal fallback flag, so a Phase7 fallback rate cannot
be reconstructed from those different measurements. This is a logging/reporting gap, not zero
fallback. The protocol-v2 K curve does exist for the paired12-query/10-engine diagnostic; its
small, reused-engine scope is retained rather than presented as a full all-alert K experiment.

Whole-engine empirical bootstrap intervals can equal[1,1] when every observed engine succeeds.
They describe resampling this finite engine population; they do not guarantee population-wide
certainty or future-unit reliability. No state-binomial interval is substituted for an engine
interval. Undefined conditional denominators remain undefined, with their counts reported.

The new machine-pack, sign-off, readiness and security requirements are not yet implemented
by the frozen research baseline. In particular, the existing API can run without an API key
when its environment key is absent; it does not satisfy authentication-on-by-default. Phase12
starts no service or industrial advisory deployment. These obligations are assigned to
Phases13-18 and remain explicit until their tests pass. No absent engineer/classmate identity,
public repository, hosted CI evidence or real plant benefit is invented for a gate.

## Plausible telemetry spoofing

On the registered FD001 XGBoost v1 sample, two of 16 bounded spoofing attempts
published proxy prescriptions that failed the model-risk check on the
original recorded observation. The four presets represent three simulated
units. The two bypasses crossed the fixed 20% threshold on recheck. Keep
authenticated upstream telemetry and independent engineering review as
deployment requirements. See the [advisory safety case](safety_case.md).
