# Phase 9 — systematic testing and hardening

Status: final gate pending. Historical Phase7/8 runs and schemas2.0.0 remain unchanged.
QA configuration: `configs/experiments/phase9-hardening.yaml`, first committed in `ebc9570`.
Science/golden/E2E and profiling preregistration: `bf50dff`; measured optimization: `2fd1055`.

| Requested area | Concrete evidence |
|---|---|
| Coverage | Explicit all62-source-file inventory; scoped line gate90%, only AppTest entrypoint `dashboard/app.py` excluded; full-package line/branch floors also checked by `scripts/quality/coverage_gate.py` |
| Properties | Hypothesis deterministic20examples/property plus explicit successful/no-op examples; frozen features, bounds, sparsity, raw/scaled roundtrip, distance norm, tier truth, finite outputs and triage rules |
| Fuzzing | Nonfinite/None/boolean/complex/extreme values, malformed contexts/history, wrong columns/dtypes, Unicode, empty/oversized batches, concurrent actual HTTP requests and isolated IDs |
| Fault injection | Corrupt/unfitted/mismatched artifacts, missing calibrator/coupling, missing regime assigner, singular covariance, unsuccessful search, malformed configuration and post-load predictor failure |
| Goldens | Four actual fitted triage outcomes, exact structure/verdicts, numeric atol1e-6/rtol1e-5; explicit `--update-golden` required; timings and execution/path identities excluded |
| Numerics | Bitwise scaler equality against installed StandardScaler across8flag/dtype cases; fitted-width failure; two same-process and two fresh-process runs; float32/64 public decision agreement |
| Performance | Preregistered serial120calls per segment, profiles, complete decision parity, engine-bootstrap intervals and10000-call memory study below |
| Security | Owner-trusted resolved artifact roots, SHA-bound decoded bytes, no upload/request grants trust; pip-audit and value-free credential-pattern scanning; API streamed bytes and row limits |
| Science | Explicit tests for all11listed error classes, including heldout perturbation invariance, solver-tuning leakage, full-validator frozen regime and exactly-once calibration |
| End-to-end | Actual temporary raw archive->train->calibrate->fit learned coupling/covariance->recommend->validate->HTTP->dashboard AppTest; separate CLI train/evaluate/report workflow |
| CI | Ruff, strict mypy, full coverage gates, uploaded XML/JSON/gate, dependency/secret checks; nightly slow/e2e/gpu marker selection and explicit CPU hardware disclosure |

All implementation was performed by the primary agent. Independent agents only audited/reproduced
faults and recomputed saved numerical records. Forty-two defects and their regressions are listed
in `docs/defects.md`. Preserved legacy artifacts remain Python objects: trusted-root restrictions
are not a pickle sandbox or authentication of downloaded artifacts. See `artifact_security.md`.

## Scientific checks

`tests/unit/test_phase9_science.py` checks holdout-only perturbations cannot alter predictor tensors,
scaler statistics, calibration outputs or frozen solver configuration; declared tuning on evaluated
engines is rejected. It explicitly checks scaling direction, exact threshold/RUL boundaries,
frozen operating-regime selection through `validate_candidate`, true rather than surrogate safety,
exactly-once calibration, signed cumulative rate limits, failed-query denominators, independent
plausibility/physical/joint definitions and upper-only latency budgets. Primary fitting identity
validation also rejects matching but invalid model/scaler IDs before readiness is granted.

The temp workflow trains a genuine seed17 MLP on synthetic C-MAPSS-format raw rows using engines
1–4, calibrates on5–6 and observes7–8. Coupling propagation fits only training rows; residual
thresholds use validation rows; covariance uses only predictor training engines. CSV replay can
round one final binary bit; dashboard/API states and measurements are compared with explicit
1e-12 tolerance while tier verdicts remain exact. Fixture outcomes are software checks, not
claims about predictive accuracy, maintenance efficacy or fresh C-MAPSS generalization.

## Profile and serial latency

Run `phase9-fixture-performance-v1`; config `configs/experiments/phase9-performance.yaml`, SHA256
`310bfb08160ee76a0e91e1bf7a3a15e507ec65987f7e3cad935e00b3c0b461cc`.
Preregistered in `bf50dff`, before preparation and measurement. Protocol fixture-only-v1,
k_max3,K1,D_max versionv1=5,tau_danger.80,tau_safe.20. Predictor/bootstrap seed17; solver/covariance
configuration seed1729. Population: all six saved synthetic observations, engines7–8 with
three cycles each, repeated20times. Each fresh process uses one native CPU thread, six warmups
and twelve separately profiled calls before120serial measured calls. All samples are retained.

