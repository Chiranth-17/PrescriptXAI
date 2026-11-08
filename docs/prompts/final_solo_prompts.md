# PrescriptXAI: FINAL prompts, all in one file (paste in order)

For one person with a coding agent, after Phases 1-11. This file is the only one you need. It merges the solo plan and the dashboard addendum. Older prompt files are superseded.

## Paste order

| Paste | What | Where in this file |
|---|---|---|
| 0 | The 8 rules into AGENTS.md (once) | "Rules" |
| 1 | Close Phase 12 + fast and slow tests | Step 1 |
| 2 | Generic framework | Step 2 |
| 3 | Dashboard | Step 3 |
| 4 | Dashboard objectives and acceptance script | Step 3B |
| 5 | Security (lite) | Step 4 |
| 6 | Packaging (lite) | Step 5 |
| 7 | Audit, viva, report, release | Step 6 |

Paste one at a time. Let the agent finish. Read only its final message. While a long job runs, check at most once an hour. Step 1 starts only after the current clean-clone gate has finished.

Before Step 3: take two screenshots of the design mock "PrescriptXAI Operations Dashboard" (1360 px and 390 px wide) and save them as `docs/design/dashboard_mock_desktop.png` and `docs/design/dashboard_mock_phone.png`.

## The plan

| Step | What you get | Rough effort* | Stop here and you have |
|---|---|---|---|
| 1 | Phase 12 closed, fast tests, trusted baseline | 1-2 days | A reproducible result base |
| 2 | Generic framework: spec files, CSV adapter, minimal data checks, toy second machine | 3-4 days | A project that is not tied to one dataset |
| 3 | The simple, good-looking simulator dashboard with feedback | 3-4 days | The full demo |
| 4 | Security (lite) | 2 days | Your cybersecurity branch shown |
| 5 | Packaging (lite): Docker, `make demo`, README | 1-2 days | Anyone can run it |
| 6 | Audit, viva questions, report, demo script, release | 2-3 days | Submission-ready |

*Rough guesses for one person using an agent. Treat them as guides.

How to work: paste one step at a time, let the agent finish, read only its final message. While a long job runs, check at most once an hour.

## What is deliberately left out (say so as future work)

Plant connectors (SQL, OPC UA, MQTT), an approval workflow and audit chain, onboarding wizard, drift monitoring, a model registry, a synthetic pump simulator and a second real machine. They are designed in `prescriptxai_final_prompts_12_to_19.md` if you ever need them. In your report, write: "Designed but not built: ..." That is honest and fine.

---

## Rules (paste once into AGENTS.md; keep rules 1-29)

```text
30. ADVISORY ONLY. The system recommends; a human decides. It never writes to a machine or control system.
31. MACHINE-AGNOSTIC CORE. src/prescriptxai/core has no dataset, machine or sensor names. Machine details live in spec files and adapters. A test enforces it.
32. TESTED-ONLY CLAIMS. Name the machines tested. Never write "works on any machine", "proven", "certified" or "extends engine life".
33. FAIL SAFE. If data is bad or a check fails, show "Recommendation withheld: <reason>".
34. LABEL SYNTHETIC AND SIMULATED DATA everywhere (tables, charts, exports, UI).
35. DETERMINISTIC AND TIERED TESTS. Fixed seeds; iteration budgets for search (wall-clock only for reporting). `make check` is fast; the full regression runs only before a tag. Do not run the full regression more than once per phase unless production source changed.
36. NO POOLED NUMBERS. Results are per machine, with machine id, spec hash, protocol version, run id, K and population on every table.
37. LIMITS NEED AN ENGINEER. Bounds, step limits and the failure definition have an "engineer confirmed by / date" field in the machine spec. Empty means the machine runs in Alerts-only mode.
Send a short status with real numbers after every phase.
```

---

## Step 1: Close Phase 12 and fix the test cost

Run this after the current clean-clone gate finishes. Do not start any new run before then.

