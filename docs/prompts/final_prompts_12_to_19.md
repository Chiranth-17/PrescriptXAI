# PrescriptXAI: final prompts, Phases 12-19 (one file, self-contained)

For after Phases 1-11. Aim: a **generic prescriptive-maintenance framework** for industrial machinery and engines that extends predictive maintenance: it takes a machine described by a spec file, predicts risk, prescribes the smallest allowed change, validates it, and records whether it was followed. It ships with a simple, good-looking simulator dashboard, safe-operation features, security, packaging and a pilot guide.

This file replaces `prescriptxai_phases_12_to_23_industrial.md`, `prescriptxai_simple_final_4_phases.md`, `prescriptxai_phase11G_generic_framework_prompt.md` and the dashboard prompts v2 and v3 (the dashboard is now Phase 17, written out in full below). Paste the **rules** once, then the phases in order, one at a time.

## Decision on "redo or continue"

Continue. Phase 12 fixes the reproducibility problem found by the audit (712 of 32,116 mismatches, 15 Tier 2 changes, 3 triage changes). A rebuild only makes sense if Phase 12's root-cause experiments show the scoring definitions cannot be reconciled or results stay non-reproducible after the code is made deterministic.

## Map

| # | Phase | Why | Suggested owner |
|---|---|---|---|
| 12 | Closure: explain the 712 mismatches, freeze the baseline | Everything after depends on a trustworthy baseline | A |
| 13 | Generic framework: spec files, adapters, CSV adapter, contract tests | Makes it work for any machine described by a spec | A |
| 14 | Common machine features, synthetic pump, closed-loop check | Proves the framework runs on a second machine | D |
| 15 | Safe operation: data checks, withholding, approvals, audit log, onboarding with engineer sign-off | What an industry team needs before trusting it | B |
| 16 | Security hardening | Your cybersecurity branch; fits industrial settings | C |
| 17 | Final dashboard: simple, good-looking simulator | The demo and the teacher's feedback feature | D |
| 18 | Packaging, deployment, CI, health and drift monitoring | Anyone can run it | C |
| 19 | Evaluation per machine, pilot guide, final audit, viva pack, release | Evidence, handover, defence | all |

Dependencies: 13 needs 12. 14, 15 and 17 need 13. 16 needs 15. 18 needs 15 and 17. 19 needs everything. If time is short, trim in this order: the closed-loop part of 14, then drift monitoring in 18, then the approvals workflow in 15. Keep 12, 13, 16, 17, 19.

---

## Rules (paste once into AGENTS.md; keep rules 1-29)

```text
30. ADVISORY ONLY. The system recommends; a human decides. It never writes to a machine, PLC, historian or control system. All connectors are read-only.
31. MACHINE-AGNOSTIC CORE. src/prescriptxai/core has no dataset, machine or sensor names. Machine details live in spec files, adapters and the asset library. A test enforces it.
32. TESTED-ONLY CLAIMS. Name the machines tested and mark each real-benchmark or synthetic. Never write "works on any machine", "proven", "certified" or "extends engine life".
33. ENGINEER SIGN-OFF. Bounds, step limits, failure definition and the controllable/frozen split need a named engineer's confirmation (name, role, date). Without it a machine runs in Alerts-only mode.
34. FAIL SAFE. If data quality, input integrity, plausibility or any check fails, withhold the recommendation and say why.
35. EVIDENCE-GATED MODES. Alerts only, Advisory (shadow), Advisory (live). A readiness scorecard decides which are allowed. Promotion is manual, demotion can be automatic.
36. NO POOLED NUMBERS. Results are per machine. Every table carries machine id, spec hash, protocol version, run id, K and population.
37. LABEL SYNTHETIC AND SIMULATED DATA everywhere: tables, charts, exports, UI.
38. SECURITY BY DEFAULT. Authentication on, least-privilege roles, no secrets in the repo, tamper-evident audit log.
39. STANDARDS ARE GUIDANCE ONLY (ISO 13374, ISO 14224, ISO 17359, OPC UA, IEC 62443). Never claim compliance.
40. REPRODUCIBLE. Results are deterministic: fixed seeds, iteration budgets for search (wall-clock only for reporting). Every release passes `make verify` from a clean clone.
Send a short status with real numbers after every phase.
```

---

## Phase 12: Closure, explain the mismatches, freeze the baseline

