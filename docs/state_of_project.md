# State of the project - Phase 12 in progress

**Latest status,5 November2026 IST:** the user explicitly resumed diagnosis/repair after
an independently verified2,589-case mismatch in the complete32,116-query run. The selected
five-case factorial diagnosis completed20calls/native0 and independently isolates calibration
arithmetic for those examples. The proposed repair selects legacy math only for24exact
audited model hashes; other missing versions keep currentmath with a warning. Explicit
versions remain authoritative. Correctedfocused60tests pass; fullgate, independent repair
review, full32,116replay, fixturepromotion andcleanclone verification remainpending.
Phase12 is open and Phase13 has not started. [Repair policy and evidence](phase12_regression_repair.md).
The [complete failed run](phase12_regression_failure.md) remains immutable. Automatic
continuation was recreated after the user's continue; historical stop receipts are preserved.

Status date: 4 November 2026. The user supplied and authorized the complete
[Phases 12-20 prompt](prompts/final_phases_12_to_20.md). Phase 12 adds no product features;
its full scientific regression and clean-clone verification are still pending.

The existing implementation is a C-MAPSS research reference, with a typed library,
configuration, CLI, API, Streamlit dashboard, four separate checks, sparse proxy recourse,
experiment checkpoints and reproducible reports. It has been evaluated on NASA C-MAPSS
FD001 and FD002; the benchmark is simulation-derived, not industrial actuator telemetry.
Software test fixtures are separate from those benchmark results. No synthetic-pump
implementation or generic industrial-machine capability is claimed yet.

## Verification and history

The initial Phase 12 `mingw32-make all-checks` exited **0**: **540 tests passed**, **66**
expected short-fit warnings, **250.98 seconds** for pytest. Ruff passed; strict mypy passed
for **65 source files**; strict documentation built in **3.71 seconds**. Overall elapsed
time was **264.8431117 seconds**. Product source is `a6e6067fbd91a5db98ac969a1bd3ba5f03fa13dd`;
the check ended at the prompt/governance-only commit
`f36db81671dcfeb32ea8b41f17eb921aa344f67c`. Exact logs and exit metadata are in
`artifacts/phase12/initial-full-gate.log` and `initial-full-gate-status.json`.

Coverage did not decrease: scoped **7663/8426 = 90.94469499169239%**;
full-package **7663/8519 = 89.95187228547951%**; branch-inclusive
**9757/11277 = 86.52123791788597%**. These results precede the new regression helper;
its focused 25-test check is separate and does not substitute for the final full gate.

The final prelaunch gate subsequently passed **573 tests / 66 warnings / 240.99 seconds**,
Ruff, strict mypy65 and strict docs4.16s, native exit0. Full elapsed time was251.9467118s.
It includes all33 new helper probes, including actual-result corruption tests, both serialized
and object checkpoint paths and finish-time source/config/asset/code/runtime changes.
Coverage increased to scoped **7664/8426 = 90.95656301922621%**, full
**7664/8519 = 89.96361075243573%**, branch-inclusive **9759/11277 = 86.5389731311519%**.
`configs/experiments/phase12-quality.yaml` ratchets these exact floors without extending
exclusions; `make all-checks` enforces both the historical and the new quality gates.
Output: `artifacts/phase12/registered-prelaunch-full-gate.log` and its actual exit metadata.
This is a prelaunch software pass, not the pending measured regression or Phase12 closure.

Closure tags `phase4-closed` through `phase11-closed` exist. `phase1-closed`,
`phase2-closed` and `phase3-closed` are absent. This is a documented historical exception,
not permission to manufacture contemporaneous closure evidence. The current worktree was
clean after the prompt-preservation commit, before adding the Phase 12 verification files.
No `phase12-closed` tag exists at this checkpoint.

The complete Phase 11 frozen replay finished **34,298 records / 64 groups** and passed
both saved seed comparisons plus **576 whole-engine confidence-interval objects**.
Those records remain on their original source and populations. The complete research draft
and editable 26-slide deck subsequently passed independent review; publication and native
PowerPoint application interoperability remain separate limitations.

## Headline results and their scope

The [complete target/CI/gap matrix](final_targets.md) contains every one of the **24**
headline model/protocol/population strata. It is the authoritative result table; this
checkpoint does not reassign old numbers to new code. Every group has its original run,
config set, engine count, seed observations, protocol, K and D_max labels.

Historical run `phase7-20261020T102540Z`, measured source
`63c2ed445fba16c73a2771e184f635abf76b4405`, committed study
`configs/experiments/phase7-study.yaml`, SHA256
`67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`:
FAST, all alerts, five solver seeds, k_max=3, assumed K=1, D_max v1=5 / v2=8.
FD001 XGBoost/MLP miss the all-alert 95% model-validity target; the frozen LSTM achieves
no model-valid intervention. FD002's model validity is high but distribution/coupling
failures remain visible. Both Tier 2 denominators, Tier 3, Tier 4, joint success, support
and true-model risk drop are reported separately. Validity alone is weak evidence.

