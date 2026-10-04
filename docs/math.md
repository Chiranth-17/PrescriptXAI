# Mathematical formulation and units

Given a raw feature state \(x\), a calibrated risk estimator \(f\), and an alert condition
\(f(x) \ge \tau_{danger}\), the optimizer searches for a candidate \(x'=x+\Delta x\) satisfying
\(f(x')\le\tau_{safe}\). The default thresholds are 0.80 and 0.20, respectively, and are read
from YAML.

The configured optimization is

\[
\min_{z_A}\ \|z_A-z_{A,0}\|_1 + \lambda_{pred}\,\ell(f(x'(z_A)),\tau_{safe})
\]

subject to the configured scaled-distance limit, actuator bounds, per-step rate limits, and the
model-risk target. Here \(A\) is the actuator set, \(z=(x-\mu)/s\) is the training-fitted
standardized vector, and non-actuators remain fixed. The implemented solver uses bounded SLSQP
with automatic derivatives from a differentiable MLP or XGBoost's distilled MLP surrogate when
available; other predictors fall back to finite differences. A deterministic subset search then
checks the configured maximum number of changed actuators. An infeasible or unsafe result remains
a failed recommendation.

## Unit mapping

- `OptimizationResult.state` and each `DeltaMapping.raw_delta` are in the original feature units.
- `DeltaMapping.scaled_delta` is the corresponding difference after applying the training-only
  scaler: \(\Delta z_j=\Delta x_j/s_j\).
- Optimization distance is computed in scaled space. Engineering bounds, actuator rates, and
  operator-facing reports use raw units.
- Tier 2 Mahalanobis distance is computed on standardized model features against the covariance
  fitted on training engines only.

The overall response reports Tier 1 model validity separately from physical validity (all of
Tiers 2–4). Neither implies real-machine safety. See [limitations](limitations.md).
