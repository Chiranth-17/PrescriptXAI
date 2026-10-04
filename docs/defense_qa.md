# Defense Q&A

## How is leakage prevented?

Engine IDs, rather than rows, define train, validation, and internal holdout groups. Feature
filtering and scaling fit on train engines only. Early stopping and calibration use validation
engines only. The internal holdout is reserved for reported evaluation metrics and calibration
diagnostics; it is not used for fitting.

## Why separate model validity and physical plausibility?

Tier 1 only establishes that the fitted predictor returns risk at or below its configured safe
threshold. Tiers 2–4 separately check empirical distribution distance, actuator/rate constraints,
and configured coupling rules. A model-valid state may still be implausible.

## Can the system claim an intervention extends RUL on C-MAPSS?

No. C-MAPSS is static run-to-failure telemetry and does not provide interactive counterfactual
trajectories. RUL impact requires a validated dynamic simulator or transition model, neither of
which is supplied by the default project.

## What does the current FD001 run demonstrate?

It demonstrates the model and evaluation plumbing on an engine-held-out split. The current default
taxonomy has no verified actuators or coupling rules, so no actionable recourse is produced. The
measured recourse-validity and full physical-plausibility rates are zero for the sampled high-risk
queries; this is an explicit configuration limitation, not evidence that a physical intervention
failed.

## What is required to demonstrate actionable physical recourse?

A domain-validated mapping from controllable actuators to model features, raw-unit operating bounds,
maximum rate changes, sensor coupling rules and tolerances, and preferably intervention-aware
simulator or field validation. These settings must be reviewed before adding them to
`configs/features.yaml`.