```text
PHASE 12 CLOSURE: EXPLAIN THE 712 MISMATCHES AND FREEZE THE BASELINE.
Read the stop report (commit 147d846), the saved records, the audit output, AGENTS.md (rules 1-40), PROGRESS.md and docs/phase4_final.md. Do not edit saved records. Do not promote any fixture until step 6.

1. CLASSIFY all 712 mismatches in a table: by field (candidate, risk, each tier verdict, triage, timing), mode (FAST or THOROUGH), population, seed and unit; size of the difference; whether the candidate itself differs or the same candidate was scored differently. For every verdict or triage flip record the margin to the threshold.
2. FIND THE ROOT CAUSE by experiment: (a) rerun the 712 queries twice, in one process and in fresh processes: do results differ run to run? (b) one thread versus default threads; (c) score the SAME saved candidates with the production scorer and the audit scorer (separates scoring from search); (d) check for wall-clock stopping in search and compare library versions with the lockfile.
3. FIX the cause (rule 40): fixed seeds, deterministic math settings, iteration-count budgets, stable tie-breaking. If scorers disagree, decide which is right against the written definition and fix the other.
4. FIXTURE POLICY: discrete outputs (settings changed, verdicts, triage) match exactly; floats within a documented tolerance. Cases within a tiny margin of a threshold are flagged "borderline" and reported separately, never rounded silently.
5. IMPACT: recompute the headline tables as a NEW run id. Keep the old run, mark it "superseded" with the reason, and show old and new numbers side by side with engine-bootstrap CIs. Never overwrite a protocol version's earlier results.
6. PROMOTE the fixture (tests/regression/cmapss_baseline.parquet plus a test that reruns and compares) only when two consecutive full reruns reproduce identical discrete outputs and the independent audit shows zero unexplained mismatches.
7. OPEN-ITEM LEDGER: list every open or partial item from Phases 4-11 (strict plausibility metric, fallback rate of constraint-first search, exact intervals near 100%, validity-versus-K under protocol v2, FAST p95 against the 1.8 s budget, run labels on every table) and mark each Closed, Open or Accepted-with-reason with evidence. Write docs/state_of_project.md and map every synopsis objective to code, tests and evidence in docs/traceability.md.

Gate: ruff, mypy, pytest green; regression test passes on a clean clone. Commit and tag phase12-closed.
Reply with: the classification table, the root cause, whether headline numbers changed (with CIs), the ledger summary and the commit hash.
```

---

## Phase 13: Generic framework

```text
PHASE 13: GENERIC FRAMEWORK.
Read AGENTS.md, PROGRESS.md, features.yaml, the frozen RecourseResult schema, the core code and tests/regression.

NON-NEGOTIABLE
G1. The C-MAPSS regression test passes after every step with identical discrete outputs. If anything differs, explain before continuing.
G2. src/prescriptxai/core imports no machine. A test greps core for dataset, machine and sensor names ("C-MAPSS", "FD001", sensor ids, "engine", "turbofan") and fails on any hit.
G3. Schema changes are versioned with a migration (old rows get machine_id = "cmapss_fd001").

TASKS
T1. MACHINE SPEC (pydantic, versioned): configs/machines/<id>/machine.yaml with: identity (id, display name, unit word and plural, asset class, data source and license note, synthetic flag); features (id, friendly label, SI unit, role in {sensor, controllable, frozen}, bounds, per-step limit, plain-language "why" template, coupling group); failure definition (horizon H, label source, tau_safe, tau_danger); validation settings (plausibility thresholds by protocol version, coupling groups and residual limit, step-limit assumption, intervention horizon K); triage thresholds; k_max; FAST and THOROUGH latency budgets; sign-off block (engineer name, role, date, scope); sentence templates. Convert the C-MAPSS configuration into configs/machines/cmapss_fd001/machine.yaml with no change in values.
T2. ADAPTERS (src/prescriptxai/adapters/): a base interface with load() -> one standard long table (unit id, time index, features, optional event or remaining life), split(seed) by UNIT with a per-machine leakage audit, and failure_labels(H). Implement CmapssAdapter (moved code, no logic change) and TabularAdapter: bring-your-own CSV or Parquet configured only through machine.yaml column mappings. Registry, `--machine` flag on every CLI command, API prefix /machines/{id}/..., GET /machines.
T3. CORE REFACTOR: solver, four validity tiers, calibration, triage, FAST and THOROUGH modes, feedback and explain_result read a MachineSpec and a dataset handle instead of C-MAPSS constants. Rename "engine" to "unit" inside the core. Add machine_id and spec_hash to RecourseResult and the feedback log.
T4. CONTRACT TESTS parametrized over registered machines: spec validates; no unit in two splits; labels match the failure definition; candidates respect bounds and step limits; frozen features never change; verdicts equal direct library calls; calibration error below tolerance; FAST and THOROUGH agree where both succeed; triage covers every case; adherence matches constructed cases.
T5. PROOF AND TEMPLATE: a throwaway toy machine inside the tests, defined by a machine.yaml plus a tiny CSV, runs train, score, prescribe, check and feedback without touching core; record the lines it needed. Add templates/new_machine/ and docs/adding_a_machine.md (what an engineer must decide with a domain expert: which settings can be changed, bounds, step limits, failure definition, horizon, related sensors).

Gate: G1 and G2 pass; contract suite passes for cmapss_fd001 and the toy machine; ruff, mypy, pytest (coverage not lower) green; PROGRESS.md updated; commit and tag phase13-closed.
Reply with: regression result, registered machines, lines needed for the toy machine, commit hash.
```

