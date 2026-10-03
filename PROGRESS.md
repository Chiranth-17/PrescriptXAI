# Progress

## Current status

Phase 2 (data and predictive models) is complete. The user-provided synopsis has been read and
copied unchanged to `docs/synopsis.pdf`; its SHA-256 digest matches the original file.

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

## Decisions

- The case-study values in the synopsis are illustrations, never baseline or dashboard results.
- Model validity (`f(x') <= tau_safe`) and physical plausibility (Tiers 2–4) are independent
  outputs.
- Initial C-MAPSS recommendations must distinguish measured operating settings from verified
  controllable actuators; no causal or RUL-extension claims are supported by the static data.
- All tunable thresholds and physical limits are YAML configuration.

## Open issues and blockers

- Phase 2 model summaries do not evaluate recourse. Tiered physical validation and the evaluation
  suite are still unimplemented, so no synopsis target has been tested.

## How to run

The end-to-end package is not yet complete. Phase 2 used Python 3.13.9; the suite reported 49
passed with 85% total coverage, Ruff passed, and mypy reported no issues across 17 source files.
The real FD001 training run used seed 1729 and default configuration: 69 training engines, 16
validation engines, 15 internal holdout engines, and 3,229 validation rows. The validation label
prevalence was 0.1536 and mean predicted risk was 0.1488; these are run observations, not recourse
validity or physical-plausibility results. Run `uv sync --all-extras`, `uv run ruff check .`,
`uv run mypy src`, and `uv run pytest --cov=prescriptxai` to reproduce. Data and fitted models are
git-ignored.
