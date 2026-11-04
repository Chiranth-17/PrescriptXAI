# PrescriptXAI: FINAL prompts for Phases 12-20 (after Phases 1-11)

One self-contained file. It replaces the earlier Phase 12 dashboard files, the Phase 11G file, the 12-phase industrial file and the 4-phase simple file. Nothing else is needed except your repo.

## What this builds

A **generic prescriptive-maintenance framework for industrial machinery and engines**. It extends predictive maintenance: it predicts the risk, prescribes the smallest allowed change to the machine's settings, checks the prescription, and records whether the operator followed it. A machine is described by a spec file, so the same core works on jet engines (NASA C-MAPSS), a synthetic pump, and a company's own data. A simple, good-looking simulator dashboard lets anyone set conditions and see the risk and the prescription.

## What "implementable by industries" honestly means

You deliver a tested reference implementation, an onboarding process, and a pilot protocol. A plant still needs its own engineers to confirm limits and to run a shadow pilot. The system is advisory only. Do not claim safety certification or proven benefit on real plants.

## The plan

| # | Phase | Why it exists | Priority |
|---|---|---|---|
| 12 | Reality check and baseline freeze | Close open items; protect your C-MAPSS results | Must |
| 13 | Generic framework | Spec file + adapters + bring-your-own CSV + data quality | Must |
| 14 | Common features, synthetic pump, closed-loop test | Proves it is generic; gives a real test of prescriptions | Must (pump simulator can shrink) |
| 15 | Onboarding and readiness | How an industry team adds a machine safely | Should |
| 16 | Operations and security | Approvals, audit log, roles, spoofing defenses | Must for security, Should for the rest |
| 17 | Final dashboard | The simple, good-looking simulator | Must |
| 18 | Deploy and monitor | Docker, one-command demo, CI, drift and health | Must |
| 19 | Evaluation and pilot playbook | Per-machine results, ablations, industry guide | Must |
| 20 | Final audit, viva, release | Independent audit, report, v1.0.0 | Must |

**If time is short:** keep 12, 13, 17, 18, 19, 20, plus the security part of 16. Shrink 14 to the pump generator without the closed-loop test. Skip 15 and the rest of 16. Say in your report that these are future work.

**Four-person split:** A: 12, 13. B: 15 and data parts of 13. C: 16, 18. D: 14, 17, 19. All: 20.

---

## AGENTS.md amendment (paste once; skip any rule you already added)

```text
Append to AGENTS.md (keep rules 1-29):
30. ADVISORY ONLY. The system never writes to a machine, PLC, historian or control system. Connectors are read-only. Every output is a recommendation that a human approves.
31. MACHINE-AGNOSTIC CORE. src/prescriptxai/core contains no dataset, machine or sensor names. Machine knowledge lives in machine specs, adapters and the asset-class library. A test enforces this.
32. TESTED-ONLY CLAIMS. Docs and UI name the machines the framework was tested on and mark each as real benchmark or synthetic. Never write "works on any machine".
33. ENGINEER SIGN-OFF. Bounds, rate limits, failure definitions and the controllable/frozen split need a named engineer's sign-off (name, role, date) stored in the machine pack. Without it a machine runs in Alerts-only mode.
34. FAIL SAFE. If data quality, input integrity, plausibility or any check fails, withhold the recommendation and say why. Never fall back to a weaker answer silently.
35. EVIDENCE-GATED MODES. Alerts only, Advisory (shadow), Advisory (live). The readiness scorecard decides which are allowed; promotion is always manual. Thresholds live in config with their rationale.
36. SECURITY BY DEFAULT. Authentication on, least privilege, no secrets in the repo, tamper-evident audit log, hashed machine packs.
37. NO POOLED NUMBERS. Results are per machine. Every table carries machine id, spec hash, protocol version, run id, K and population.
38. LABEL SYNTHETIC AND SIMULATED DATA everywhere: tables, charts, exports, UI. Simulated operator rows read "Simulated operator (demo)".
39. STANDARDS ARE GUIDANCE. Mention ISO 13374, ISO 14224, ISO 17359, OPC UA and IEC 62443 only as alignment guidance. Never claim compliance or certification.
40. REPRODUCIBLE RELEASES. A release builds from a clean clone and passes `make verify`.
Send a short status with real numbers after every phase.
```

---

## Phase 12: Reality check and baseline freeze

