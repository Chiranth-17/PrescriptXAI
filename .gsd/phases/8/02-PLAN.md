---
phase: 8
plan: 2
wave: 2
depends_on: [8.1]
files_modified: [src/prescriptxai/dashboard/app.py, src/prescriptxai/dashboard/components.py, src/prescriptxai/dashboard/charts.py, tests/unit/test_phase8_charts.py, tests/integration/test_phase8_dashboard.py, .streamlit/config.toml]
autonomous: true
must_haves:
  truths: [Operator sees true calibrated risk and every tier, Edited controls revalidate live, Failures are structured diagnostics and never prescriptions]
  artifacts: [Operator Console, Measured chart builders, JSON/CSV/print exports, Colorblind-safe responsive theme]
---

# Plan 8.2: Complete Operator Console

## Task 1 — Pure charts, tables and exports

Files: dashboard/charts.py, dashboard/components.py, tests/unit/test_phase8_charts.py.
Action: v2 risk gauge/history thresholds, raw action table <=k with bounds/percentages,
before/after scaled bars and locked immutable indicators, tier cards/margins/reasons/grey
NullSimulator, D_M gauge, measured sequential waterfall with documented order and cheap exact
permutation average. Export actual current result JSON/CSV and escaped printable HTML.
Verify: unit tests assert chart traces/titles/thresholds, raw/scaled values, undefined percentages,
empty/failure cases, waterfall conservation/order averaging and escaped exports.
Done: no duplicate risk/tier/triage logic and no synthetic performance values.

## Task 2 — Widgets, manual previews and operator AppTests

Files: dashboard/app.py, dashboard/components.py, .streamlit/config.toml,
tests/integration/test_phase8_dashboard.py.
Action: sidebar subset/engine/cycle/model/mode/protocol, read-only thresholds and Recompute;
live risk/trace, recommendation vs closest-candidate labels, <=k control sliders using shared
preview, RECOVERABLE/PARTIAL/ESCALATE/NO_INTERVENTION banners with inspection/maintenance
language. Permanent honesty/evidence/version/config/mode and measured stage budgets. Session
state stays in state.py; resources/data cached, solve only on request. Measure render/build
scope separately from model/solve and label exclusion of browser/network paint honestly.
Verify: AppTest widget/risk/cycle/engine/sliders/triage/failure/export assertions with genuinely
fitted fixtures and no monkeypatched recommendation results; no training import/performance
literal tests. Lint/mypy/targeted tests, then atomic commits.
Done: real operator path is usable and stale/failed results cannot masquerade as prescriptions.
