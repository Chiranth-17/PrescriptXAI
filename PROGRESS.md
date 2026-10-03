# Progress

## Current status

Phases 1–5 are complete. The
user-provided synopsis was copied unchanged to `docs/synopsis.pdf` (SHA-256 matches the source).

## Done

- Preserved the synopsis, established package/configuration foundations, and recorded a phased spec.
- Implemented safe C-MAPSS ingestion (including NASA's nested ZIP layout), failure labels, engine-ID
  splits, training-only scaling, grouped calibration, XGBoost/PyTorch models, and artifact
  provenance.
- Downloaded the public FD001 archive to ignored `data/raw/CMAPSSData.zip`.
- Implemented scaled-space SLSQP recourse, actuator-only changes, raw bounds/rates, distance/risk
  constraints, exact small-subset sparsification, explicit raw/scaled deltas, and baselines.
- Implemented independent Tier 1 predictor-risk validation, Tier 2 training-only Mahalanobis,
  Tier 3 engineering bounds/rates, Tier 4 fail-closed sensor coupling, and the optional disabled
  simulator interface.
- Added shared engine, Typer CLI, optional FastAPI endpoints, Streamlit dashboard, deterministic
  held-out evaluation, target-aware JSON/Markdown reports, and UI/API/evaluation tests.
- Added end-to-end and empty-evaluation regression tests, technical documentation, and
  pre-commit configuration.
- Default `configs/features.yaml` has no verified actuators and no coupling rules; this is
  intentional and prevents treating telemetry features as safe controls without evidence.

## Decisions and assumptions

- Synopsis case-study values (88% → 17%, fuel −3.2%, bypass +1.1%) are illustrative and are never
  represented as measured results.
- Model validity (`f(x') <= tau_safe`) and physical plausibility (Tiers 2–4) are reported
  separately.
- No RUL-extension or real-machine safety claims are supported by the static C-MAPSS dataset.
- Thresholds, ranges, masks, rate limits, recourse limits, model parameters, and evaluation targets
  are configured in YAML. Standardized optimization deltas and raw physical-unit deltas are both
  explicit.
- The evaluation sample is deterministically selected from an engine-held-out split. Synthetic
  models are used only for software contract tests, never to populate real-run reports.

## Measured default FD001 run

Using seed 1729, the final training run assigned 69 engines to training, 16 to validation, and 15
to internal holdout. Of 354 held-out rows meeting the configured high-risk gate, 100 were sampled.
There were 0/100 model-valid recommendations and 0/100 candidates passing all physical tiers. The
optimizer explicitly returned `no controllable actuators are configured`; Tier 4 fails closed with
no coupling rules. Tier 2 alone passed on 77/100 states, Tier 3 passed on 100/100 unchanged states.
These separate tier observations do not imply a successful recommendation.

Measured latency means: inference 19.31 ms (target <15 ms, fail), optimization 18.87 ms (target
1,200–1,800 ms, fail), validation 23.13 ms (target <100 ms, pass), and optimization plus validation
42.00 ms (pipeline target 1,500–2,200 ms, fail). Per-state telemetry ingestion and interactive
dashboard render latency are unmeasured; archive loading is not counted as per-state ingestion.
Model-validity target (>=95%) and full physical-plausibility target (>=90%) both fail on this
configuration. Average sparsity is unmeasured because no candidate is model-valid. See the ignored
generated `artifacts/FD001-evaluation.md` and `.json` for all sampled records and exact values.

## Open issues and blockers

- The default C-MAPSS taxonomy cannot demonstrate actionable physical recourse without a verified
  actuator mapping, raw physical bounds/rates, and domain-reviewed coupling rules, or a different
  dataset with known controls. This is a domain-evidence blocker; the engine reports it explicitly.
- The optimization and total-latency targets fail for the default no-actuator configuration. These
  targets were not retuned. A future run with verified actuators will measure solver runtime on
  feasible cases.
- Ingestion and dashboard render latency require an instrumented live-input deployment and remain
  unmeasured.

## How to run

From the repository root with Python 3.11+ and uv:

```powershell
uv sync --all-extras
uv run prescriptxai download
uv run prescriptxai train
uv run prescriptxai evaluate
uv run streamlit run src/prescriptxai/dashboard/app.py
uv run ruff check .
uv run mypy src
uv run pytest --cov=prescriptxai --cov-report=term-missing
```

The optional HTTP service starts with `uv run prescriptxai serve`. Raw/processed data and fitted
artifacts are ignored by Git; rerun training to recreate model and validator files.

## Verification (2026-10-03)

- `ruff check .`: passed.
- `mypy src`: passed (47 source files).
- `pytest --cov=prescriptxai --cov-report=term-missing`: 74 passed, 79% total coverage.
- CLI `--help`, API recommendation path, Streamlit empty-state AppTest, and browser rendering were
  checked. The visible dashboard explains C-MAPSS and the missing actuator/coupling limits.