---

## Phase 14: Common machine features, synthetic pump, closed-loop check

```text
PHASE 14: COMMON MACHINE FEATURES, SYNTHETIC PUMP, CLOSED-LOOP CHECK.
Read AGENTS.md, the machine spec schema and the adapter interface from Phase 13.

PART A. COMMON-FEATURE LIBRARY (src/prescriptxai/assets/, YAML plus tests)
A1. Signal taxonomy shared by industrial machines, with SI units: temperature, pressure, flow, rotational speed, vibration, electrical (current, voltage, power), energy input (fuel or electrical demand), valve or damper position, load, ambient conditions, run time.
A2. Control-lever taxonomy (speed setpoint, valve position, load or feed rate, cooling flow, pressure setpoint) and fixed-context taxonomy (ambient temperature, demand, fluid properties).
A3. Asset-class templates for rotating equipment: pump, fan, compressor, gas or steam turbine, electric motor, gearbox, turbofan engine. Each gives default roles, typical adjustable and fixed features, typical failure modes (named after ISO 14224-style categories, as guidance) and plain-language "why" templates.
A4. Physics relations as coupling templates for the sensor-consistency check, never as ground truth: pump and fan affinity relations (flow ~ speed, head ~ speed squared, power ~ speed cubed); hydraulic power relation; a simple heat balance; compressor pressure ratio versus speed. Each is fitted to healthy data with a learned residual limit. If a relation does not fit a machine's healthy data, report that and switch it off for that machine.
A5. `prescriptxai assets list`; a test that every template validates against the machine spec schema.

PART B. SYNTHETIC PUMP "simpump" (label "Synthetic machine (framework test)")
B1. docs/simpump.md documents the model: sensors (flow, head, speed, motor current, bearing vibration, bearing temperature, suction pressure); adjustable settings (speed, discharge valve opening, cooling flow); fixed conditions (ambient temperature, fluid density, demand); hidden wear that grows with operating stress; a failure hazard that is a documented function of wear and stress and HIDDEN from the learned model; noisy sensors that follow the affinity relations.
B2. Generate run-to-failure data with fixed seeds (at least 200 units), versioned with the generator config hash. Implement a simpump adapter and machine.yaml. Run the full pipeline with NO change to core: train, calibrate, prescribe, four checks, triage, evaluation tables (validity, plausibility, joint, triage, validity-versus-K curve, unit-bootstrap CIs) under reports/simpump/, labeled synthetic. Never mix with C-MAPSS tables.

PART C. CLOSED-LOOP CHECK
C1. Optional fifth check "Simulator check": roll the prescription forward in the pump generator and verify the true hazard falls. Shown only for machines with a simulator; C-MAPSS keeps four checks.
C2. For every prescription, run the generator forward with and without it over many noise seeds and report true failure frequency in both arms with CIs. Report the gap between the learned model's predicted risk drop and the simulator's true drop, even if large.
C3. TRAP TEST: construct a prescription the learned model rates safe but the simulator shows is harmful, and show the simulator check catches it.
C4. Docs state plainly: simpump shows that the framework and checks behave correctly where the truth is known. It does not show performance on real pumps.

Gate: contract suite passes for all registered machines; relations documented with fit statistics; closed-loop table with CIs; ruff, mypy, pytest green; commit and tag phase14-closed.
Reply with: the simpump evaluation table, closed-loop table, predicted versus simulated risk drop, which relations were enabled or disabled, commit hash.
```

---

## Phase 15: Safe operation (data checks, withholding, approvals, audit, onboarding)