```text
PHASE 12 FAST CLOSE. Time box: about 4 hours of work. No new full replay of 32,116 cases.
Use the finished clean-clone gate output and the audit's list of 712 mismatches as they are.

1. SPLIT the 712 into (a) the 15 Tier 2 flips plus 3 triage flips, and (b) the rest.
2. FOR GROUP (a), for each case: record the margin to the threshold; rerun that query three times in fresh processes, with one thread and with the default thread count; score the same saved candidate with the production scorer and the audit scorer. Classify each as: borderline float difference (margin below tolerance), search nondeterminism (different candidates), or scoring-definition difference.
3. FOR GROUP (b): summarize by field and largest absolute and relative difference. If all are within the float tolerance, label them float noise. If not, list the fields and test the cause on a sample of 50 cases only.
4. FIX only what group (a) shows. Nondeterminism: fixed seeds, iteration-count budgets instead of wall-clock stopping, stable tie-breaking. Scoring difference: align the wrong scorer to the written definition. Borderline: add a "borderline" flag and report it separately, never rounded silently.
5. BASELINE = KNOWN-DIFFERENCES LIST. Write tests/regression/known_diffs.json (case id, field, saved value, accepted value or range, reason). The regression test passes only if every difference from the saved records is on this list and no other difference exists.
6. TIER THE GATES and document them in docs/testing.md (what each proves and does not prove):
   - `make check` (fast, target under 10 minutes): ruff, mypy, unit and contract tests, and a regression SUBSET: a fixed seeded stratified set in tests/regression/subset_ids.json with its hash, containing all 712 cases, all borderline cases, and a fixed number of cases from each stratum (mode, population, triage, risk band).
   - `make regression-full`: all 32,116 cases, resumable. Each saved case result is keyed by a hash of the result-affecting source files + config + data hash + case id; reuse an entry only on an exact key match; log reused versus recomputed counts; missing assets must fail, never skip.
   - `make release-gate`: `make check` plus `make regression-full`. Keep `all-checks` as an alias for `make check`.
   Failure workflow: rerun only failed tests first (`pytest --lf -x`), fix, then `make check`.
7. IMPACT: show how many headline counts the 18 cases change, with the confidence interval. Rerun the full evaluation as a new run id only if the fix changed the search itself, and schedule that single run at the end of the phase.
8. CLOSE: update the open-item ledger and docs/state_of_project.md. Unexplained group (b) items become "Phase 12b" entries, not blockers. Run `make check`, commit and tag phase12-closed.
Reply with: classification of the 18, whether group (b) is float noise, what changed in the headline numbers, the timings of each make target, and the commit hash.
```

---

## Step 2: Generic framework

