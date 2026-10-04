# Limitations and intended use

- **No validated actuator mapping for default FD001.** C-MAPSS features are telemetry and operating
  settings; the default taxonomy deliberately has no controls. The current real-data run therefore
  reports no recourse rather than converting a sensor into an actuator.
- **No coupling rules are supplied.** Tier 4 fails closed until domain-reviewed relationships and
  tolerances are configured.
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
- **Evaluation scope.** Metrics are for the configured model, seed, engine split, taxonomy, and
  sampled held-out rows. Synopsis case-study values are illustrative and never substituted for
  measured results.
- **Latency scope.** The evaluation measures inference, optimization, and validation in the Python
  process. Raw telemetry ingestion and interactive dashboard render latency remain unmeasured until
  an instrumented live-input deployment is available.
- **Operator review.** The current package is research/decision-support software, not an autonomous
  control system. Recommendations require qualified engineering review and independent safety
  controls before any deployment.