```text
PHASE 15: SAFE OPERATION.
Read AGENTS.md (rules 30, 33, 34, 35, 38), the adapters, the feedback module and the API.

PART A. DATA INPUT AND QUALITY
A1. Read-only adapters: a SQL adapter (SQLAlchemy, parameterized read-only queries from config), plus optional OPC UA (asyncua) and MQTT (paho-mqtt) subscribers behind optional extras, tested against local mocks only. No write method exists anywhere; a test asserts it.
A2. Time handling: time-zone parsing, resampling to the machine's decision step, a definition of "operating cycle" for continuous machines (fixed windows), unit conversion to SI from the spec, gaps and late data.
A3. Label sources: remaining-life data, or an event or maintenance log with horizon labeling and RIGHT-CENSORING (units that did not fail are not permanent negatives); after a maintenance action a unit starts a new life segment. Report counts of failure events, units and censored units for every machine.
A4. DATA-QUALITY ENGINE: score and reason codes per window for missing values, stuck sensors, out-of-range values, unit mismatches, timestamp gaps, clock drift, duplicates and sensor-swap-like step changes. Thresholds in config.
A5. INTEGRITY CHECKS on live input: range and rate-of-change sanity, cross-sensor consistency through the coupling relations, stale or replayed timestamps.
A6. FAIL SAFE (rule 34): bad data quality or failed integrity returns "Recommendation withheld: <reason>". Fault-injection tests: inject each defect into clean data and show it is flagged and the pipeline withholds.
A7. docs/data_requirements.md: signals, sampling rate, history length, failure or event records and setting definitions an industry team must provide, as a one-page checklist.

PART B. APPROVALS AND AUDIT
B1. RECOMMENDATION LIFECYCLE: issued -> approved or rejected by a supervisor (with reason) -> applied by the operator (applied values) -> outcome scored (risk re-scored, adherence computed) -> closed. Persist every transition with user, time, input hash and machine pack hash. Test illegal transitions.
B2. ROLES: operator (view, record applied values), engineer (approve or reject), admin (users, machine packs). Enforce them in the API, not only the UI.
B3. AUDIT LOG: append-only, hash-chained (each entry stores the previous hash). A verify command detects any edit or deletion.
B4. WORK-ORDER EXPORT: CSV and JSON, plus an optional outbound signed webhook (HMAC). It never changes a machine.
B5. SHADOW MODE: run on live or replayed data, store recommendations, show operators nothing. A later job compares settings actually used (from the history) with what was recommended and with the risk that followed. This is the core of an industry pilot.
B6. The feedback store from earlier phases and this lifecycle use one database. The simulated operator stays labeled and excluded from real statistics by default.

PART C. ONBOARDING WITH ENGINEER SIGN-OFF
C1. `prescriptxai onboard` (CLI, with a matching Advanced page later in the dashboard), resumable steps: connect data; profile and data quality; map columns to roles (suggestions from names, units, variance; the engineer confirms); define failure labels; set bounds and step limits (suggestions from data percentiles and observed rates, marked DRAFT); train and check calibration; validate on held-out units (plus simulator checks where available); readiness scorecard.
C2. SIGN-OFF (rule 33): store name, role, date and scope for bounds, step limits, failure definition and the controllable/frozen split. Changing any of them invalidates the sign-off.
C3. READINESS SCORECARD decides the mode (Alerts only, Advisory shadow, Advisory live). Criteria and thresholds in config with rationale, labeled heuristics: enough failure events, calibration error, validity and plausibility lower confidence bounds, data-quality pass rate, sign-off present, simulator check where available, latency within budget. A failed criterion lists the reason and the fix. Promotion is manual.
C4. MACHINE PACK: one bundle (spec, trained model, calibration, plausibility and coupling models, validation report, scorecard, sign-off, data hash, code version) with a SHA-256 manifest. Loading verifies hashes and refuses a modified pack.
C5. Test the wizard end to end on cmapss_fd001, simpump and a bring-your-own-CSV sample; test that a pack without sign-off cannot enter an Advisory mode.

TESTS: every adapter on sample data; leakage audit per machine; censoring on constructed cases; every defect type detected; no network in tests; lifecycle and RBAC matrix across every endpoint; audit tamper detection; HMAC verification; shadow comparison on constructed operator behavior.
Gate: ruff, mypy, pytest green; a teammate onboards the sample CSV machine from the docs alone and records time and problems in docs/usability_notes.md; commit and tag phase15-closed.
Reply with: defect-detection table, RBAC matrix, audit tamper test result, scorecard outputs for the three machines, commit hash.
```

---

## Phase 16: Security hardening

