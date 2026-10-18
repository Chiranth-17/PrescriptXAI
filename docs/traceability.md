# Phases 5–11 requirement traceability

## Orchestration preflight — 2026-10-18

Status: **Not met — required source instructions are unavailable.** No phase has started under the
new Phases 5–11 orchestration request. No phase gate, commit, or closure tag is claimed.
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

Phases **5, 6, 7, 8, 9, 10, and 11** are **Not started** for this orchestration. Their individual
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
execution now. Phase 6–11 and Part B remain unavailable; no replacements are invented.

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

Phases 6–11 still require their actual prompts and the actual Part B table. No such content was
invented and no later closure tag is claimed.
