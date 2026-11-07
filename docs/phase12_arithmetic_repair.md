# Phase 12: audited arithmetic cause and repair

## Evidence and scope

The complete graph/scaler factorial ran under committed configuration
`configs/experiments/phase12-arithmetic-v1.yaml`, original source
`17fece8773a0820efa1ce96a834a66144333dc5e`, with the explicitly registered second
execution segment at `28853b0375fd58663c7362ec5034bb4f71b87574`. Segment two finished
native 0 on 7 November 2026 at 05:04:06 UTC. Its extra 712 current controls and 47
retained-arm rechecks agreed exactly. All 759 original payloads, including timings,
were retained; 2,089 missing factorial observations were appended. The first segment's
termination cause remains unverified. This was two disclosed segments.

Independent complete-record audit passed for 2,848 observations, 102 input files,
183 registered hash entries and 65 production source blobs. Evidence:
`artifacts/phase12/arithmetic-complete-independent-audit/report.json`, SHA256
`e7fa55021c67e3718d82c839eb12c7df1d0463ea1e0ed237d3b7a047d357bb4f`.

| Factorial arm | Cases differing from historical, abs1e-6/rtol0 | Cases differing at exact equality |
|---|---:|---:|
| Current shared graph and C-order copy | 712 | 712 |
| Historical separate graphs only | 10 | 492 |
| Historical scaler layout only | 702 | 704 |
| Both historical factors | 0 | 0 |

These are all selected diagnostic cases, FAST/full/seed1729, from FD001/FD002 XGBoost
under protocols v1/v2 and the original held-out, grouped-OOF and official populations.
Counts describe mismatch recovery, not pooled machine performance. The complete
classification, identities, units, differences and threshold margins remain in
`artifacts/phase12/closure-712-20261106-v1/classification.csv` and the independent
report. No diagnostic-subset headline or new generalization estimate is inferred.

## Demonstrated causes

Sharing the feature-lift autograd graph between risk and feasibility feedback changed
floating-point gradient accumulation and hence L-BFGS-B search trajectories. Restoring
separate callbacks recovers every historical candidate and primary risk exactly,
including all 704 changed candidates (36 changed direct supports, 668 changed values
on the same direct support). It removes all 15 Tier 2 and three joint/triage flips.
No primary scorer disagreement was found in the independent 1,424 saved-candidate
score comparisons. No wall-clock search stopping or lockfile version mismatch was found.

The scaler fast path forced a C-order copy where StandardScaler preserved memory order.
Logical scaled values were identical, but tensor strides differed, changing float32
surrogate reduction arithmetic. The independent 5,696-row scoring audit reproduced
each saved historical surrogate score exactly with historical layout, and each repaired
score exactly with C-order layout. Production and historical tensor calibration agreed
within either layout. Maximum layout-only surrogate difference was
1.1026859283447266e-6. This explains the eight originally identical-candidate discrepancies
and the ten surrogate-only residuals after graph restoration (two other candidates
become identical after restoring graphs). Both factors recover every selected historical
scientific field exactly; zero unexplained selected mismatches remain.

## Repair and deterministic policy

`FittedFeatureScaler.transform` retains its input/order/finite/fitted-width guards and
uses `copy(order="K")`. Tests compare both logical values and strides against the installed
StandardScaler for C/F layouts, both input precisions, all centering/scaling flags,
and two-row 18/24-feature float32 tensor matrix operations. Inputs remain unmodified.
`RecourseOptimizer.solve` uses separate feature lifts for risk and feasibility feedback.
The generic objective's optional shared API remains available to existing callers.

Loaded-model search now honors the existing `model.torch_deterministic` setting through
PyTorch's deterministic-algorithms policy; unsupported nondeterministic operations fail.
This is a process-wide policy: an opt-out request does not disable an already enabled
policy, so concurrent requests cannot weaken it. Training/global-policy reconfiguration
must use a separate process from serving requests.
The prior diagnostic flag was false and is disclosed in its retained receipts. Enabling
the configured policy is an additional guard, not the cause inferred from the factorial;
its parity must pass the new full-corpus runs. No fitted bytes or scientific configuration
are changed. Per-query NumPy RNG uses the configured seed. Existing finite solver
iterations, line-search, restart, grid and support limits are retained; wall-clock is
reporting only. Stable first-minimum selection follows deterministic candidate enumeration;
stable support ranking retains configured feature order on equal magnitudes. No new tie
rule is chosen from observed outcomes.

## Full-corpus registration and pending gates

Focused repair checks: 60 tests passed in 10.25 seconds, Ruff clean, strict mypy clean
for 65 source files and strict documentation build passed in 4.12 seconds. These checks
do not replace the fresh full software gate on the final committed source.

Independent production review issued conditional GO for the fresh full gate and the
registered full pair, with no static blocker. Receipt:
`artifacts/phase12/arithmetic-repair-independent-review/review.json`, SHA256
`de5ee0953a144d108d5043e7663de784dc48694773bbf6e9d4b9107e286faa43`.
The reviewer performed zero scientific queries and did not implement the repair.

`configs/experiments/phase12-corrected-pair-v1.yaml` registers two consecutive full
32,116-query/24-group runs using the unchanged baseline execution configuration and runner.
Commit the repair/registration and pass independent code review plus a fresh full software
gate before launch. Preserve both runs under their new IDs and the same source/runtime;
any mismatch stops dependent execution with every completed result/timing retained.
No healthy run overlaps source edits or another gate. Quality timings do not certify latency.

Discrete settings, supports, verdicts and triage must match exactly. Retain abs1e-6/rtol0
for floating reports: it is the original absolute reporting envelope, not a relaxed
outcome-dependent rule. The factorial's combined recovery is exact even at zero tolerance.
Margins within 1e-6 in each predicate's native units are separately flagged borderline;
verdicts are never rounded or changed. Full-corpus errors must be assessed before any
future numeric-policy decision.

Headline recomputation, whole-engine bootstrap CIs with engine counts/all failure
denominators, pairwise complete audit, fixture promotion, an actual full-corpus regression
on a clean clone with byte-verified external assets, final software gate, ledger and
closure commit/tag remain pending. Historical results and fixtures are unchanged.
The open-item ledger and synopsis status counts are not changed by this diagnostic result.
Maximum evidence remains E3 under C-MAPSS proxy assumptions, with no physical-benefit,
real-machine safety, certification or RUL-extension claim. Phase 12 remains open.