```text
PHASE 12: REALITY CHECK AND BASELINE FREEZE.
Read AGENTS.md (rules 1-40), PROGRESS.md, docs/phase4_final.md, docs/traceability.md and the Phase 5, 6 and 7 reports. Add no features in this phase.

R1. Verify tags phase1-closed to phase11-closed exist and the tree is clean. Run ruff, mypy and the full tests; record counts and coverage in docs/state_of_project.md.
R2. OPEN-ITEM LEDGER. List every open or partial item from earlier phases and mark it Closed, Open or Accepted-with-reason, with evidence. Check at least: strict plausibility metric (distance against the 95th percentile of real low-risk states); fallback rate of constraint-first search; exact intervals near 100%; validity-versus-K curve under protocol v2; preregistration commit check; FAST-mode optimization p95 against the 1.8 s budget; engine-bootstrap confidence intervals everywhere; oracle-superset rule; run labels on every table. Fix what is small. Record the rest honestly in docs/limitations.md.
R3. BASELINE FREEZE. Run the Phase 7 headline evaluation on a fixed seed and store per-state outputs (risk, candidate, four check verdicts, triage, run label) in tests/regression/cmapss_baseline.parquet with the config hash and commit. Add a test that reruns it and compares: counts identical, floats within 1e-6.
R4. TRACEABILITY. Map every objective in the synopsis to code, tests and evidence in docs/traceability.md, marked Met, Partial or Not met.
R5. Write docs/state_of_project.md: what exists, headline results with run labels, what is weak, and what Phases 13 to 20 change.

GATE: all checks green; regression test passes on a clean clone; ledger complete. Commit and tag phase12-closed. Reply with ledger counts by status and the commit hash.
```

---

## Phase 13: Generic framework

```text
PHASE 13: GENERIC FRAMEWORK. Spec file, adapters, bring-your-own CSV, data quality.
Read AGENTS.md, PROGRESS.md, features.yaml, the frozen RecourseResult schema, the core modules and tests/regression. Inspect the repo and adapt names.

NON-NEGOTIABLE
G1. The C-MAPSS regression test passes after the refactor with identical counts. If anything differs, explain it before continuing.
G2. src/prescriptxai/core imports no machine. A test greps core for dataset, machine and sensor names ("C-MAPSS", "FD001", sensor ids, "engine", "turbofan") and fails on any hit.
G3. Schema changes are versioned with a migration (old rows get machine_id = "cmapss_fd001").

TASKS
T1. MACHINE SPEC (pydantic schema, versioned). One file per machine at configs/machines/<id>/machine.yaml:
 - identity: id, display_name, unit_noun and plural ("engine", "pump"), asset_class, data source and license note, synthetic flag.
 - features: id, friendly label, unit (SI), role in {outcome_sensor, controllable, context_frozen}, bounds, per-step rate limit, plain-language "why" template, coupling group.
 - failure definition: horizon H, how labels are produced (RUL threshold, event table, or column), tau_safe, tau_danger.
 - validation: plausibility thresholds by protocol version, coupling groups and residual limit, rate-limit assumption and intervention horizon K.
 - triage thresholds, k_max, FAST and THOROUGH latency budgets.
 - sign-off block: engineer name, role, date, scope (empty for benchmark or synthetic machines, flagged).
 - sentence templates for explain_result using {unit_noun}, {feature_label}, {from}, {to}, {pct}.
 Convert the existing C-MAPSS configs to configs/machines/cmapss_fd001/machine.yaml with no value changes.
T2. ADAPTERS (src/prescriptxai/adapters/base.py): load() returns a standard long table (unit_id, time_index, features, optional event or RUL); split(seed) by UNIT with a per-machine leakage audit; failure_labels(H); simulator() returns a Simulator or NullSimulator. Implement CmapssAdapter by moving the existing loading code. Implement TabularAdapter (CSV, Parquet or a folder) configured only through the spec's column mapping, so a company can bring its own data without writing Python. Add an optional SQL adapter (SQLAlchemy, read-only, parameterized queries from config). Add a registry, a --machine flag on every CLI command, API routes under /machines/{id}/..., and GET /machines.
T3. LABEL SOURCES AND CENSORING: support (a) run-to-failure RUL, (b) event or maintenance logs with horizon labeling and RIGHT-CENSORING (units that never failed are not permanent negatives; after a maintenance action start a new life segment), (c) expert-labeled alarms. Report for every machine: units, failure events, censored units. Warn when failure events are few.
T4. DATA-QUALITY ENGINE: per-window score with reason codes for missing values, stuck sensors, out-of-range values, unit mismatch, timestamp gaps, duplicates and step changes. Thresholds in config. FAIL SAFE: below the threshold the pipeline returns "Recommendation withheld: <reason>" and never prescribes from broken data. Inject each defect into clean data in tests and show it is flagged and withheld.
T5. CORE REFACTOR: solver, all four validity tiers, calibration, triage, FAST and THOROUGH modes, feedback and explain_result take a MachineSpec and a dataset handle. Rename "engine" to "unit" inside the core. Add machine_id and spec_hash to RecourseResult and the feedback log. Run G1, then commit.
T6. CONTRACT TESTS parametrized over registered machines: spec validates; no unit in two splits; labels match the failure definition; candidates respect bounds and step limits; frozen features never change; check verdicts equal direct library calls; calibration error below tolerance; FAST and THOROUGH agree where both succeed; triage covers every case; adherence matches constructed cases.
T7. TEMPLATE AND PROOF: templates/new_machine/ (commented machine.yaml, adapter skeleton, 20-row sample, registering test) and docs/adding_a_machine.md (what to decide with a domain expert, and that bounds and step limits need sign-off). PROOF TEST: a throwaway toy machine built from a machine.yaml and a tiny generated CSV runs train, score, prescribe, check and feedback without touching core. Record the lines it needed.
T8. docs/data_requirements.md: one page listing what an industry team must provide (signals, sampling rate, history length, failure or event records, which settings are controllable).

GATE: G1 and G2 pass; contract suite passes for cmapss_fd001 and the toy machine; defect tests pass; ruff, mypy, pytest (coverage not lower) green; PROGRESS.md updated; commit and tag phase13-closed.
Reply with: regression result, registered machines, lines needed for the toy machine, defect-detection table, commit hash.
```

