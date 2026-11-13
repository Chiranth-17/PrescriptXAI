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

## Fixed-operation localization

The separately preregistered `phase18-operator-probe-v1.yaml` ran at `79b28e8`.
It selects three cases by the previously recorded largest surrogate-gradient,
full-objective-value and surrogate-value differences, with three fixed points
each. This selection supports diagnosis, not a population estimate. Both native
runs exited 0, reproduced all nine earlier surrogate values/gradients exactly,
and verified that sequential tracing reproduces the production forward and
backward path exactly. Windows/Linux operational times were 8.37/2.58 s.

Linux then replayed the exact Windows input operands at each existing operation.
All architecture and layer-parameter hashes match. On these common operands:

| Operation | Forward differences / 9 | All-ones VJP differences / 9 | Maximum forward delta | Maximum VJP delta |
| --- | ---: | ---: | ---: | ---: |
| First Linear | 9 | 9 | 2.980232238769531e-7 | 4.76837158203125e-7 |
| First ReLU | 0 | 0 | 0 | 0 |
| Second Linear | 3 | 9 | 5.960464477539063e-8 | 9.5367431640625e-7 |
| Second ReLU | 0 | 0 | 0 | 0 |
| Output Linear | 6 | 0 | 2.384185791015625e-7 | 0 |
| Probability sigmoid | 0 | 0 | 0 | 0 |
| Fitted calibration | 0 | 0 | 0 | 0 |

The first differing operation is the first Linear layer at every tested point.
The all-ones vector-Jacobian products are isolated operation diagnostics, not
the complete upstream-weighted gradient of an archived solve. Inputs to later
native operations can differ; the table deliberately compares common Windows
operands to separate that effect. Raw native and common-input traces are both
preserved in `artifacts/phase18/operator-probe-20261113-v1`.

The original runtime receipts record the same PyTorch package version 2.14.1
and source commit, but different native builds: Windows embeds MKL 2026.1
(product build 20260612), Linux MKL 2024.2 (product build 20240605). Both report
AVX2. Windows is built without CUDA; the Linux wheel is CUDA-enabled while all
these diagnostics execute on CPU. These are observed build differences, not a
controlled proof that replacing MKL alone repairs the full search. No backend,
dependency, precision, model or scientific policy has been changed.

The next numerical investigation should isolate a compatible native backend in
a separate environment, retain the original native controls, and test the
fixed-operation discrepancy before any search is authorized. A production
repair needs an explicit versioned execution policy and verification against
unchanged historical results; another complete regression is premature. The
separate legacy path-identity migration and Linux software failures also remain
open. Windows demo and original reports stay available; Phase 18 is partial.

## Registered isolated backend-policy check

Read-only ELF inspection retained under
`artifacts/phase18/native-linkage-20261113-v1` finds MKL/SGEMM symbols defined
inside the original Linux `libtorch_cpu.so` and no dynamic MKL library dependency.
This is a linkage observation, not a claim that an arbitrary external library
can safely replace the embedded implementation. No model was imported or scored
by that inspection; the original volume was read-only.

`configs/experiments/phase18-backend-policy-v1.yaml` preregisters four fresh
child processes: native and `MKL_CBWR=COMPATIBLE` on each OS, nine fixed points
per arm. Both arms log `MKL_VERBOSE=1`; each unchanged native arm must reproduce
the full previous native operation trace exactly. Compatible-arm changes are
explicitly retained. All arms require exact repeats and exact traced versus
public forward/backward paths. No solve, fit or production-policy change occurs.