```text
PHASE 13: GENERIC FRAMEWORK (solo version).
Read AGENTS.md, PROGRESS.md, features.yaml, the frozen RecourseResult schema, the core code and tests/regression.

NON-NEGOTIABLE
G1. The C-MAPSS regression (known-differences policy) passes after every step. If anything new differs, explain before continuing.
G2. src/prescriptxai/core imports no machine. A test greps core for dataset, machine and sensor names ("C-MAPSS", "FD001", sensor ids, "engine", "turbofan") and fails on any hit.
G3. Schema changes are versioned with a migration (old rows get machine_id = "cmapss_fd001").

TASKS
T1. MACHINE SPEC (pydantic, versioned): configs/machines/<id>/machine.yaml with: identity (id, display name, unit word and plural, data source and license note, synthetic flag); features (id, friendly label, SI unit, role in {sensor, controllable, frozen}, bounds, per-step limit, plain-language "why" template, coupling group); failure definition (horizon H, label source, tau_safe, tau_danger); validation settings (plausibility thresholds by protocol version, coupling groups and residual limit, step-limit assumption, intervention horizon K); triage thresholds; k_max; FAST and THOROUGH latency budgets; "engineer confirmed by / role / date" block; sentence templates. Convert the C-MAPSS configuration into configs/machines/cmapss_fd001/machine.yaml with no change in values.
T2. ADAPTERS (src/prescriptxai/adapters/): a base interface with load() -> one standard long table (unit id, time index, features, optional event or remaining life), split(seed) by UNIT with a leakage audit, failure_labels(H). Implement CmapssAdapter (moved code, no logic change) and TabularAdapter: bring-your-own CSV or Parquet configured only through machine.yaml column mappings. Registry, `--machine` flag on every CLI command, API prefix /machines/{id}/..., GET /machines.
T3. CORE REFACTOR: solver, four validity tiers, calibration, triage, FAST and THOROUGH modes, feedback and explain_result read a MachineSpec and a dataset handle instead of C-MAPSS constants. Rename "engine" to "unit" inside the core. Add machine_id and spec_hash to RecourseResult and the feedback log.
T4. MINIMAL DATA CHECKS (rule 33): a small module that scores an input window and returns reason codes for missing values, NaN or infinity, out-of-range values, stuck sensors and timestamp gaps; thresholds in the spec. If the check fails, the pipeline returns "Recommendation withheld: <reason>". Fault-injection tests: inject each defect into clean data and show it is flagged and the pipeline withholds.
T5. CONTRACT TESTS parametrized over registered machines: spec validates; no unit in two splits; labels match the failure definition; candidates respect bounds and step limits; frozen features never change; verdicts equal direct library calls; FAST and THOROUGH agree where both succeed; triage covers every case; adherence on constructed cases.
T6. PROOF AND DOCS: a throwaway toy machine (machine.yaml plus a small generated CSV, defined inside the tests) runs train, score, prescribe, check and feedback without touching core; record the lines it needed. Add templates/new_machine/ and docs/adding_a_machine.md (what an engineer must decide: which settings can be changed, bounds, step limits, failure definition, horizon, related sensors; limits need engineer confirmation).

Gate: G1 and G2 pass; contract suite passes for cmapss_fd001 and the toy machine; `make check` green; PROGRESS.md updated; commit and tag phase13-closed.
Reply with: regression result, registered machines, lines needed for the toy machine, `make check` time, commit hash.
```

---

## Step 3: The dashboard (simple, good-looking, simulator)

Reference: the published design mock "PrescriptXAI Operations Dashboard". Take screenshots at 1360 px and 390 px and save them to `docs/design/dashboard_mock_desktop.png` and `dashboard_mock_phone.png` before you paste.