---

## Phase 14: Common features, synthetic pump, closed-loop test

```text
PHASE 14: COMMON-FEATURE LIBRARY, SYNTHETIC PUMP, CLOSED-LOOP TEST.
Read AGENTS.md, the machine spec schema and the adapter interface from Phase 13.

PART A. COMMON-FEATURE LIBRARY (src/prescriptxai/assets/, YAML plus tests)
A1. Signal taxonomy shared by industrial machines, with SI units and plain labels: temperature, pressure, flow, rotational speed, vibration (RMS and band energies), electrical (current, voltage, power), energy input (fuel flow or electrical demand), position (valve opening), load, ambient conditions, run time and cycle count.
A2. Control-lever taxonomy: speed setpoint, valve or damper position, load or throughput setpoint, feed or fuel rate, cooling flow, pressure setpoint. Context taxonomy (frozen): ambient temperature, demand, fluid properties, product or shift mode.
A3. Asset-class templates for rotating equipment: pump, fan, compressor, gas or steam turbine, electric motor, gearbox, turbofan engine. Each gives default roles, typical controllable and frozen features, typical failure modes (ISO 14224-style vocabulary as guidance), default coupling groups and plain-language "why" templates.
A4. PHYSICS RELATION LIBRARY used as coupling templates for the "sensors stay consistent" check, never as ground truth: pump and fan affinity relations (flow ~ speed, head or pressure ~ speed squared, power ~ speed cubed); hydraulic power relation (power ~ density x g x flow x head / efficiency); simple heat balance; compressor pressure ratio versus speed; bearing temperature rise versus load. Fit each to healthy data and learn its residual limit. The check reports the residual in plain words and fails when it exceeds the limit. If a relation does not fit healthy data on a machine, report that and disable it for that machine.
A5. `prescriptxai assets list`; a test that every template validates against the spec schema.

PART B. SYNTHETIC PUMP "simpump" (label "Synthetic machine (framework test)")
B1. docs/simpump.md documents the model. State: flow, head, speed, motor current, bearing vibration, bearing temperature, suction pressure. Controllable: speed setpoint, discharge valve opening, cooling flow. Frozen: ambient temperature, fluid density, demand. Latent health: impeller wear and bearing wear growing with operating stress. Failure hazard: a documented function of wear and stress, HIDDEN from the learned model. Sensors: noisy functions of state, consistent with A4 plus noise.
B2. Generate run-to-failure data with fixed seeds (at least 200 units), versioned with the generator config hash. Implement SimPumpAdapter and a Simulator (step, rollout). Register the machine.
B3. Run the full pipeline on simpump with no core changes. Produce the same tables (validity, plausibility, joint, triage, K curve, unit-bootstrap CIs) in reports/simpump/, labeled synthetic.

PART C. CLOSED-LOOP TEST
C1. Add an optional fifth check "Simulator check": roll the prescription forward and verify the true hazard falls. Shown only for machines with a simulator. C-MAPSS keeps NullSimulator and four checks.
C2. For every prescription, roll the simulator forward with and without it over many noise seeds. Report true failure frequency in both arms with CIs, and the gap between the learned model's predicted risk drop and the simulator's true drop. Report honestly even if the gap is large.
C3. TRAP TEST: construct a prescription the learned model rates safe but the simulator shows is harmful, and show the fifth check catches it.
C4. State in the docs: simpump shows the framework and checks behave correctly where the truth is known. It does not show performance on real pumps.

GATE: contract suite passes for cmapss_fd001, simpump and the toy machine; relations documented with fit statistics; closed-loop table with CIs; ruff, mypy, pytest green; PROGRESS.md updated; commit and tag phase14-closed.
Reply with: closed-loop table, predicted versus simulated risk drop, relations enabled or disabled, commit hash.
```

---

## Phase 15: Onboarding and readiness

