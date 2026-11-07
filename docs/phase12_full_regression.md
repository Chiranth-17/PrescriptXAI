# Phase 12 complete regression and impact registration

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