```text
PHASE 17 (solo): FINAL DASHBOARD. Single-page simulator: set conditions -> see risk -> get prescription -> record whether it was followed.
Read AGENTS.md, the RecourseResult schema, the machine spec, the data-check module and the existing dashboard. Compare with docs/design/dashboard_mock_*.png. Do not delete analysis pages: move them under "Advanced". NOT in scope: approval workflow, onboarding wizard, drift pages, a fifth simulator check.

RULES
R1. Every figure comes from the real model, result files or live computation. A test scans the main-page source and fails on hardcoded numbers (the mock's numbers are placeholders).
R2. Simulated-operator rows are labeled "Simulated operator (demo)" everywhere and excluded from real statistics by default.
R3. Plain language on the main page. No Mahalanobis, tier, surrogate, protocol or k_max; technical names only in tooltips and Advanced.
R4. Never claim extra engine life or physical proof. Say "predicted risk" and "model-based checks".
R5. Accessible and responsive: colour-blind-safe (blue, amber, vermilion, always with text or icon), contrast at least 4.5:1, controls at least 44 px, keyboard use, every slider has a visible label and value, works at 390 px.
R6. Offline: bundle fonts (IBM Plex Sans and Mono) or use a system stack; no runtime network calls.
R7. Stale-result safety: every result carries a hash of its inputs; a result whose hash no longer matches the sliders is never shown as current.

LOOK (from the mock)
Page background #F3F5F8; white cards with 1 px #DDE3EA border and 12 px radius; ink #17212B; muted text #566474; accent blue #1D4ED8 for actions and "after" values. Status colours: safe or pass #0B5F6E on #E3F3F5; watch #6B4400 on #FFF2CF; alert or fail #A8310F on #FCE9E2. Large risk numbers in IBM Plex Mono; step numbers in blue circles; pills for status; a dark theme with matching tokens. If Streamlit cannot reproduce this look, you may build the page as a static HTML and JavaScript front end served by FastAPI that calls the same API; then replace AppTest with Playwright tests covering the same cases.

LAYOUT (one page; panels stack on narrow screens)
Header: product name, one-line purpose, MACHINE SELECTOR (from GET /machines; labels, units, slider ranges and wording come from the machine spec; choice kept in the URL), and a chip from the spec: "Sample data - replay of NASA C-MAPSS engines" or "Synthetic or sample machine". A MODE note: if the spec has no engineer confirmation, show "Alerts only: limits not yet confirmed by an engineer" and do not show prescriptions.
Scenario bar: preset buttons generated by a script from real saved states (one per triage state when available; named for what the state is), plus Reset and Copy link (all slider values in the URL query string).

STEP 1 SET THE CONDITIONS (left card). The base state is a real (unit, time) from the presets or a selector; it supplies every sensor the user does not override. Group "Situation (fixed)": cycles flown (moves along the unit's real trajectory) and context features. Group "Current settings (the operator can change these)": one slider per adjustable feature, bounded by the spec; under each slider the prescription changes, show "Recommended: <value> (<% change>)". Slider ranges come from data percentiles, never hardcoded. Moving a slider updates dependent sensors through the coupling model. If the user-built state is unusual compared with real data, show an amber banner: "This combination of conditions is unusual for real equipment. The risk estimate may be less reliable." A flag, not a block.

STEP 2 PREDICTED RISK. Large "Risk now" (calibrated model, colour plus text), an arrow and "With the prescription", one plain sentence from explain_result, a triage badge (No action needed, Fixable now, Partly fixable, Needs maintenance) and a Safe/Watch/Alert meter with Now and After markers. Risk now updates instantly while sliders move (target under 50 ms).

STEP 3 PRESCRIPTION. One to three rows: name, from -> to, % change, a track inside the allowed range, and a "Why" line that reports how many points of predicted risk that single change removes (measured with the real model) plus a template sentence from the spec. A line "Not changed: ..." for fixed features. Four safety-check rows (pass or fail icon plus text and a plain hint): Predicted safe; Looks like normal behaviour; Within control limits; Sensors stay consistent. States: no action needed; fixable; partly fixable ("schedule an inspection"); needs maintenance ("Setting changes cannot make this safe. Plan maintenance." with a log-only "Schedule maintenance"); WITHHELD ("Recommendation withheld: <reason>" for bad data or failed checks). "Try your own change": the user edits the settings by hand and sees "Your settings: risk X%, checks n of 4" beside "Prescription: risk Y%, checks 4 of 4". COMPUTE STRATEGY: instant tier (risk only); FAST tier after a 400 ms pause with a "Calculating..." state and cancellation of superseded solves; if the budget is exceeded, show a cached nearby result with a "cached" badge.

STEP 4 WAS IT FOLLOWED? (full-width card). Buttons "Followed as recommended", "Followed partly", "Not followed" plus sliders for the applied value of each recommended setting; "Not followed" takes an optional reason. ADHERENCE: a_j = clip(1 - |applied_j - recommended_j| / max(|recommended_delta_j|, eps), 0, 1); adherence = mean of a_j; labels from config: Followed >= 0.80, Partly 0.40-0.80, Not followed < 0.40; one bar per action. OUTCOME: re-score the APPLIED state with the real model and rerun the checks; show "Risk after applied settings" beside the prescription's risk and "Checks passed: n of 4". TREND CHART: predicted risk over the next 30 cycles, "No intervention (model prediction)" versus "With the applied settings (model prediction)", dashed safe and alert levels; for replayed units add a third line "Observed in the recorded data". "Record this follow-up" appends to the log. FOLLOW-UP LOG: scenario, result, adherence, risk before -> after, source ("Operator (this session)" or "Simulated operator (demo)"), scrolling sideways on phones. A "Simulate operators" control (sidebar) draws seeded compliance, builds applied states by interpolation and scores them with the real model and checks.

FOOTER: SDG 9 line and one button "About this view and how it was checked": data source, what the checks mean in plain words, assumptions (model-based, benchmark data, step limit and intervention horizon, proxies for controls), what a real deployment would add, the simulated-operator note, protocol version, run id, config hash.

ADVANCED (sidebar): the existing analysis pages, evaluation results per machine, About and limits.

BACKEND: POST /simulate/risk (instant), POST /simulate/prescribe (FAST, cancellable, returns input hash), GET /machines, GET /machines/{id}/spec, GET /machines/{id}/scenarios, POST /feedback, GET /feedback/summary. CLI: scenarios generate (writes configs/machines/<id>/scenarios.yaml from saved results and precomputes a cache), feedback add, feedback simulate. "Download scenario report": one-page HTML with sliders, risk, prescription, checks, follow-up, labels and run ids.

TESTS: page loads for every registered machine; each preset renders; moving a slider updates risk immediately; stale results never show; every state above renders (including withheld and Alerts-only); the unusual-combination banner appears for an implausible combination; "Try your own change" shows both columns; URL round trip restores state; adherence on constructed cases (exact = 1.0, opposite = 0.0, half = 0.5) and label boundaries 0.40 and 0.80; outcome uses the real model; per-action risk contributions sum to the total drop within tolerance; frozen features never change; slider bounds equal spec bounds; hardcoded-number scan; banned-jargon scan; no machine or feature name hardcoded in dashboard source; simulated rows labeled and excluded by default; works offline; instant tier under 50 ms and FAST tier within budget on the presets; screenshots at 390 px and 1360 px saved to docs/screenshots/ and compared with the mock in docs/design_diff.md.

GATES
1. USABILITY: two classmates use the page for 2 minutes with no help; record what they said and where they hesitated in docs/usability_notes.md; fix what confused them.
2. EXPLAIN TEST: you explain the four steps in 60 seconds using only the page.
3. DESIGN DIFF: list differences from the mock; fix or justify each.
4. `make check` green; commit and tag phase17-closed.
Reply with: screenshots, usability notes, test counts, `make check` time, commit hash.
```

