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

The historical Phase 4 measurements remain in that versioned report. Its old evidence labels
and the phrase “joint Tiers 2–4” are superseded by the definitions below; the Phase 5 paired
report derives independent Tier 2, physical Tiers 2–4 and joint Tiers 1–4 from saved query records.

## Evidence levels (current rules 18 and 29)

- E1: true calibrated predictor validity only.
- E2: E1 plus statistical distributional plausibility (Tier 2).
- E3: E1–E2 plus proxy engineering and sensor relationship constraints (Tiers 3–4).
- E4: a learned emulator validated on held-out units and operating regions.
- E5: a validated physics simulator.

These levels describe checks actually reached, not operational safety. FD001 has observational
run-to-failure telemetry and no intervention ground truth. A learned coupling regressor is not
an emulator of counterfactual dynamics or a physics simulator. E4/E5 are unavailable. Skipped
checks never pass. No RUL extension is claimed.

## Phase 5 statistical validation assumptions

The committed `docs/evaluation_protocol.md` specifies train-only Ledoit–Wolf covariance,
Cholesky scoring, all-cycle reference, unchanged fixed D_max versions and validation-only
coupling residual calibration. Healthy-to-moderate covariance reference and quantile thresholds
are supported but are not evaluated alternatives until the Phase 7 ablation. Regime assignments
are determined from frozen original operating settings. Changing a sensor cannot select a
friendlier regime. Fitting and calibration engines are disjoint from test engines.

Coupling propagation preserves the original observed residual:
`d_prime = d + g(c_prime, settings) - g(c, settings)`. It does not reset a machine to the healthy
regression mean. Consequently an initial residual outside its validation-calibrated threshold
can make all propagated candidates fail Tier 4. The bounded feedback loop may return such a
diagnostic candidate with an explicit failure, never a validated recommendation.
