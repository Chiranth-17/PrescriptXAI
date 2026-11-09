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
| Advisory and stale-result guards | Alerts-only for missing confirmation, input binding and invalid-input withholding | Simulator integration and browser absence of a prescription control | Passed locally |
| Validity, statistical plausibility, control limits and coupling | Four labeled checks in the confirmed prescription view | Available archive remains in Alerts-only mode | Pending end-to-end acceptance |
| Sparsity, risk-drop badges and waterfall | Sparsity caption implemented | Full badges and measured attribution pending | Partial |
| Timing and performance | Local risk timing in the risk card | Controlled latency and full stage budgets pending | Partial |
| Applied outcome, trend and feedback | Applied settings can be rechecked and logged for a confirmed prescription | Full workflow, trend and simulated operators pending | Partial |
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

## Local verification

The focused suite passed 71 tests in 33.19 seconds, including nine simulator
tests. Ruff, mypy over 81 source files, and the strict documentation build
also passed. The full quality gate and the controlled latency suite were
outside this checkpoint.

Chromium captured the [desktop](screenshots/phase17-simulator-desktop.png)
and [phone](screenshots/phase17-simulator-phone.png) layouts at widths of 1,360
and 390 CSS pixels, with no horizontal overflow, external requests or
browser page errors during the check. The browser receipt is
`artifacts/phase17/browser-20261110-v4/browser.json` and the native exit is
zero. Earlier captures and the tooltip timeout in v3 are retained. The v4
server log contains a Windows connection reset during browser teardown.

[Design comparison](design_diff.md) · [Usability notes](usability_notes.md)