---

## Step 3B: Make the dashboard meet every synopsis objective (paste right after Step 3)

Run this in the same session as Step 3 or straight after it. It adds the waterfall chart, the sparsity and risk-drop badges, the timing strip, the case-study preset and the objectives scorecard, then makes the agent run the app and fix it until an acceptance script passes.

### What each objective looks like on the dashboard

The dashboard meets an objective when it **demonstrates it with real computation**. It does not meet it by showing numbers that were not measured. Here is what that looks like:

| Synopsis objective | What the dashboard shows | Where |
|---|---|---|
| Sparse: at most 3 changed parameters | "2 of 3 allowed changes" badge on the prescription | Step 3 |
| Risk reduction of 0.60 or more | "Risk drop: 71 points (target 60+)" badge, ticked when met | Step 3 |
| Valid: predicted risk at or below 0.20 | "Predicted safe" check and the After value | Steps 2, 3 |
| Plausible (Mahalanobis within D_max) | "Looks like normal engine behaviour" check | Step 3 |
| Engineering bounds and rate limits | "Within control limits" check, tracks inside allowed ranges | Step 3 |
| Sensor coupling rules | "Sensors stay consistent" check | Step 3 |
| Immutable features frozen | "Not changed: altitude, speed, ..." line; frozen sliders cannot change the prescription | Steps 1, 3 |
| Waterfall impact chart | Risk waterfall: Now, then each change's drop, then After | Step 3 ("Why this?") |
| Interactive sliders, risk-reduction deltas | Sliders in Step 1, "Recommended" markers, delta badges | Steps 1, 3 |
| Latency budget (about 1.5-2.2 s end to end) | "Computed in 1.4 s" with a per-stage timing strip | Step 3 |
| Case study (88% to a safe state) | A "Case study" preset chosen by a fixed rule from real states | Scenario bar |
| Feedback: was it followed? | Step 4 | Step 4 |
| Overall validity, plausibility, triage rates | "Objectives scorecard" with measured values, targets and CIs | Advanced |

