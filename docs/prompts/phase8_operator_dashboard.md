# Phase 8 — Streamlit operator dashboard

Source: the user's direct Phase 8 prompt, received 2026-10-20. The user explicitly chose to
wait for the Phase 7 gate before starting this implementation. This file preserves the queued
requirements; it does not mark any task implemented. Existing orchestration rules still apply.

Read AGENTS.md, PROGRESS.md and the frozen RecourseResult schema. The dashboard calls the
library directly by default and the FastAPI service optionally (config switch). Inspect the
repo and adapt names.

## UX requirements

1. Sidebar: subset, engine selector, cycle slider (replays telemetry), model choice, mode
   (FAST or THOROUGH), thresholds display (tau_danger, tau_safe), Recompute button.
2. Top of main view: live risk gauge (calibrated probability), alert banner when
   p >= tau_danger, and a risk-over-cycles line chart with the alert and safe thresholds drawn.
3. Recommendation panel: table of prescribed actions (feature label, current value,
   recommended value, change in raw units and percent, bounds) with at most k_max changes;
   control sliders preset to the recommended values; when the operator edits a slider the app
   re-scores risk and re-runs all validation tiers live using the same library functions
   (no duplicated logic).
4. Waterfall chart (plotly) of each action's contribution to the risk reduction: state which
   method is displayed (sequential application in a documented order, and an order-independent
   Shapley-style average if cheap).
5. Validation panel: four tier cards (Model Safety, Distributional Plausibility, Engineering
   Constraints, Sensor Relationships) with pass or fail, margin and reason; a greyed fifth
   card "Dynamic Simulator: not available" unless a validated one is configured; Mahalanobis
   D_M versus D_max as a gauge.
6. Triage banner for every alert: RECOVERABLE, PARTIAL or ESCALATE. For PARTIAL show the
   achieved risk reduction and recommend scheduled inspection. For ESCALATE show the
   structured failure (closest candidate, why it failed) and a scheduled-maintenance
   recommendation, never a bare error.
7. Before/after comparison of sensors (radar or bars, scaled), with frozen features visibly locked.
8. Honesty banners (permanent): "Model-based validity is not physical validity";
   "No RUL extension is claimed on static datasets"; "Actuator limits are proxy assumptions
   on C-MAPSS"; the evidence level of the current recommendation; model version, config hash
   and mode; measured per-stage latency next to the budget.
9. Export: recommendation as JSON and CSV, and a printable summary.
10. Polish: consistent theme, colorblind-safe palette, spinners, st.cache_resource for artifacts
    and st.cache_data for computations, session state in state.py, responsive layout, nothing
    heavy on the main thread beyond the solve; measure and show the UI render time against
    the 250 ms budget.
11. Pages: (1) Operator Console; (2) Fleet Overview (risk ranking of all engines at a chosen
    cycle with one-click recommend and triage column); (3) Model and Validation Diagnostics
    (calibration curve, coupling fit, Mahalanobis distribution, constraint ladder,
    validity-versus-K curve, funnel); (4) Evaluation Results (loads the Phase 7 outputs:
    metrics, ablations, design target / measured / gap table); (5) About and Limitations.

All displayed numbers come from results files or live computation; none are hardcoded.

## Tests

streamlit.testing.v1.AppTest for every page (loads without exception, key widgets exist,
changing engine or cycle updates risk, editing a slider triggers re-validation, each triage
state renders, failure state renders); chart-builder unit tests (correct traces and titles,
empty or edge data handled); table-content checks; a Playwright smoke test if it installs
(optional); a test that the dashboard never imports training code at runtime; a test that
no number in the UI source is hardcoded.

## Gate

App starts with the project's dashboard command; a manual walkthrough on a real high-risk
engine shows recommendation, sliders, waterfall, tiers, triage and a failure path; screenshots
saved to docs/screenshots/; all checks green; PROGRESS.md updated.
