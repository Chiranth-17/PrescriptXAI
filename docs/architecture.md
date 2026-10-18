# Architecture

## Data flow

1. `data.download` fetches an archive into the configured raw-data directory and validates the ZIP.
2. `data.cmapss` parses FD001–FD004; `data.preprocess` creates labels from the final-cycle RUL and
   fits the scaler only on training-engine rows.
3. `data.splits` assigns whole engine IDs to train, validation, and internal holdout partitions.
4. `models.train` fits XGBoost, a differentiable MLP, or an LSTM using only train engines. Early
   stopping and probability calibration use the disjoint validation engines; the internal test
   engines are reserved for one-time reporting. XGBoost gets a distilled MLP surrogate for its
   gradient path. The versioned registry stores weights, calibrator, scaler, feature order, config
   hash, Git revision, metrics, and engine provenance.
5. The recourse optimizer changes only configured controllable proxy features. It uses bounded
   L-BFGS-B with torch-autograd gradients from the MLP or distilled MLP, propagates changes through
   the fitted dependent-sensor model, enforces top-k sparsity by support re-optimization, and
   re-scores every final candidate with the true calibrated predictor. It returns raw/scaled proxy
   deltas, solver diagnostics, and an independent model-risk result.
6. The validator runs Tier 1 model safety, Tier 2 training-distribution Mahalanobis distance,
   Tier 3 actuator bounds/rates and immutable-feature checks, and Tier 4 configured coupling rules.
   Missing coupling rules fail closed. Simulator support is a Protocol boundary, not a simulator
   implementation, and remains disabled by default.
7. `PrescriptXAIEngine.recommend` is the shared typed boundary used by CLI, FastAPI, and Streamlit.
   Evaluation deterministically samples high-risk rows from engine-held-out data and records
   per-stage latency and independent validity outcomes.

## Configuration and artifacts

`configs/default.yaml` owns risk thresholds, split fractions, model settings, optimization limits,
latency/quality targets, and artifact paths. `configs/features.yaml` owns the feature taxonomy,
actuator ranges/rates, and coupling rules. Training writes model and Mahalanobis artifacts under
`artifacts/`; raw and processed data and fitted artifacts are ignored by Git.

The LSTM consumes windows built within each engine. Early windows are left-padded by repeating that
engine's first observed row. In recourse, the final timestep is the candidate state; earlier
timesteps remain fixed observed history. The current snapshot recommendation API does not accept
sequence history, so use `predict_risk_sequence` and `torch_forward` for LSTM sequence inference.

The default C-MAPSS taxonomy maps seven measured sensor channels to configurable controllable
proxies and keeps all three operating settings immutable. Those channels are telemetry, not direct
actuator commands. Coupling models estimate dependent sensor outputs from training-data
co-variation; neither the proxy map nor the learned relations establish causal physics or operational
safety. See [limitations](limitations.md).

## Interfaces

- CLI: download, train, recommend, evaluate, serve.
- Optional FastAPI: `/health` and `/recommend`.
- Streamlit: raw state upload, measured risk/delta visualization, per-tier results, and limitation
  notices.
- Evaluation: JSON and Markdown report with denominators, configured target statuses, and
  unmeasured stages left unmeasured, including direction agreement among nearby states and explicit
  frozen-feature, actuator-bound, and rate-limit violation counts.


## Phase 5 validation boundary

All consumers share `validation.pipeline.validate_candidate`. Its report has independent
`model_valid`, `plausible` (Tier 2 only), `constraints_ok` (Tiers 3–4), `joint`, failing-tier names,
signed margins, per-rule explanations and E1–E5 evidence. Collect-all and fail-fast use the same
checks; fail-fast unrun tiers and unavailable dynamics are skipped rather than passed. Version
1.1.0 of the public result/report adds this evidence, status and assumptions without changing the
underlying delta units. The Phase 6 interface freeze has not occurred yet.

`validation.feasibility` supplies differentiable penalties to the existing optimizer, while final
acceptance reuses the exact runtime checks and true calibrated predictor. At most N configured
feedback refinements increase only the penalty weight. The diagnostic return remains separate
from an accepted counterfactual. Persisted validators are checked against runtime feature order,
fitting engines, threshold method/value, reference choice, covariance floor and regime count.

Run the frozen real-data funnel/preparation with:

```powershell
uv run python scripts/diagnostics/phase5_validate.py
```

Commit code, protocol and configs before measuring. This command verifies the raw archive hash,
loads the saved Phase 4 candidates, preserves query denominators, fits validators on the declared
fitting engines, calibrates coupling residuals on validation engines, writes ignored fitted
artifacts/query caches, and generates `docs/phase5_changes.md` plus the K sensitivity figure.
Historical configs under `configs/experiments/phase4-historical-*` are executable mirrors created
for traceability, not retroactive preregistration. Original effective hashes/measurement commits
remain attached to each historical report column.