```text
PHASE 15: MACHINE ONBOARDING AND READINESS.
Read AGENTS.md (rules 33, 34, 35), Phases 13 and 14.

O1. `prescriptxai onboard` (CLI) and an Advanced dashboard page. Steps, each resumable and saved: 1 connect data; 2 profile and data quality; 3 map columns to roles (suggestions from names, units and variance; the engineer confirms); 4 define failure labels; 5 set bounds and step limits (suggestions from data percentiles and observed rates, clearly marked DRAFT; sign-off required); 6 train, calibrate and check calibration; 7 validate on held-out units (plus the simulator check if the machine has one); 8 readiness scorecard.
O2. ENGINEER SIGN-OFF: record name, role, date and scope for bounds, step limits, failure definition and the controllable/frozen split. Changing any of them invalidates the sign-off and the pack.
O3. READINESS SCORECARD with modes Alerts only, Advisory (shadow), Advisory (live). Criteria and thresholds live in config with their rationale (labeled as heuristics): enough failure events, calibration error, lower confidence bounds of validity and plausibility, data-quality pass rate, sign-off present, simulator check where available, latency within budget. A failed criterion lists the exact reason and the fix. Never promote a mode automatically.
O4. MACHINE PACK: one bundle (spec, trained model, calibration, plausibility and coupling models, validation report, scorecard, sign-off, data hash, code version) with a SHA-256 manifest. Loading verifies hashes and refuses a modified pack.
O5. AUTO REPORT: an HTML onboarding report in plain language with machine id and run ids.
O6. Tests: onboarding end to end on cmapss_fd001, simpump and a sample CSV machine; a pack without sign-off cannot enter an Advisory mode; a modified pack is refused.

GATE: ruff, mypy, pytest green. A teammate who did not write the code onboards the sample CSV machine from the docs only; record time and problems in docs/usability_notes.md. Commit and tag phase15-closed.
Reply with the scorecard outputs for the three machines and the commit hash.
```

---

## Phase 16: Operations and security

```text
PHASE 16: OPERATIONS AND SECURITY.
Read AGENTS.md (rules 30, 33, 34, 36, 39), the feedback module and the API.

PART A. HUMAN-IN-THE-LOOP OPERATIONS
H1. LIFECYCLE: issued -> approved or rejected by a supervisor (with reason) -> applied by the operator (applied values recorded) -> outcome scored (risk re-scored, adherence computed) -> closed. Persist every transition with user, time, input hash and machine pack hash. Test illegal transitions.
H2. ROLES: operator (view, record applied values), engineer (approve or reject), admin (users, machine packs). Enforce least privilege in the API, not only in the UI. Test every endpoint against every role.
H3. AUDIT LOG: append-only and hash-chained (each entry stores the previous hash); a verify command detects any edit or deletion.
H4. WORK-ORDER EXPORT, CMMS-agnostic: CSV and JSON files, plus an optional HMAC-signed webhook payload with recommendation id, unit, actions, checks, risk before and after, and approver. Outbound notification only; it never changes a machine.
H5. SHADOW MODE: runs on live or replayed data, stores recommendations, shows nothing to operators. A later job compares the settings actually used with what was recommended (retrospective adherence) and the risk that followed. This is the heart of an industry pilot.
H6. The follow-up feedback ("was the recommendation followed?") shares this store. Adherence: a_j = clip(1 - |applied_j - recommended_j| / max(|recommended_delta_j|, eps), 0, 1); adherence = mean(a_j); labels from config (Followed >= 0.80, Partly 0.40 to 0.80, Not followed < 0.40). The simulated operator stays labeled and excluded from real statistics by default.

PART B. SECURITY
S1. THREAT MODEL (docs/threat_model.md, STRIDE) with a data-flow diagram and trust boundaries. Include threats specific to this system: sensor spoofing, replayed or stale data, poisoned training data, tampered machine pack, tampered audit log, malicious webhook, confused-deputy approvals. For each: mitigation, test, residual risk.
S2. AUTH: authentication required by default (local accounts with strong password hashing, OIDC-ready config), short-lived tokens, CSRF protection, secure cookies, session timeout, login rate limiting. Secrets only from environment or a secret file; startup refuses default credentials.
S3. API HARDENING: strict pydantic validation with size limits; reject NaN and infinity; schema-based fuzzing (Hypothesis or Schemathesis) on every endpoint; errors without stack traces; request ids; locked-down CORS; security headers.
S4. INPUT-INTEGRITY DEFENSES: range and rate-of-change sanity on the input stream, cross-sensor redundancy through the coupling relations, stale or replayed timestamp detection, sudden-jump detection. On failure, withhold the recommendation (rule 34) and record why.
S5. ADVERSARIAL SENSOR TESTS: for a sample of states, search within plausible ranges for perturbations that make the system output a prescription that the simulator (simpump) or the four checks judge harmful. Report attack success rate and what caught the rest. List any successful attack in docs/limitations.md.
S6. SUPPLY CHAIN: pinned dependencies with hashes, pip-audit, Bandit, secret scanning, CycloneDX SBOM, license check. `make security` runs everything and fails on any high finding without a dated, documented exception.
S7. SAFETY CASE (docs/safety_case.md, claims-arguments-evidence): claims limited to advisory use, fail-safe behavior and traceability; hazards list (wrong recommendation accepted, ignored alert, spoofed data, stale model) with mitigations. State that it is not a certified safety case.

GATE: lifecycle, RBAC matrix, audit-tamper, export and shadow tests pass; every high threat has a mitigation and a test; fuzz tests pass; adversarial results documented; ruff, mypy, pytest green; commit and tag phase16-closed.
Reply with the RBAC matrix, audit-tamper result, attack success table, scan summaries and commit hash.
```

---

## Phase 17: Final dashboard (the simple, good-looking simulator)

