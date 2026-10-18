# Evaluation assumptions

This file records assumptions that affect Phase 4 measurements. They are explicit model inputs,
not established engine dynamics.

## Sensor-proxy rate limits

The configured per-step action limits are estimated separately for each controllable proxy from
the 99th percentile of absolute adjacent-cycle telemetry changes, calculated within training
engines only. Differences never cross engine boundaries. Fitted values are stored in the model
and coupling artifacts and checked against the source training-engine IDs.

C-MAPSS contains sensor readings, not commanded actuator values or intervention trajectories.
These limits therefore describe an empirical envelope of observed sensor movement, not verified
actuator slew rates. Every recourse validity result is conditional on this assumption. A stricter
or looser real actuator limit can change which states are actionable and the measured success
rate.

## Intervention horizon K

`K=1` applies one empirical per-step allowance. Sensitivity values `K>1` multiply that allowance
by K and assume an intervention can be distributed over K steps. C-MAPSS does not identify K,
actuator dynamics, persistence, or the resulting sensor response. The K curve is a software
sensitivity analysis, not evidence that an intervention is safe over those horizons.

## Thresholds and sparsity

The safety thresholds remain `tau_danger=0.80` and `tau_safe=0.20`. The headline action support is
`k_max=3`. The Phase 4 closure run does not change thresholds, physical bounds, proxy masks, or
per-step rate limits to meet a target. The k=5 case is a one-factor sensitivity only.

## Plausibility protocols

Tier 2 v1 retains `D_max=5.0`. The separately frozen v2 protocol uses `D_max=8.0`; it is reported
alongside v1 and never replaces it. The v2 threshold was committed before its evaluation. Both
versions use the same training-engine-fitted covariance and features.

The 95th percentile of real low-risk validation-state Mahalanobis distances is reported as a
secondary diagnostic. It does not replace either fixed `D_max` protocol.

## Phase 4 closure run

The final report is `docs/phase4_final.md`, with the complete machine-readable run at
`docs/phase4_full_diagnosis_results.json`. The v1 and v2 headline protocols use `k_max=3`, `K=1`,
and `D_max=5` or `8`, respectively; v2 was frozen before evaluation. Holdout and sensitivity
measurements were computed from source commit `7860fed5a99b6c94eefc2ffd2c8327052ea56b24`;
grouped OOF and official-test measurements were computed from
`4a8275a788c9998d80acf07f3e7e9dfe2fcbe179`. The report renderer/source was at
`d1a6945fa9671beb6c48ebbbf89f0a2c72221488` for the run/oracle measurements. The final Markdown
renderer correction only fixes labels and historical audit context; it does not recompute or alter
measurements. The report records compatible checkpoint reuse and stage source commits explicitly;
checkpoint reuse does not change the listed effective configuration or dataset/model artifact hashes.

The headline engine-cluster bootstrap sample has 15 engines and 200 queries. Model-valid rate is
0.560 under both protocols. V2 raises all-query Tier 2 plausibility from 0.530 to 0.990, but joint
Tiers 2–4 plausibility is 0.525 and p95 optimization time is 2,022.5 ms. Targets are reported as
missed where applicable. The holdout has 378/378 actionable high-risk rows; rows are still clustered
by their 15 engines for uncertainty. Results are conditional on C-MAPSS sensor proxies and are E1
evidence only.

## Evidence level

FD001 is observational run-to-failure data. Sensor propagation and learned residual constraints
measure observed statistical relationships; they do not provide intervention ground truth. The
available evidence can establish implementation and dataset-level behavior (E1), but not validated
simulation behavior (E2) or operational safety (E3). No RUL extension is claimed.
