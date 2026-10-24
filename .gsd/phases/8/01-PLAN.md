---
phase: 8
plan: 1
wave: 1
depends_on: []
files_modified: [src/prescriptxai/pipeline.py, src/prescriptxai/api.py, src/prescriptxai/dashboard/backend.py, src/prescriptxai/dashboard/data.py, src/prescriptxai/dashboard/state.py, configs/dashboard.yaml, tests/integration/test_phase8_backend.py]
autonomous: true
must_haves:
  truths: [Manual controls use the same predictor/propagation/tiers/triage as production, Genuine LSTM histories and frozen v2 schemas are preserved, Runtime imports no training code]
  artifacts: [Typed direct/API adapters, Configured real telemetry/profile/evaluation sources, Explicit session selection lifecycle]
---

# Plan 8.1: Validated operator data and preview path

Discovery: existing pinned Streamlit/Plotly/FastAPI; installed source and official Streamlit
caching/AppTest documentation checked. No new framework or external account. Phase7-closed
commit b4a8614 is verified; its measurements are immutable. Implement only in the root agent;
subagents independently audit. No human checkpoint is needed for already authorized work.

## Task 1 — Shared manual-preview library/API path

Files: pipeline.py, api.py, tests/integration/test_phase8_backend.py.
Action: extract existing result composition without changing recommendation behavior; expose
typed manual control validation with existing normalization, genuine-history bundle, residual-
preserving coupling, engineering/sparsity constraints and all static tiers. Keep RecourseResult/
ValidationReport2.0.0 unchanged. Add optional API validation route using the same method.
Verify: targeted tests cover manual parity, immutables/nonfinite/order, >k/rate/bounds failures,
missing history and API response/error behavior; frozen schema tests pass.
Done: direct and API preview agree; raw/scaled deltas and triage reflect actual shared checks.

## Task 2 — Direct/API adapters and measured source loading

Files: dashboard/backend.py, dashboard/data.py, configs/dashboard.yaml, backend tests.
Action: load available committed profiles, raw observed telemetry and Phase7 savedJSON only;
cache model resources and copied computations with explicit artifact/input identities. Direct
is default; API config/model compatibility is checked, secrets stay in environment. Keep
training/evaluation fitting modules out of runtime imports. Use real per-engine LSTM prefixes.
Verify: real fitted fixture/profile tests, missing/corrupt source errors, no-training subprocess
import assertion, backend parity, cache invalidation and observed-history tests.
Done: operator/fleet/diagnostic inputs are reproducible and no model is fitted during use.

## Task 3 — Session lifecycle and settings

Files: dashboard/state.py, configs/dashboard.yaml, backend tests.
Action: preserve existing upload parser, add typed settings and selection/session helpers;
invalidate stale solver/preview/sliders when engine/cycle/model/mode/profile changes. Keep
thresholds read-only; expose prior D_max protocols explicitly. No illustrative UI values.
Verify: state/selection/parser tests; lint/mypy; commit verified foundation tasks conventionally.
Done: stale results cannot be shown for another telemetry selection.
