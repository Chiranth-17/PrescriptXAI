# Architecture

## Data flow

1. `data.download` fetches an archive into the configured raw-data directory and validates the ZIP.
2. `data.cmapss` parses FD001–FD004; `data.preprocess` creates labels from the final-cycle RUL and
   fits the scaler only on training-engine rows.
3. `data.splits` assigns whole engine IDs to train, validation, and internal holdout partitions.
4. `models.train` trains an XGBoost or PyTorch classifier and calibrates risk using grouped
   validation folds. The registry stores model, scaler, feature order, and training-engine
   provenance.
5. The recourse optimizer changes only configured actuator features. It returns raw and scaled
   deltas and an independent model-risk result.
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

The default C-MAPSS taxonomy has no actuator mapping. This is intentional: changing a sensor or
operating setting is not evidence that a physical actuator can safely control it.

## Interfaces

- CLI: download, train, recommend, evaluate, serve.
- Optional FastAPI: `/health` and `/recommend`.
- Streamlit: raw state upload, measured risk/delta visualization, per-tier results, and limitation
  notices.
- Evaluation: JSON and Markdown report with denominators, configured target statuses, and
  unmeasured stages left unmeasured.