This AMD host motivates testing the mode documented for non-Intel processors,
rather than assuming AVX2 CNR selection is supported. Intel documents the
`COMPATIBLE` policy and fixed-thread conditions in its
[conditional reproducibility guide](https://www.intel.com/content/www/us/en/docs/onemkl/developer-reference-c/2026-0/getting-started-with-conditional-numerical.html).
[PyTorch's reproducibility note](https://docs.pytorch.org/docs/2.14/notes/randomness.html)
does not promise identical results across platforms. These sources motivate a
diagnostic, not proof that a mode change fixes this application.

If the compatible arms agree with each other but change the approved Windows
native values, they demonstrate only a possible future execution policy. That
would not preserve the historical baseline or authorize another regression.
If the arms still differ, reject the mode-only repair and keep the negative
result. Original builds, package dependencies, baselines and tolerances remain
unchanged. This registration precedes calls; it is not a reported outcome.

The study subsequently ran at preregistered source `0079eee`. All four fresh
child arms exited 0, wrote nine points and repeated exactly. Each native arm
exactly reproduced all nine original complete operation controls. Native BLAS
logs confirm `CNR:OFF` versus `CNR:COMPATIBLE`, with one MKL thread in each arm;
the mode was actually applied, not merely echoed from an environment setting.

| Fixed-point contrast | Different surrogate values / 9 | Different gradients / 9 | Maximum surrogate delta | Maximum gradient delta |
| --- | ---: | ---: | ---: | ---: |
| Windows/Linux native | 9 | 9 | 5.364418029785156e-7 | 9.059906005859375e-6 |
| Windows/Linux compatible | 6 | 9 | 4.76837158203125e-7 | 6.67572021484375e-6 |
| Windows native/compatible | 0 | 0 | 0 | 0 |
| Linux native/compatible | 6 | 6 | 8.344650268554688e-7 | 8.821487426757812e-6 |

Both compatible arms still differ at the first Linear forward and all-ones VJP
for all nine common-input points. A `COMPATIBLE` mode setting alone is therefore
not a repair of this discrepancy. No setting was adopted into production, no
new dependency was installed into either original environment, and no search or
fit was executed. The negative result, all four raw arms, native logs and exact
comparison are preserved in `artifacts/phase18/backend-policy-20261113-v1`.
Operational arm times were 6.17/5.80 s on Windows and 6.14/2.42 s on Linux;
these are not latency-budget measurements.

Backend build/version alignment remains a candidate investigation, not a tested
fix. It must use a separate environment and fixed-operation controls before
any new search, without weakening historical comparison. Phase 18 remains open.

## Registered direct-SGEMM build comparison

`configs/experiments/phase18-sgemm-build-v1.yaml` registers a narrower library
comparison before any calls. The original fitted parameters and nine fixed
points are exported without scoring, guarded against bundle/network forward
calls. Each parameter hash must match both completed native operation traces.
All three Linear layers yield 27 fixed matrix operations. Raw operands remain
ignored outside version control and are bound to this registration by receipt.

The first arm loads the exact original Linux library in a fresh process without
importing Torch. Its explicit forward/bias and all-ones VJP SGEMM calls must
reproduce every saved Linux common-input operation exactly. If this control
fails, stop before interpreting or running the aligned-library arm. The second
arm uses the separately hash-pinned MKL 2026.1.0 Linux runtime. Both use unchanged
float32 operand bytes, one thread, GNU/LP64 mode, no `LD_PRELOAD` and no package
installation or changes to either original environment. Actual versions, hashes,
verbose dispatch, outputs and exact repeat controls are retained.

The runtime wheel and matching Linux license wheel were obtained from published
PyPI release metadata, verified against the registered raw SHA256 values and
kept outside the repository. A metadata-only first attempt incorrectly expected
one license wheel globally; the registry has Windows and Linux wheels. Its
assertion is preserved, and exact Linux-wheel selection was corrected before
any library or model call. See `mkl-release-metadata-20261113-v1` for provenance.

Even exact Windows agreement here would establish only a fixed native-operation
lead. It would not validate Torch integration, full gradients, complete search,
FD001 parity or a release, and would not authorize changing historical results
or launching a complete regression. A mismatch is retained as a negative result.
This is preregistration, not an observed outcome or adopted backend change.

The v1 guarded Windows operand export passed with zero forward calls, 27
operations and both original parameter-hash controls. Linux preparation verified
and extracted the runtime/license into a separate lab, but the embedded arm
stopped at metadata preflight before loading the numerical library or calling
SGEMM. The v1 registration had incorrectly pinned the Windows metadata JSON's
raw bytes on Linux. The original Windows file is 18,180 bytes with 204 CRLF
sequences; Linux is 17,976 bytes with LF. Their complete parsed JSON is exactly
equal. No original metadata or scientific input file has been changed.
All v1 receipts, original export, metadata copy, logs and failure remain pinned
in `sgemm-build-20261113-v1/failure-preservation.json`. Neither matrix arm has
produced a numerical result, and the aligned arm was not launched.

`phase18-sgemm-build-v2.yaml` preregisters the correction: exact original raw
metadata pins per native OS, plus an exact canonical binding of the complete
parsed JSON. Arbitrary whitespace or value changes still fail. Original asset,
fixture, design and production/helper guards remain. This is an explicit
diagnostic schema-2 registration, not a weakened scientific comparison.
It reuses only the verified runtime/license files from the failed setup, mounted
read-only and checked again against the pinned wheels; no numerical observation
is reused. New processes and output paths are required. Each attempted operation
is persisted before any failed-control rejection. Five ABI/metadata harness
tests passed in 0.57 seconds. At that registration checkpoint no matrix calls
had run under v2.

The registered v2 subsequently completed at controller source `77eb6e8`.
Since MAIN's dashboard code had changed, the Windows export used the preserved
v5 clone at `e97fbdb` with its own interpreter and imports. All original 90 source/
helper and 97 scientific input guards passed before export. It produced the
same 27 operand pairs as v1 with zero forward calls, fits or solves. Original
Linux model and runtime-lab volumes were read-only, and every extracted runtime/
license member was checked again against the pinned wheels.

| Fresh isolated library arm | Exact original Linux forward/VJP pairs | Exact original Windows forward/VJP pairs | Repeats | Native exit |
| --- | ---: | ---: | --- | ---: |
| Embedded MKL2024.2, build20240605 | 27/27 | 3/27 | Exact | 0 |
| Separate MKL2026.1, build20260612 | 3/27 | 27/27 | Exact | 0 |

Each pair includes the forward result and all-ones VJP from unchanged float32
operands/weights. The aligned-library Windows comparison has maximum delta0
for both fields. These are three cases/nine fixed points and all three Linear
layers, not a new population evaluation. Both children avoided importing Torch.
Actual verbose output retains 108 SGEMM lines per arm with one thread.
Operational times1.07675303/1.06065207 seconds are not latency certification.

Receipts and raw outputs are in `artifacts/phase18/sgemm-build-20261113-v2/`.
Its `comparison.json` recomputes all exact comparisons and pins the evidence;
the saved-file root verifier also confirms the original v1 failure files are
unchanged. This is a diagnostic arithmetic check, not an independent audit.

Aligning this isolated native build repairs the measured fixed SGEMM contrast.
It does not yet establish full Torch/autograd integration, complete gradients,
search outcomes, FD001 parity or a passing packaging/release gate. No production
environment, model, backend, threshold, tolerance or known difference changed.
Any integration proof needs a new committed design and isolated original
controls before calls. No complete regression is authorized by this result.

For the academic Phase 2 evaluation, use the established Windows demonstration
and the supplied report with its original snapshot. The public benchmark and
synthetic sample are advisory demonstrations, not evidence of physical efficacy,
RUL extension, engineer confirmation or certified plant safety.
