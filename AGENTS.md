# PrescriptXAI contributor instructions

- Read `docs/synopsis.pdf` and `.gsd/SPEC.md` before changing model, recourse, or validation behavior.
- Treat the synopsis case study as illustrative. Generate reported numbers from saved, reproducible runs.
- Keep model safety (`f(x') <= tau_safe`) separate from plausibility checks in Tiers 2–4.
- Never claim RUL extension from static C-MAPSS data. Keep the simulator interface optional and off by default.
- Keep thresholds, bounds, masks, rate limits, `D_max`, and sparsity limits in YAML configuration.
- Split by engine ID. Fit scalers, calibrators, and covariance validators on training engines only.
- Keep raw-unit and scaled-space deltas explicit and test their mappings.
- Add unit, integration, and negative/edge tests for each behavior phase. Do not make tests pass by skipping, stubbing, or fabricating results.
- Run `ruff`, `mypy`, and `pytest --cov=prescriptxai`; update `PROGRESS.md` after every phase.
- Keep generated data and fitted artifacts out of version control.
