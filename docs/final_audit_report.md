# Phase 11 final audit — exceptions

The independent audit is complete. Product source `4995c301331db78b1e31f58de3cdcd957b1ca336`
passed all **527 tests**, with increased coverage, installed reproduction, actual API/dashboard
checks and Docker verification. The installed workflow completed **20 queries / 11 engines**;
all attained evidence labels, 18 output hashes and 68 source hashes were verified.

Frozen source `63c2ed445fba16c73a2771e184f635abf76b4405` completed the entire registered
**34,298-query / 64-group** replay. Comparisons against historical seeds1730 and1729 each
found **zero mismatches**; all **576 whole-engine CI objects** passed independent checks.
Configs are `configs/experiments/phase11-seed1730-replay.yaml` and
`configs/experiments/phase11-audit.yaml`;
full hashes, tolerances, run labels and actual outputs are in [final verification](final_verification.md).
All completed records and timings are preserved in an independently verified raw backup.

Traceability contains **33 Done / 19 Partial / 12 Not met** requirements. The following
lists every one of the **31 Partial or Not met** items. Audit completion does not establish
the absent physical, historical-protocol or roadmap outcomes.

All synopsis requirements and implementing files/tests/evidence are in [traceability](traceability.md).
Every measured target/engine CI/count/denominator/gap is in [the target appendix](final_targets.md);
actual command outputs, failures and source identities are in [final verification](final_verification.md).
The following lists every current Partial or Not met row without hiding absent field evidence.

| Requirement / obligation | Status | Why |
|---|---|---|
| RQ — sparse, actionable, physically plausible interventions avoiding operating-distribution extrapolation | Partial | research question answered empirically for statistical/proxy action spaces; not established for actual actuator interventions. Substantial validity/plausibility gaps remain. |
| §1 safely restore operation without halting production | Not met | as a real-machine outcome. Software provides decision support and truthful escalation; no observed ongoing-production intervention. |
| §3 composite objective and x'=x+delta | Partial | for literal formula equivalence: implemented scaled control-space L1 plus propagated dependents, squared/linear hinge, hard masks/bounds and extra feasibility penalties; not literal raw full-state L1 or a certified global solve. Adaptations are documented. |
| §4 claim that four tiers guarantee no surrogate artifact exploitation | Partial | rejects false-safe surrogate outputs and specified constraint failures, but cannot guarantee completeness, physical safety or causal fidelity. |
| §5 graph node 1 sensor telemetry / pipeline table ingestion: 21-sensor C-MAPSS data | Partial | dataset ingestion and explicit single-state interfaces exist; no independently demonstrated industrial live-stream connector. Constant-channel filtering means predictors need not consume all 21 channels. |
| §7 bounded L-BFGS-B optimization 1.20–1.80s | Partial | implemented/measured; both upper budgets missed. Lower endpoint is not a minimum. Exact values/CIs in [target appendix](final_targets.md). |
| §7 UI <250ms | Partial | for literal complete UI latency: server construction passes, browser paint/network/loading/scoring/solve/attribution excluded. No browser p95 is established. |
| §7 total about1.5–2.2s | Partial | backend FAST misses and full end-to-end UI/network/startup total is unmeasured. Separate studies cannot be summed to manufacture a full-pipeline p95. |
| §8 validity >=95% | Partial | metric fully implemented, target population-dependent and missed on FD001. FD002 Tier1 is accompanied by poor plausibility/coupling/joint. |
| §8 distributional plausibility >=90% | Partial | FD001v1 and FD002v1/v2 miss; FD001v2 passes. Joint is not substituted for this metric. |
| §8 failure-risk reduction >=.60 | Partial | measured model-score target passes some populations, misses others; no physical failure reduction is established. |
| §8 simulated trajectory health conditional on simulator | Not met | as a measured outcome; optional interface is Done and absence is not an implementation blocker. |
| §9 controllable: Fuel Flow, Fan Speed, Bypass Ratio, Bleed Valve | Partial | against literal actuator taxonomy: all mapped channels are sensor proxies; no direct bleed-valve command or real actuator telemetry. |
| §9 immutable environmental: ambient temperature/pressure | Partial | generic freezing is implemented, actual requested environmental telemetry is absent. Do not silently equate inlet sensor readings with frozen ambient conditions. |
| §9 dependent: HPC temp, LPT temp, Core Speed | Partial | HPC/LPT/corrected core are covered, but physical core speed sensor9 is controllable in YAML. Disclose this mapping choice instead of claiming literal taxonomy identity. |
| §10 target9.4 resource-use efficiency / retrofit motivation | Partial | alignment discussion Done; measured contribution to9.4 Not met. |
| §10 target9.1 reliable, sustainable, resilient infrastructure motivation | Partial | alignment discussion Done; measured contribution to9.1 Not met. |
| §10 industrial effect: extends equipment lifespan | Not met | No dynamic response, lifespan or RUL intervention ground truth; prohibited as a current result. |
| §10 industrial effect: avoids premature disposal | Not met | No measured deployment, lifecycle or disposal evaluation exists. |
| §10 industrial effect: minimizes emergency downtime losses | Not met | No deployment, downtime, cost or operational economic baseline exists. |
| §11 research manuscript: academic paper submission / peer review | Partial | for manuscript preparation; actual complete submission and peer-reviewed publication Not met. Do not relabel outline as a paper submission. |
| §11 software: production Python library + Streamlit; open-source GitHub repository | Partial | as literal roadmap: local installable MIT package/UI Done; no configured Git remote or verified published GitHub repository. Production deployment/safety certification is not shown by package tests. |
| §11 presentation deck + live demo, covering problem/math/SDG | Partial | live demo Done, actual presentation deck Not met. Script/outline is not a slide deck. |
| §4 optional dynamic validation / E4–E5 | Not met | No validated dynamic execution exists. Conservative default is disabled; no real safety or RUL effect follows from proxy checks. |
| §6 replicated physical high-altitude cruise intervention | Not met | The illustrative risk/fuel/bypass percentages are not observed physical outcomes or efficacy targets. |
| §10 measured SDG 9.4 field contribution | Not met | Alignment is motivation; a model-risk reduction cannot establish resource efficiency. |
| §10 measured SDG 9.1 field contribution | Not met | Infrastructure benefit remains unmeasured. |
| §11 completed research paper submission / peer review | Not met | A skeleton/generated results table is not a completed submission or peer-reviewed publication. |
| §11 published public GitHub repository | Not met | Local installable MIT software is verified; no public repository publication evidence exists. |
| §11 authored presentation deck | Not met | Live demo is available; deck deliverable is absent. |
| Phase11 strict once-ever held-out evaluation and fresh-engine v2 provenance | Partial | Development-only predictor selection and fit isolation are supported; strict never-before-seen test/fresh-engine and every older diagnosis preregistration cannot be certified retroactively. |

Maximum available evidence is E3 under assumed proxy channels, bounds, rates and K. Model
validity, Tier2statistical plausibility, Tier3engineering checks, Tier4coupling and joint success
remain separate; none establishes real-machine safety or RUL extension. Future evidence
priorities are validated simulator integration, N-CMAPSS, first-principles coupling and richer
actuator telemetry. The missing paper/deck/publication/field outcomes are recorded as absent;
no feature was added to manufacture audit completion.
