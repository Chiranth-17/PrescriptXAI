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

## Registered first-objective gradient probe

`configs/experiments/phase18-gradient-probe-v1.yaml` registers the next diagnostic,
using the same 53 cases and both saved candidates. Before collecting gradients,
each runtime must reproduce all 159 earlier native scoring/validation controls
exactly. A diagnostic-only interception captures the first dense production
objective and raises before SciPy executes. It restores the original callback
even on an error; harness tests verify that no numerical solver is invoked.

The probe records unchanged raw-vector scaling, surrogate risk and derivatives,
and the captured objective's full and separate risk/feasibility gradients.
Candidate-derived dense points use the existing production bounds and lift;
they are diagnostic evaluations, not newly solved recommendations. Every full
objective is evaluated twice with fresh graphs and must agree exactly. This
does not execute optimizer iterations, refit models, alter historical data or
authorize another regression. A difference could further localize the numerical
path; it would not alone establish a particular kernel cause or a valid repair.

The registered probe ran at `38a8c9e`. Both runtimes completed 53 cases and
159 rows, reproduced all prior native scoring/full-validation controls exactly,
and passed every fresh-graph repeat. All fixed raw/scaled inputs, feature and
control orders, tensor strides, bounds, decisions and solver options match.
There were zero SciPy iterations, new solver queries or fits. Operational
Windows/Linux times were 23.6510266999976/17.77520129000186 seconds, not latency
benchmarks. Original stopped containers and volumes remain unchanged.

| Fixed-state diagnostic field | Differing rows of 159 | Maximum absolute delta |
| --- | ---: | ---: |
| Direct surrogate risk | 80 | 5.364418029785156e-7 |
| Direct surrogate gradient | 159 | 9.059906005859375e-6 |
| Dense objective value | 130 | 5.9655678112946475e-6 |
| Dense full gradient | 136 | 0.0002199386049852592 |
| Dense risk-component value or gradient | 159 | 1.6710791203244924e-5 |
| Dense feasibility-component value or gradient | 116 | 2.2560016077477485e-9 |
| Dense lifted features | 107 | 2.1496693314304594e-14 |

In particular, all 53 original first-start objective gradients differ before
any optimizer iteration. Direct surrogate gradients also differ for all 53
cases on identical fixed scaled tensors. This establishes a numerical-path
difference before SciPy, separate from final true-estimator validation. It does
not identify a particular linear-algebra kernel, prove that it explains every
later search divergence, or establish a portable repair. FD001 discrepancies
and independent legacy identity/software failures remain outside this probe.

An additional diagnostic control is deliberately reported separately: direct
surrogate values on saved candidates exactly match the historical recorded
surrogate in only 34/106 Windows and 26/106 Linux evaluations. Maximum native
differences are 8.642673492431641e-7 and 7.152557373046875e-7 respectively.
The direct-gradient probe uses a newly constructed contiguous float32 tensor;
its call layout is not asserted to reproduce every archived surrogate call.
These values are retained, not accepted or used to replace saved results. The
earlier original-risk/full-validation controls do reproduce exactly on each
native runtime. Do not describe this as exact reproduction of historical
gradients, which were not recorded.

Receipts, native exits, all raw gradients, exact field differences and maxima
are under `artifacts/phase18/gradient-probe-20261113-v1`. The original failed
subset remains failed, all 1,547 out-of-envelope observations remain unaccepted,
and no regression, numerical policy or production math was changed.

For the academic Phase 2 evaluation, use the established Windows demonstration
and the supplied report with its original snapshot. The public benchmark and
synthetic sample are advisory demonstrations, not evidence of physical efficacy,
RUL extension, engineer confirmation or certified plant safety.
