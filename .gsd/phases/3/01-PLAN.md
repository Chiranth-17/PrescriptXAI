---
phase: 3
plan: 1
wave: 1
depends_on: []
files_modified:
  - src/prescriptxai/constraints/bounds.py
  - src/prescriptxai/constraints/coupling.py
  - src/prescriptxai/recourse/objective.py
  - src/prescriptxai/recourse/optimizer.py
  - src/prescriptxai/recourse/sparsify.py
  - src/prescriptxai/recourse/baselines.py
  - tests/unit/
autonomous: true
user_setup: []
must_haves:
  truths:
    - Optimization changes only configured actuators in scaled space and reports raw and scaled deltas.
    - Physical bounds, per-step rates, total scaled distance, target risk, and sparsity are enforced.
    - Failed optimization is explicit and never presented as a successful recommendation.
  artifacts:
    - src/prescriptxai/recourse/optimizer.py
    - src/prescriptxai/recourse/sparsify.py
    - src/prescriptxai/constraints/bounds.py
---

# Plan 3.1: Bounded sparse recourse

## Objective

Implement actuator-only optimization, exact small-subset sparsification, constraint helpers, and honest baselines.

## Context

- `.gsd/SPEC.md`
- `docs/synopsis.pdf`
- `configs/default.yaml`
- `configs/features.yaml`
- `src/prescriptxai/models/registry.py`

## Tasks

<task type="auto">
  <name>Implement objective, bounds, and constrained optimizer</name>
  <files>src/prescriptxai/constraints/bounds.py, src/prescriptxai/recourse/objective.py, src/prescriptxai/recourse/optimizer.py, configs/default.yaml</files>
  <action>Optimize scaled actuator values only, using configured physical/rate intervals, L1 distance, a safe-risk constraint, and total scaled movement limit. Return explicit infeasibility and low-risk/no-actuator results. AVOID changing environmental, operational, or dependent sensor values. USE raw/scaled mappings from the fitted training scaler and do not infer actuator mappings.</action>
  <verify>Unit tests for exact objective math, actuator bounds/rates, safe candidate, raw/scaled delta mapping, no actuators, and infeasible/low-risk inputs.</verify>
  <done>Every returned action changes only configured actuators and includes separate model-valid status.</done>
</task>

<task type="auto">
  <name>Enforce sparsity and provide comparison baselines</name>
  <files>src/prescriptxai/recourse/sparsify.py, src/prescriptxai/recourse/baselines.py, tests/unit/</files>
  <action>Rescore each candidate subset and keep only a safe subset within configured `k`; implement no-action and one-actuator-at-a-time baselines. AVOID assuming a sparse projection remains model-valid. USE fitted-model reevaluation for every subset.</action>
  <verify>Tests include safe subset selection, no feasible sparse subset, and explicit no-action behavior.</verify>
  <done>No optimizer or baseline claims model validity without scoring the final candidate.</done>
</task>

## Must-Haves

- [ ] Only YAML-declared actuators can change.
- [ ] Bounds, rate, distance, risk, and sparsity constraints are observable.
- [ ] All output deltas preserve physical and scaled units separately.