### Prompt (Step 3B)

```text
DASHBOARD OBJECTIVES AND ACCEPTANCE. Apply on top of the Phase 17 dashboard prompt. Read the synopsis objectives table in docs/traceability.md (or docs/synopsis_objectives.md if present) and the existing dashboard.

PRINCIPLE: every objective is demonstrated with real computation. No hardcoded or typed-in results, no random outcomes presented as real, no thresholds changed to pass a target. If a measured value is below target, show the measured value.

A. ADDITIONS TO THE MAIN PAGE
A1. SPARSITY AND DROP BADGES in Step 3: "N of K allowed changes" (K from the spec's k_max) and "Risk drop: X points (target: from config)". A badge shows a tick when the target is met and a neutral note when not; never colour a miss as a pass.
A2. WATERFALL CHART in Step 3 under a "Why this?" expander: bars Now -> one bar per change showing the risk points that change removes (measured by applying the changes one at a time in order of size with the real model) -> After. The bars must sum to the total drop within tolerance (test it). Chart text uses theme tokens and works in both themes.
A3. TIMING STRIP: "Computed in X s" with a tooltip listing measured stage times (ingestion, model inference, optimization, validation, rendering) next to the budget from the spec. Timings are measured, not typed. If the budget is exceeded, show the measured value and the cached badge when a cached result was used.
A4. CASE-STUDY PRESET: a script picks the real first-alert state whose calibrated risk is closest to 0.88 among states with at least two prescribed changes; store its id and the selection rule in configs/machines/<id>/scenarios.yaml. Name it "Case study (selected by rule)". Never hand-pick.
A5. DEMO PRESETS: a script picks presets by a written rule (for example, first alert per engine ordered by risk drop, with at most 3 changes; one per triage state when available) and records the rule in scenarios.yaml. The scenario bar shows "Examples selected by rule" in a tooltip.
A6. FROZEN FEATURES: the situation sliders (altitude, speed, ambient values, cycles flown) update the risk but are never changed by the prescription; a test asserts it.

B. ADVANCED: OBJECTIVES SCORECARD
A page listing each synopsis metric with its target, the measured value, the engine-bootstrap confidence interval, the population (early warning and all alerts), the run label (machine id, spec hash, protocol version, run id), and a plain one-line explanation for any value below target. Include: validity (target 95%), plausibility (90%), sparsity (at most 3 changed parameters), risk reduction (0.60 drop), latency budget per stage, and triage rates. All values load from the result files. A test fails if any number on this page is not found in a result file.

C. STREAMLIT NOTE
The synopsis names Streamlit. Prefer Streamlit with custom CSS or components to reach the look in docs/design/. If Streamlit cannot meet the look and the acceptance tests, you may serve a static HTML front end from FastAPI; record the reason in docs/deviations.md so the report can explain it.

D. MAKE IT WORK: ACCEPTANCE SCRIPT
D1. Start the app and drive it with a scripted browser (Playwright, or AppTest if Streamlit) through this path for every registered machine: open page -> choose a preset -> read risk -> move a settings slider and see risk update -> see the prescription, the four checks, the sparsity and drop badges and the waterfall -> open "Why this?" -> try your own change and compare -> record "Followed partly" with applied values -> see adherence, risk after applied settings and the trend chart -> record the follow-up and see it in the log -> run "Simulate operators" and see labeled rows -> open Advanced scorecard and check every number against the result files -> reload the URL and see the same state.
D2. States to cover: no action needed; fixable; partly fixable; needs maintenance; withheld (bad data injected); Alerts-only (no engineer confirmation in the spec).
D3. Run the script, fix every failure at its root cause, rerun, and repeat until it passes. Save the passing run's screenshots at 1360 px and 390 px in docs/screenshots/ and the script output in docs/acceptance_report.md with a table: objective, dashboard element, test name, result.
D4. No test may be skipped, mocked with toy data or loosened to pass. Use `make check` while iterating; run the full regression only if production source changed.

E. GATES
1. docs/acceptance_report.md shows every objective in the table above with a passing test.
2. You can explain each screen in 60 seconds.
3. Commit and tag dashboard-accepted.
Reply with: the acceptance table, screenshots list, any value below target (with its explanation), and the commit hash.
```

