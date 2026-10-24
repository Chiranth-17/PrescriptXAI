# Phase 8 real dashboard walkthrough

The live walkthrough used the official FD001 test observations from the local public
C-MAPSS archive, the existing fitted XGBoost bundle, and
`configs/experiments/phase7-FD001-xgb-v1.yaml`: FAST, protocol v1, K=1, k_max=3,
D_max=5, alert .80 and safe .20. No model or constraint was tuned for these examples.
These previously evaluated public engines are demonstrations, not fresh generalization.

## Run it

From the repository root, with the existing ignored data/artifacts available:

```powershell
uv sync --all-groups --locked
mingw32-make dashboard
```

Open the printed localhost address. The default is direct library access. Choose FD001,
XGBoost / v1, FAST and Operator Console. The sidebar shows the selected model, config hash
and original predictor training source. Select an engine and cycle, then Recompute.
`configs/dashboard.yaml` lists the observed-data source, profiles and saved Phase 7 report.
For API mode, start `uv run prescriptxai serve --config configs/experiments/phase7-FD001-xgb-v1.yaml`,
select the API adapter in the dashboard configuration, and keep credentials in the environment.
The adapter checks server/model/config/artifact identity before accepting a result.

Restart Streamlit after updating package Python source. Streamlit development hot reload can
retain a cached engine instance from the previous class definition; this produced a safely
handled missing-info-field error during development. The final cold process and tests pass.
Do not interpret a package hot reload as an artifact migration or a production deployment.

## Recorded cases

All three exported results were independently reconstructed from raw telemetry, the saved
scaler/calibrated predictor, coupling model and validators. The complete reports match library
validation; all 33 raw/scaled/percentage deltas match, with propagation roundoff at most
3.64e-12. Evidence: ignored `artifacts/phase8/independent-export-audit.json` and the three
`walkthrough-*.json` exports. Their config hash is
`47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271`.

| Selection / action | True calibrated risk before -> after | D_M | Decision and evidence |
|---|---:|---:|---|
| Engine 20, cycle 179; Recompute | .9466699900787514 -> .1208627930431905 | 4.848460785318865 | RECOVERABLE, all four static tiers pass, E3; three proxy changes |
| Same original state; move sensor_8 manual preview to 2387.9534 | .9466699900787514 -> .05420929572835379 | 7.0131710477 | ESCALATE, E1 only; Tier 2 and fan-speed rate check fail despite low model risk |
| Engine 76, cycle 205; Recompute | .9849537709689737 -> .3509700699647453 | 4.6669503123 | PARTIAL; Tier 1 fails, proxy tiers pass, no E1 reached; scheduled inspection |

The manual rejection's Tier 2 margin is -2.0131710477 and the sensor_8 rate margin is
-.0966. A lower model score is insufficient to accept the edit. The PARTIAL case reduces
model risk by about 64.37% relative to its original value, but remains above .20. These are
individual demonstrations and must not be pooled into a quality estimate.

Inspect the raw action table, independent tier reasons/margins, Mahalanobis gauge, locked
scaled-feature bars, sequential alphabetical waterfall and cheap exact permutation average.
The waterfall uses the same original residual and genuine context for every ordering; it
explains the predictor, not a causal machine response. Exports retain rejection/diagnostic
labels and provenance. No dynamic simulator is configured.

Fleet Overview ranks all engines at the chosen cycle, preserves missing/unassessed entries,
and hands the actual selected engine/cycle to the console. Diagnostics shows saved calibration,
coupling residuals, distance distributions, the real L0-L7 ladder, separate acceptance funnel
and protocol-separated K curve. Evaluation loads the complete Phase 7 output with engine
intervals and target/gap tables. About remains usable without fitted artifacts.

## Screenshots

These are actual browser captures, not generated mockups. Earlier captures precede the final
display-only provenance/timer correction; the decision and validation path is unchanged.

| View | Capture |
|---|---|
| Accepted real candidate | [RECOVERABLE](screenshots/phase8-recoverable.jpg) |
| Safe-model but rejected manual edit | [Manual rejection](screenshots/phase8-manual-rejected.jpg) |
| Inspection outcome | [PARTIAL](screenshots/phase8-partial.jpg) |
| Constraint-removal experiment | [Ladder](screenshots/phase8-diagnostics-ladder.jpg) |
| Assumed-horizon sensitivity | [K curve](screenshots/phase8-diagnostics-k.jpg) |
| All-population target gaps | [Evaluation](screenshots/phase8-evaluation.jpg) |
| Real engine ranking | [Fleet](screenshots/phase8-fleet.jpg) |
| Permanent qualifications | [About](screenshots/phase8-about.jpg) |
| Final source / registered UI callback | [Final UI](screenshots/phase8-final-ui-timing.jpg) |

## Registered UI build measurement

Run `phase8-ui-render-20261024-v1`, committed study
`configs/experiments/phase8-ui-render.yaml` (SHA-256
`05f692de6b78fa6c9ca3477de8e3c4dd7454cfccff7d9259ef43909d5b4c6f5b`),
preregistration `215cb1f50a318660c4b126d2abb077c24a3e850a`, measured implementation
`52affd06d39b03f76a0dd70417c3a75bd76f55c4`. The registered browser callbacks were run serially
without competing test/training jobs. Four Recompute callbacks per engine used last observed
cycles 1/31, 2/49, 3/126, 4/106, 5/98, 6/105, 20/184 and 76/205.

All 32 callbacks completed, all result IDs are distinct, zero timings were discarded and zero
operator failures occurred. One locator wait timed out; observation recovered the same completed
callback without another click, and its timing remains included. The driver event is saved.

| Statistic | Measured ms | Budget / verdict |
|---|---:|---|
| p50 | 100.10 | descriptive |
| p95 | 115.3545 | <=250: pass for this scope |
| p95 95% whole-engine bootstrap CI | [108.80, 120.46], 8 engines / 32 callbacks | 2000 replicates, seed 1729 |
| p99 | 119.1177 | descriptive |

The timer covers complete Operator Python UI construction, including header/sidebar/result
panels, subtracting explicitly timed loading/scoring/solve/attribution work. Browser paint,
network, startup and other pages remain unmeasured. The desktop was not isolated: this is not
a production SLA or a replacement for the Phase 7 backend timing study. Faster than the
synopsis band's lower number passes; only its upper budget is a limit.

Raw records/manifest/summary remain ignored in `artifacts/phase8/ui-render-20261024-v1/`.
Records SHA-256: `eb7d53c86bd2c49925e27973f91c0f56f3390fc9524844469705c66492f9d861`.
Regenerate the report without rerunning callbacks:

```powershell
uv run python scripts/diagnostics/phase8_ui_render_report.py
```

Static C-MAPSS sensor channels are actuator proxies; bounds, rates and K are assumptions.
Model validity is distinct from plausibility and physical proof. Evidence reaches at most E3;
no real actuator efficacy, validated dynamics or RUL extension is established.
