# Phase 12 repaired replay - regression gate still fails

Status: 6 November 2026 IST. All **32,116 queries** completed, but **712 cases** differ
from the frozen reference. Actual runner exit is **1**. No fixture or complete marker was
exported. Phase 12 is not closed; Phase 13 has not started.

The user orchestrator explicitly says to stop when the C-MAPSS regression changes.
Automatic continuation `prescriptxai-phases-12-20` was deleted again after this condition.
The earlier transport pause was explicitly resumed; this new stop is a scientific gate failure.

## Run identity and comparison

Run `phase12-repaired-20261104T231405Z`; measured source
`a6c906cb7bf5dd91184316a0910c31e75826085f`; implementation repair
`decf66c5c87444e6a5f288b86162e49824d8276e`. Configuration
`configs/experiments/phase12-baseline-v1.yaml`, runtime SHA256
`be26bf6ce264db835d62a193bec19b4f7c7e5818a1e57a7c7097a9c4119a7978`, committed LF SHA256
`9e7ce88d108d32beb39662284a3c806d46ebae4ed191960950fe61462965fcac`.
The runtime/blob line-ending disclosure is `artifacts/phase12/repaired-registration-provenance.json`.
Compatibility policy is `configs/experiments/phase12-calibration-migration-v1.yaml`.

Reference: `phase7-20261020T102540Z`, source
`63c2ed445fba16c73a2771e184f635abf76b4405`, original study
`configs/experiments/phase7-study.yaml`. Both sides contain all FAST/full cases in the
24 registered model/protocol/population groups: FD001 LSTM/MLP/XGBoost and FD002 XGBoost;
protocols v1/v2; internal held-out, grouped OOF and official-test alerts. Seed 1729, K=1,
k_max=3, D_max=5/8 and the original thresholds, bounds, rates, models and populations remain
fixed. All failures remain in the population. These are regression counts across labeled
groups, not pooled model-performance rates. Parallel quality timings do not certify latency.

Acceptance remains absolute tolerance **1e-6**, relative tolerance **0**, with exact
structural, tier, triage and count identities. The complete comparison reports:

| Field | Cases differing |
|---|---:|
| Any required scientific field | 712 |
| True model risk after | 51 |
| Tier 2 plausibility verdict | 15 |
| Joint success / triage | 3 each |
| Sparsity / proxy sparsity | 34 each |

Field counts overlap. Independent complete comparison confirms712cases:44structural and
668numeric-only. All are XGBoost cases across10groups:FD002700 andFD00112. Tier1, Tier3,
Tier4, returned-result and action-feasibility verdicts are unchanged. The maximum absolute
risk_after difference is0.1691702562816351, so these are not all near-tolerance discrepancies.
Of the712,702were also mismatches in the earlier failed run and10are new;1887previous
mismatches now match. This is not full parity. These diagnostics must not be interpreted as
physical benefit, real-machine safety or RUL-extension evidence.

## Preservation and execution segments

All records, registered cases, failures and timings remain at
`artifacts/phase12/phase12-repaired-20261104T231405Z/records.sqlite3`:
468,729,856 bytes, SHA256
`b9643edaab8df034346ca3ca4cec0e093a036d39204f34b0c5e1800b8ee810aa`.
The full `historical-comparison.json` is 340,436 bytes, SHA256
`980a336e6b69e90266269db0255a9f5c93cd8d09c892cb4ec215e1468e446d91`.
`artifacts/phase12/repaired-failed-run-preservation.json` pins these and the manifest,
segments, both stderr logs and actual resume exit receipt. The older 2,589-mismatch run
and its expected source remain unchanged. Neither failed output may become a new golden fixture.

Segment 1 saved 23,185 results before the explicit transport pause. The operator-requested
worker stop produced a recorded BrokenProcessPool/native exit 1, while the parent closed the
transactional checkpoint store. All 23,185 payloads including timings and 23,189 registered
cases were hash-verified before resume; SQLite integrity, code, runtime and 97 input hashes
matched. Four registered queries without committed results were eligible to retry. Receipt:
`artifacts/phase12/resume-compatibility-20261106.json`.

Segment 2 started at 2026-11-05 19:03:28 UTC, saved the remaining 8,931 results, and finished
query execution at 22:04:23 UTC. Its execution-success flag does not imply scientific parity.
The subsequent comparison failed, and the wrapper recorded actual exit 1 at 22:04:40 UTC.
The current receipt is the adjacent `.resume-20261106.exit`; the older canonical `.exit`
retains the original pause receipt. No completed result or timing was replaced.

## Diagnosis and next required work

The independently verified five-case factorial diagnosis established that historical tensor
calibration restored those five examples under either feature-lift implementation. Exact-byte
migration was independently reviewed for all 24 historical model artifacts. This did not
establish full-population parity, and the complete replay now demonstrates that additional
numerical/search differences remain. Their causes are not yet isolated. Do not attribute all
remaining differences to the feature graph, calibration or another change without evidence.

Preserve both failed runs, inspect the complete independent audit, and localize remaining
counterexamples under a committed diagnostic protocol before another measurement. Do not
relax tolerance, change scientific settings, replace failures or regenerate expectations.
Full parity, actual fixture promotion, a complete-corpus regression test, clean-clone replay
and the final gate are still required. No Phase 12 closure tag is created.

## Independent final acceptance of the failure evidence

The independent reviewer completed the full scan with native exit0 and all18consistency
checks true; scientific parity is false. Exactly31,404cases match and712differ. All32,116
input/config/history identities match; both SQLite integrity checks pass; all97frozeninputs,
source/config/runtime identities and before/after raw-file hashes match. All23,185pre-pause
result payloads including timings and all23,189pre-pause registered cases exactly match
their original fingerprints. No provenance defect explains away the scientific differences.

Audit `artifacts/phase12/repaired-complete-independent-audit/audit.json`, SHA256
`d60436ce072ff8529ff3a8d5573a6e4b76c19dfce58460ef442a903ddeeac42d`;
report `report.md`, SHA256
`811f6291502ff0ef2bb1950164f65505f8cb33e3f347b37fd651f93d659c5085`.
Audit-helper corrections for a serialized alias, fingerprint metadata and legitimate
no-optimization early exits are disclosed, with initial receipts preserved; the final full
scan was rerun. This successful audit verifies the failure evidence, not a regression pass.

The stop report changes documentation only. Ruff and strict documentation checks pass;
the prior608test software gate remains scoped to the measured implementation. There is no
new scientific run, calibration/solver setting change or phase-closure tag.
