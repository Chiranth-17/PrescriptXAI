---
phase: 3
plan: 2
wave: 2
depends_on: [3.1]
files_modified:
  - src/prescriptxai/validation/
  - src/prescriptxai/constraints/coupling.py
  - tests/unit/
  - tests/integration/
autonomous: true
user_setup: []
must_haves:
  truths:
    - Tier 1 model validity is reported separately from Tiers 2–4 physical plausibility.
    - Mahalanobis statistics fit only on the model's training engines.
    - Missing coupling rules fail closed and are explained.
    - Simulator validation remains optional and disabled unless an adapter is explicitly provided.
  artifacts:
    - src/prescriptxai/validation/tier1_model.py
    - src/prescriptxai/validation/tier2_mahalanobis.py
    - src/prescriptxai/validation/tier3_engineering.py
    - src/prescriptxai/validation/tier4_coupling.py
    - src/prescriptxai/validation/pipeline.py
---

# Plan 3.2: Independent validation tiers

## Objective

Implement the separate predictor, empirical-distribution, engineering, coupling, and optional simulator checks.

## Context

- `.gsd/SPEC.md`
- `docs/synopsis.pdf`
- `src/prescriptxai/models/train.py`
- `configs/features.yaml`

## Tasks

<task type="auto">
  <name>Implement training-only distribution, engineering, and coupling checks</name>
  <files>src/prescriptxai/validation/tier2_mahalanobis.py, src/prescriptxai/validation/tier3_engineering.py, src/prescriptxai/validation/tier4_coupling.py, src/prescriptxai/constraints/coupling.py</files>
  <action>Fit regularized covariance only from declared training engine rows; check absolute actuator bounds, rates, and unchanged non-actuators; evaluate typed coupling rules. AVOID vacuously passing an empty coupling-rule set. USE explicit diagnostics and finite/shape checks.</action>
  <verify>Unit tests for train/held-out ID mismatch, singular/constant columns, NaN/wrong shape, bounds/rates, immutable changes, each relation type, and empty rules.</verify>
  <done>Tiers 2–4 return separate results; absent physical knowledge remains an explicit failed check.</done>
</task>

<task type="auto">
  <name>Integrate all tiers and optional simulator adapter</name>
  <files>src/prescriptxai/validation/tier1_model.py, src/prescriptxai/validation/pipeline.py, src/prescriptxai/validation/simulator.py, tests/integration/</files>
  <action>Orchestrate four checks while keeping model validity distinct from physical validity; map to public result schemas; run injected simulator validation only when enabled. AVOID claiming RUL improvement or treating missing simulator adapters as successful. USE clear failure diagnostics.</action>
  <verify>Integration test flows a synthetic fixture through recourse and all four tiers; simulator tests cover disabled, enabled, and missing-adapter cases.</verify>
  <done>Aggregate success is true only when model safety and every required physical tier pass.</done>
</task>

## Must-Haves

- [ ] Model and physical validity remain separate in all outputs.
- [ ] Training-only covariance and configurable physical constraints are checked.
- [ ] Simulator behavior is opt-in and cannot produce C-MAPSS RUL-extension claims.