```text
PHASE 16: SECURITY HARDENING.
Read AGENTS.md (rules 30, 34, 38, 39). Context: industrial and operational-technology settings. Treat IEC 62443 ideas (zones, conduits, security levels) as guidance only.

S1. THREAT MODEL (docs/threat_model.md, STRIDE) with a data-flow diagram and trust boundaries: data sources, ingestion, machine packs, API, dashboard, audit log, exports. Rate each threat, list mitigations and tests, mark residual risk. Include threats specific to this system: sensor spoofing, replayed or stale data, poisoned training data, tampered machine pack, tampered audit log, malicious webhook, approvals by the wrong person.
S2. AUTH: authentication required by default (strong password hashing; OIDC-ready configuration), short-lived tokens, CSRF protection and secure cookies for the dashboard, session timeout, login rate limiting and lockout. Secrets only from environment or secret files; startup refuses default credentials.
S3. API HARDENING: strict validation with size limits; reject NaN and infinity; schema-based fuzzing (Hypothesis or Schemathesis) on every endpoint; uniform error format with no stack traces; request ids; TLS configuration documented; locked-down CORS and security headers.
S4. ADVERSARIAL SENSOR TESTS: for a sample of states, search within plausible ranges for sensor changes that make the system output a prescription which the simulator (simpump) or the four checks judge harmful. Report the attack success rate and which defenses caught the rest. Report honestly even if some attacks succeed, and list them in docs/limitations.md.
S5. SUPPLY CHAIN AND BUILD: pinned dependencies with hashes; pip-audit; Bandit; secret scanning (detect-secrets or gitleaks); CycloneDX SBOM; license check; SHA-256 manifests on machine packs and releases.
S6. CONTAINER HARDENING: non-root user, read-only root filesystem, dropped capabilities, minimal image, healthcheck, vulnerability scan.
S7. SAFETY CASE (docs/safety_case.md, claims-arguments-evidence): claims limited to advisory use, fail-safe behavior and traceability; list hazards (wrong recommendation accepted, ignored alert, spoofed data, stale model) with mitigations and test evidence. State clearly that it is not a certified safety case.
S8. `make security` runs all scans and security tests and fails on any high or critical finding without a dated, documented exception.

Gate: every high threat has a mitigation and a test; fuzz tests pass; adversarial results documented; ruff, mypy, pytest green; commit and tag phase16-closed.
Reply with: scan summary, attack success table, commit hash.
```

---

## Phase 17: Final dashboard (simple, good-looking, simulator)

Reference: the design mock "PrescriptXAI Operations Dashboard" (the published Design artifact). Take screenshots at 1360 px and 390 px and save to `docs/design/dashboard_mock_desktop.png` and `dashboard_mock_phone.png`.

