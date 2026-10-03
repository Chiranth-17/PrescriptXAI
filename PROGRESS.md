# Progress

## Current status

Phase 1 (repository foundation) is complete. The user-provided synopsis has been read and copied
unchanged to `docs/synopsis.pdf`. Its SHA-256 digest matches the original file.

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

## Decisions

- The case-study values in the synopsis are illustrations, never baseline or dashboard results.
- Model validity (`f(x') <= tau_safe`) and physical plausibility (Tiers 2–4) are independent
  outputs.
- Initial C-MAPSS recommendations must distinguish measured operating settings from verified
  controllable actuators; no causal or RUL-extension claims are supported by the static data.
- All tunable thresholds and physical limits are YAML configuration.

## Open issues and blockers

- The workspace started without a Git repository; initialize it before the Phase 1 commit.
- No C-MAPSS dataset or trained model is present. Real benchmark metrics cannot be reported until
  data is obtained and the training/evaluation pipeline is implemented.

## How to run

The end-to-end package is not yet complete. Phase 1 verification used Python 3.13.9 and the local
`.venv`: Ruff passed, mypy passed, and pytest reported 15 passed with 91% total coverage. Re-run
with `uv run ruff check .`, `uv run mypy src`, and `uv run pytest --cov=prescriptxai` after syncing
the full lockfile. `uv sync --all-extras` installs the full model, API, and dashboard stack.
