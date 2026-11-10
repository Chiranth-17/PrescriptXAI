# Dashboard acceptance status

The Phase 17 technical gate passed. Human usability and full Step 3B
acceptance remain pending. The registered dashboard machine is the NASA FD001
simulated archive. It uses demonstration limits, as does the Phase 13 toy test
fixture. Both have empty engineer confirmation blocks.

| Objective | Dashboard evidence | Verification | Status |
| --- | --- | --- | --- |
| Machine-scoped observed state | Registered machine, unit and recorded cycle | Simulator integration and browser preset selection | Passed locally |
| Calibrated risk and interactive controls | Fitted model risk after an edit; URL restores the settings | Simulator integration with retained FD001 assets | Passed locally |
| Case-study preset | FD001 unit 82, cycle 156, with 87.7% live predicted risk | Registered selection rule, browser capture and live AppTest comparisons for all four presets | Passed locally |
| Immutable features | Only declared adjustable settings can be overridden | Simulator API rejects a frozen feature | Passed locally |
| Advisory and stale-result guards | Input-bound FAST work, a 400 ms debounce and Alerts-only for an unclassified spec | Tests cancel queued work, discard a superseded running response and exercise all three limits statuses. | Passed locally for guards and job lifecycle |
| Validity, statistical plausibility, control limits and coupling | Four labeled checks in the demonstration prescription view | Fitted FD001 replay and toy status tests | Verified locally for demonstration |
| Sparsity, risk-drop badges and waterfall | Labeled badges and sequential calibrated scores | A replay test recomputes archived endpoints and verifies the changes add to the total. The demo renders current input-bound results. | Verified locally for demonstration |
| Timing and performance | Actual keyboard-to-risk and server scoring timings for all four FD001 presets at both widths | The repeated browser benchmark met 250 ms in one of eight groups. See [deviations](deviations.md). | Browser target missed |
| Applied outcome, trend and feedback | Live model recheck, configured adherence labels, same-unit trend and scoped SQLite log with seeded demo records | Tests cover adherence boundaries, deterministic interpolation, real FD001 trend re-scoring and backward-compatible log reads. The demonstration path is available for local checks. | Partial |
| Edited-settings comparison | A separately labeled recorded-settings reference for the exact same base input | Both risk values use independent checks. Edits clear current prescriptions. | Verified locally for demonstration |
| Scenario export | Standalone HTML with current settings, predicted risk and provenance | The HTML carries the active limits label and withholds stale results | Verified locally |
| Synopsis scorecard | Machine-scoped Advanced page with saved FAST alert and first-alert results | AppTest compares each displayed metric and serial latency interval with its saved source | Passed locally for archived results |
| Design and usability | Local desktop and phone captures, keyboard preset activation, slider editing and visible focus | Checked both widths and compared the supplied references. Full accessibility review and two participant sessions remain pending. | Partial |

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
not use one as advice. Slider edits still receive the risk preview. On a classified machine, a
comparison can show the previous prescription's risk and check count as a
reference only when its recorded-input hash matches the selected window. It
offers no current actions or follow-up for an edited input. The recorded-input
prescription and its report carry the active limits label.

An offline component test rechecks the registered FD001 candidate using the
fitted model, then renders the measured risk waterfall and applied-setting
comparison. It exercises the recorded trend and a temporary follow-up log.
The demo row appears only after opting in. These component checks do not
grant publication approval.

The waterfall test uses the archived case-study action controls and re-scores
each prefix with the same fitted model and coupling reference. It matches the
saved risk endpoints within an absolute probability tolerance of 1e-9. This
is an archival diagnostic. The FD001 page and export can publish an independently
checked current prescription with the demonstration label.

## Follow-up evidence

The application checks entered applied values with the fitted predictor and
the existing four independent checks. It compares model scores side by side,
separates the reported choice from the measured adherence label, and records
the reason if supplied. Replay context is stored in a versioned companion table
beside the existing feedback records. Older logs remain readable. The report
attaches a follow-up only when the current input, machine, unit, time, and
decision run and configuration match. The follow-up view also checks the machine's publication mode before showing
input or recording controls.

The trend re-scores up to 30 subsequent recorded windows for the selected
unit, or fewer when the archive ends. It compares the recorded inputs with
the same applied proxy settings and labels both series as model predictions.
Archive outcomes and labels appear separately when available. The archive
does not contain measured failure probabilities. Tests verify the time
boundary, the archive labels and the actual model predictions.

Demo rows are generated from seeded interpolation, independently scored,
labeled “Simulated operator (demo)” and excluded by default. The registered
FD001 replay keeps its demonstration label while eligible advice and follow-up
are displayed.

## Software-only coverage diagnostic

The diagnostic of `138d9ef` completed with 728 passing tests, one deselected
test, and 68 warnings in 249.71 seconds. It excluded the fixed subset and
full scientific replay. Coverage was 87.71% scoped lines, 86.83% package lines
and 83.75% combined. Both coverage checks failed and the wrapper exited 1.
The retained Phase 12 floors remain 91.01415094339623% scoped lines,
90.02682841479063% package lines and 86.64259927797833% combined.
Receipts and reports are in `artifacts/phase17/software-138d9ef`.

