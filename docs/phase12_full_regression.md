# Phase 12 complete regression and impact registration

## Coverage reporter equality fix - 8 November 2026 IST

The first provisioning fix in v2 passed all657 software diagnostic tests (66 warnings,
310.62s), including every previously failed/skipped path. True coverage returned exactly
to91.01415094339623% scoped /90.02682841479063% full /86.64259927797833% combined.
The diagnostic nevertheless exited1: the installed coverage plugin compares the total
rounded to12 decimal places with the unrounded86.64259927797833% floor. At exact equality,
86.642599277978 is incorrectly judged lower. This is a reporting precision defect;
no covered lines or branches were lost. All v2 receipts and exact coverage counts remain
in `artifacts/phase12/clean-clone-attempt2-diagnostics/failure-preservation.json`; no actual
full gate or full replay was launched in v2, and that clone is preserved.

The second root-cause fix increases report precision to17 while retaining every exact
coverage floor. A regression test uses the installed coverage comparison to require that
equality passes and even the next representable float below the floor fails. No metric,
coverage exclusion, scientific tolerance, model, bound, population or verdict changes.
The updated attempt2 registration uses a NEW v3 clone with the same97+3 genuine inputs,
its own locked environment, focused/complete software diagnostics, strict docs and an
independent prelaunch GO before the next actual full32116 replay/gate. If this second
root-cause fix fails, preserve the result and stop for review; no silent third fix/retry.
Phase12 remains open with unchanged ledger counts. The independently audited attempt1
scientific replay is exact over all32116 cases and101382 borderline rows; final audit
SHA256 `3a43f1cbdbad9e19022bad3a48b1fdccdf5cb68fd5ccac1694635b37a04b88a7`.

## Clean-clone attempt1 regression PASS; full software gate FAIL - 8 November 2026 IST

Source `bac3d653c9bde86588dd7878a0c30fd47e617015` completed the genuine clean-clone
32,116-query/24-group regression with native exit0 at05:55:00UTC. Both the mismatch
list and exact-float difference list are empty. The wider `all-checks` gate ended
05:56:16UTC with native exit2:656 passed,1 failed,1 skipped,66 warnings in26,623.24s.
A packaged taxonomy CRLF mismatch failed the workspace initialization test; omitted
FD001 training CSV caused the existing real-data test to skip. The omitted genuine
raw archive bypassed the default dashboard ZIP route, losing2 covered lines/1 branch:
combined coverage86.6161838513692%, below the retained86.64259927797833% floor.
Strict documentation and subsequent coverage gates were not reached. Scientific replay
success does not certify the whole software gate. Phase12/A10 remain open; noPhase13/tag.

All failed clone outputs, including every query and timing, remain intact. Seventeen
originals and exact copies are pinned in
`artifacts/phase12/clean-clone-gate-attempt1-preservation/preservation.json`.
Independent saved-evidence audit pin passed all97 inputs,67 source/helper files and
17 preservation pairs (pin SHA256 `85de007857ae4faa4997baa2dc41a39e34f5d4689d56c76b15a4c147defa797a`).
Full independent science audit is pending. The failed v1 clone is immutable.

The explicit first root-cause fix is provisioning in a NEW v2 clone: restore the exact
registered historical bytes for both tracked taxonomy and packaged duplicate, prove
canonical Git blobs/index tree unchanged, and provide the genuine hash-pinned CSV/archive
outside Git. Registration: `configs/experiments/phase12-clean-clone-gate-attempt2-v1.yaml`.
No production, test, threshold, tolerance, model or population change is needed. Focused
checks and a disclosed software-only diagnostic precede independent prelaunch review;
then a separately recorded `mingw32-make all-checks` must genuinely replay all32,116 again.
No passed receipt or cached result replaces the actual test. Floors are never lowered;
quality timings do not certify serial latency. Ledger counts stay8 Closed/7 Open/35 Accepted.

## Independent full-pair PASS and fixture promotion - 8 November 2026 IST

Independent audit `corrected-pair-independent-audit/report.json` SHA256
`6efa7a8304c277562bde0822cd1b148c94dc62cbabe8945ff6fd606736e33861` passed all64,232
new observations, all32,116 cases per run, all97 external input bytes and66 source/helper
files. A/history, B/history and A/B scientific outputs and complete validation/settings
match EXACTLY, including floats; maximum measured scientific/margin difference0.
No unexplained mismatch, support/tier/triage flip or case/config hash change remains.
All negative queries stay included:696 infeasible intervals and78 mandatory-sparsity
failures per run. Those78 retain withheld nearest diagnostics above k_max, returned=false,
action_feasible=false/joint=false/ESCALATE, exactly as historical. The auditor corrected
and preserved preliminary reviewer assumptions about Windows path normalization and
these rejected diagnostics; no production result was changed to satisfy the audit.

The approved complete A export is now promoted to `tests/regression/cmapss_baseline.parquet`,
59,294,365bytes, SHA256 `382bbf1fac0f0a467e252772b8a47c94e9460bc9bb02196d312e6ac401cb3f15`.
Its adjacent committed manifest records all97 external hashes and both completion/audit
proofs. No fitted weights or raw archives are added. Actual clean-clone replay/full gate
remains pending; promotion alone is not Phase12 closure.