| Segment / source | Calls / engines | p50 ms | p95 ms | p99 ms | 95% whole-engine p95 CI, engines |
|---|---:|---:|---:|---:|---|
| Before / `bf50dff` | 120 / 2 | 18.554700 | 37.418115 | 46.227248 | [37.036770,39.071975],2 |
| After / `2fd1055` | 120 / 2 | 12.626000 | 23.855240 | 26.482568 | [23.808220,23.855240],2 |

Every interval resamples whole synthetic engines, preserving all cycles/repeats;2000draws,
seed17. p95 decreased36.25% in this declared fixture workload. Two clusters give limited CI
resolution. This result does not replace Phase7 timings or establish a deployment-wide budget.
Loading, training, warmup, profiling, UI and recording are outside these timed public calls.

cProfile identified repeated pandas column selection and scaler validation as hot paths.
The optimization reuses already ordered frames and uses the same dense float64 subtraction then
division as StandardScaler, retaining finite/order/fitted-width checks and returning owned data.
Settings, fitted artifacts and goldens were unchanged. Nine direct scaling cases, property tests,
four-triage goldens, fresh-process checks and temp E2E pass. Later fitting-metadata checks execute
while loading artifacts, outside the measured warm-call scope; their full-gate source is separate.

Independent recomputation found zero discrepancies:120attempts/results per segment, zero errors;
all120paired decisions match exactly, including5160numeric fields (maximum absolute difference0).
The160timed cases corresponding exactly to stored golden inputs match those goldens. The helper
also checked the full four-case snapshot. Configuration, six input files and seven helper/
dependency/golden identities match across preparation, before, after and memory. Four distinct
PIDs and exclusive stage manifests are retained; no completed segment was replaced or resumed.

## Memory

The separate `2fd1055` process completed10000public recommend calls after100warmups, alternating
declared7/c3 and8/c1 already-safe observations. There are10000attempts/results, no errors,
5000calls per synthetic engine, allNO_INTERVENTION. Their measurement vectors are identical;
this checks the safe/no-op path, not optimizer memory stress. Complete scientific output parity
was asserted during execution; compact per-call logs retain status/risk rather than full reports.

Eleven persisted post-GC checkpoints include baseline and every1000calls. Tracemalloc live Python
growth=98686bytes; RSS growth=737280bytes; peak traced Python=674441bytes. Predeclared final-growth
budgets5MiB Python/50MiB RSS both pass. RSS includes native allocations; tracemalloc covers Python
allocations. These regression limits do not establish an unbounded service-lifetime memory bound.
No test, training or other quality workload ran during either timing segment or the memory stage.

## Gate and reproduction

Intermediate fullwave3:466passed/1oldCLI-expectationfailure/70warnings/400.89s. The old test expected
a raw ValueError; it now requires a friendly exit2 with the same precise engine-provenance error.
Its focused repair passes. SQLite audit connection lifetime was subsequently fixed with an actual
closed-handle regression. Full final checks are still required before closure.

Wave3 coverage: scoped7334/8116=90.36471168063085%; full7334/8209=89.34096723108783%line;
branch-inclusive85.85710354948179%. Both full-package Phase8 floors are retained. Complete output,
not the rounded console percentage, feeds the explicit gate. No extra source files are excluded.

```powershell
mingw32-make all-checks
uv run pytest -m 'slow or e2e or gpu'
uv run python scripts/quality/secret_scan.py --include-history --output artifacts/phase9/final-secret-scan.json
uv run pip-audit --path .venv/Lib/site-packages --format json --output artifacts/phase9/final-dependency-audit.json
```

Performance preparation/before/after/memory are complete and deliberately refuse overwrite.
Their ignored evidence is in `artifacts/phase9/performance-v1/`; do not rerun those stages into
that directory. Reproducing a new study requires a separately named, preregistered run; historical
samples remain intact. CI upload follows the official [artifact action interface](https://github.com/actions/upload-artifact/tree/v4).
Hosted CI execution and GPU hardware results are not inferred from local Windows CPU checks.
