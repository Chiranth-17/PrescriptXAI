phase: 4
created: 2026-10-17
status: in_progress
---

# Phase 4 State Snapshot — Constrained Recourse

## Implemented follow-up

- Added a configurable five-point bounded sparse grid fallback against the true calibrated model.
  It uses the existing actuator/rate/trust intervals, counts mandatory projections against `k_max`,
  propagates dependent features with the fitted coupling estimators, and prefers a candidate that
  passes Tiers 2–4 when one is found.
- Added a true-model-safe recovery test under surrogate mismatch, a structured best-effort test for
  unreachable targets, and mandatory-projection support coverage.
- Added per-record grid-search time and true-model candidate counts to evaluation artifacts.

## Final measured FD001 run

- Command: `uv run prescriptxai evaluate --queries 200 --config data/processed/phase4-grid-final.yaml`.
- 200 / 378 actionable high-risk held-out states evaluated.
- True model validity: 131/200 (65.5%); physical plausibility: 152/200 (76%); sparse feasibility:
  129/200 (64.5%); joint success: 127/200 (63.5%).
- Mean risk reduction: 0.66151; mean joint-success sparsity: 2.59055.
- Mean / P95 optimization: 705.04 / 1,171.68 ms; mean / P95 pipeline: 712.74 / 1,179.41 ms.
- Frozen-feature, actuator-bound, and rate-limit violations: 0 / 0 / 0.
- Grid ran on 178/200 states, averaging 3,103 candidate scores and 39.77 ms per evaluated state.
- The 9-point grid diagnostic found no additional validity or joint-success cases versus five points,
  while increasing mean optimization latency from about 660 ms to about 888 ms on its 40-state sample.

## Acceptance status

Implementation and tests are present, but the synopsis gate remains unmet: validity target 95% versus
65.5%, physical-plausibility target 90% versus 76%, and mean latency measurements below both target
minimum bands. Mean risk reduction and sparsity targets pass. Keep the definition and thresholds
unchanged. The current single-step C-MAPSS sensor-proxy rates are not verified actuator limits; new
physical evidence or a reviewed action horizon is required before claiming the missing target rates.
