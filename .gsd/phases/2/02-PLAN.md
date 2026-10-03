---
phase: 2
plan: 2
wave: 2
depends_on: [2.1]
files_modified:
  - src/prescriptxai/models/
  - configs/default.yaml
  - tests/unit/
  - tests/integration/
autonomous: true
user_setup: []
must_haves:
  truths:
    - Model implementations expose calibrated risk probabilities through one typed interface.
    - Calibration is fitted on training engines only and evaluated on separate validation engines.
    - Model artifacts carry feature order, training split identity, and configuration metadata.
  artifacts:
    - src/prescriptxai/models/base.py
    - src/prescriptxai/models/xgb_model.py
    - src/prescriptxai/models/torch_models.py
    - src/prescriptxai/models/calibration.py
    - src/prescriptxai/models/registry.py
    - src/prescriptxai/models/train.py
---

# Plan 2.2: Predictive model and calibration

## Objective

Train deterministic risk classifiers with calibrated outputs using the leakage-safe Phase 2.1 data contract.

## Context

- `.gsd/SPEC.md`
- `src/prescriptxai/data/`
- `configs/default.yaml`

## Tasks

<task type="auto">
  <name>Implement typed model interfaces and estimators</name>
  <files>src/prescriptxai/models/base.py, src/prescriptxai/models/xgb_model.py, src/prescriptxai/models/torch_models.py, configs/default.yaml</files>
  <action>Implement deterministic XGBoost classifier and a small PyTorch MLP behind one risk-model protocol. Validate rank, feature count, finite values, and fitted state. AVOID hardcoded seeds, mutable feature order, or uncalibrated scores represented as probabilities.</action>
  <verify>Unit tests cover fit/predict, wrong shape, NaN, empty input, constant columns, and repeatability.</verify>
  <done>Both estimators return finite probabilities in [0,1] and reject malformed inputs with clear errors.</done>
</task>

<task type="auto">
  <name>Implement calibration, registry, and reproducible training workflow</name>
  <files>src/prescriptxai/models/calibration.py, src/prescriptxai/models/registry.py, src/prescriptxai/models/train.py, tests/integration/</files>
  <action>Fit calibration only from training-engine predictions, persist estimator/calibrator plus feature order and engine IDs, and load only artifacts whose metadata matches requested feature order. Add an integration test over a small explicitly synthetic test fixture; never use it for reported benchmark metrics.</action>
  <verify>Integration test trains, calibrates, saves, reloads, and compares predictions while proving held-out engine IDs are absent from fit metadata.</verify>
  <done>Training and reload are deterministic and auditable, with calibration provenance captured.</done>
</task>

## Must-Haves

- [ ] Classifier scores satisfy the common typed risk interface.
- [ ] Calibration provenance is restricted to training engines.
- [ ] Saved artifacts can be checked for feature-order and engine leakage.
