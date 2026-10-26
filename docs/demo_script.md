# Five-minute operator demo

Use the README five commands in an empty operator directory. The packaged dashboard selects
FD001 XGBoost reproduction v1 and **train-file telemetry**, which includes the predeclared
internal held-out engines used below. These example engines are held out from fitting. Choose
**THOROUGH** in the sidebar; FAST is a different effective solver mode. Keep all thresholds,
proxy bounds/rates and K unchanged. The preserved historical Phase 8 screenshots use another
population/model artifact and must not be relabeled as this run.

## Run identity and exact examples

Fitted artifacts: `reproduce-20261025T062618591382Z`, source
`10d546474e7b211155d2fe190c671cab6ff8d3df`, committed
`configs/experiments/phase10-reproduce-v1.yaml`, runtime config SHA256
`b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e`.
Protocol v1, k_max=3, assumed K=1, D_max v1=5, internal held-out FD001 train-file engines.
Each case below is an individual observed state, not a population estimate or interval.

<!-- demo-values:start -->
| Engine / cycle | Public triage | Risk before | True risk after | Evidence reached |
|---|---|---:|---:|---|
| 5/241 | RECOVERABLE | 0.8833731521 | 0.1284214696 | E3 |
| 2/278 | ESCALATE | 0.9970382956 | 0.3612983062 | none |
<!-- demo-values:end -->

The installed CLI verified these exact examples. A separately recorded live browser walkthrough
verifies the widgets, exports and diagnostics; see [Phase 10 verification](phase10_changes.md).
A reproduction on another numerical platform may yield slightly different candidates; display
what the current artifact actually returns, and retain unexpected failures.

## 0:00–0:40 — purpose and boundary

Open Operator Console. Explain prediction versus diagnostic explanation versus sparse proxy
recourse. Point to E1/E2/E3 and the proxy-assumption notice. Say explicitly that model validity
is not real-machine safety and static C-MAPSS establishes no RUL extension.

## 0:40–2:10 — high-risk RECOVERABLE example

Select engine **5**, cycle **241**, THOROUGH. Show its observed high risk, then click Recommend.
Allow the actual solve to finish; do not present a cached screenshot as live inference. Show
true risk before/after, separate four-tier results, Mahalanobis distance, raw/scaled deltas,
control count and E3 evidence. Download the JSON result so its config/model identity travels
with the example. Explain that dependent sensor changes come from learned coupling.

## 2:10–3:10 — escalation and safe failure handling

Select engine **2**, cycle **278** and recommend. The recorded case remains ESCALATE: final
model risk exceeds tau_safe and Tier 2 fails. Its closest diagnostic change is not an accepted
control instruction. Show the reason and evidence level without hiding the outcome.

For the distinct invalid-input failure, use a second terminal in the operator directory:

```powershell
.venv/Scripts/prescriptxai recommend --engine-id 5 --cycle 999999 --mode thorough
```

This nonexistent cycle must fail with exit code 2 and a readable observation error, producing
no recommendation. On Unix substitute `.venv/bin/prescriptxai`. Do not modify the dataset.

## 3:10–4:10 — measured evaluation

Open Evaluation Results. Show 20 completed queries / 11 engines, validity, both Tier 2
 denominators, joint success and whole-engine intervals. Open Model and Validation Diagnostics
for the predictor and learned coupling diagnostics. The short run has no ladder/K curve or
isolated latency study; point to the separately preserved [full results](results.md) and
[Phase 7 report](phase7_changes.md), including target misses and unresolved finite searches.

## 4:10–5:00 — reproducibility and limits

Show the manifest, exact source/config identity, seeds, actual 69/16/15 engine split and output
hashes. Explain the independent audit and portable installation. End on limitations and the
conditional SDG 9.1/9.4 motivation: no measured field reliability or efficiency improvement.

## Backup recording and offline preparation

Before presenting, record the real browser with the operating system's screen recorder, showing
its run/config/model labels and all three outcomes. Keep the original recording beside the
ignored run directory, with date, software source and SHA256 in a separate manifest. Do not
edit out failed outcomes or relabel old screenshots. No backup video is claimed until recorded.
For offline use, prepare dependencies and the verified NASA ZIP beforehand; keep fitted artifacts
and their manifest together. If the live server fails, disclose the failure and show the
captured screenshots/JSON as a labeled saved run, never as current computation.

## Slide outline mapped to the synopsis

1. **Problem / motivation:** predictive maintenance flags risk; operators need justified next steps.
2. **Gap:** explanations and model-changing counterfactuals do not prove feasible interventions.
3. **Mathematics:** sparse objective, raw/scaled mapping, hard bounds, assumed rates/K and D_max.
4. **Architecture:** engine-disjoint fitting, surrogate search, true-model rescore, four tiers, UI/API.
5. **Real case study:** engine 5/241, actual saved risks/deltas/checks, then engine 2/278 escalation.
6. **Evaluation:** generated population table, design-target/measured/gap latency table, both
   protocols, both plausibility denominators, engine CIs, funnel, ladder, K curve and oracle scope.
7. **Limitations:** static data, proxies, learned coupling, surrogate error, reused engines and E3 ceiling.
8. **SDG 9 / next evidence:** Targets 9.1/9.4 as motivation; prospective response validation needed.

Use `docs/figures/phase7-rates.png` or its PDF export and the generated table in `paper/results.md`.
All numerical statements must keep their source/config/population labels and units.
