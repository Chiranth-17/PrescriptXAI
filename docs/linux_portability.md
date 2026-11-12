# Linux portability status

## Measured scope, 13 November 2026 IST

The Windows clean-clone verification at `e97fbdb` passed. The Linux clean-clone
demo at `909986c` also passed both named-machine API assessments and dashboard
HTTP readiness in 445.506961002 seconds, with its own locked environment and
fresh FD001 and separately synthetic sample fits. HTTP readiness is distinct
from complete browser acceptance. Linux scientific and software verification
has **not** passed. Phase 18 remains open; there is no final release.

The later Linux recovery retained that demo without refitting. Its original
volume was mounted read-only and a separate volume held a verified snapshot of
the original clone, environment and all 28 demo files. All 109 registered asset
pairs matched, and installed package versions matched the original Linux
environment. No Windows cache was imported.

## Failed verification and preserved evidence

The actual Linux `make check` failed with native exit 2. `make verify` and the
outer Linux/host controllers also failed. Pytest reported 787 passed, 7 failed,
4 setup errors, one release-only full-marker deselection and 74 warnings in
5,838.86 seconds. Combined coverage was 85.39239084655343%, below the unchanged
86.64259927797833% floor. Package line coverage derived from the saved JSON was
88.55877468167559%. Subsequent configured coverage-report commands, security,
distribution build, installed-wheel smoke and strict docs were not reached.

All 15,525 requested cases have fresh saved observations, 15,525 registered
inputs and zero uncommitted cases in the retained SQLite database. Its integrity
check passes. This is computation completion, not regression success. Comparison
failed at the first unlisted `/config_hash` difference, and no record was
admitted into the regression cache. There is no passing subset completion
receipt. Native exits, logs, database/WAL/SHM, cases, every observation including
timings, segment records and cache are preserved under
`artifacts/phase18/linux-verify-recovery-909986c-v1` and its original stopped
container/volume. `failure-preservation.json` pins the files. No retry was made.

## Complete saved-record diagnosis

The root read-only comparison covers all 15,525 failed Linux observations and
their genuine immutable Windows references. It is not an independent audit,
new execution or accepted-difference policy.

| Finding | Observed count or value |
| --- | ---: |
| Configuration hashes differ | 15,525 |
| Full case/config values equal after path-separator normalization | 15,525 |
| Each original hash matches its own original serialized configuration | 15,525 on each side |
| Other fields differ exactly, excluding only the separately classified config hash | 7,101 cases |
| Other fields differ beyond the existing absolute 1e-6 envelope | 1,547 cases |
| Tier 2 verdict changes | 52: 35 pass-to-fail and 17 fail-to-pass |
| Joint-success and triage changes | 14: 10 ESCALATE-to-RECOVERABLE and 4 reverse |
| Tier 2 flip cases within the 1e-6 borderline band | 0 on either side |
| Largest absolute final-risk difference | 0.1932961316758587 probability units |

These counts describe this complete fixed diagnostic subset, not a pooled
headline success rate or fresh-engine generalization. The existing 24-group
Windows estimates and engine intervals remain unchanged. The per-case and
per-group outputs, full native-field maxima and selection IDs are in
`artifacts/phase18/linux-parity-diagnosis-909986c-v1`.

Canonical production/helper hashes, all registered scientific input hashes,
baseline design hash and workers=4/CPU-threads=1 execution policy match across
the runs. Python is 3.13.9 on both, while their platform/native-build fingerprints
differ. This does not establish a particular numerical-library cause. The
non-borderline verdict changes must not be labelled harmless float noise.

Separately, native path serialization changes legacy machine-spec identities;
the archived FD001 preset manifest fails closed on Linux. Four simulator fixture
setups and related UI/API tests consequently fail. A fitted golden test also
reports differing numerical explanation text. The scope and causes of these
software failures need individual repair and tests. Their existence is not
permission to weaken hashes, skip tests, change the golden or lower coverage.

## Preregistered fixed-vector diagnostic

The committed design `configs/experiments/phase18-crossscore-v1.yaml` registers
53 cases: every Tier 2/triage flip plus the largest final-risk-delta case. It
revalidates the exact original, saved Windows candidate and saved Linux
candidate on both runtimes, 159 rows per runtime. It uses only original pinned
fitted artifacts, genuine LSTM history and the production prediction/validation
functions. There is no search, propagation, projection, refit or new intervention
population. Each runtime's own saved-state control must reproduce exactly before
interpreting cross-runtime differences. The study ran after committing its design and implementation (`10d6390`).
Both runtime controls passed exactly: 53 cases and 159 rows each, with no fit,
optimization or new solver query. All selected cases are FD002/XGBoost, across
five protocol/population groups; this does not cover FD001 numerical-only gaps.
For all 106 fixed-candidate pairs, true risk, numeric validation fields and the
four pass/fail verdicts match exactly across the runtimes. One pair retains a
formatted surrogate-warning text difference (`0.129527` versus `0.129526`).
Nothing was silently rounded or accepted. The full raw reports and comparison
are preserved in `artifacts/phase18/crossscore-20261113-v1`.

For these selected cases, the original Tier 2/triage changes therefore follow
different candidate vectors produced upstream of final validation. This localizes
the failure; it does not identify the numerical operation or establish a repair.
Surrogate computation, gradient/optimizer execution, deterministic ordering and
process-start context still require controlled investigation. All 1,547 original
out-of-envelope cases remain unaccepted. The complete per-dataset diagnostic
counts are 828 FD001 and 719 FD002; these are fixed-subset discrepancy counts,
not scientific population success rates or new engine intervals.

No threshold, bound, rate, model, tolerance, baseline, case population or
known-difference list is changed. Do not launch another regression until the
retained discrepancies have been investigated. Any repair affecting numerical
execution needs preregistration and appropriate verification. Linux remains
partially verified, and Phase 19 release gates remain unmet.

For the academic Phase 2 evaluation, use the established Windows demonstration
and the supplied report with its original snapshot. The public benchmark and
synthetic sample are advisory demonstrations, not evidence of physical efficacy,
RUL extension, engineer confirmation or certified plant safety.