**What it looks like.** A single page in four numbered steps: 1 Set the conditions, 2 Predicted risk, 3 Prescription, 4 Was it followed? A scenario bar on top, a machine selector in the header, and a follow-up log at the bottom. Everything technical sits under "Advanced". Take screenshots of the published design mock ("PrescriptXAI Operations Dashboard") at desktop and phone width and save them as `docs/design/dashboard_mock_desktop.png` and `docs/design/dashboard_mock_phone.png` before you run this phase.

```text
PHASE 17: FINAL DASHBOARD. A SINGLE-PAGE SIMULATOR.
Read AGENTS.md, PROGRESS.md, the frozen RecourseResult schema, machine specs and adapters, Phases 15 and 16, the Phase 7 results and the existing dashboard. Compare against docs/design/dashboard_mock_desktop.png and dashboard_mock_phone.png. Inspect the repo and adapt names. Do not delete analysis code: move it under an "Advanced" sidebar section. The default and only main page is described below.

RULES
R1. Every figure on the main page comes from the real model, real result files or live computation. A test scans the main-page source and fails on hardcoded numbers. The mock's numbers are placeholders.
R2. Simulated operator rows are labeled "Simulated operator (demo)" in every table, chart and export. They are stored with mode = simulated and excluded from real-feedback statistics unless the user toggles them in (then the title says so).
R3. Plain language on the main page. No Mahalanobis, tier, surrogate, protocol, k_max. Technical names live in tooltips and Advanced.
R4. Never claim extra machine life or physical proof. Say "predicted risk" and "model-based checks". Limits are removed from the main screen but kept complete and accurate in the "About this view" panel and in Advanced.
R5. Colour-blind-safe: status uses blue, amber and vermilion with text or icon, never colour alone. Contrast at least 4.5:1. Controls at least 44 px. Works at 390 px wide (panels stack, tables scroll sideways). Keyboard accessible; every slider has a visible label and a number.
R6. Works offline: bundle IBM Plex Sans and IBM Plex Mono (or use the system font stack); no runtime network calls.
R7. Stale-result safety: every computed result carries a hash of its inputs; a result whose hash differs from the current slider values is never shown as current.

DESIGN TOKENS (match the mock; implement via .streamlit/config.toml plus a small CSS file)
Page background #F3F5F8, card #FFFFFF, border #DDE3EA, text #17212B, muted text #566474, accent blue #1D4ED8. Status: safe or fixable teal #0B5F6E on #E3F3F5; watch or partly fixable amber #6B4400 on #FFF2CF; alert or needs maintenance vermilion #A8310F on #FCE9E2. Cards have a 12 px radius and a 1 px border, no heavy shadows. Large risk numbers in IBM Plex Mono, labels in IBM Plex Sans. Numbered step badges 1 to 4 in the accent colour. Provide a dark theme with matching tokens.

LAYOUT (one page; panels stack on narrow screens)
HEADER: product name, a one-line purpose, a machine selector filled from GET /machines (every label, unit, slider range, sentence template and noun comes from the machine spec; the choice is stored in the URL), a mode badge (Alerts only, Advisory (shadow), Advisory (live)), and a chip "Sample data - replay of <data source>" (text from the spec). Synthetic machines show "Synthetic machine (framework test)".
SCENARIO BAR: preset buttons generated from real states by a script (never hand-picked): one healthy early-life state, one fixable alert, one partly fixable alert, one end-of-life alert. Name them by what they are. Add "Reset" and "Copy link to this scenario" (all slider values in the URL).

STEP 1: SET THE CONDITIONS (left card)
- Base state: a real (unit, time) state chosen by a preset or a unit selector. It supplies every sensor value the user does not override. Never synthesize a sensor vector from nothing.
- Group "Situation (fixed)": cycles or time run (moves along the unit's recorded trajectory) and the context features of the spec. Slider ranges come from the data (1st to 99th percentile), never hardcoded. These are frozen: the system never recommends changing them.
- Group "Current settings (the operator can change these)": one slider per controllable feature, bounded by the spec's real bounds. Under each slider the prescription changes, show "Recommended: <value> (<% change>)" in the accent colour.
- When a slider moves, dependent sensors update through the coupling model so the state stays consistent; show the note "Related readings update with this slider".
- UNUSUAL-COMBINATION WARNING: if the user-built state fails the plausibility check, show an amber banner: "This combination of conditions is unusual for real machines. The risk estimate may be less reliable." Still score it.

STEP 2: PREDICTED RISK (right column, top)
- Large "Risk now" (calibrated true model, colour plus text from tau_safe and tau_danger), an arrow, "With the prescription", a one-sentence plain explanation from explain_result, a triage badge (No action needed, Fixable now, Partly fixable, Needs maintenance) and a meter with Safe, Watch and Alert zones and Now and After markers.
- "Risk now" updates instantly while sliders move (predictor only, target under 50 ms).

STEP 3: PRESCRIPTION (right column, bottom)
- "Change these settings": one to three rows with name, from -> to, % change, a track showing the move inside the allowed range, and a "Why" line. The Why line is REAL: for each action, the points of predicted risk that single change removes, measured with the true model, plus the feature's plain-language template. Add "Not changed: ..." for frozen features.
- "Safety checks": four rows with a pass or fail icon, text and a plain hint: Predicted safe; Looks like normal behaviour; Within control limits; Sensors stay consistent. For machines with a simulator add a fifth row, "Simulator check (synthetic machine)". Results come from the same library functions as the CLI and API.
- States: SAFE ("Nothing to change"), FIXABLE, PARTLY FIXABLE (best allowed result and "schedule an inspection"), NEEDS MAINTENANCE ("Setting changes cannot make this machine safe. Plan maintenance." plus a log-only "Schedule maintenance" button).
- WITHHELD: when data quality, input integrity or a mandatory check fails, or the machine is in Alerts-only mode, show "Recommendation withheld: <plain reason from the scorecard or check>" instead of a prescription.
- "Try your own change": the user edits the settings by hand and sees "Your settings: risk X%, checks n of 4" next to "Prescription: risk Y%, checks 4 of 4".
- "Send for approval" moves the recommendation through the Phase 16 lifecycle (roles decide which buttons appear). "Apply recommended settings" moves the settings sliders to the prescription, re-scores, and opens Step 4 with the recommendation snapshot stored.
- COMPUTE STRATEGY (never block the UI): (1) instant tier: predictor risk; (2) FAST tier: prescription computed after a short delay or on a button press, with a "Calculating..." skeleton, using the Phase 6 FAST mode and a cache keyed by the input hash; (3) if the FAST budget is exceeded, show the cached result for the nearest cached state with a "cached" badge. In Streamlit use session state, fragments and caching so only the affected panel reruns; if Streamlit cannot reach the targets, say so in docs/design_diff.md and propose the smallest change.

STEP 4: WAS THE RECOMMENDATION FOLLOWED? (full-width card; your teacher's feedback feature)
- Capture: buttons "Followed as recommended", "Followed partly", "Not followed", plus sliders for the applied value of each recommended setting. "Not followed" takes an optional reason (not feasible, disagree, no time, other). Applied values are stored as entered.
- ADHERENCE (computed): a_j = clip(1 - |applied_j - recommended_j| / max(|recommended_delta_j|, eps), 0, 1); adherence = mean(a_j); labels from config: Followed >= 0.80, Partly 0.40 to 0.80, Not followed < 0.40. One bar per action.
- OUTCOME (real scoring): re-score the APPLIED state with the true calibrated predictor and re-run the checks with the same library functions. Show "Risk after applied settings" beside the prescription's risk and "Checks passed: n of 4".
- TREND CHART: predicted risk over the next 30 cycles with and without the change, both labeled "model prediction", dashed safe and alert levels. For replayed units add a third line labeled "Observed in the recorded data". For simulator machines add the closed-loop result.
- "Record this follow-up" appends to the log. Follow-up log table: scenario, result, adherence, risk before -> after, source ("Operator (this session)" or "Simulated operator (demo)"). Scrolls sideways on phones.
- "Simulate operators" (sidebar, not the main flow): seeded compliance draws, applied states built by interpolation between current and recommended, scored with the real model, stored as mode = simulated.

FOOTER: SDG 9 line and a button "About this view and how it was checked" opening a short panel: data source and what "sample data" means; the four checks in plain words; assumptions (model-based checks, benchmark or synthetic data, step-limit assumption, proxies for settings); what a real deployment adds (engineer sign-off, shadow pilot, validated simulator); the simulated-operator note; machine pack hash, protocol version and run id.

ADVANCED (sidebar, never on the main page): Onboarding wizard (Phase 15); Approvals queue and Audit log with a "verify chain" button (Phase 16); Data quality and Drift monitor (Phase 18); Machine packs; Evaluation results per machine (Phase 19); full limits.

LOGIN: use the Phase 16 authentication and roles; the offline rule still holds.

TESTS
- AppTest: the page loads for each registered machine and each role; each preset renders; moving a slider updates risk immediately; the prescription appears after the compute step; stale results never display (R7); "Try your own change" shows both columns; each state (safe, fixable, partial, needs maintenance, withheld, Alerts-only) renders; the unusual-combination banner appears for an implausible slider combination; follow-up capture and outcome re-score; the URL round trip reproduces the same state.
- Unit: adherence on constructed cases (exact = 1.0, opposite = 0.0, half = 0.5) and boundaries 0.40 and 0.80; outcome uses the true model; per-action risk contributions are consistent with the total drop within tolerance; frozen features never change; slider bounds equal the spec bounds.
- Policy: hardcoded-number scan of the main-page source; banned-jargon scan of main-page text; no machine or feature name hardcoded in dashboard source; simulated rows labeled and excluded from real statistics by default; About panel lists the assumptions; works offline.
- Performance: instant tier under 50 ms; FAST tier meets the Phase 6 budget on the presets (report p95).
- Responsive and accessibility: screenshots at 390 px and 1360 px in docs/screenshots/, contrast and keyboard checks, and docs/design_diff.md listing every difference from the mock (fix or justify).

GATES
1. Two classmates who have not seen the project use the page for 2 minutes with no help; record what they said and where they hesitated in docs/usability_notes.md; fix what confused them.
2. Each team member explains the four steps in 60 seconds using only the page.
3. ruff, mypy, pytest (coverage not lower) green; PROGRESS.md updated; commit and tag phase17-closed.
Reply with the test summary, performance numbers, screenshots list and commit hash.
```

