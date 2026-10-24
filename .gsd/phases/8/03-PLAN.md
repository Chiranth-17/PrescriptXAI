---
phase: 8
plan: 3
wave: 3
depends_on: [8.2]
files_modified: [src/prescriptxai/dashboard/pages.py, src/prescriptxai/dashboard/data.py, src/prescriptxai/dashboard/charts.py, src/prescriptxai/dashboard/app.py, tests/integration/test_phase8_dashboard.py]
autonomous: true
must_haves:
  truths: [All five pages load, Fleet action targets the chosen real engine/cycle, Diagnostic/evaluation values are saved measured evidence]
  artifacts: [Fleet Overview, Model and Validation Diagnostics, Evaluation Results, About and Limitations]
---

# Plan 8.3: Fleet and evidence pages

## Task 1 — Fleet and About

Files: dashboard/pages.py, dashboard/app.py, dashboard/data.py, dashboard AppTests.
Action: risk ranking for each available engine at chosen cycle with explicit missing/early
history behavior, one-click recommendation and triage column that distinguishes unassessed
from computed outcomes. About explains static/proxy/model/plausibility/evidence limits.
Verify: all-page AppTest, fleet ordering/one-click selection/triage/empty/missing history tests.
Done: fleet never represents risk-only ranking as a validated action.

## Task 2 — Diagnostics and evaluation

Files: dashboard/pages.py, dashboard/charts.py, dashboard/data.py, dashboard AppTests.
Action: saved calibration curve, coupling fit/residual evidence, D_M distribution, constraint
ladder, validity-K curve and funnel. Evaluation page loads all Phase7 metrics/ablations and
design-target/measured/gap values with full run/config/protocol/population/engine-CI labels.
Missing evidence is shown as unavailable, not a placeholder chart/result. Keep raw telemetry
and fitted artifacts outside Git. Verify saved-result table/chart equality and every page's
AppTest; unit empty/edge tests, lint/mypy; commit verified tasks.
Done: all five pages and required charts/tables are complete and source-traceable.
