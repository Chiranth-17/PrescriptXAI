# PrescriptXAI — IEEE-style paper skeleton

This is an editable manuscript skeleton, not a submitted or peer-reviewed paper.
Authors/affiliations, venue formatting and bibliography must be completed by the project owners.
Every literature citation is marked **TODO-VERIFY**; no publication details are invented.
The experiment table in [results.md](results.md) is generated from saved real measurements by
`scripts/docs_results.py`, which also records full provenance under `docs/results_provenance.json`.

## Abstract

Predictive maintenance estimates failure risk but does not alone determine a permissible
intervention. We present PrescriptXAI, a prototype that searches for sparse changes to configured
control proxies and evaluates true calibrated model validity separately from statistical
plausibility, proxy engineering constraints and learned coupling. Engine-disjoint C-MAPSS
experiments retain failed queries, distinguish all-query and returned-candidate denominators,
and use whole-engine bootstrap intervals. Results show population-dependent validity and
plausibility trade-offs and unresolved optimization latency gaps. Current evidence reaches
at most E3 under proxy assumptions; static data cannot establish physical efficacy or RUL extension.

**Index terms:** algorithmic recourse, predictive maintenance, calibration, sparse optimization,
uncertainty, reproducibility.

## I. Introduction

State the maintenance decision problem and distinguish prediction, explanation and recourse.
Explain the gap between a predictor-changing candidate and a physically justified action.
The contribution is an auditable integration of constrained search, separate evidence tiers,
explicit failure handling, reproducible artifacts and an operator interface. Avoid claiming a
new causal model or universal optimizer superiority.

## II. Related Work

- **TODO-VERIFY:** predictive maintenance and the original C-MAPSS dataset publication.
- **TODO-VERIFY:** counterfactual explanations and algorithmic recourse foundations.
- **TODO-VERIFY:** DiCE and other constrained/diverse recourse methods; compare using their actual
  supported constraints rather than asserting all baselines are unconstrained.
- **TODO-VERIFY:** probability calibration and proper evaluation under grouped data.
- **TODO-VERIFY:** Mahalanobis/OOD methods, model-based recourse limitations and causal validity.

## III. Method

Include the complete objective and constraints from [math](../docs/math.md): raw versus scaled
deltas; smooth L1 surrogate plus explicit support cap; train-only covariance; fixed/empirical/
chi-square D_max methods; validation calibration; retained coupling residuals. Specify which
quantities are assumed proxy limits. Explain search modes and the final true-model rescore.
Define E1–E5 and RECOVERABLE/PARTIAL/ESCALATE without equating plausibility to physical proof.

## IV. Experimental Protocol

Use the committed [protocol](../docs/evaluation_protocol.md), keeping development on validation
engines and reporting internal held-out, grouped OOF and official-test populations side by side.
Retain both D_max versions, all queries, effective settings, solver seeds, K sensitivity,
constraint ladder and finite-reference-search scope. Predictor choice uses predictive and
calibration metrics only. State all fitting/calibration IDs and repeat-use limitations.

## V. Results and Discussion

Insert [the automatically filled table](results.md) and
[the generated figure](../docs/figures/phase7-rates.pdf). The complete source includes 24
model/protocol/population rows and serial latency design-target/measured/gap comparisons.
Explain failed-query denominators and attach engine counts to every CI. Discuss target gaps
using the acceptance funnel, paired constraint ladder and unresolved reference cases. Cite
surrogate error and coupling residual diagnostics when discussing fidelity or consistency.
The short fresh-install demonstration is a separate reproducibility check, not another study
of independent generalization. No new numerical result should be typed into this skeleton.

## VI. Limitations

Static C-MAPSS has no observed intervention response. Channels are control proxies, and bounds,
rates and K are assumptions. The gradient surrogate and learned coupling may be wrong outside
their data support. Statistical plausibility is not engineering certification. Finite search
cannot prove infeasibility, and repeated public-engine experiments cannot establish fresh
generalization. No RUL extension, validated emulator or physics simulation result is claimed.

## VII. Conclusion

Summarize the verified software and measured trade-offs. Future work requires independently
validated response evidence, prospective evaluation and operational safety review. SDG 9.1/9.4
provides a motivation for reliability and resource efficiency; neither benefit is measured here.

## References

**TODO-VERIFY:** populate only after inspecting each primary source. Use citation keys that
resolve to verified bibliographic records; no placeholder author/title/DOI should be presented
as an actual citation.
