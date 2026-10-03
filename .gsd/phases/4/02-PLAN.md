---
phase: 4
plan: 2
wave: 2
depends_on: [4.1]
files_modified:
  - src/prescriptxai/evaluation/
  - configs/default.yaml
  - tests/
autonomous: true
user_setup: []
must_haves:
  truths:
    - Evaluation reports model validity separately from Tiers 2–4 plausibility.
    - Targets are configurable and pass/fail is based on measured runs.
    - Unsupported latency stages are reported unmeasured instead of fabricated.
    - Reports include denominators and sample counts.
  artifacts:
    - src/prescriptxai/evaluation/metrics.py
    - src/prescriptxai/evaluation/runner.py
    - src/prescriptxai/evaluation/ablations.py
    - src/prescriptxai/evaluation/latency.py
    - src/prescriptxai/evaluation/report.py
---

# Plan 4.2: Evaluation suite and measured reports

## Objective

Measure recourse validity, plausibility, sparsity, risk reduction, and latency against the synopsis targets.

## Context

- `.gsd/SPEC.md`
- `docs/synopsis.pdf`
- `src/prescriptxai/pipeline.py`
- `configs/default.yaml`

## Tasks

<task type="auto">
  <name>Implement reproducible held-out engine evaluation and metrics</name>
  <files>src/prescriptxai/evaluation/metrics.py, src/prescriptxai/evaluation/runner.py, src/prescriptxai/evaluation/ablations.py, src/prescriptxai/evaluation/latency.py</files>
  <action>Evaluate deterministically sampled high-risk rows from internal held-out engines, time actual stages, and keep Tier 1 vs physical validity separate. Include configured limits, empty-sample handling, and baseline/ablation outputs. AVOID treating no-action attempts as valid recourse or borrowing synopsis case-study outcomes.</action>
  <verify>Unit/integration tests for denominators, no high-risk cases, failed recourse, repeatability, ablations, and unmeasured stages.</verify>
  <done>Metrics derive only from actual records and clearly report sample counts and missing evidence.</done>
</task>

<task type="auto">
  <name>Generate machine-readable and human-readable evaluation reports</name>
  <files>src/prescriptxai/evaluation/report.py, tests/</files>
  <action>Write JSON and Markdown reports from evaluated metric objects, including configured target thresholds and honest pass/fail/unmeasured statuses. AVOID embedding expected outcomes in templates.</action>
  <verify>Run a fixture evaluation and assert report values equal source metric objects; inspect JSON schema and Markdown content.</verify>
  <done>Reports can be regenerated from saved raw evaluation records without code changes.</done>
</task>

## Must-Haves

- [x] Every synopsis target is measured or labeled unmeasured.
- [x] Model validity and physical plausibility have separate denominators and outcomes.
- [x] Report values are computed from the current run.