---

## Step 4: Security (lite)

```text
PHASE 16 (solo, lite): SECURITY. Do only S1, S2, S3, S4 (small), S5 and S7. Everything else in this prompt is out of scope.
Read AGENTS.md (rules 30, 33). Context: industrial settings. Treat IEC 62443 ideas as guidance only; never claim compliance.

S1. THREAT MODEL (docs/threat_model.md, STRIDE): data-flow diagram and trust boundaries for data input, API, dashboard, stored feedback and exports. Rate each threat, list mitigations and tests, mark residual risk. Include: sensor spoofing, replayed or stale data, poisoned training data, tampered model file, tampered feedback log, unauthorized user.
S2. AUTH: authentication required by default (strong password hashing), short-lived tokens, secure cookies and CSRF protection for the dashboard, session timeout, login rate limiting. Secrets only from environment or a secret file; startup refuses default credentials. Roles: operator (view, record follow-up) and admin (users, models).
S3. API HARDENING: strict validation with size limits; reject NaN and infinity; schema-based fuzzing (Hypothesis or Schemathesis) on every endpoint; one error format with no stack traces; locked-down CORS and security headers.
S4. SPOOFING TEST (small): for a sample of states, search within plausible ranges for sensor changes that make the system output a prescription the four checks judge unsafe. Report the attack success rate and which checks caught the rest. Report honestly even if some succeed, and list them in docs/limitations.md.
S5. SUPPLY CHAIN: pinned dependencies; pip-audit; Bandit; secret scanning (detect-secrets or gitleaks); SBOM (CycloneDX); SHA-256 checksums for trained model files, verified when loaded (refuse a modified file).
S7. docs/safety_case.md (claims, arguments, evidence): claims limited to advisory use, fail-safe behavior and traceability; hazards (wrong recommendation accepted, ignored alert, spoofed data, stale model) with mitigations and test evidence. State clearly it is not a certified safety case.
`make security` runs the scans and security tests and fails on any high or critical finding without a dated, documented exception.

Gate: every high threat has a mitigation and a test; fuzz tests pass; `make check` and `make security` green; commit and tag phase16-closed.
Reply with: scan summary, spoofing success table, commit hash.
```

---

## Step 5: Packaging (lite)

```text
PHASE 18 (solo, lite): PACKAGING. Do only P1, P2, P3, P6 and P10 below. Out of scope: metrics, drift, registry, nightly CI.
The developer uses Windows with uv and mingw32-make; keep Windows parity.

P1. Package: pyproject with optional extras (api, dashboard, dev); one version source; CLI entry point `prescriptxai`.
P2. Docker: one image for API and dashboard; docker-compose with volumes for models, data and logs, healthchecks, restart policy and an env-file template; non-root user, read-only root filesystem where possible.
P3. Configuration through environment variables with a documented table; clear startup messages when it is wrong.
P6. `make verify` (lint, types, `make check`, security, build, smoke test) and `make demo`, which starts the API and dashboard with sample data for the C-MAPSS machine and the sample CSV machine in one command. Both must work from a clean clone using only the README, on Windows (mingw32-make) and Linux.
P10. README: five-minute quickstart, architecture diagram (core, adapters, specs, API, dashboard), "use it on your own machine" section pointing to docs/adding_a_machine.md, honest "tested on" and "not built yet" lists.

Gate: a fresh clone runs `make demo` from the README alone; `make verify` green; commit and tag phase18-closed.
Reply with: smoke-test result, image size, commit hash.
```

---

## Step 6: Audit, viva, report, release