---

## Phase 18: Deploy and monitor

```text
PHASE 18: DEPLOYMENT, CI AND MONITORING.
Read AGENTS.md (rules 36, 40). The user develops on Windows with uv and mingw32-make; keep Windows parity.

P1. PACKAGE: pyproject with optional extras (api, dashboard, sql, security, dev); version from one source; `uv tool` or `pipx` install works; CLI entry point `prescriptxai`.
P2. DOCKER: multi-stage Dockerfile for api, dashboard and worker; docker-compose with volumes for machine packs, data and logs, healthchecks, restart policy and an env-file template; SQLite default, PostgreSQL option. Non-root user, read-only root filesystem where possible, dropped capabilities, minimal base image, image vulnerability scan.
P3. CONFIG: environment-variable overrides with a documented table; validation at startup with clear errors.
P4. OFFLINE INSTALL: `make wheelhouse` and docs for air-gapped installs (many industrial sites have no internet).
P5. CI (GitHub Actions): lint, types, tests with a coverage gate, security scans, container build and scan, docs build; artifacts (wheel, SBOM, image digest). A nightly job runs the C-MAPSS regression and the closed-loop suite.
P6. `make verify` runs everything needed for a release on Linux and Windows; `make demo` starts the API, dashboard and sample data for both machines in one command.
P7. MONITORING: per-machine drift monitors (PSI and Kolmogorov-Smirnov per feature, plausibility-distance drift, risk-score drift) with a plain status (Stable, Watch, Drifted); calibration and performance tracking when outcomes arrive, with CIs and "not enough data" when events are few; AUTOMATIC DEMOTION from Advisory to Alerts only when drift or data quality collapses (promotion stays manual); /health, /ready and /metrics (Prometheus text format); structured JSON logs; retention and delete commands for stored feedback and logs.
P8. MACHINE-PACK REGISTRY: versions with hashes, metrics and status (candidate, shadow, active, retired); a candidate runs in shadow beside the active pack with a comparison report; one-command rollback; refuse a pack that fails verification.
P9. DOCS SITE (mkdocs): quickstart, concepts, adding a machine, data requirements, onboarding, operations, security, API reference, troubleshooting, FAQ.

GATE: a fresh clone on a machine without the dev environment runs `make demo` using only the README; CI green; image scan has no unwaived high findings; drift detected on injected shifts and not on null shifts; rollback tested; commit and tag phase18-closed.
Reply with the CI run summary, image size, smoke-test result, drift detection table and commit hash.
```

