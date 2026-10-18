# Limitations and intended use

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
- **LSTM recourse history input.** The LSTM scores fixed within-engine histories and its gradient
  interface treats only the latest timestep as mutable. The current snapshot recommendation request
  does not carry that history, so LSTM bundles are for sequence scoring until that API is extended.
- **Mahalanobis model assumptions.** A single empirical covariance is a coarse description of
  potentially multimodal operation. A passing distance is not a physics proof.
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
- **Latency scope.** The evaluation measures inference, optimization, and validation in the Python
  process. Raw telemetry ingestion and interactive dashboard render latency remain unmeasured until
  an instrumented live-input deployment is available.
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
statistics and threshold provenance are persisted. The default validator/coupling paths now point
to Phase 5 artifacts; run the Phase 5 preparation/evaluation command before using the dashboard.
