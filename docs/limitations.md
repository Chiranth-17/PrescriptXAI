# Limitations and intended use

- **Controllable channels are telemetry proxies, not actuators.** C-MAPSS reports measured
  sensor outputs and operating settings. The configurable mapping in `configs/features.yaml`
  treats fuel-flow ratio (phi), bypass ratio (BPR), fan/core speed, and bleed-related channels as
  *controllable proxies* for synopsis-style experiments. These are not verified actuator commands
  and must not be interpreted as direct engine control inputs without domain review.
- **Coupling models describe observed co-variation, not causal physics.** Learned propagation and
  Tier 4 residual bounds capture statistical coupling on training engines in a healthy-to-moderate
  degradation regime. Passing a coupling check is not proof of a physically realizable intervention.
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
- **Phase 4 FD001 outcome.** On a seeded sample of 200 of 308 feasible-interval high-risk states
  in the internal held-out split, no candidate met the true calibrated `tau_safe` target. Mean risk
  reduction was 0.12047 and the configured 0.60 target failed. Mean returned diagnostic changes
  were 2.595 features; valid-candidate sparsity is unmeasured because there were no valid results.
  The benchmark used explicitly recorded reduced search limits (25 iterations, one restart, three
  alpha steps, one L1 step, two support candidates); these settings are in the generated evaluation
  report. The result does not demonstrate successful recourse and is not a maintenance-effect
  claim.
- **Latency scope.** The evaluation measures inference, optimization, and validation in the Python
  process. Raw telemetry ingestion and interactive dashboard render latency remain unmeasured until
  an instrumented live-input deployment is available.
- **Operator review.** The current package is research/decision-support software, not an autonomous
  control system. Recommendations require qualified engineering review and independent safety
  controls before any deployment.