---

## Phase 19: Evaluation and pilot playbook

```text
PHASE 19: EVALUATION AND INDUSTRY PILOT PLAYBOOK.
Read AGENTS.md (rules 32, 37, 38, 39), the Phase 7 outputs and all machine reports.

PART A. EVALUATION
E1. Produce reports/<machine_id>/ for every registered machine: validity, plausibility, joint success, triage rates, validity-versus-K curve, unit-bootstrap CIs, early-warning and all-alert populations, FAST latency. Add the closed-loop table for machines with a simulator.
E2. A comparison page lists machines side by side with run labels (machine id, spec hash, protocol version, K, population). No pooled numbers. Add the section "What generality we tested": machines (real benchmark or synthetic), what was identical (core code, checks, tests), what was machine-specific (spec, adapter, model, limits).
E3. ABLATIONS per machine: without plausibility, without coupling, without step limits, without sparsity, and a risk-model-only baseline. Report how often the weaker version accepts a prescription that a stronger check rejects.
E4. BASELINES: plain alerting without a prescription, a simple rule-based fix, and an off-the-shelf counterfactual method (for example DiCE if installable; otherwise a documented simple counterfactual baseline), compared on validity and plausibility.

PART B. PILOT PLAYBOOK AND INDUSTRY DOCS (docs/ and templates/)
B1. Stages: offline replay on historian data; shadow mode; advisory with approval. Closed-loop control is OUT OF SCOPE and stated so. For each stage: entry and exit criteria, duration guidance, roles, data needed, risks.
B2. KPIs and how to measure them: alert precision and lead time, recommendation acceptance, adherence, predicted-versus-observed risk change, withheld-recommendation rate and reasons, time to decision, false-recommendation reports. Success criteria are agreed BEFORE the pilot (template).
B3. TEMPLATES: data-request checklist, engineer sign-off form, risk register, pilot charter, safety-case template, incident log.
B4. ROI WORKSHEET: a parameterized spreadsheet or YAML model whose inputs the industry team enters (downtime cost, maintenance cost, alert volume, acceptance rate). No default figures presented as results; output shows ranges.
B5. docs/for_plant_managers.md: two plain-language pages: what it does, what it needs, what it does not do, what a pilot costs in people time, what to ask the vendor team.
B6. docs/standards_mapping.md: a table mapping system parts to ISO 13374 data-processing blocks, ISO 14224 failure-mode vocabulary, OPC UA data access and IEC 62443 zone and conduit ideas, titled "alignment guidance, not compliance".

GATE: every table has run labels; ablation and baseline tables complete; templates open and are complete; ruff, mypy, pytest green; commit and tag phase19-closed.
Reply with the comparison summary, ablation findings, baseline findings and commit hash.
```

