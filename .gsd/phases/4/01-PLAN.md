---
phase: 4
plan: 1
wave: 1
depends_on: []
files_modified:
  - src/prescriptxai/pipeline.py
  - src/prescriptxai/cli.py
  - src/prescriptxai/api.py
  - src/prescriptxai/dashboard/
  - src/prescriptxai/validation/pipeline.py
  - configs/default.yaml
  - tests/
autonomous: true
user_setup: []
must_haves:
  truths:
    - CLI can download, train, recommend, and evaluate using configured artifact paths.
    - API and dashboard serialize measured result fields and independent tier statuses.
    - Missing model, covariance, actuator, or coupling configuration produces an explicit blocker.
    - Dashboard explains that C-MAPSS does not support RUL-extension claims.
  artifacts:
    - src/prescriptxai/cli.py
    - src/prescriptxai/api.py
    - src/prescriptxai/dashboard/app.py
---

# Plan 4.1: CLI, service, and operator dashboard

## Objective

Expose the validated package workflow through command-line, optional HTTP, and Streamlit interfaces.

## Context

- `.gsd/SPEC.md`
- `docs/synopsis.pdf`
- `PROGRESS.md`
- `configs/default.yaml`
- `configs/features.yaml`

## Tasks

<task type="auto">
  <name>Implement configured engine pipeline and CLI</name>
  <files>src/prescriptxai/pipeline.py, src/prescriptxai/cli.py, src/prescriptxai/validation/pipeline.py, configs/default.yaml</files>
  <action>Build engine from YAML and fitted artifacts; add Typer commands for download, train, recommend, and evaluate. Store the training-only covariance validator alongside the model. AVOID printing fabricated examples or swallowing unavailable artifacts. USE JSON inputs and typed results.</action>
  <verify>CLI integration tests invoke help and commands against local synthetic fixtures; download tests avoid network.</verify>
  <done>CLI reports a valid recommendation only when all configured checks pass and otherwise exposes tier diagnostics.</done>
</task>

<task type="auto">
  <name>Implement optional FastAPI and Streamlit surfaces</name>
  <files>src/prescriptxai/api.py, src/prescriptxai/dashboard/app.py, src/prescriptxai/dashboard/charts.py, src/prescriptxai/dashboard/components.py, src/prescriptxai/dashboard/state.py, tests/</files>
  <action>Add a typed `/health` and recommendation endpoint plus an operator UI with actual user-provided state input, measured risk and delta values, separate Tiers 1–4, and diagnostic states. Keep simulator off by default and show the static C-MAPSS RUL limitation. AVOID hardcoded case-study values and fabricated dashboard data.</action>
  <verify>FastAPI TestClient checks valid/malformed inputs; Streamlit AppTest checks empty, failure, and returned-state views; capture a browser screenshot of the rendered page.</verify>
  <done>API/UI consume the same engine path and never conflate model validity with physical plausibility.</done>
</task>

## Must-Haves

- [x] User-facing surfaces call the same typed pipeline.
- [x] All user-visible numbers originate from requests, configured targets, or measured runs.
- [x] Static-dataset and missing-domain-configuration limits remain visible.
