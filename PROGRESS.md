# Progress

## Current status

Phase 3 (constrained recourse and validation) is complete. The user-provided synopsis has been
read and copied unchanged to `docs/synopsis.pdf`; its SHA-256 digest matches the original file.

## Done

- Read `C:\Users\chira\Downloads\new5thsemel.pdf` and confirmed the mathematical framing,
  four validation tiers, latency/validity/sparsity targets, illustrative case study, and C-MAPSS
  limitation.
- Recorded the project specification and phased roadmap in `.gsd/`.
- Added a `src/` package foundation, typed YAML config loader, feature taxonomy constraints,
  public state/recourse schemas, config files, and data/artifact ignore rules.
- Added unit and integration coverage for threshold ordering, split fractions, invalid YAML,
  overlapping features, unknown coupling references, non-finite inputs, and result validity.
- Locked 121 dependencies with uv in `uv.lock` and installed the phase verification toolchain in
  the local `.venv`.
- Implemented safe C-MAPSS archive download and parsing, including NASA's nested ZIP layout,
  exact RUL/failure labels, deterministic engine-level splits, and train-only feature scaling.
- Implemented XGBoost and PyTorch classifiers, engine-grouped probability calibration, the training
  workflow, artifact provenance, and save/reload checks.
- Downloaded the public FD001 archive to ignored `data/raw/CMAPSSData.zip` and parsed it successfully.
- Trained and saved `artifacts/FD001-xgboost.joblib` using the default config and seed.
- Implemented scaled-space SLSQP recourse, hard actuator/rate/distance/risk constraints, exact
  small-subset sparsification, raw/scaled delta reporting, and no-action/single-actuator baselines.
- Implemented independent Tiers 1–4, train-engine-only Mahalanobis fitting, engineering/rate
  checks, fail-closed coupling validation, and an opt-in simulator protocol.
- Integrated the full optimizer and four-tier validation pipeline with synthetic fixtures used
  only to verify behavior, not as benchmark results.

## Decisions

- The case-study values in the synopsis are illustrations, never baseline or dashboard results.
- Model validity (`f(x') <= tau_safe`) and physical plausibility (Tiers 2–4) are independent
  outputs.
- Initial C-MAPSS recommendations must distinguish measured operating settings from verified
  controllable actuators; no causal or RUL-extension claims are supported by the static data.
- The default C-MAPSS taxonomy declares no actuator mapping or coupling rules. Empty coupling
  configuration fails Tier 4, and no actuator configuration returns a failed recourse result.
- All tunable thresholds and physical limits are YAML configuration.

## Open issues and blockers

- Phase 2 model summaries do not evaluate recourse. Tiered physical validation and the evaluation
  suite are now implemented, but evaluation reports/ablations are not yet implemented, so synopsis
  performance targets have not been measured.
- A physically valid recommendation cannot be demonstrated on the default C-MAPSS setup without a
  verified telemetry-to-actuator mapping, physical limits/rates, and domain-reviewed sensor
  coupling rules. Provide these in `configs/features.yaml`, use a dataset with known controls, or
  keep FD001 results limited to an explicit no-recourse outcome.

## How to run

The end-to-end package is not yet complete. Phase 2 used Python 3.13.9; the suite reported 49
passed with 85% coverage. Phase 3 verification reports 63 passed with 86% total coverage, Ruff
passed, and mypy reports no issues across 32 source files.
The real FD001 training run used seed 1729 and default configuration: 69 training engines, 16
validation engines, 15 internal holdout engines, and 3,229 validation rows. The validation label
prevalence was 0.1536 and mean predicted risk was 0.1488; these are run observations, not recourse
validity or physical-plausibility results. A real high-risk FD001 validation row scored 0.9690;
with the default empty actuator taxonomy, recourse correctly failed with “no controllable
actuators are configured.” Tier 1 failed, Tier 2 exceeded the configured plausibility limit,
Tier 3 passed for the unchanged state, and Tier 4 failed because no coupling rules exist. Run
`uv sync --all-extras`, `uv run ruff check .`, `uv run mypy src`, and
`uv run pytest --cov=prescriptxai` to reproduce. Data and fitted models are git-ignored.