```text
PHASE 17: FINAL DASHBOARD. A single-page simulator: set conditions -> see risk -> get prescription -> record whether it was followed.
Read AGENTS.md, the RecourseResult schema, the machine spec, the Phase 15 lifecycle and the existing dashboard. Compare with docs/design/dashboard_mock_*.png. Do not delete analysis pages: move them under "Advanced".

RULES
R1. Every figure comes from the real model, result files or live computation. A test scans the main-page source and fails on hardcoded numbers (the mock's numbers are placeholders).
R2. Simulated-operator rows are labeled "Simulated operator (demo)" everywhere and excluded from real statistics by default.
R3. Plain language on the main page. No Mahalanobis, tier, surrogate, protocol or k_max; technical names live in tooltips and Advanced.
R4. Never claim extra engine life or physical proof. Say "predicted risk" and "model-based checks".
R5. Accessible and responsive: colour-blind-safe (blue, amber, vermilion, always with text or icon), contrast at least 4.5:1, controls at least 44 px, keyboard use, every slider has a visible label and value, works at 390 px.
R6. Offline: bundle fonts (IBM Plex Sans and Mono) or use a system stack; no runtime network calls.
R7. Stale-result safety: every result carries a hash of its inputs; a result whose hash no longer matches the sliders is never shown as current.

LOOK (from the mock)
Page background #F3F5F8; white cards with 1 px #DDE3EA border and 12 px radius; ink #17212B; muted text #566474; accent blue #1D4ED8 for actions and "after" values. Status colours: safe or pass #0B5F6E on #E3F3F5; watch #6B4400 on #FFF2CF; alert or fail #A8310F on #FCE9E2. Large risk numbers in IBM Plex Mono; step numbers in blue circles; pills for status. Provide a dark theme with matching tokens. If Streamlit cannot reproduce this look, you may implement the page as a static HTML and JavaScript front end served by FastAPI that calls the same API; then replace AppTest with Playwright tests that cover the same cases.

LAYOUT (one page; panels stack on narrow screens)
Header: product name, one-line purpose, MACHINE SELECTOR (from GET /machines; labels, units, slider ranges and wording come from the machine spec; choice kept in the URL), a MODE BADGE (Alerts only, Advisory shadow, Advisory live), and a chip "Sample data - replay of NASA C-MAPSS engines" or "Synthetic machine (framework test)" from the spec.
Scenario bar: preset buttons generated by a script from real saved states (one per triage state when available; named for what the state is), plus Reset and Copy link (all slider values in the URL query string).

STEP 1 SET THE CONDITIONS (left card). Base state is a real (unit, time) from the presets or a selector; it supplies every sensor the user does not override. Group "Situation (fixed)": cycles flown (moves along the unit's real trajectory) and the context features. Group "Current settings (the operator can change these)": one slider per adjustable feature, bounded by the spec; under each slider the prescription changes, show "Recommended: <value> (<% change>)". Slider ranges come from data percentiles, never hardcoded. Moving a slider updates dependent sensors through the coupling model. If the user-built state is unusual compared with real data, show an amber banner: "This combination of conditions is unusual for real equipment. The risk estimate may be less reliable." It is a flag, not a block.

STEP 2 PREDICTED RISK. Large "Risk now" (calibrated model, colour plus text), an arrow and "With the prescription", one plain sentence from explain_result, a triage badge (No action needed, Fixable now, Partly fixable, Needs maintenance) and a Safe/Watch/Alert meter with Now and After markers. Risk now updates instantly while sliders move (target under 50 ms).

STEP 3 PRESCRIPTION. One to three rows: name, from -> to, % change, a track inside the allowed range, and a "Why" line that reports how many points of predicted risk that single change removes (measured with the real model) plus a template sentence from the spec. A line "Not changed: ..." for fixed features. Four safety-check rows (pass or fail icon plus text and a plain hint): Predicted safe; Looks like normal behaviour; Within control limits; Sensors stay consistent. Machines with a simulator add a fifth row "Simulator check". States: no action needed; fixable; partly fixable ("schedule an inspection"); needs maintenance ("Setting changes cannot make this safe. Plan maintenance." plus a log-only "Schedule maintenance"); WITHHELD ("Recommendation withheld: <reason>" for bad data, failed integrity or failed checks); NOT ENABLED (Alerts-only mode shows the scorecard reason). "Try your own change": the user edits the settings by hand and sees "Your settings: risk X%, checks n of 4" beside "Prescription: risk Y%, checks 4 of 4". COMPUTE STRATEGY: instant tier (risk only), FAST tier after a 400 ms pause with a "Calculating..." state and cancellation of superseded solves, then a cached nearby result with a "cached" badge if the budget is exceeded (rule R7 applies).

STEP 4 WAS IT FOLLOWED? (full-width card). Buttons "Followed as recommended", "Followed partly", "Not followed" plus sliders for the applied value of each recommended setting; "Not followed" takes an optional reason. "Send for approval" and approval status come from the Phase 15 lifecycle; roles decide which buttons appear. ADHERENCE: a_j = clip(1 - |applied_j - recommended_j| / max(|recommended_delta_j|, eps), 0, 1); adherence = mean of a_j; labels from config: Followed >= 0.80, Partly 0.40-0.80, Not followed < 0.40; one bar per action. OUTCOME: re-score the APPLIED state with the real model and rerun the checks; show "Risk after applied settings" beside the prescription's risk and "Checks passed: n of 4". TREND CHART: predicted risk over the next 30 cycles, "No intervention (model prediction)" versus "With the applied settings (model prediction)", dashed safe and alert levels; for replayed units add a third line "Observed in the recorded data". "Record this follow-up" appends to the log. FOLLOW-UP LOG table: scenario, result, adherence, risk before -> after, source ("Operator (this session)" or "Simulated operator (demo)"), scrolling sideways on phones. A "Simulate operators" control (sidebar) draws seeded compliance, builds applied states by interpolation and scores them with the real model and checks.

FOOTER: SDG 9 line and one button "About this view and how it was checked": data source, what the checks mean in plain words, assumptions (model-based, benchmark data, step limit and intervention horizon, proxies for controls), what a real deployment adds, the simulated-operator note, protocol version, run id and config hash.

ADVANCED (sidebar, not the main page): onboarding wizard, approvals queue and audit log with a "verify chain" button, data quality, drift and health (Phase 18), machine packs, evaluation per machine (Phase 19), About and limits.

BACKEND ENDPOINTS: POST /simulate/risk (instant), POST /simulate/prescribe (FAST, cancellable, returns input hash), GET /machines, GET /machines/{id}/spec, GET /machines/{id}/scenarios, POST /feedback, GET /feedback/summary. CLI: scenarios generate (writes configs/machines/<id>/scenarios.yaml from saved results and precomputes a cache), feedback add, feedback simulate. "Download scenario report": one-page HTML with sliders, risk, prescription, checks, follow-up, labels and run ids.

TESTS: page loads for every registered machine and role; each preset renders; moving a slider updates risk immediately; stale results never show; every state above renders (including withheld and not enabled); out-of-range banner appears for an implausible combination; "Try your own change" shows both columns; URL round trip restores state; adherence on constructed cases (exact = 1.0, opposite = 0.0, half = 0.5) and label boundaries 0.40 and 0.80; outcome uses the real model; per-action risk contributions sum to the total drop within tolerance; frozen features never change; slider bounds equal spec bounds; hardcoded-number scan; banned-jargon scan; no machine or feature name hardcoded in the dashboard source; simulated rows labeled and excluded by default; works offline; instant tier under 50 ms and FAST tier within the budget on the presets; screenshots at 390 px and 1360 px saved to docs/screenshots/ and compared with the mock in docs/design_diff.md.

GATES
1. USABILITY: two classmates use the page for 2 minutes with no help; record what they said and where they hesitated in docs/usability_notes.md; fix what confused them.
2. EXPLAIN TEST: each team member explains the four steps in 60 seconds using only the page.
3. DESIGN DIFF: list differences from the mock; fix or justify each.
4. ruff, mypy, pytest (coverage not lower) green; commit and tag phase17-closed.
Reply with: screenshots, usability notes, test counts, commit hash.
```