Complete impact run `phase12-impact-20261108-v1`, config committed before aggregation,
analysis source `0d0e6db33bdc47b87ffcd601985eda910fccaf3d`, native0, all24 groups and32,116
queries per run: every historical/A/B estimate, whole-engine CI and denominator/count
matches exactly. Report JSON SHA256 `31707dc3e8687e2db8db6764439fcdaaeba6693bf951cad6fa807ae09379bc7f`.
Full side-by-side tables: [headline impact](phase12_headline_impact.md). This restores the
original reference, with no new performance or fresh-generalization claim. Only failed
intermediate Phase12 arithmetic results are superseded for headline use; all archives
remain immutable. Borderline export includes304,146 run/predicate rows over three
identical corpora, including structural zero check margins; no verdict is rounded or
changed. Aggregate Tier4 margin is within1e-6 for13,538 cases per corpus.

A separate clean clone with its own locked133-package environment is prepared outside
the protected historical checkout. Independent final tool/fixture review, actual complete
clean-clone replay and full software/coverage gate remain pending. Phase12 remains open;
noPhase13 or phase12-closed tag. Ledger A11 closes on independent full parity:8 Closed/7 Open/35 Accepted-with-reason; A10 stays Open for the pending clean-clone gate. Objective statuses remain unchanged.

Both corrected runs at source `3441e259b7b57c5ca4b8981298deb24acb1c0ae0` finished all
32,116 queries and 24 groups with native exit 0 and zero runner historical mismatches.
The independent complete pair audit must give GO before fixture promotion. Runner
completion alone does not close Phase12. The source/input audit pin passed for all97
registered inputs; full independent record audit remains pending at this registration.

## Actual replay contract

`scripts/diagnostics/phase12_regression.py` reads the derived audited parquet fixture.
Its committed adjacent JSON manifest binds the fixture, execution design, all97 external
input bytes, reference runtime and independent approval. The fixture contains genuine
case inputs, including fixed observed LSTM contexts, and reference observations. It does
not contain fitted weights. External model/calibration/coupling/distribution artifacts
stay outside Git, at the exact relative paths and SHA256 values in the manifest.

Missing fixture, manifest or external asset is a test failure. No downloading, refitting,
toy substitute, reduced population, automatic skip or existing completed receipt is used.
Every test invocation starts a fresh child process and actually solves all32,116cases
with the existing four-worker/one-thread production experiment runner. The slow marker
does not exclude the test from the default suite. New output directories are unique;
previous partials and timing records are preserved and never silently overwritten.

The comparison covers every observation field except variable timing and rounded
presentation prose (`validation/*/diagnostics` and check `explanation`). All numerical
validation measurements, limits and margins, check names/verdicts, evidence, assumptions,
effective solver settings/counters, supports, triage and nested status fields remain in
the comparison. Discrete types and values are exact; numeric floats retain abs1e-6/rtol0.
Exact float differences are also reported. Native tier margins within1e-6 are listed
separately without rounding or changing verdicts. Every actual checkpoint/timing persists.

Inputs, current source files and runtime are hashed before and after replay. Imports must
resolve to the executing checkout. Numerical dependency versions match the audited
reference; the local package version can evolve because this test gates later refactors.
Source must be fully committed. The replay is parallel quality evidence, not a serial
latency measurement, and reaches at most E3 under existing proxy assumptions.

## Clean-clone gate

After independent fixture approval and committing the infrastructure/fixture, create a
new clean clone outside the protected historical replay. Install its own locked uv
environment, then copy only the registered external inputs to their required relative
paths and verify every SHA256. Do not copy old run databases or any completion receipts.
From that clone, run `mingw32-make all-checks`; its default pytest suite includes the
actual full regression above. Native stdout, stderr, exit, coverage, replay checkpoints
and complete/comparison receipts are retained. Source and assets stay frozen during
the healthy run. Never call this gate passed before actual native0/full completion.

The last passed652-test software gate measured scoped91.01415094339623%, full90.02682841479063%
and combined86.64259927797833%. These floors are ratcheted into the gate and cannot fall.

## Headline impact

`configs/experiments/phase12-impact-v1.yaml` registers analysis run
`phase12-impact-20261108-v1`. `scripts/diagnostics/phase12_impact.py` reads all original
and corrected observations and recomputes old/A/B estimates and whole-engine intervals
for every original dataset/model/protocol/population group. Every row has engine N and
its actual denominator; all-query failures, conditional returned counts and triage
counts are explicit. Bootstrap seed1729,2000replicates,95% confidence are unchanged.
No result is pooled across datasets. Earlier results stay immutable. Empirical [1,1]
bootstrap intervals do not establish certainty on unseen engines.

Planned commands, after independent GO and a committed fixture:

```powershell
uv run python -m scripts.diagnostics.phase12_impact --output artifacts/phase12/phase12-impact-20261108-v1
uv run pytest tests/regression/test_cmapss_baseline.py -v
mingw32-make all-checks
```

The second command is the real full solve, not a small smoke test. Running the third
command already includes it; no duplicate full solve is required for the same gate.
Final Phase12 ledger/status updates and the closure commit/tag require the independent
pair audit, full impact report and actual clean-clone regression/full gate to pass.