Both dashboard entrypoints reported zero coverage in the original run.
A mixed direct-script and imported AppTest run also reported zero for both.
Using the imported application entrypoints consistently in the same 27
AppTests recorded 101 lines and 24 branches for the legacy entrypoint and
159 lines and 29 branches for the simulator. The standalone browser check
still runs the shipped Streamlit entrypoint. These are targeted measurements
under `artifacts/phase17/coverage-entrypoint-20261110-v2`. A fresh
software-only package measurement at `a61d51a` passed all 729 selected tests
in 258.97 seconds and missed all three retained coverage floors. It measured
88.68% scoped lines, 87.80% package lines and 84.52% combined. The full run
still included two legacy AppTests launching the source file directly, and
recorded zero lines for that entrypoint. Those tests now use the same imported
entrypoint as the other workflows. Chromium still launches the shipped script.
The package receipt remains at `artifacts/phase17/software-a61d51a`.

The `a91e6b9` diagnostic ran 732 selected tests in 271.88 seconds, with one
deselected and 68 warnings. Both package floors passed at 90.33% lines and
86.98% combined. Scoped lines reached 90.25%, below the retained
91.01415094339623% floor. The Phase 9 gate and pytest exited zero. The Phase
12 gate and wrapper exited one. The receipt is
`artifacts/phase17/software-a91e6b9`. The fixed subset and full science
remained outside this diagnostic.

The diagnostic of `58cd33a` passed 733 tests and failed two Windows
multiprocessing tests. A temporary Streamlit AppTest entrypoint persisted as
the process main module. Spawned workers re-executed it and could not access
the parent's Streamlit session state. The simulator test fixture now restores
the pytest entrypoint. The triggering AppTest and both worker tests passed
together in the recovery check at
`artifacts/phase17/windows-apptest-spawn-recovery-v1`. The failed package
receipt and its 85.97% combined coverage are retained at
`artifacts/phase17/software-58cd33a`.

The recovery diagnostic at `7626483` passed 737 selected tests in 277.02
seconds, with one deselected and 68 warnings. It cleared all retained
floors at 91.03340496190663% scoped lines, 91.10337491538536% package lines
and 87.76066612629873% combined. Pytest, both coverage gates and the wrapper
exited zero. Evidence is in `artifacts/phase17/software-7626483`. This result
covers software tests. The fixed subset, full regression, controlled latency,
and the external acceptance requirements remain pending.

## Command-line workflows

`prescriptxai scenarios generate --output PATH` writes a new scenario
registration from the saved archive and refuses to replace an existing file.
With a named machine and matching protocol, `--profile` and
`--preview-cache PATH` also save input-bound risk previews. The cache
contains no prescription and does not change what the dashboard publishes.

`prescriptxai --machine MACHINE feedback add WINDOW --result RESULT
--applied VALUES` accepts the same inputs as the original form without
`add`. `feedback simulate WINDOW --result RESULT --seed SEED --count COUNT`
uses the same scoring and validation as the dashboard, and labels every
generated record as simulated. Both forms enforce the active limits mode.

## Controlled interactive timing

Run `preview-latency-20261110-v2` used source
`6a9ba75e352381f55afc9fd790a5afd7ebb1e7ed` and
`configs/experiments/phase17-preview-latency-v2.json`
(SHA-256 `3f979abf539faf8ff5fb7b2662925454929539419368e61e0c191c7bd874affe`).
It measured the four registered FD001 official-test XGBoost v1 presets in
Alerts-only mode. Active spec
`72d91ddb5ab7b415044060847c5934d7ce45b53e346600494f4d792c59dfff0d`,
protocol v1, `k_max=3`, `K=1`, `D_max=5.0`.
One local Chromium 143.0.7499.4 client used light theme on Windows, serially.
Each group has 20 measured edits and four retained warmups. The table gives
nearest-rank p50, p95 and maximum in milliseconds.

| Viewport | Recorded unit / time | Browser p50 / p95 / max | Server scoring p50 / p95 / max |
| --- | --- | ---: | ---: |
| desktop 1360 px | 82 / 156 | 338.4 / 372.8 / 396.8 | 20.1 / 23.3 / 26.8 |
| desktop 1360 px | 31 / 190 | 339.5 / 389.0 / 418.6 | 20.2 / 24.3 / 25.2 |
| desktop 1360 px | 76 / 205 | 338.1 / 396.8 / 400.0 | 21.9 / 23.7 / 23.9 |
| desktop 1360 px | 76 / 201 | 338.5 / 380.7 / 433.4 | 21.2 / 24.3 / 30.8 |
| phone 390 px | 82 / 156 | 337.1 / 364.4 / 406.2 | 19.4 / 24.7 / 25.5 |
| phone 390 px | 31 / 190 | 344.6 / 390.8 / 400.8 | 21.0 / 24.3 / 25.3 |
| phone 390 px | 76 / 205 | 335.7 / 385.1 / 402.1 | 21.6 / 24.6 / 25.6 |
| phone 390 px | 76 / 201 | 341.9 / 376.8 / 396.5 | 21.1 / 23.5 / 25.1 |

