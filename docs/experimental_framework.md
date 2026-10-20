# Experimental framework

The committed evaluation protocol and `configs/experiments/phase7-study.yaml` govern the study.
The fixed headline solver is inherited from Phase 6. Predictor selection uses predictive and
calibration evidence; this framework does not select predictors using recourse outcomes.

## Execution and resume

Run from the repository root:

```powershell
uv sync --all-groups --locked
uv run python scripts/diagnostics/phase7_experiments.py --run-id <unique-run-id> --stage all
```

Stages can also be invoked individually: `assets`, `diagnostics`, `quality`, `reference`,
`latency`, and `report`. Reuse the same run ID to resume. Every completed query is committed
transactionally to SQLite. Its exact effective config, raw state and observed LSTM history are
saved before execution. A conflicting manifest or completed result is rejected rather than
overwritten. A stage is complete only after all expected query identities have committed results.

The manifest fingerprints the study, frozen solver profile, protocol, archive, feature mapping,
model/validator artifacts and selected populations. It records source, packages and hardware.
The completed preparation seal retains the original preparation source and records the later
seal date/source. The archive is compared against the saved Phase 6 checksum; audited source
predictors and the prepared index are anchored by the completion seal on subsequent resumes.

The frozen FD001 XGBoost outer folds retain their actual historical seeds, 1730–1734. The other
prepared bundles use 1729. Actual per-model seed, training config hash, source and metrics are
written into the measurement manifest and `model_metadata.json`; the study's model seed governs
new fits. Original MLP/LSTM weights, scaler statistics and calibration are preserved by the
explicit legacy metadata migration.

## Populations and uncertainty

FAST includes every supported alert from internal held-out, grouped outer-fold and official test
engines. Development uses validation engines. THOROUGH uses true first alerts, selected before
development sampling. LSTM windows contain genuine earlier cycles; unavailable early windows
are counted. Alert selection and final risks use singleton scoring to avoid batch-dependent
numerical differences at a gate. The same predictor scores are reused across D_max versions.

The five seeds are solver repetitions of fixed fitted predictors. Across-seed standard deviation
does not estimate predictor training uncertainty. Bootstrap draws retain whole engines, with
all their states and solver repetitions. Conditional returned-counterfactual intervals resample
the complete cohort, including engines without returned actions. Zero denominators are explicit.

Failed queries remain in all-query metrics. A saved closest diagnostic exists for every query;
a returned counterfactual means a nonzero, action-feasible change. Action sparsity counts directly
optimized inputs, including deliberately freed immutable/dependent inputs in unsafe research
variants. Original-proxy sparsity and successful-action sparsity are reported separately.
Raw proximity sums mixed physical units and is descriptive; scaled L1 is dimensionless.

Validity always uses the true calibrated predictor and the frozen headline safe threshold.
Tier 2 is distributional plausibility; Tier 3, Tier 4 and joint success remain separate.
Sensitivity triage/evidence is relative to its explicitly stated target. Horizon-label experiments
retain paired source states, retrain/recalibrate on the same engine partitions, and disclose the
fraction that still meets the new predictor's alert gate. They do not redefine the headline cohort.

## Diagnostic search scope

Component removals change the search itself. Final checks always use the original constraints.
The ladder progressively adds immutable freezing, bounds, rates, dependent propagation, sparsity,
Mahalanobis and coupling. Dense research variants retain dense gradient search; their fallback
grid keeps the frozen sparse support budget to avoid exponential materialization.

Reference classification applies only to failed production queries. Exact production replay uses
the same mode/seed and final singleton rescore. The reference union contains the configured
production grid, a finer sparse grid, traced terminal candidates and the production return.
Finite absence is unresolved. A reproduced search with an algebraically empty actuator interval
can certify infeasibility only under the configured proxy assumptions. No finite grid proves
global real-machine infeasibility. Endpoint leverage respects bounds, rates and the search trust
region, and reports true risk, distance and coupling margins.

Changing beta cannot relax a hard immutable freeze. A bounds penalty can be inactive inside a
hard box. The corresponding one-factor sensitivity may therefore be invariant; that is reported
as an algorithmic consequence, not evidence of physical robustness. Changing H also updates
components whose documented healthy-regime definition depends on H. No independent factor is tuned.

## Latency and generated evidence

Serial latency runs after training and quality workers stop. Warmups are excluded, every measured
call actually executes recommendation, and each sample is checkpointed. Source, artifacts,
runtime and workload are part of resume identity. Budgets use the p95 upper figure; faster passes.
Ingestion timing is request normalization, not bulk dataset download. UI, network and cold startup
are unmeasured. Quality-run timing includes experiment-driver overhead and is not substituted for
the separate warm serial benchmark.

`report.md`, `report.html`, `metrics.csv`, `records.jsonl`, `summary.json`, `K_curve.html` and
`risk_reduction.html` are generated from saved results. Incomplete required stages produce a
PARTIAL report. Tables retain run/config/source/protocol/population labels, whole-engine intervals,
solver-seed variation, design targets and gaps. FAST first-alert strata use stored FAST results,
so mode and population are not confounded. Raw evidence stays under ignored `artifacts/`.

All findings are conditional on C-MAPSS sensor proxies, empirical bounds and one-step limits.
K is an assumed intervention horizon. Evidence reaches at most E3; simulated trajectory health is
**not evaluated**. There is no validated emulator or physics simulator, and no RUL extension is claimed.