---

## Phase 20: Final audit, viva pack and release

```text
PHASE 20: FINAL AUDIT, VIVA PACK AND RELEASE.
Read everything. Use a SEPARATE subagent for the audit; the agent that built the work does not grade it.

F1. INDEPENDENT AUDIT (docs/final_audit.md): rules 1-40 compliance with evidence per rule; claims audit (search docs and UI for "extends life", "works on any machine", "proven", "certified", "compliant", and unlabeled synthetic data); leakage audit per machine; reproducibility from a clean clone (`make verify`, `make demo`); test counts and coverage; regression baseline; security scan status; dashboard hardcoded-number scan; traceability to synopsis objectives. Every finding gets an owner, severity and fix or accepted-with-reason.
F2. Fix all high-severity findings, then re-run the audit on the changed parts.
F3. VIVA PACK (docs/viva_rehearsal.md): at least 40 likely questions with answers citing screens, files and real numbers. Include: "Does it work on any machine?", "Why is the second machine synthetic?", "What does the simulator prove?", "Is this safe to use on a plant?", "What if sensors are spoofed?", "How do you know the model is calibrated?", "Why not 95% on all alerts?", "What did each team member build?", "What does the simulated operator show?", "What would you do with six more months?".
F4. EVALUATOR GUIDE: update docs/evaluator_guide.html (plain-language guide for someone who knows nothing) with the final per-machine numbers and the "What generality we tested" section. Keep the placeholders only for numbers that do not exist.
F5. FINAL REPORT (docs/final_report.md): problem, background (predictive versus prescriptive maintenance, algorithmic recourse), design, the framework and machine specs, validation checks, results per machine with run labels, operations and security, deployment, pilot playbook, limitations, SDG 9 (Targets 9.1 and 9.4, modest wording), conclusion and future work. Figures generated from result files.
F6. DEMO RUNBOOK (docs/demo_runbook.md): a 7-minute script (problem, set conditions, risk, prescription, checks, follow-up, second machine, onboarding glimpse, audit glimpse, results, SDG 9), exact scenarios, start command, cached fallback and a backup plan.
F7. HANDOVER: README with a five-minute quickstart, CONTRIBUTING, architecture diagram, team roles and who built what, a license (propose a permissive default and record the choice), citation file.
F8. RELEASE: version 1.0.0 tag, release notes, built wheel, SBOM, image digest, checksum file; smoke-test the release artifacts.

GATE: no open high audit findings; clean-clone verify and demo pass; commit and tag v1.0.0.
Reply with the audit summary (counts by severity and status), test and coverage numbers and the checksum list.
```

---

## Orchestrator (optional)

```text
ORCHESTRATOR for Phases 12-20.
Read AGENTS.md (rules 1-40), PROGRESS.md and docs/prompts/final_phases_12_to_20.md (this file). Execute Phase 12 to 20 in order.
For EACH phase: (1) run the phase prompt in full; (2) run its gate (ruff, mypy, pytest with coverage, phase-specific checks, the C-MAPSS regression test, and the contract suite once it exists); (3) update PROGRESS.md and docs/traceability.md; (4) commit and tag phase<N>-closed; (5) send a short status with real numbers and open issues; (6) start the next phase only after the gate passes.
STOP and report (do not continue) only if: a test failure survives two root-cause fix attempts; the C-MAPSS regression changes; a rule in AGENTS.md would be violated; a manual decision or download is needed (offer a default); or a result looks implausibly good (run the leakage audit first). You may use subagents for independent audits, never for the work being audited.
Do not skip tasks. If a task cannot be done, record it as Partial or Not met with evidence in docs/traceability.md and continue.
```

---

## One paragraph for your report and viva

"PrescriptXAI extends predictive maintenance for industrial machinery and engines. A machine is described by a spec file and a data adapter. The system predicts the risk of failure, prescribes the smallest allowed change to the machine's settings that lowers it, and checks the prescription for model safety, normal behaviour, control limits and sensor consistency, plus a simulator check where a simulator exists. It is advisory only, withholds recommendations when data or checks fail, records approvals and what operators actually did, and ships with onboarding, security, monitoring and a pilot playbook. We tested it on NASA C-MAPSS jet engines and a synthetic pump. A real plant would still need engineer sign-off and a shadow-mode pilot."

## Cautions

- Run Phase 12 first. A refactor on top of unresolved results hides problems.
- The more you add, the more you must defend. Every capability needs a test and an honest limit. Drop stretch items before you drop tests.
- Do not tell an examiner the system is safe for plants, certified, or proven on real machines. Say it is a tested reference implementation with a pilot protocol.
- Phase 16 security is where your cybersecurity branch shows. Keep it even if you trim elsewhere.