All eight browser p95 values exceeded the 50 ms target. Browser timing
covers the trusted keyboard event through the first frame that observes the
new settings and risk on the idle page. Server timing covers the
`simulate_risk` call, as shown in the dashboard caption. The measurement
does not allocate the remaining delay among input handling, transport,
server rerun work and browser rendering. It is separate from the archived
serial FAST measurements. Prescription and follow-up timing remain
unmeasured while the machine is Alerts-only.

The completed run exited zero and retained all 192 trials. A separate check
verified the 12 file hashes, recalculated all eight distinct model inputs and
matched every displayed score and timing summary. See
`artifacts/phase17/preview-latency-20261110-v2/{summary.json,trials.jsonl,verification.json}`.
The v1 runner stopped on a repeated endpoint key during warmup and its
receipt remains in `artifacts/phase17/preview-latency-20261110-v1`.

See [the repeated timing and remaining UI gap](deviations.md) for the demonstration run.

## Local verification before demonstration limits

The focused suite passed 86 tests in 66.96 seconds, including 19 simulator
tests. Ruff, mypy over 85 source files, and the strict documentation build
also passed. The full quality gate was outside that software checkpoint.

Chromium checked the [desktop](screenshots/phase17-simulator-desktop.png)
and [phone](screenshots/phase17-simulator-phone.png) layouts at 1,360 and 390
CSS pixels in both themes. [Dark desktop](screenshots/phase17-simulator-desktop-dark.png)
and [dark phone](screenshots/phase17-simulator-phone-dark.png) captures are
also saved. The browser receipts are
`artifacts/phase17/browser-20261110-v13-light/browser.json` and
`artifacts/phase17/browser-20261110-v13-dark/browser.json`. Both exited zero.
Each viewport verified offline operation, no horizontal overflow, Alerts-only
HTML export, and the keyboard edit from 87.7% to 92.1% with URL restoration.
All measured action buttons, selectors and expanders were at least 44 CSS
pixels tall. The preset text measured 14.24:1 contrast in light mode and
15.56:1 in dark mode. The preset and edited slider both showed visible keyboard
focus. The checks cover those controls. The external design comparison and
full accessibility review remain open.

Earlier receipts include the v3 tooltip timeout, v7 and v9 attempts that
targeted the recorded-time slider instead of an adjustable setting, the v8
port reservation refusal, the v12 selector probe that matched no controls,
and Windows connection resets during browser teardown.
The first focused run found adherence defaults in the UI module. The final
run passed the original hardcoded-results guard after the defaults moved
to typed configuration.

## Demonstration-mode verification

Chromium verified the live demo chip, the About label and scenario downloads
at 1,360 and 390 CSS pixels. The registered case rendered an 87.7% predicted
risk and a current 15.0% model prediction with the prescription. A keyboard
edit changed the risk to 92.1%, cleared the current prescription and follow-up
and restored the edited risk on reload. The
[desktop](screenshots/phase17-demonstration-desktop.png) and
[phone](screenshots/phase17-demonstration-phone.png) captures are local renders.
The browser receipt and exports are in
`artifacts/phase17/browser-20261110-v14-demonstration`.

Software-only verification at `bbe8142b99e0c388019af2676d1c9fb2e86ef396`
passed 739 tests in 316.73 seconds, with 68 warnings and the full marker
deselected. The fixed subset was excluded from this diagnostic. Coverage was
91.4413104584666% scoped lines, 91.50834772596431% package lines and
88.26627651792246% combined.

## Fixed-subset gate

`mingw32-make check REUSE_ONLY=0` at
`735cc4bf40c4f27cb36d6461b3dcdc921d632c97` ran for 13,487.87 seconds
(3 h 44 min 48 s) on November 10, 2026. Ruff and mypy passed. Pytest reported
740 passed, 1 deselected and 68 warnings. Both coverage gates passed at
91.4413104584666% scoped lines, 91.50834772596431% package lines and
88.26627651792246% package combined. Make and the wrapper exited zero.

The registered subset recomputed all 15,525 cases in 23 groups, with zero reuses.
The receipt lists zero float-exact differences and zero accepted exceptions.
The read-only record count matched the requested count. Full regression is
reserved for the release gate.

- Run and coverage receipts: `artifacts/phase17/fixed-subset-check-20261110-v1`
- Subset comparison: `artifacts/regression-tiers/check-20261110T064255542551Z-48236/complete.json`
- Context SHA-256: `d064d495a6383f3b2fdb1f8040ab479147294d4d1ffec7f23fdaaf3011d1878e`

## Human tasks for dashboard acceptance

The supplied desktop and phone mockups are in the [design comparison](design_diff.md).
Their values are illustrative. The live captures and benchmark receipts report
the measured values.

Run two separate sessions of about ten minutes with participants new to the
project. Each session includes two minutes of unassisted free use. Record their
observations and task outcomes using the [facilitator kit](usability_notes.md).
The timed explanation and usability findings remain pending while the
technical roadmap proceeds.

[Design comparison](design_diff.md) · [Usability notes](usability_notes.md)