```text
PHASE 19 (solo, lite): FINISH. Use a SEPARATE subagent for the audit; the agent that built the work does not grade it.

F1. INDEPENDENT AUDIT (docs/final_audit.md): rules 1-37 with evidence per rule; claims audit (grep docs and UI for "extends life", "works on any machine", "proven", "certified", "compliant" and for unlabeled synthetic data); leakage audit per machine; reproducibility from a clean clone (`make verify`, `make demo`); coverage and test counts; regression status; security scan status; dashboard hardcoded-number scan; traceability to the synopsis objectives in docs/traceability.md. Every finding gets a severity and a fix or accepted-with-reason note. Fix all high findings and re-audit the changed parts.
F2. ONE ABLATION: on C-MAPSS, compare the risk model alone against the full set of four checks: how often the weaker version accepts a prescription that the full checks reject. Report with engine-bootstrap CIs. Add a simple baseline of plain alerting (no prescription).
F3. VIVA PACK (docs/viva_rehearsal.md): at least 30 likely questions with answers citing screens, files and real numbers. Include: "Does it work on any machine?" (tested on C-MAPSS plus a toy machine through a spec file), "Is this safe to use on a plant?" (advisory only; a plant needs engineer confirmation of limits and a shadow pilot), "What if sensors are spoofed?", "How do you know the model is calibrated?", "Why not 95% on all alerts?", "What was the mismatch problem and how did you fix it?", "What did you not build and why?", "What would you do with six more months?".
F4. FINAL REPORT (docs/final_report.md): problem, background (predictive versus prescriptive maintenance, algorithmic recourse), design, framework and machine specs, the four validity checks, results per machine with run labels, security and safety, deployment, limitations, a short "pilot stages" section (offline replay, shadow mode, advisory with approval; closed-loop control out of scope), "designed but not built" list, SDG 9 (Targets 9.1 and 9.4, modest wording), conclusion and future work. Figures generated from result files.
F5. DEMO RUNBOOK (docs/demo_runbook.md): a 6-minute script (problem, set conditions, risk, prescription, checks, follow-up, second machine via spec file, results, SDG 9), exact scenarios, start command, a cached fallback and a backup plan.
F6. RELEASE: tag v1.0.0 with release notes and checksums; run the smoke test on the release build.

Gate: no open high findings; clean-clone verify and demo pass; every table has run labels; commit and tag v1.0.0.
Reply with: audit summary (counts by severity and status), ablation result, test and coverage numbers, commit hash.
```

---

## If your deadline is close

- **A week left:** do Step 1, a short Step 2 (T1, T2, T3, T5, T6 only), Step 3, then Step 6 without the ablation.
- **Two weeks:** do all six steps.
- **Less than a week:** close Phase 12, do Step 3 (dashboard), and write the report and viva questions by hand with the agent's help. Say plainly that generality is designed but not built.

## One paragraph for your report and viva

"PrescriptXAI extends predictive maintenance for industrial machinery and engines. A machine is described by a spec file. The system predicts failure risk and prescribes the smallest allowed change to the machine's settings. Every prescription passes independent checks for model safety, normal behaviour, control limits and sensor consistency. It is advisory only and withholds recommendations when data or checks fail. It records what operators actually did and re-scores the risk. We tested it on NASA C-MAPSS jet engines and showed that a new machine can be added through a spec file. A real plant would still need engineer confirmation of limits and a shadow-mode pilot."

---

## Fix this in your synopsis

Section 10 of your synopsis says the system "extends equipment lifespan through micro-adjustments". Section 12 says you do not claim RUL extension. These contradict each other, and an examiner can quote one against the other. Reword section 10 to something like: "reduces predicted failure risk through small setting changes, which can reduce emergency shutdowns and premature part replacement." Use the same wording in the report and slides.

---

## Your 5-minute demo path

1. **Case study preset:** risk is high, then the prescription brings it down; point to the sparsity badge, the drop badge and the four checks.
2. **Waterfall:** show how much each change contributes.
3. **Move a slider:** the risk updates live; try your own change against the prescription.
4. **Step 4:** record "Followed partly"; show adherence and the risk with the applied settings.
5. **Needs maintenance example:** show that the system refuses unsafe advice.
6. **Scorecard (Advanced):** show the measured values against the targets and say which cases fall short and why.