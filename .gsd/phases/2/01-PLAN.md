---
phase: 2
plan: 1
wave: 1
depends_on: []
files_modified:
  - configs/default.yaml
  - src/prescriptxai/data/download.py
  - src/prescriptxai/data/cmapss.py
  - src/prescriptxai/data/preprocess.py
  - src/prescriptxai/data/splits.py
  - tests/unit/
  - tests/integration/
autonomous: true
user_setup: []
must_haves:
  truths:
    - C-MAPSS download verifies ZIP content and extraction does not allow path traversal.
    - Train, validation, and test partitions contain disjoint engine IDs.
    - RUL labels and binary failure labels follow configurable cap and horizon definitions.
    - Scalers fit training-engine rows only and handle constant features deterministically.
  artifacts:
    - src/prescriptxai/data/cmapss.py
    - src/prescriptxai/data/preprocess.py
    - src/prescriptxai/data/splits.py
---

# Plan 2.1: C-MAPSS ingestion and leakage-safe preprocessing

## Objective

Create a deterministic, testable data pipeline for NASA C-MAPSS, including engine-level splits and train-only fitted transformations.

## Context

- `.gsd/SPEC.md`
- `docs/synopsis.pdf`
- NASA PCoE data page: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/

## Tasks

<task type="auto">
  <name>Implement verified archive download and C-MAPSS parsing</name>
  <files>configs/default.yaml, src/prescriptxai/data/download.py, src/prescriptxai/data/cmapss.py</files>
  <action>Accept a configured dataset URL and destination. Verify HTTP and ZIP data, extract only expected files safely, parse the documented 26-column C-MAPSS schema, and combine official training/test RUL data without mixing engine identities. AVOID silent fallback data and unsafe generic extraction. USE logging and raise typed actionable errors.</action>
  <verify>Unit tests for valid, corrupt, empty, and path-traversal archives; parser shape and malformed rows; no network required in tests.</verify>
  <done>Real C-MAPSS files parse deterministically and malformed/download failures surface explicitly.</done>
</task>

<task type="auto">
  <name>Implement RUL labels, engine splits, and train-only scaling</name>
  <files>src/prescriptxai/data/preprocess.py, src/prescriptxai/data/splits.py, tests/unit/, tests/integration/</files>
  <action>Derive RUL from run-to-failure engine endpoints and test RUL offsets, cap RUL if configured, define failure as `RUL <= H`, split whole engine IDs with a deterministic seed, and fit all scaling only on training engine rows. AVOID row-level splits or fitting on validation/test. Handle NaN, empty inputs, shape mismatch, and constant columns explicitly.</action>
  <verify>Unit and integration tests assert disjoint engine IDs, exact label math, train-only scaler statistics, finite transformed output, and deterministic repeats.</verify>
  <done>All splits are reproducible and engine-disjoint; no held-out rows affect fitted preprocessing.</done>
</task>

## Must-Haves

- [ ] No row leakage between engine partitions.
- [ ] Scaler and labels have explicit train-only and threshold semantics.
- [ ] Download/parser failure cases are visible and tested.
