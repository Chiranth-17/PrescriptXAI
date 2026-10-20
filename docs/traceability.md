# Phases 5–11 requirement traceability

## Orchestration preflight — 2026-10-18

Historical status: **Not met — required source instructions were unavailable.** At this preflight
no phase had started under the new Phases 5–11 orchestration request. Later direct Phase 5/6 prompts
supersede this missing-input status for those phases; see their task records below.
A separate read-only audit independently confirmed the missing inputs and older-roadmap mismatch.

- **Full Phase 5–11 prompts — Not met.** `docs/prompts/remaining_phases_5_to_11.md` does not exist.
  `Test-Path` returned `False`; a repository search, including hidden paths, found no file with that
  name. The existing `.gsd/phases/5/01-PLAN.md` belongs to the earlier roadmap and cannot establish
  the contents of the newly requested seven phase prompts.
- **Part B change table — Not met.** `docs/prompts/phase_changes.md` does not exist, and the current
  user request does not include the Part B table to copy into it. The known conversation attachment
  `Pasted text.txt` contains Phase 4 closure tasks C1–C12 only, not the requested Phase 5–11 prompts
  or Part B. The changes file must be populated from the supplied table rather than invented.
- **Referenced AGENTS.md rules 12–21 — Met.** The user supplied these ten rules after the initial
  preflight; they are now included verbatim. The ten unnumbered original rules, numbered additions
  22–29, and the per-phase status instruction have all been preserved.

## Phase execution status

At preflight, phases **5, 6, 7, 8, 9, 10, and 11** were **Not started** for this orchestration. Their individual
tasks and gates cannot be enumerated or marked complete until the referenced source prompts and
Part B changes are available. No implementation task has been skipped or replaced with an inferred
task. Earlier completion labels in `PROGRESS.md` describe the previous roadmap, not these missing
phase prompts.

## Required inputs to resume

The remaining required sources are `docs/prompts/remaining_phases_5_to_11.md` and the Part B table
(or the document containing it). After these are available, copy the Part B table into
`docs/prompts/phase_changes.md` and start Phase 5. Preserve the closed Phase 4 protocols and
measurements.


## Phase 5 direct prompt — closed revision

The user supplied Phase 5 directly after preflight. This supplies its tasks/gate and authorizes
execution. The user subsequently supplied Phase 6 directly. Phase 7–11 and Part B remain unavailable;
no replacements are invented.

| Prompt task | Implementation / evidence | Final status |
|---|---|---|
| 1. Training-only shrinkage/Cholesky, regimes, both quantiles, reference choice | validation/tier2_mahalanobis.py, validation/pipeline.py; statistical and regime tests | Met: real FD001 artifact fit; singular/regime/quantile/reference tests pass |
| 2. Bounds/rates with violation margins | validation/tier3_engineering.py reuses constraints/bounds.py | Met |
| 3. Validation-only residual calibration and per-rule margins | validation/tier4_coupling.py; calibration ID overlap tests | Met: 16 validation engines; saved calibration diagnostics |
| 4. True calibrated risk and surrogate warning | validation/tier1_model.py, shared pipeline | Met |
| 5. Dynamic hook and skipped NullSimulator, evidence | validation/simulator.py, base.py, versioned schemas | Met: explicit skipped NullSimulator and interface; E4/E5 unavailable |
| 6. Ordered modes and independent verdict truth table | validation/pipeline.py; all sixteen combinations tested | Met |
| 7. Shared in-search constraints and bounded refinement | validation/feasibility.py; recourse/objective.py and optimizer.py | Met: 752 integrated population rows; refinement cap verified |
| 8. Engine-bootstrap paired/integrated funnels | scripts/diagnostics/phase5_validate.py, validation/funnel.py | Met: 42 funnels, before/after CIs, two protocols and K curve |
| Full OOF all-alert paired replay | Saved sample retains 11 missing records; separately evaluate actual first alerts | Partial: no before candidates for every OOF alert |
| New unseen-engine generalization after validator change | No new public FD001 engines beyond existing populations | Not met; paired replay explicitly labeled |

No generated telemetry or simulator results substitute for missing evidence. A measured target
miss is recorded with gap analysis, not treated as an implementation blocker.


### Phase 5 closure gate evidence

`docs/phase5_changes.md` contains all run/config/git/protocol/population labels, before/after
engine-bootstrap CIs, coupling/covariance diagnostics, headline target gaps and measured latency.
Real-run source is `8b1a206fc1800a0674019b6e0527c2a31a5159df`; preregistration is
`d64826c5c1bd69dc6310c7c2d11506a7add11822`. The phase-specific audit reproduced frozen
predictor scores and distances, checked all twelve engine partition sets, and found no accepted
constraint or safety violations. Rejected infeasible development diagnostics remain visible.

Final `mingw32-make all-checks` exited zero: Ruff, strict mypy, 215 pytest cases with 79.7753%
coverage (displayed 80%), and docs presence checks. Independent audits were read-only; their
findings were fixed by the primary agent. No predictor, risk gate, physical bound, proxy rate,
sigma multiplier or D_max was tuned using evaluation results. New real-data outputs, validators
and caches remain git-ignored. E3 is a proxy constraint level, not causal or real-machine safety.