Historical serial FAST optimization p95 is **2339.07478 ms**, whole-engine 95% CI
**[2256.86622525, 2403.2715535]**, **16 engines / 1000 calls**: the **1800 ms** upper budget
is missed by **539.07478 ms**. The serial population is the FD001 XGBoost/v1 development
workload, config runtime hash
`47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271`, K=1, k_max=3.
It is distinct from both the 60-state quality-development sample and the headline test
populations. Current repaired-source serial results and full browser interaction timing
are not yet available. No p95 budget is closed by a partial or parallel quality run.

The [open-item ledger](phase12_open_items.md) contains all 31 earlier exceptions plus
19 additional obligations: **7 Closed / 8 Open / 35 Accepted-with-reason**. The
[current synopsis map](traceability.md) has **35 Met / 18 Partial / 11 Not met** rows.
The [Phase 11 map](traceability_phase11.md) is preserved unchanged.

## Complete regression freeze

The independently reconstructed fixed-seed headline is **32,116 FAST/full queries across
24 groups**: all internal held-out, grouped out-of-fold and official-test alerts for
FD001 XGBoost/MLP/LSTM and FD002 XGBoost, both protocols, solver seed 1729. No development
or first-alert subset replaces these populations. Every failed query remains included.

`configs/experiments/phase12-baseline-v1.yaml` registers the complete group and engine counts,
original source, case/record fingerprints and absolute tolerance **1e-6**, with **zero**
relative tolerance and exact discrete verdicts/triage/counts. It will be committed with the
protocol before solving. `scripts/diagnostics/phase12_baseline.py` preserves full per-case
inputs, genuine LSTM histories, candidates, four verdicts, effective settings and timings.
The preflight verified all **97 frozen inputs**; this is not yet numerical parity evidence.

Independent code review accepted runner SHA256
`9969081fa976a1c86e294c31d30266ebf6b109a84421f47ee9257d6ab45c088b`
and Windows runtime config SHA256
`be26bf6ce264db835d62a193bec19b4f7c7e5818a1e57a7c7097a9c4119a7978`.
Approval is conditional on a clean preregistration commit of those exact bytes. The runner
retains both original and actual parsed runtime cases, explicit new run labels, source and
config hashes. Streaming limits expanded cases to bounded in-flight work, without reducing
the population. It owns a verified temporary Windows idle-sleep request for the entire run.

Only the fully completed, independently checked measured output may become
`tests/regression/cmapss_baseline.parquet`. This requested test corpus is the narrow explicit
exception to keeping generated measurements out of Git. Raw archives and fitted weights
remain excluded. A clean-clone replay needs byte-verified provision of those external fitted
assets; it must fail clearly when they are absent, never skip or substitute a toy model.

## What remains weak and what changes next

The bounds, rate limits, control proxy mapping and K are assumptions. Statistical coupling is
not causal physics, and observed bootstrap endpoint intervals are not certainty about new
machines. Maximum current evidence is E3 under these assumptions. Strict fresh-engine/once-ever
history cannot be reconstructed retroactively. Field safety, lifespan, resource savings,
downtime and RUL extension are not established. Missing simulator/actuator data is an honest
limitation; it does not prevent continuing the authorized reference implementation.

The new requirements do not retroactively make the legacy API secure by default or supply
engineer sign-off/readiness modes. Phase 12 is local research replay, not deployment of that
service. No industrial connection or actuation is enabled.

| Phase | Queued change, subject to its complete gate |
|---|---|
| 13 | Versioned machine specifications, adapters, right-censoring, data quality, generic contracts and an unchanged C-MAPSS regression. |
| 14 | Shared feature/asset templates and an explicitly synthetic pump with known-truth simulator tests. |
| 15 | Resumable onboarding, engineer sign-off, hashed packs and evidence-gated manual promotion. |
| 16 | Approval lifecycle, adherence/outcome records, roles, authentication, input integrity and security verification. |
| 17 | One-page four-step dashboard with stale-input protection, measured UI performance and responsive/accessibility checks. |
| 18 | Clean installation/deployment, offline dependencies, CI, drift/health monitoring and pack rollback. |
| 19 | Per-machine evaluations/ablations/baselines plus advisory pilot templates and guidance. |
| 20 | Independent final audit, viva/report/demo handover and a verified v1.0.0 release. |

No engineer identity, classmate usability result, hosted CI receipt, public repository or
published design mock is fabricated. If unavailable, its obligation retains a concrete
Partial/Not met diagnosis and the prescribed blocker protocol applies.