---

## Phase 18: Packaging, deployment, CI, health and drift

```text
PHASE 18: PACKAGING, DEPLOYMENT, CI, HEALTH AND DRIFT.
Read AGENTS.md (rules 38, 40). The team develops on Windows with uv and mingw32-make; keep Windows parity.

P1. PACKAGE: pyproject with optional extras (api, dashboard, opcua, mqtt, sql, security, dev); one version source; CLI entry point `prescriptxai`.
P2. DOCKER: multi-stage image for API, dashboard and a worker; docker-compose with volumes for packs, data and logs, healthchecks, restart policy and an env-file template; SQLite by default with a PostgreSQL option; Phase 16 hardening applied.
P3. CONFIG: environment overrides in a documented table; validation at startup with clear messages.
P4. OFFLINE INSTALL: `make wheelhouse` and docs for air-gapped sites.
P5. CI (GitHub Actions): lint, types, tests with coverage gate, security scans, container build and scan, docs build, artifacts (wheel, SBOM, image digest). A nightly job reruns the regression baseline and the closed-loop suite.
P6. `make verify` (lint, types, tests, security, build, smoke test) on Linux and on Windows; `make demo` starts API, dashboard and both sample machines with sample data in one command.
P7. HEALTH AND METRICS: structured JSON logs; /health, /ready and /metrics (Prometheus text format) with latency by mode, withheld recommendations by reason, data-quality scores, pending approvals.
P8. DRIFT MONITOR per machine: per-feature drift (PSI and Kolmogorov-Smirnov) against training data, multivariate drift through the plausibility distance, and drift of the risk-score distribution; status Stable, Watch or Drifted with thresholds in config. If Drifted or data quality collapses, the machine drops from Advisory to Alerts only and an admin is notified (rule 35). Tests: drift detected on injected shifts and not on null shifts.
P9. MACHINE PACK REGISTRY: versions, hashes, status (candidate, shadow, active, retired); one-command rollback; refuse a pack that fails verification.
P10. DOCS SITE (mkdocs): quickstart, concepts, adding a machine, data requirements, onboarding, operations, security, API reference, troubleshooting.
P11. RELEASE PROCESS: semantic versioning, CHANGELOG, release notes; smoke test on the built image and wheel from a clean container.

Gate: a fresh clone runs `make demo` from the README alone; CI green; image scan has no unwaived high findings; ruff, mypy, pytest green; commit and tag phase18-closed.
Reply with: CI summary, image size, smoke-test result, drift detection table, commit hash.
```

---

## Phase 19: Evaluation per machine, pilot guide, audit, viva pack, release