Phases 7–11 still require their actual prompts and the actual Part B table. Phase 6 is authorized
by the subsequent direct prompt. No missing content is invented.

## Phase 6 direct prompt — closed with measured performance gaps

The directly supplied Phase 6 prompt is the specification for this implementation. Its preregistration
is committed at `9921c38`; measured implementation is `a72832c`; subsequent interface corrections
are committed at `79cb7f4`. No frozen predictor or constraint setting changed in those corrections.

| Prompt task | Implementation / evidence | Status |
|---|---|---|
| 1. Public factories, assessment, recommendations, batches, explanation | `pipeline.py`; typed facade, artifact fingerprints, bounded CPU workers, structured explanations | Met: factory, serialization, process/single parity and explanation tests passed |
| 2. Full result, triage, provenance, timings, schema freeze | `schemas.py`; schema 2.0.0 snapshots and `schema_changelog.md`; strict round-trip consistency | Met: snapshots frozen, all three triage cases covered; real PARTIAL remains above tau_safe |
| 3. Below-alert gate | Zero change below tau_danger; exact boundary tests; independent tier diagnostics retained | Met: 0.79/0.80 boundary and zero-change checks passed |
| 4. FAST and THOROUGH | Request-local modes and recorded effective settings; production budget measured | Partial: both modes delivered; FAST p95<=1.80 s target Not met (OOF v1 6.84 s, v2 6.28 s) |
| 5. Real stage p50/p95/p99 | `evaluation/latency.py`, `phase6_pipeline.py`, `phase6_report.py`; direct total, engine CIs | Met: 600 real results, both modes/protocols, four populations; interrupted-run timing qualification retained |
| 6. Input handling | Vector/Series/dict, named order, finite values, units, observed history/context, typed errors | Met: malformed, NaN/inf/boolean, shape/unit/history and artifact mismatch tests passed |
| 7. CLI | Recommend by engine/cycle or JSON, batch CSV, assess, latency-bench, info; observed sequence context | Met: CliRunner plus real RECOVERABLE/ESCALATE and both-mode latency-bench delivery gates passed |
| 8. FastAPI | Six endpoints, OpenAPI, request IDs, 422/503, CORS, environment API key, actual-byte limit | Met: TestClient success/error paths, real high-risk parity and payload/security checks passed |
| 9. Cache/thread safety/model choice | Fingerprint cache, shared inference lock, request config copies, xgb/MLP/LSTM adapters | Met: concurrent threads, seeded repeatability, process parity, genuine fitted MLP/LSTM/history and batch-memory tests passed |
| UI rendering latency and cold startup | Excluded from backend timing; returned as unmeasured | Not measured in this phase; no inferred pass |
| Fresh unseen-engine efficacy / real actuators / dynamics | Previously evaluated public engines and documented telemetry proxies only | Not established; E3 maximum, simulator skipped |

Constructed fixtures exercise PARTIAL and negative cases only in tests. Real benchmark results are
never replaced with synthetic values. No deployment-readiness or causal maintenance-benefit claim
follows from a passing software gate. Phase closure can retain measured target gaps under rule 13.

### Phase 6 closure gate evidence

Population run `phase6-20261018T114827Z`, source `a72832c271015a2391ed452a9dca7776a5131a98`;
protocol snapshot committed before measurement; configs `configs/experiments/phase6-pipeline-v1.yaml`,
`phase6-pipeline-v2.yaml` and ten explicit fold configs. The complete run/config/runtime-hash labels,
K=1, k_max=3, D_max v1=5/v2=8, population definitions, independent quality metrics and engine-bootstrap
intervals are in `docs/phase6_changes.md`. All outcomes remain in their disclosed denominators.

`mingw32-make all-checks` exited zero on delivered runtime `d177460`: 260 tests passed, Ruff and
strict mypy passed (51 files), coverage 81.017036% versus Phase 5 79.775281%, docs check passed.
Both public schemas are frozen at 2.0.0 with serialization snapshot tests and migration notes.
The real CLI/API delivery smoke used `1e41d77`; subsequent annotation corrections passed the full gate.

The independent audit verified all 600 records, all 16 true-first-alert cohorts, 12 engine partitions,
36 fitted-artifact hashes and 16 committed config references with zero acceptance/leakage failures.
True-risk error was zero; maximum D_M error was 1.78e-15. Evidence is conditional on proxy assumptions,
at most E3. The raw run, delivery smoke and audit hashes are recorded in the report and PROGRESS.md.

FAST optimization and backend-total budgets remain Not met. The interruption-affected timings
retain all outliers; controlled steady-state latency remains unestablished. No frozen predictor,
risk threshold, D_max, actuator bound, rate limit or intervention horizon changed after outcomes.
Phase closure is recorded with tag `phase6-closed` and this target gap under rule 13.
