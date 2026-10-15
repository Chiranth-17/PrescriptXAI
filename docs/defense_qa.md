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

It demonstrates predictor evaluation on an engine-held-out split, and measured statistical coupling
fit on training engines with grouped cross-validation. The configured features include measured
sensor proxies and learned coupling relations, but these are not verified control inputs or causal
physics. FD001 coupling fit is below its configured R² floor for `sensor_3` and `sensor_6`; these
relations are flagged in the report. A safe-looking recommendation is not evidence of a realizable
or safe real-world intervention.

## What is required to demonstrate actionable physical recourse?

A domain-validated mapping from actual control commands to model features, raw-unit operating
bounds, maximum rate changes, validated sensor coupling rules and tolerances, and preferably
intervention-aware simulator or field validation. The current C-MAPSS channels are configurable
proxies only; their mapping does not satisfy this requirement. Review any mapping before operational
use.
