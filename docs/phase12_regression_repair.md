# Phase 12 calibration compatibility repair - verification pending

The user explicitly resumed work after the regression stop on5November2026. The failed
32,116-query run and its complete mismatch/audit evidence remain unchanged. Phase12 is
still open; Phase13 has not started. The expected outputs and absolute1e-6/relative0
acceptance rule are unchanged.

## Controlled diagnostic

Diagnostic run `localization-v1`; source
`d220d56b470176e5797e8e7eb3c3d1cb95dfb6fa`; config
`configs/experiments/phase12-localization-v1.yaml`, runtime SHA256
`0447dc33743fc8afa5c1cda4e0ad022a1f09fbe91abeea80735591e259b9d6cb`.
Five preregistered failure examples, four factorial arms,20actual queries, seed1729,
original effective configurations, K1/k_max3 and each original v1/v2 threshold/population.
These are selected counterexamples, not a representative evaluation population or pooled
performance measure. All original fitted inputs are unchanged; all outcomes/timings remain
in `artifacts/phase12/localization-v1/records.sqlite3`.

Current code and historical feature-graph construction alone each reproduce zero of five
historical cases. Restoring historical calibration arithmetic alone reproduces all five,
including while retaining the shared graph. Restoring both also reproduces all five.
All20calls completed, native exit0. This isolates the calibration change for these cases;
it does not prove complete-population parity or establish physical benefit.

## Repair and version policy

Calibration hardening changed the differentiable map's precision, clipping and interpolation
for already fitted objects without versioning that numerical behavior. True NumPy scoring
remained unchanged, but optimization followed different gradients and selected different
candidates. Unit-level approximate gradient equivalence was insufficient to detect this.

`ProbabilityCalibrator` now versions its tensor arithmetic. Newly constructed/successfully
fitted instances persist `tensor_map_version=2`, retaining the hardened float64 NumPy-aligned
map. Missing metadata does not identify an old map: post-Phase9 fits also lack that field.
A fitting commit alone is insufficient because a bundle may have been recalibrated later.

The loader therefore migrates only the exact24 audited historical model artifact SHA256
identities to version1 in memory. Their bytes match the original frozen input manifest;
their five distinct fitting-source commits all contain the same complete tensor-method AST
as source63 (AST SHA256 `8eaadfb76cb404fa14547432bb21a27a86888db21b9fb1fc9b6999471af60163`,
computed with Python3.13.9 `ast.dump(include_attributes=False)`). The committed identity inventory is
`configs/experiments/phase12-calibration-migration-v1.yaml`; its ignored source receipt is
`artifacts/phase12/calibration-migration-provenance.json`, SHA256
`d0c85cefc15c300933d7412d8b37574a4750cda6076c43ff376fc1a819c15617`.
The decoded bytes must match the fingerprint used for migration, and the saved fitting
source must match that identity's audited provenance. No frozen artifact is rewritten.
Explicit version1/2 is authoritative; a new fit is always version2 even on an old bundle.

Every other unversioned bundle preserves the immediately preceding version2 behavior and
logs that its original numerical contract is unverified. An unversioned standalone
calibrator also defaults to version2. This conservative compatibility default is not a
claim that every unknown historical artifact has a verified original contract. Further
legacy identities require source/byte evidence, never a better observed recourse outcome.
All finite/range/shape guards remain active before either map; unknown explicit versions
fail, including through the NumPy probe used by artifact loading. The version1 constant
isotonic case has a finite zero derivative. True NumPy risk computation, final safety
validation, weights, bounds, rates, thresholds and solver settings remain unchanged.

This is internal fitted-artifact numerical compatibility metadata. The public RecourseResult
and ValidationReport schemas remain2.0.0. Their version/owner rules are not bypassed or changed.
It is not a new configurable solver knob selected to pass a target.

The initial, broader missing-metadata policy passed595tests/66warnings in322.44s, Ruff,
strict mypy65 and strict docs. Its scoped/full/combined coverage was
90.99184300744768% /90.0023386342376% /86.59720995938548%. Those checks preceded the
independent review's artifact-ambiguity correction and do not verify the final policy.
The corrected exact-byte migration, fresh software gate and complete32,116-query replay
remain pending. No five-example pass closes that gate.

Independent exact-byte review:24/24model hashes and fitting sources match both the original
manifest and baseline inputs; all24unversioned raw objects resolve to v1 through the public
loader; all files remain unchanged. The registry map, committed YAML and provenance receipt
agree. Audit `artifacts/phase12/calibration-migration-independent-audit/audit.json`, SHA256
`dbe3603521cd1ffbd5fdb04c3bf79952d8d88bd81f852fd81d66802676e1de48`.
The reviewer gives conditional approval for the full replay only after a fresh passing
software gate and clean preregistration commit. No full-population parity is established.
