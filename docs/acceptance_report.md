# Dashboard acceptance status

Phase 17 and Step 3B are in progress. The registered dashboard machine is the
NASA FD001 simulated archive. Its engineer confirmation block is empty.
The Phase 13 toy remains a framework test fixture.

| Objective | Dashboard evidence | Verification | Status |
| --- | --- | --- | --- |
| Machine-scoped observed state | Registered machine, unit and recorded cycle | Simulator integration and browser preset selection | Passed locally |
| Calibrated risk and interactive controls | Fitted model risk after an edit; URL restores the settings | Simulator integration with retained FD001 assets | Passed locally |
| Case-study preset | FD001 unit 82, cycle 156, with 87.7% live predicted risk | Registered selection rule and browser capture | Passed locally |
| Immutable features | Only declared adjustable settings can be overridden | Simulator API rejects a frozen feature | Passed locally |
| Advisory and stale-result guards | Input-bound FAST work, a 400 ms debounce and Alerts-only for missing confirmation | Tests cancel queued work and discard a superseded running response. Chromium verifies withholding. | Passed locally for guards and job lifecycle |
| Validity, statistical plausibility, control limits and coupling | Four labeled checks in the confirmed prescription view | Available archive remains in Alerts-only mode | Pending end-to-end acceptance |
| Sparsity, risk-drop badges and waterfall | Confirmed-view badges and sequential calibrated scores | A replay test recomputes archived endpoints and verifies the changes add to the total. Confirmed rendering remains pending. | Partial |
| Timing and performance | Risk preview time and measured prescription stages beside configured budgets | Controlled browser and serial latency remain pending | Partial |
| Applied outcome, trend and feedback | Existing applied-setting recheck and local log. The summary scopes rows by machine, spec and protocol. | Demo rows excluded by default and shown separately when requested. Full follow-up, trends and seeded generation remain pending. | Partial |
| Scenario export | Standalone HTML with current settings, predicted risk and provenance | Downloaded at both widths and matched to the displayed Alerts-only case study | Passed locally for Alerts-only |
| Synopsis scorecard | Machine-scoped Advanced page with saved FAST alert and first-alert results | AppTest compares each displayed metric and serial latency interval with its saved source | Passed locally for archived results |
| Design and usability | Local desktop and phone captures | Published mock and two participant sessions pending | Partial |

The four scenario presets were generated from the saved
`phase7-20261020T102540Z` FD001 XGBoost v1 FAST official-test results.
The selection configuration `configs/experiments/phase17-dashboard-v1.yaml` was committed before
generation at `18f60c6fcec38bf6ceb607b9c128b331cfad85b6`. Its SHA-256 is
`679e5f88abddf11474055f324ccd216b2c3758aed301d0a5a162f2329b5a48b3`.
The saved source results SHA-256 is
`d4ffef41bccc178c7021320b318f225c75fdcf140e87a2bc34749cb18a5ab51f`.

## Archived objectives and gaps

The Advanced scorecard loads the retained Phase 7 summary from the configured
report directory. Its all-alert and first-alert columns use the same FAST
mode. Each interval preserves the number of engines and the denominator.
The historical labels retain the source and config hashes. The current
machine spec hash is shown separately because the study predates named
machine specs. Missing first-alert metrics remain absent.

For example, the default archived FD001 LSTM v1 official-test group had
0.0% calibrated model validity against a 95% design target and 31.2%
all-query plausibility against 90%. Mean predicted risk dropped 11.2 points
against a 60-point design target. Those all-alert estimates use 16 engines
and 690 observations, including the original saved seeds. The first-alert
stratum uses 16 engines and 80 observations. These are historical benchmark
gaps for that model and population. The live simulator case study uses a
separately selected FD001 XGBoost v1 profile.

The saved FAST serial optimization p95 was 2,339.1 ms against a 1,800 ms
budget and the backend pipeline p95 was 2,348.2 ms against 2,200 ms.
These are separate measurements from the development population. Browser
rendering was unmeasured in that serial report.

## Publication and replay limits

The simulator cancels delayed or queued requests when their input hash changes.
If the numerical call has already started, it may finish on the isolated worker.
Its result is discarded. The simulator publishes only an exact current result.
A nearby cached candidate could describe different settings, so the view does
not use one as advice. Operator slider edits still receive the risk preview.
Prescription comparison with edited settings and the full confirmed browser
flow remain pending.

The waterfall test uses the archived case-study action controls and re-scores
each prefix with the same fitted model and coupling reference. It matches the
saved risk endpoints within an absolute probability tolerance of 1e-9. This
is an archival diagnostic. The FD001 page and HTML export show only the current
risk and withholding message.

## Local verification

The focused suite passed 75 tests in 38.11 seconds, including 13 simulator
tests. Ruff, mypy over 84 source files, and the strict documentation build
also passed. The full quality gate and the controlled latency suite were
outside this checkpoint.

Chromium captured the [desktop](screenshots/phase17-simulator-desktop.png)
and [phone](screenshots/phase17-simulator-phone.png) layouts at widths of 1,360
and 390 CSS pixels, with no horizontal overflow, external requests or
browser page errors during the check. The browser receipt is
`artifacts/phase17/browser-20261110-v5/browser.json` and the native exit is
zero. Both downloads contain the same 87.7% risk and Alerts-only label, with
identical HTML SHA-256. Earlier captures, the tooltip timeout in v3 and
Windows connection resets during browser teardown remain in the run logs.

[Design comparison](design_diff.md) · [Usability notes](usability_notes.md)
