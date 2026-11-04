# Phase 12 regression failure - advancement stopped

Status: 5 November 2026 IST. Phase12 is **not closed**. The complete scientific replay
finished saving its queries, but its comparison failed with native exit **1**. No golden
Parquet fixture was exported or promoted, and no Phase13 implementation was started.

The user's [orchestrator](prompts/final_phases_12_to_20.md) explicitly requires:
"STOP and report (do not continue)" when "the C-MAPSS regression changes".
Automatic continuation `prescriptxai-phases-12-20` was deleted after this condition occurred.
This is a deliberate gate stop, not a missing-simulator or missing-actuator blocker.

## Exact scope and evidence

New run `phase12-baseline-20261104T173007Z`; source
`4048ea5319f774f3925cec1ed4dfaddbb9d34840`; design
`configs/experiments/phase12-baseline-v1.yaml`, Windows runtime SHA256
`be26bf6ce264db835d62a193bec19b4f7c7e5818a1e57a7c7097a9c4119a7978`;
committed LF blob SHA256
`9e7ce88d108d32beb39662284a3c806d46ebae4ed191960950fe61462965fcac`.
The line-ending difference is disclosed in `artifacts/phase12/registration-provenance.json`.

Reference run `phase7-20261020T102540Z`; measured source
`63c2ed445fba16c73a2771e184f635abf76b4405`; source study
`configs/experiments/phase7-study.yaml`, SHA256
`67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`.

Both sides cover **32,116** FAST/full queries in **24** model/protocol/population groups,
seed1729: FD001 LSTM/MLP/XGBoost and FD002 XGBoost, protocols v1/v2, all internal held-out,
grouped OOF and official-test alerts. K=1, k_max=3, D_max=5/8 and thresholds .20/.80 remain
fixed. Each group retains its original engine population and effective configuration.
Counts below are regression differences across those labeled groups, not pooled performance
rates. All failed queries remain included. This quality replay does not certify latency.

The registered comparison uses absolute tolerance1e-6 and relative tolerance0 for scientific
floats, with exact discrete/tier/triage values. **2,589 cases differ**. In particular:

- True `risk_after` differs beyond tolerance in **748** cases.
- Tier2 verdicts differ in **167** cases.
- Joint success and triage differ in **35** cases each.
- Direct support counts differ in **471** cases.

These field counts overlap and must not be summed as independent cases. Some differences
are close to the absolute tolerance; others are substantive. For FD001/MLP/v1/grouped OOF,
case `369d2fae0c83458608f7861b8e2ee9ce744e2773f245c176559c395f6154d0ba`,
model risk after changes from **0.0810874119466206** to **0.16597096732047406**.
Its RECOVERABLE verdict is unchanged, but its candidate and search path differ. This is
neither a hardware failure-risk estimate nor physical-benefit evidence.

## Preservation and diagnosis

All32,116 new result payloads, original registered cases and operational timings remain in
`artifacts/phase12/phase12-baseline-20261104T173007Z/records.sqlite3`.
The database has468,754,432bytes, SHA256
`134b1fddf8a43c818a903ee8f82db1794a838cba31c572c49c318a8d672b6a58`.
The complete mismatch list is `historical-comparison.json`,1,544,224bytes, SHA256
`258407859066da7c21d099cfd3119d429231bec1cccbb426c44de16f108184bd`.
The manifest, one execution segment, stdout/stderr, actual exit file and their preservation
receipt are retained. The segment's `actual_success=true` describes query execution only;
it does not mean scientific parity passed. The wrapper correctly records exit1 and no
completion marker. Original Phase7/Phase11 data and source63 checkout remain unchanged.

The helper's final source/config/input verification passed before the comparison failed.
An independent reviewer checked all32,116 paired records,24groups and97 frozen inputs:
zero input/identity errors, both SQLite integrity checks OK and all evidence files unchanged
before/after audit. Its independent comparator reproduced exactly2,589 mismatches and29,527
matching cases:625 cases have discrete/structural differences and1,964 have numeric-only
differences. Tier2 changes comprise89fail-to-pass and78pass-to-fail; triage changes comprise
20ESCALATE-to-RECOVERABLE and15RECOVERABLE-to-ESCALATE, all35in FD002. Tier1, Tier3,
Tier4, returned-candidate and action-feasibility flags are unchanged. These are administrative
regression counts over the labeled groups above, not pooled quality estimates.

The audit exited0 because it successfully verified the evidence; its `scientific_parity` is
explicitly false. Detailed JSON/CSV and native exit are retained under
`artifacts/phase12/independent-complete-run-audit/`. Audit JSON SHA256:
`66d63a595db0327d6e7185055cd6da1beb0cdbf4acfa44d6b3928425132968f4`.
Earlier unit/gradient equivalence and573 passing software tests do not
establish solver-outcome parity. There are43 changed source files between the historical and
current commits; the latest shared-feature-graph repair is one hypothesis, not an established
sole cause. No predictor, bound, threshold, rate or tolerance was adjusted to hide the failure.

Independent source-history review also identifies calibration hardening in `ebc9570`:
the torch calibration path moved from float32 clamp/logit arithmetic to a float64,
NumPy-aligned transform. Identical fitted weights therefore do not imply identical search
gradients. That revision and the later shared-feature lift are candidate boundaries for
controlled diagnosis; neither is established as the sole cause by a history diff alone.

The next proposed diagnostic is to isolate the earliest behavior-changing revision, using
the preserved counterexamples and frozen assets. A repair must restore the contract and
pass a separately preregistered complete regression. Replacing expected candidates with
these new outputs or widening the tolerance would not repair this gate. Work beyond this
diagnosis remains stopped under the user's explicit condition.