```text
PHASE 19: EVALUATION, PILOT GUIDE, AUDIT, VIVA PACK, RELEASE.
Read everything. Use a SEPARATE subagent for the audit; the agent that built the work does not grade it.

PART A. EVALUATION
E1. For every registered machine produce reports/<machine_id>/ with the protocol tables (validity, plausibility, joint, triage, validity-versus-K curve, unit-bootstrap CIs, early-warning and all-alert populations, FAST latency); add the closed-loop table for machines with a simulator. A comparison page lists machines side by side with run labels; no pooled numbers (rule 36). Include "What generality we tested": machines (real benchmark or synthetic), what was identical (core code, checks, tests), what was machine-specific (spec, adapter, model, limits).
E2. ABLATIONS per machine: without plausibility, without the coupling check, without step limits, without sparsity, and with the risk model only. Report how often the weaker version accepts a prescription that a stronger check rejects.
E3. BASELINES: plain alerting (no prescription), a simple rule-based fix, and an off-the-shelf counterfactual method (for example DiCE if installable; otherwise a documented simple counterfactual baseline), compared on validity and plausibility.

PART B. INDUSTRY PILOT GUIDE (docs/pilot_playbook.md and templates/)
B1. Stages: offline replay on historian data; shadow mode; advisory with approval. Closed-loop control is OUT OF SCOPE and stated as such. For each stage: entry and exit criteria, duration guidance, roles, data needed, risks.
B2. KPIs and how to measure them: alert precision and lead time, recommendation acceptance, adherence, predicted-versus-observed risk change, withheld-recommendation rate and reasons, time to decision, false-recommendation reports. Success criteria are agreed BEFORE the pilot (template).
B3. TEMPLATES: data-request checklist, engineer sign-off form (bounds, step limits, failure definition), risk register, pilot charter, incident log.
B4. ROI WORKSHEET: inputs entered by the industry team (downtime cost, maintenance cost, alert volume, acceptance rate); no default figures presented as results; output shows ranges.
B5. docs/for_plant_managers.md: two plain-language pages: what it does, what it needs, what it does not do, what a pilot costs in people's time, what to ask the team.
B6. docs/standards_mapping.md: maps system parts to ISO 13374 data-processing blocks, ISO 14224 failure-mode vocabulary, OPC UA data access and IEC 62443 zone and conduit ideas; titled "alignment guidance, not compliance".

PART C. AUDIT AND RELEASE
F1. INDEPENDENT AUDIT (docs/final_audit.md): rules 1-40 with evidence per rule; claims audit (grep docs and UI for "extends life", "works on any machine", "proven", "certified", "compliant" and for unlabeled synthetic data); leakage audit per machine; reproducibility from a clean clone (`make verify`, `make demo`); coverage and test counts; regression baseline; security scan status; dashboard hardcoded-number scan; traceability to synopsis objectives. Every finding gets an owner, severity and a fix or an accepted-with-reason note. Fix all high findings and re-audit the changed parts.
F2. VIVA PACK (docs/viva_rehearsal.md): at least 40 likely questions with answers that cite screens, files and real numbers. Include: "Does it work on any machine?", "Why is the second machine synthetic?", "What does the simulator prove?", "Is this safe to use on a plant?", "What if sensors are spoofed?", "How do you know the model is calibrated?", "Why not 95% on all alerts?", "What was the 712-mismatch problem and how did you fix it?", "What did each team member build?", "What would you do with six more months?".
F3. FINAL REPORT (docs/final_report.md): problem, background (predictive versus prescriptive maintenance, algorithmic recourse), design, framework and machine specs, the four validity checks, results per machine with run labels, security and safety, deployment, pilot guide, limitations, SDG 9 (Targets 9.1 and 9.4, modest wording), conclusion and future work. Figures generated from result files.
F4. DEMO RUNBOOK (docs/demo_runbook.md): a 7-minute script (problem, set conditions, risk, prescription, checks, follow-up, second machine, onboarding and audit glimpse, results, SDG 9), exact scenarios, start command, a cached fallback and a backup plan.
F5. HANDOVER: README with a five-minute quickstart, CONTRIBUTING, architecture diagram, team roles and who built what, license choice (propose a permissive license and record the decision), citation file.
F6. RELEASE: tag v1.0.0, release notes, built wheel, SBOM, image digest, checksum file; run the smoke test on the release artifacts.

Gate: audit has no open high findings; clean-clone verify and demo pass; every table has run labels; commit and tag v1.0.0.
Reply with: comparison page summary, ablation findings, baseline findings, audit summary (counts by severity and status), test and coverage numbers, checksum list, commit hash.
```

---

## Orchestrator (optional; or paste phases one at a time, which is safer with four people)

```text
ORCHESTRATOR for Phases 12-19.
Read AGENTS.md (rules 1-40), PROGRESS.md and docs/prompts/final_prompts_12_to_19.md. Execute Phases 12 to 19 in order. For EACH phase: (1) run the phase prompt in full; (2) run its gate (ruff, mypy, pytest with coverage, phase-specific checks, the C-MAPSS regression test, and the contract suite once it exists); (3) update PROGRESS.md and docs/traceability.md; (4) commit and tag phase<N>-closed; (5) send a short status with real numbers and open issues; (6) start the next phase only after the gate passes.
STOP and report only if: a test failure survives two root-cause fix attempts; the regression changes; a rule would be violated; a manual decision or download is needed (offer a default); or a result looks implausibly good (run the leakage audit first). Use subagents for independent audits, never for the work being audited.
Do not skip tasks. If one cannot be done, record it as Partial or Not met with evidence in docs/traceability.md and continue.
```

## One paragraph for your report and viva

"PrescriptXAI extends predictive maintenance for industrial machinery and engines. A machine is described by a spec file. The system predicts failure risk and prescribes the smallest allowed change to the machine's settings. Every prescription passes independent checks for model safety, normal behaviour, control limits and sensor consistency, and a closed-loop check where a simulator exists. It is advisory only, withholds recommendations when data or checks fail, records approvals and what operators actually did, and ships with onboarding, security, monitoring and a pilot guide. We tested it on NASA C-MAPSS jet engines and a synthetic pump. A real plant would still need engineer sign-off and a shadow-mode pilot."

## Cautions

- Do not start Phase 13 before Phase 12 closes; the regression baseline protects every refactor after it.
- Each added capability needs tests and honest limits. If time runs short, cut the stretch items listed under the map, never the tests.
- Do not tell an examiner the system is safe for plants, certified, or proven on real machines. Say it is a tested reference implementation with a pilot protocol.