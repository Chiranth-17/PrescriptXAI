# Limitations and intended use

- **Controllable channels are telemetry proxies, not actuators.** C-MAPSS reports measured
  sensor outputs and operating settings. The configurable mapping in `configs/features.yaml`
  treats fuel-flow ratio (phi), bypass ratio (BPR), fan/core speed, and bleed-related channels as
  *controllable proxies* for synopsis-style experiments. These are not verified actuator commands
  and must not be interpreted as direct engine control inputs without domain review.
- **Coupling models describe observed co-variation, not causal physics.** Learned propagation and
  Tier 4 residual bounds capture statistical coupling on training engines in a healthy-to-moderate
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
- **Phase 4 FD001 outcome.** The final seeded sample included 200 of 378 actionable high-risk
  states in the engine-held-out split. True model validity was 65.5%, Tiers 2–4 plausibility was
  76%, and 127/200 (63.5%) were joint successful sparse recourses. Mean risk reduction was
  0.66151, and mean sparsity among the 127 joint successes was 2.59055. Mean/P95 optimization
  latency was 705.04/1,171.68 ms; mean/P95 pipeline latency was 712.74/1,179.41 ms. There were
  zero frozen-feature, actuator-bound, or rate-limit violations. Validity, plausibility, sparse
  feasibility, and joint success remain separately reported. The run used explicitly recorded
  reduced search limits (25 iterations, one restart, three alpha steps, one L1 step, two local
  supports) plus a five-point bounded true-model grid fallback; all per-state measurements and
  settings are saved in the ignored generated report. The synopsis validity, plausibility, and
  latency targets remain unmet, and the run does not establish a maintenance effect.
- **Latency scope.** The evaluation measures inference, optimization, and validation in the Python
  process. Raw telemetry ingestion and interactive dashboard render latency remain unmeasured until
  an instrumented live-input deployment is available.
- **Operator review.** The current package is research/decision-support software, not an autonomous
  control system. Recommendations require qualified engineering review and independent safety
  controls before any deployment.
