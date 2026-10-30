# Final verification — Phase 11

All required audit gates passed. The current software gate, installed reproduction, API/dashboard
checks and Docker verification are complete. The entire **34,298-query / 64-group** frozen
replay completed with actual exit0; both reference-seed comparisons had zero mismatches,
all **576 whole-engine CI objects** passed, and every result/case payload including timings
is preserved in an independently verified raw backup. The chronological interrupted checkpoints
below are retained as history, followed by the final accepted outputs.

The requirement map is **33 Done / 19 Partial / 12 Not met**. Missing physical evidence,
historical once-ever/fresh-engine certainty and roadmap outputs remain explicit exceptions;
they are not converted into achieved results by audit completion.

Main checkout: `C:/Users/chira/OneDrive/Desktop/5thsemEL`.
Release under audit: `b219041801d720f75973da24a1c5b43d5dcd0154` /0.2.0.
Initial report corrections: `d12dec1a1a776d9e8416cec22d879e560498875f`; current follow-up
`4995c301331db78b1e31f58de3cdcd957b1ca336` retains each query's attained level. Independent reviewers did not implement product code.
Schemas RecourseResult/ValidationReport remain2.0.0; frozen scientific source/YAML values and fitted
artifacts are preserved in the separate replay checkout. A disclosed Git taxonomy newline-byte
difference is detailed in the replay provenance section below. Quality replay timings are not isolated latency evidence.

## Latest complete software verification — source4995

Commit `4995c301331db78b1e31f58de3cdcd957b1ca336` fixes the independently identified AGENTS18
presentation gap: future legacy evaluation/JSONL records retain their canonical validation
report's attained level. Historical unlabelled records deserialize as unknown (null), never a
fabricated `none` outcome. Public RecourseResult/ValidationReport schemas remain2.0.0; models,
solver decisions, thresholds, bounds and rates are unchanged. Committed review proof:
`artifacts/phase11/legacy-evidence-level-committed-review.json`.

The full `mingw32-make all-checks` command passed: **527tests/66warnings/1498.23s**, Ruffclean,
strictmypy65clean, strictdocs25.62s. Exact coverage improves over d12without exclusions/floor changes:
scoped7659/8424=90.91880341880342%, full7659/8517=89.92603029235646%,
combined9751/11275=86.48337028824834%. Proof `coverage-evidence-level-independent-audit.json`
and actual `evidence-level-all-checks.log/.exit`. Real output excerpt:

```text
uv run ruff check .
All checks passed!
uv run mypy src
Success: no issues found in 65 source files
uv run pytest --cov=prescriptxai --cov-report=term-missing --cov-report=json --cov-report=xml
Required test coverage of 86.07837763770897% reached. Total coverage: 86.48%
================ 527 passed, 66 warnings in 1498.23s (0:24:58) ================
INFO    -  Documentation built in 25.62 seconds
```

Current wheel/installed Python3.13.9 source hashes68/68match4995;75wheel entries/311sdist entries.
Wheel SHA256 `d783e9d3669098cd72a62d04750806307055eeb37d2dbd1a6b4b5ba5cae617ea`.
The new Docker build and installed68source-hash audit passed; image
`sha256:f4e9444876fe2582d318da3d89354beda4c2a1fdd92cd0c7465cdeaf2966fb87`,
tag `prescriptxai:phase11-4995c30`. UID10001/read-only mounts/API/dashboard200/invalid422 passed.
Actual Linux HTTP REC5/c241 risk0.10835729296287716/E3 and ESC2/c278risk0.3612983062471661/none
bothpassed, schemas2.0.0. Only two ownership-checked containers were removed; all preexisting
running container IDs were retained. Source/context/commands/real outputs are in
`evidence-level-full-check-docker-audit.md` and `evidence-level-package-docker-independent-audit.json`.
No Windows/Linux action identity or isolated latency result is claimed.

Fresh workspace `C:/Users/chira/prescriptxai-phase11-evidence-final` completed actual
`prescriptxai init .` then `prescriptxai reproduce` from its installed venv. Runtime
`configs/default.yaml` is byte-identical to committed `configs/experiments/phase10-reproduce-v1.yaml`,
SHA256 `b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e`.
Run `reproduce-20261029T100600311811Z` completed all five stages, **exit0/2042.3577359000337s**,
20queries/11engines from378alerts/0exclusions; fit/calibration/test partitions69/16/15.
All18output hashes and68installed source hashes pass. Common scientific record fields, selected
CSV and all8saved metric/CI objects match FOUR previous Windows runs exactly. The new annotation
is separately verified, not silently removed: every20saved labels matches freshly recomputed
canonical validation and the independent prior-flag policy, with countsE3=10/E1=2/none=8.
All report/checkpoint records agree. Manual whole-engine bootstrap recomputation agrees within1e-12.

Real completed stdout:

```text
Starting data_prepare
Completed data_prepare (30.84s)
Starting train_and_calibrate
Completed train_and_calibrate (128.46s)
Starting fit_validators
Completed fit_validators (1.86s)
Starting evaluate
Completed evaluate (1877.39s)
Starting report
Completed report (2.99s)
Completed reproduction: C:\Users\chira\prescriptxai-phase11-evidence-final\artifacts\reproduction\manifest.json
```

Actual measured engine intervals for this small packaging workflow (not the complete study):

Run `reproduce-20261029T100600311811Z`; source `4995c301331db78b1e31f58de3cdcd957b1ca336`;
committed config `configs/experiments/phase10-reproduce-v1.yaml`, SHA256
`b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e`.
FD001/XGB, protocolv1, THOROUGH, k_max3, assumedK1, D_maxv1=5; population
`reused internal held-out FD001 engines; seeded feasible-alert sample`.
Whole-engine bootstrap:2000draws,seed1729,95%confidence; engine frame/count appears beside each interval.

| Metric | Measured [95% engine CI] | Engines | Observations / denominator |
|---|---:|---:|---:|
| validity | 0.600000000 [0.450000000, 0.777777778] | 11 | 20 / 20 |
| plausibility_all | 0.600000000 [0.428571429, 0.764705882] | 11 | 20 / 20 |
| plausibility_returned | 0.600000000 [0.428571429, 0.764705882] | 11 | 20 / 20 |
| tier3 | 1.000000000 [1.000000000, 1.000000000] | 11 | 20 / 20 |
| tier4 | 1.000000000 [1.000000000, 1.000000000] | 11 | 20 / 20 |
| joint | 0.500000000 [0.333333333, 0.687500000] | 11 | 20 / 20 |
| mean_risk_drop | 0.577940412 [0.492979741, 0.673580202] | 11 | 20 / 20 |
| sparsity_success | 2.900000000 [2.666666667, 3.000000000] | 11 | 20 / 10 |

Acceptance uses both JSON `passed=true` and exit0 in
`evidence-level-reproduce-comparison.json/.exit`; the consolidated proof is
`evidence-level-reproduce-independent-audit.md`. Durations are operational under concurrent
quality work, not isolated latency comparisons. Earlier d12/b219 proofs below are retained.

Preserved operational/audit failures: PowerShell5.1 promoted uv's ordinary stderr notice to
NativeCommandError before any reproduction/model run; PowerShell7/native exit checks corrected it.
A long combined Docker helper-write/run command was rejected before dispatch with no detailed reason;
separate reviewable bounded helpers and explicit invocation were accepted. Finally, the first
post-run audit incorrectly parsed the saved17digit CSV with default pandas parsing:14queries
then differed in immutable settings by about1e-16, producing false Tier3 failures. Round-trip
parsing matches standard float conversion in all480telemetry cells and restores canonical
agreement. The initial false audit/incorrectexit0 remain in `*-comparison-attempt1.*`; the helper
now fails closed unless its JSON passes. No optimizer, source scientific logic, config, model or
saved result was changed to resolve this reconstruction error.

## Complete project check command

Command: `mingw32-make all-checks` (Ruff, strict mypy, pytest with coverage gate, strict MkDocs).
Initial independent check on releaseb219041 completed **exit0**, **524passed/66warnings/457.46s**.
Warnings came from short test-only nonlinear fits; no tests were skipped to pass the gate.
Real output excerpts from `artifacts/phase11/all-checks-initial.log`:

```text
uv run ruff check .
All checks passed!
uv run mypy src
Success: no issues found in 65 source files
uv run pytest --cov=prescriptxai --cov-report=term-missing --cov-report=json --cov-report=xml
================ 524 passed, 66 warnings in 457.46s (0:07:37) =================
INFO    -  Documentation built in 5.93 seconds
```

Exact independently audited initial coverage equals the Phase10 baseline:
scoped7622/8390=90.84624553039332%, full7622/8483=89.85028881291996%,
combined9704/11233=86.38832012819371%. See `coverage-independent-audit.json` and
`coverage-initial.json/.xml` under `artifacts/phase11/`. No coverage floor was lowered.
The scoped exclusion is the AppTest-driven dashboard entrypoint; full coverage also remains visible.

Post-fix full command on d12dec1: **exit0**, **527passed/66warnings/539.52s**; Ruffclean,
strictmypy65sourcefiles clean, strictMkDocs7.95s. Durable `artifacts/phase11/all-checks-final.log/.exit`.
Independent final coverage: scoped7657/8422=90.91664687722631%, full7657/8515=89.92366412213741%,
combined9749/11273=86.48097223454272%. Improvements over actualPhase10 values are respectively
0.070401346833,0.073375309217 and0.092652106349 percentage points; exclusions/floors are unchanged.
Proof: `artifacts/phase11/coverage-final-independent-audit.json`.
Real post-fix output excerpt:

```text
uv run ruff check .
All checks passed!
uv run mypy src
Success: no issues found in 65 source files
uv run pytest --cov=prescriptxai --cov-report=term-missing --cov-report=json --cov-report=xml
Required test coverage of 86.07837763770897% reached. Total coverage: 86.48%
================ 527 passed, 66 warnings in 539.52s (0:08:59) =================
INFO    -  Documentation built in 7.95 seconds
```

Focused report/regression/evaluation/reproduce tests completed **20passed in40.37s**;
Ruffclean and strictmypy65sourcefiles clean before commit. An earlier focused invocation named
a nonexistent test path and ran zero tests; it was corrected. Two real first-run test failures
(fixture constructor and the deliberately changed wording assertion) were fixed and rerun.
These failures are not hidden or substituted for the full gate.

## Installed reproduction command

Executed from a new empty operator workspace `C:/Users/chira/prescriptxai-phase11-reproduce`
using the clean installed release CLI after `prescriptxai init .`:
`prescriptxai reproduce` (default `configs/default.yaml`).
The initial incorrect `init --directory` command exited1; corrected `init .` exited0.
Reproduction run `reproduce-20261027T141904574202Z` completed **exit0**, **711.3422288s**,
all5stages. Sourceb219041; runtime `configs/default.yaml` is byte-identical to committed
`configs/experiments/phase10-reproduce-v1.yaml`,
SHA256 `b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e`.
This is the registered20-query packaging/reproduction workflow, not the full evaluation replay.

Real tail from `artifacts/phase11/reproduce.log`:

```text
{"timestamp": "2026-10-27T14:30:55.712308+00:00", "level": "INFO", "logger": "prescriptxai.evaluation.runner", "run_id": "1f26629c5617404396fd8b46435e3e6f", "message": "Evaluated 20 feasible recourse states from 378 high-risk held-out states; infeasible=0 frozen=0 actuator_bounds=0 rate=0"}
{"timestamp": "2026-10-27T14:30:55.716205+00:00", "level": "INFO", "logger": "prescriptxai.evaluation.runner", "run_id": "1f26629c5617404396fd8b46435e3e6f", "message": "Counterfactual direction agreement for nearby states: pairs=0 agreement=None"}
Completed evaluate (665.89s)
Starting report
Completed report (0.09s)
Completed reproduction: C:\Users\chira\prescriptxai-phase11-reproduce\artifacts\reproduction\manifest.json
```

The fresh run retained378eligible alerts/0interval exclusions and20queries/11engines,
with69/16/15fit/calibration/test engine partition. Independent checks verified18output hashes,
selected CSV, all nontiming scientific records and all8whole-engine interval objects against
both previous Windows reproductions exactly. Validity12/20, T2both12/20, T3/T4both20/20,
joint10/20; full CIs/config labels are in the saved `measured_metrics.json` and Phase10 record.
No duration comparison is presented as a latency benchmark. New report rendering on these
same saved records independently preserved all8metric/CI objects and4per-query stage p95 values;
proof `artifacts/phase11/presentation-real-reproduction-audit.json`.

## Earlier d12 reproduction after initial report corrections

Because report/reproduction code changed, the then-current d12dec1 wheel was installed in a new
empty `C:/Users/chira/prescriptxai-phase11-final` workspace. Distribution inspection verifies
75wheel entries/304sdist entries and68source hashes against the installed wheel and checkout,
with0mismatches. Install/compatibility and actual `prescriptxai init .` completedexit0;
all65installed packages are compatible. Actual command was `prescriptxai reproduce`, using
default `configs/default.yaml`, byte-identical to the committed reproduction profile above.

Run `reproduce-20261028T141720017713Z` completed **exit0**, all5stages,
**626.4732678seconds**, at2026-10-28T14:27:46.490964Z. Counts:378eligiblealerts,
0intervalexclusions,20queries/11engines; engine partitions69/16/15. Independently verified:
all18outputhashes, all68installed/sourcehashes, selectedCSV and every nontiming scientific
record. All20records and8saved metric/CI objects exactly match allTHREEearlier Windows
reproductions. A separately implemented whole-engine bootstrap recomputation (2000draws,
seed1729,95%) agrees within1e-12; manual summation endpoints are not claimed bitwise identical.
Source/runtime identities and timings are retained, not discarded or treated as efficacy data.

Real completed stdout:

```text
COMMAND: C:/Users/chira/prescriptxai-phase11-final/.venv/Scripts/prescriptxai.exe reproduce
Starting data_prepare
Completed data_prepare (12.90s)
Starting train_and_calibrate
Completed train_and_calibrate (36.78s)
Starting fit_validators
Completed fit_validators (0.69s)
Starting evaluate
Completed evaluate (574.71s)
Starting report
Completed report (1.09s)
Completed reproduction: C:\Users\chira\prescriptxai-phase11-final\artifacts\reproduction\manifest.json
```

Validity12/20, Tier2bothdenominators12/20, Tier3/Tier4both20/20, joint10/20;
conditional successful-support denominator10. Complete8metric/CI objects are saved in the
run's `measured_metrics.json`. Exact comparison and manual bootstrap proof:
`artifacts/phase11/reproduce-final-comparison.json/.log/.exit`,
`reproduce-final-current-wheel-reaudit.json` and `reproduce-final-independent-audit.md`.
This20-query installed workflow is separate from the full34298-record replay below.

## Actual HTTP API smoke

Owned Uvicorn endpoint `http://127.0.0.1:8001`, main code/source02f0145 before report-only
commitd12dec1, same fresh reproduction assets and config hash above. GET health/version/config
and POST real RECOVERABLE/ESCALATE and invalid-input requests were actually sent.
Saved command/probe, complete output, per-request and result JSON remain under
`artifacts/phase11/api-smoke*`. The independent summary follows verbatim:

```json
{
  "started_utc": "2026-10-28T13:58:26.995419+00:00",
  "runtime_source": "02f0145ad9ef75b10f3235455453cbaec0f0a9da",
  "python": "3.13.9 (tags/v3.13.9:8183fa5, Oct 14 2025, 14:09:13) [MSC v.1944 64 bit (AMD64)]",
  "platform": "Windows-11-10.0.26300-SP0",
  "workspace": "C:\\Users\\chira\\prescriptxai-phase11-reproduce",
  "config_path": "configs/experiments/phase10-reproduce-v1.yaml",
  "audit_config_path": "configs/experiments/phase11-audit.yaml",
  "runtime_config_sha256": "b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e",
  "checks": [
    {
      "route": "/health",
      "status": 200,
      "body": {
        "status": "ready",
        "model": "xgb",
        "dataset": "CMAPSS",
        "mode": "FAST",
        "schema_version": "2.0.0"
      },
      "request_id_echo": "phase11-independent-smoke"
    },
    {
      "route": "/version",
      "status": 200,
      "body": {
        "service_version": "0.2.0",
        "schema_version": "2.0.0",
        "mode": "FAST"
      },
      "request_id_echo": "phase11-independent-smoke"
    },
    {
      "route": "/config",
      "status": 200,
      "body": {
        "model_version": "xgb:artifact-3:e2792cebf7673b0720da734c7bbd52c70f51cfa96c41654ed507c104d0b33dc1",
        "schema_version": "2.0.0",
        "model_git_hash": "b219041801d720f75973da24a1c5b43d5dcd0154",
        "config_hash": "f5f591525e1de8b8df2b429518d3d09856d7f6381bbc498947fdb5982a57377c",
        "artifact_identity": "be7fdf673386c6eeeb1a6e809b0867bd1a89e27ebfaf1e98582cea77e9da853c",
        "dataset": "FD001",
        "model_choice": "xgboost",
        "history_rows": 0,
        "model_diagnostics": {
          "dataset": "FD001",
          "model": "xgb",
          "horizon_H": 30,
          "tau_danger": 0.8,
          "tau_safe": 0.2,
          "feature_names": [
            "sensor_8",
            "sensor_9",
            "sensor_12",
            "sensor_15",
            "sensor_17",
            "sensor_20",
            "sensor_21",
            "op_setting_1",
            "op_setting_2",
            "op_setting_3",
            "sensor_2",
            "sensor_3",
            "sensor_4",
            "sensor_6",
            "sensor_7",
            "sensor_11",
            "sensor_13",
            "sensor_14"
          ],
          "split_engines": {
            "train": [
              3,
              4,
              6,
              10,
              12,
              14,
              15,
              16,
              17,
              18,
              19,
              21,
              22,
              24,
              27,
              31,
              33,
              35,
              36,
              38,
              39,
              40,
              42,
              44,
              45,
              46,
              47,
              49,
              50,
              52,
              53,
              54,
              55,
              56,
              59,
              60,
              61,
              63,
              65,
              67,
              68,
              69,
              70,
              71,
              72,
              73,
              74,
              75,
              76,
              77,
              78,
              79,
              80,
              81,
              82,
              84,
              85,
              87,
              89,
              90,
              91,
              92,
              93,
              94,
              95,
              96,
              97,
              99,
              100
            ],
            "validation": [
              1,
              8,
              9,
              11,
              25,
              26,
              28,
              34,
              37,
              48,
              51,
              57,
              58,
              62,
              66,
              83
            ],
            "test_holdout": [
              2,
              5,
              7,
              13,
              20,
              23,
              29,
              30,
              32,
              41,
              43,
              64,
              86,
              88,
              98
            ],
            "train_validation_overlap": false,
            "train_test_overlap": false,
            "validation_test_overlap": false
          },
          "calibration": {
            "method": "sigmoid",
            "fit_engine_ids": [
              1,
              8,
              9,
              11,
              25,
              26,
              28,
              34,
              37,
              48,
              51,
              57,
              58,
              62,
              66,
              83
            ],
            "validation_before": {
              "brier_score": 0.034069445502907025,
              "ece": 0.03157521726717902,
              "reliability_curve": [
                {
                  "bin": 0,
                  "count": 2356,
                  "mean_probability": 0.00534825015893418,
                  "fraction_positive": 0.0021222410865874364
                },
                {
                  "bin": 1,
                  "count": 74,
                  "mean_probability": 0.13836442880533836,
                  "fraction_positive": 0.04054054054054054
                },
                {
                  "bin": 2,
                  "count": 51,
                  "mean_probability": 0.2407410863567801,
                  "fraction_positive": 0.2549019607843137
                },
                {
                  "bin": 3,
                  "count": 38,
                  "mean_probability": 0.3484107295149251,
                  "fraction_positive": 0.21052631578947367
                },
                {
                  "bin": 4,
                  "count": 46,
                  "mean_probability": 0.4467309259850046,
                  "fraction_positive": 0.10869565217391304
                },
                {
                  "bin": 5,
                  "count": 39,
                  "mean_probability": 0.5459532875281113,
                  "fraction_positive": 0.28205128205128205
                },
                {
                  "bin": 6,
                  "count": 35,
                  "mean_probability": 0.6488380125590734,
                  "fraction_positive": 0.2571428571428571
                },
                {
                  "bin": 7,
                  "count": 39,
                  "mean_probability": 0.7568997679612576,
                  "fraction_positive": 0.5384615384615384
                },
                {
                  "bin": 8,
                  "count": 58,
                  "mean_probability": 0.8562827860486919,
                  "fraction_positive": 0.6206896551724138
                },
                {
                  "bin": 9,
                  "count": 409,
                  "mean_probability": 0.9823182813987172,
                  "fraction_positive": 0.941320293398533
                }
              ],
              "bin_count": 10,
              "sample_count": 3145
            },
            "validation_after": {
              "brier_score": 0.027371557795554176,
              "ece": 0.007980839019734398,
              "reliability_curve": [
                {
                  "bin": 0,
                  "count": 2459,
                  "mean_probability": 0.004728778780128489,
                  "fraction_positive": 0.0061000406669377795
                },
                {
                  "bin": 1,
                  "count": 75,
                  "mean_probability": 0.14730793709867204,
                  "fraction_positive": 0.2
                },
                {
                  "bin": 2,
                  "count": 61,
                  "mean_probability": 0.24523837973115684,
                  "fraction_positive": 0.22950819672131148
                },
                {
                  "bin": 3,
                  "count": 35,
                  "mean_probability": 0.34415141776425034,
                  "fraction_positive": 0.17142857142857143
                },
                {
                  "bin": 4,
                  "count": 27,
                  "mean_probability": 0.44154647268788816,
                  "fraction_positive": 0.4444444444444444
                },
                {
                  "bin": 5,
                  "count": 35,
                  "mean_probability": 0.54301900112545,
                  "fraction_positive": 0.5714285714285714
                },
                {
                  "bin": 6,
                  "count": 35,
                  "mean_probability": 0.6538263918115245,
                  "fraction_positive": 0.6
                },
                {
                  "bin": 7,
                  "count": 42,
                  "mean_probability": 0.753836648377258,
                  "fraction_positive": 0.6666666666666666
                },
                {
                  "bin": 8,
                  "count": 62,
                  "mean_probability": 0.8523914546960645,
                  "fraction_positive": 0.8709677419354839
                },
                {
                  "bin": 9,
                  "count": 314,
                  "mean_probability": 0.9808863462346393,
                  "fraction_positive": 0.9904458598726115
                }
              ],
              "bin_count": 10,
              "sample_count": 3145
            },
            "test_before": {
              "brier_score": 0.03527404489924365,
              "ece": 0.0363648104111989,
              "reliability_curve": [
                {
                  "bin": 0,
                  "count": 2519,
                  "mean_probability": 0.004631005425646057,
                  "fraction_positive": 0.0031758634378721714
                },
                {
                  "bin": 1,
                  "count": 63,
                  "mean_probability": 0.1488652483574928,
                  "fraction_positive": 0.047619047619047616
                },
                {
                  "bin": 2,
                  "count": 51,
                  "mean_probability": 0.25065046870240976,
                  "fraction_positive": 0.0392156862745098
                },
                {
                  "bin": 3,
                  "count": 37,
                  "mean_probability": 0.3512124628634066,
                  "fraction_positive": 0.21621621621621623
                },
                {
                  "bin": 4,
                  "count": 39,
                  "mean_probability": 0.449757823577294,
                  "fraction_positive": 0.28205128205128205
                },
                {
                  "bin": 5,
                  "count": 36,
                  "mean_probability": 0.5404825657606125,
                  "fraction_positive": 0.1388888888888889
                },
                {
                  "bin": 6,
                  "count": 32,
                  "mean_probability": 0.6548038702458143,
                  "fraction_positive": 0.25
                },
                {
                  "bin": 7,
                  "count": 38,
                  "mean_probability": 0.754786237290031,
                  "fraction_positive": 0.23684210526315788
                },
                {
                  "bin": 8,
                  "count": 60,
                  "mean_probability": 0.8584797958532969,
                  "fraction_positive": 0.5333333333333333
                },
                {
                  "bin": 9,
                  "count": 406,
                  "mean_probability": 0.9836171884548488,
                  "fraction_positive": 0.9334975369458128
                }
              ],
              "bin_count": 10,
              "sample_count": 3281
            },
            "test_after": {
              "brier_score": 0.02606791442682203,
              "ece": 0.009862563408407998,
              "reliability_curve": [
                {
                  "bin": 0,
                  "count": 2605,
                  "mean_probability": 0.004007936799645966,
                  "fraction_positive": 0.004606525911708253
                },
                {
                  "bin": 1,
                  "count": 77,
                  "mean_probability": 0.1445321994966883,
                  "fraction_positive": 0.15584415584415584
                },
                {
                  "bin": 2,
                  "count": 57,
                  "mean_probability": 0.24689495761738653,
                  "fraction_positive": 0.22807017543859648
                },
                {
                  "bin": 3,
                  "count": 29,
                  "mean_probability": 0.3503723893290187,
                  "fraction_positive": 0.13793103448275862
                },
                {
                  "bin": 4,
                  "count": 30,
                  "mean_probability": 0.44610545165621324,
                  "fraction_positive": 0.3
                },
                {
                  "bin": 5,
                  "count": 32,
                  "mean_probability": 0.5490895635922646,
                  "fraction_positive": 0.40625
                },
                {
                  "bin": 6,
                  "count": 33,
                  "mean_probability": 0.6549425267302903,
                  "fraction_positive": 0.5151515151515151
                },
                {
                  "bin": 7,
                  "count": 40,
                  "mean_probability": 0.7439254901859622,
                  "fraction_positive": 0.575
                },
                {
                  "bin": 8,
                  "count": 49,
                  "mean_probability": 0.856595259967475,
                  "fraction_positive": 0.8163265306122449
                },
                {
                  "bin": 9,
                  "count": 329,
                  "mean_probability": 0.9775149146504754,
                  "fraction_positive": 0.9787234042553191
                }
              ],
              "bin_count": 10,
              "sample_count": 3281
            }
          },
          "test_holdout": {
            "sample_count": 3281,
            "positive_count": 465,
            "negative_count": 2816,
            "auroc": 0.9907082416911046,
            "auprc": 0.9553633315138417,
            "f1_at_tau_danger": 0.8588374851720048,
            "brier_score": 0.02606791442682203,
            "confusion_matrix_labels_0_1": [
              [
                2800,
                16
              ],
              [
                103,
                362
              ]
            ],
            "high_risk_recall_at_tau_danger": 0.7784946236559139,
            "tau_danger": 0.8
          },
          "surrogate_fidelity": {
            "sample_count": 3281,
            "mae": 0.013378545890953901,
            "rank_correlation": 0.9674176955074236,
            "agreement_at_tau_safe": 0.9850655288021944,
            "agreement_at_tau_danger": 0.9896373056994818,
            "tau_safe": 0.2,
            "tau_danger": 0.8
          },
          "resolved_rate_limits": {
            "sensor_8": 0.11000000000012733,
            "sensor_9": 15.46000000000031,
            "sensor_12": 1.0799999999999272,
            "sensor_15": 0.0751649999999995,
            "sensor_17": 3.0,
            "sensor_20": 0.35999999999999943,
            "sensor_21": 0.21499999999999986
          }
        },
        "coupling_diagnostics": {
          "fit": {
            "r2": {
              "sensor_1": 1.0,
              "sensor_10": 0.5960550306646777,
              "sensor_11": 0.6895252224577968,
              "sensor_13": 0.6684737339937716,
              "sensor_14": 0.8395734670739033,
              "sensor_16": 0.75,
              "sensor_18": 1.0,
              "sensor_19": 1.0,
              "sensor_2": 0.4206152182981745,
              "sensor_3": 0.34693127887083985,
              "sensor_4": 0.6097914943633385,
              "sensor_5": 0.6490551964196917,
              "sensor_6": 0.030429647494839895,
              "sensor_7": 0.6063082848324981
            },
            "residual_std": {
              "sensor_1": 0.0,
              "sensor_10": 0.0,
              "sensor_11": 0.11432603233325224,
              "sensor_13": 0.035202323234491545,
              "sensor_14": 4.724522401380668,
              "sensor_16": 0.0,
              "sensor_18": 0.0,
              "sensor_19": 0.0,
              "sensor_2": 0.3115621680795145,
              "sensor_3": 4.111053769889324,
              "sensor_4": 4.447478727762513,
              "sensor_5": 0.0,
              "sensor_6": 0.0016527301987515474,
              "sensor_7": 0.45817327442687483
            },
            "below_r2_floor": [
              "sensor_3",
              "sensor_6"
            ],
            "torch_surrogate_mae": {
              "sensor_1": 0.0,
              "sensor_10": 0.0,
              "sensor_11": 0.0,
              "sensor_13": 0.0,
              "sensor_14": 0.0,
              "sensor_16": 0.0,
              "sensor_18": 0.0,
              "sensor_19": 0.0,
              "sensor_2": 0.0,
              "sensor_3": 0.0,
              "sensor_4": 0.0,
              "sensor_5": 0.0,
              "sensor_6": 0.0,
              "sensor_7": 0.0
            },
            "r2_floor": 0.35,
            "cross_validation_folds": 5,
            "training_engine_count": 69,
            "training_row_count": 12066
          },
          "calibration": {
            "engine_ids": [
              1,
              8,
              9,
              11,
              25,
              26,
              28,
              34,
              37,
              48,
              51,
              57,
              58,
              62,
              66,
              83
            ],
            "engine_count": 16,
            "reference_engine_ids": [
              1,
              8,
              9,
              11,
              25,
              26,
              28,
              34,
              37,
              48,
              51,
              57,
              58,
              62,
              66,
              83
            ],
            "row_count": 2649,
            "reference_distribution": "healthy_to_moderate",
            "min_rul_exclusive": 30,
            "sigma_multiplier": 3.0,
            "per_sensor": {
              "sensor_1": {
                "r2": 0.0,
                "residual_mean": 1.1368683772161603e-13,
                "residual_std": 0.0,
                "threshold": 0.0,
                "share_beyond_threshold": 1.0
              },
              "sensor_10": {
                "r2": 0.0,
                "residual_mean": -2.220446049250313e-16,
                "residual_std": 0.0,
                "threshold": 0.0,
                "share_beyond_threshold": 1.0
              },
              "sensor_11": {
                "r2": 0.6954480735439509,
                "residual_mean": -0.002833349729115227,
                "residual_std": 0.11432603233325224,
                "threshold": 0.34297809699975673,
                "share_beyond_threshold": 0.0026425066062665155
              },
              "sensor_13": {
                "r2": 0.6995432023152897,
                "residual_mean": -0.0011090493447235242,
                "residual_std": 0.035202323234491545,
                "threshold": 0.10560696970347463,
                "share_beyond_threshold": 0.0026425066062665155
              },
              "sensor_14": {
                "r2": 0.8957736124858691,
                "residual_mean": 0.24775082249500535,
                "residual_std": 4.724522401380668,
                "threshold": 14.173567204142003,
                "share_beyond_threshold": 0.003775009437523594
              },
              "sensor_16": {
                "r2": 0.0,
                "residual_mean": -6.938893903907228e-18,
                "residual_std": 0.0,
                "threshold": 0.0,
                "share_beyond_threshold": 1.0
              },
              "sensor_18": {
                "r2": 1.0,
                "residual_mean": 0.0,
                "residual_std": 0.0,
                "threshold": 0.0,
                "share_beyond_threshold": 0.0
              },
              "sensor_19": {
                "r2": 1.0,
                "residual_mean": 0.0,
                "residual_std": 0.0,
                "threshold": 0.0,
                "share_beyond_threshold": 0.0
              },
              "sensor_2": {
                "r2": 0.43298132912209497,
                "residual_mean": -0.009893932021525748,
                "residual_std": 0.3115621680795145,
                "threshold": 0.9346865042385435,
                "share_beyond_threshold": 0.0033975084937712344
              },
              "sensor_3": {
                "r2": 0.35313049017258413,
                "residual_mean": 0.048368505375370394,
                "residual_std": 4.111053769889324,
                "threshold": 12.333161309667972,
                "share_beyond_threshold": 0.003020007550018875
              },
              "sensor_4": {
                "r2": 0.608206201746859,
                "residual_mean": -0.1991807605750388,
                "residual_std": 4.447478727762513,
                "threshold": 13.342436183287539,
                "share_beyond_threshold": 0.003020007550018875
              },
              "sensor_5": {
                "r2": -3.0,
                "residual_mean": -3.552713678800501e-15,
                "residual_std": 0.0,
                "threshold": 0.0,
                "share_beyond_threshold": 1.0
              },
              "sensor_6": {
                "r2": 0.03196210865953908,
                "residual_mean": -3.966600793114597e-05,
                "residual_std": 0.0016527301987515474,
                "threshold": 0.004958190596254642,
                "share_beyond_threshold": 0.029067572668931674
              },
              "sensor_7": {
                "r2": 0.5974312930401783,
                "residual_mean": 0.004196818953469809,
                "residual_std": 0.45817327442687483,
                "threshold": 1.3745198232806244,
                "share_beyond_threshold": 0.0015100037750094375
              }
            }
          }
        },
        "artifacts": {
          "model": "artifacts\\reproduction\\model.joblib",
          "mahalanobis": "artifacts\\reproduction\\mahalanobis.joblib",
          "evaluation_report": "artifacts\\reproduction\\evaluation.json",
          "coupling": "artifacts\\reproduction\\coupling.joblib"
        },
        "tau_danger": 0.8,
        "tau_safe": 0.2,
        "D_max": 5.0,
        "feature_names": [
          "sensor_8",
          "sensor_9",
          "sensor_12",
          "sensor_15",
          "sensor_17",
          "sensor_20",
          "sensor_21",
          "op_setting_1",
          "op_setting_2",
          "op_setting_3",
          "sensor_2",
          "sensor_3",
          "sensor_4",
          "sensor_6",
          "sensor_7",
          "sensor_11",
          "sensor_13",
          "sensor_14"
        ],
        "feature_groups": {
          "controllable_actuators": {
            "features": [
              "sensor_8",
              "sensor_9",
              "sensor_12",
              "sensor_15",
              "sensor_17",
              "sensor_20",
              "sensor_21"
            ]
          },
          "immutable_operational": {
            "features": [
              "op_setting_1",
              "op_setting_2",
              "op_setting_3"
            ]
          },
          "immutable_environmental": {
            "features": []
          },
          "dependent_sensors": {
            "features": [
              "sensor_1",
              "sensor_2",
              "sensor_3",
              "sensor_4",
              "sensor_5",
              "sensor_6",
              "sensor_7",
              "sensor_10",
              "sensor_11",
              "sensor_13",
              "sensor_14",
              "sensor_16",
              "sensor_18",
              "sensor_19"
            ]
          },
          "context": {
            "features": [
              "engine_id",
              "cycle"
            ]
          }
        },
        "units": {
          "op_setting_1": "normalized",
          "op_setting_2": "normalized",
          "op_setting_3": "degrees",
          "sensor_1": "degR",
          "sensor_2": "degR",
          "sensor_3": "degR",
          "sensor_4": "degR",
          "sensor_5": "psia",
          "sensor_6": "psia",
          "sensor_7": "psia",
          "sensor_8": "rpm",
          "sensor_9": "rpm",
          "sensor_10": "ratio",
          "sensor_11": "psia",
          "sensor_12": "ratio",
          "sensor_13": "rpm",
          "sensor_14": "rpm",
          "sensor_15": "ratio",
          "sensor_16": "ratio",
          "sensor_17": "C-MAPSS units",
          "sensor_18": "rpm",
          "sensor_19": "rpm",
          "sensor_20": "lbm/s",
          "sensor_21": "lbm/s",
          "engine_id": "identifier",
          "cycle": "cycle"
        },
        "feature_metadata": {
          "op_setting_1": {
            "name": "op_setting_1",
            "label": "Normalized altitude setting",
            "unit": "normalized",
            "cmapss_column": "op_setting_1",
            "group": "immutable_operational",
            "bounds": {
              "minimum": -0.005302,
              "maximum": 0.005202,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "op_setting_2": {
            "name": "op_setting_2",
            "label": "Normalized Mach number setting",
            "unit": "normalized",
            "cmapss_column": "op_setting_2",
            "group": "immutable_operational",
            "bounds": {
              "minimum": -0.0005200000000000001,
              "maximum": 0.0005200000000000001,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "op_setting_3": {
            "name": "op_setting_3",
            "label": "Throttle resolver angle (TRA)",
            "unit": "degrees",
            "cmapss_column": "op_setting_3",
            "group": "immutable_operational",
            "bounds": {
              "minimum": 99.999999,
              "maximum": 100.000001,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_1": {
            "name": "sensor_1",
            "label": "Total temperature at fan inlet (T2)",
            "unit": "degR",
            "cmapss_column": "s1",
            "group": "dependent",
            "bounds": {
              "minimum": null,
              "maximum": null,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_2": {
            "name": "sensor_2",
            "label": "Total temperature at LPC outlet (T24)",
            "unit": "degR",
            "cmapss_column": "s2",
            "group": "dependent",
            "bounds": {
              "minimum": 641.6450000000001,
              "maximum": 643.985,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_3": {
            "name": "sensor_3",
            "label": "Total temperature at HPC outlet (T30)",
            "unit": "degR",
            "cmapss_column": "s3",
            "group": "dependent",
            "bounds": {
              "minimum": 1577.1870239999998,
              "maximum": 1606.482576,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_4": {
            "name": "sensor_4",
            "label": "Total temperature at LPT outlet (T50)",
            "unit": "degR",
            "cmapss_column": "s4",
            "group": "dependent",
            "bounds": {
              "minimum": 1391.544856,
              "maximum": 1432.3723439999999,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_5": {
            "name": "sensor_5",
            "label": "Total pressure at fan inlet (P2)",
            "unit": "psia",
            "cmapss_column": "s5",
            "group": "dependent",
            "bounds": {
              "minimum": null,
              "maximum": null,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_6": {
            "name": "sensor_6",
            "label": "Total pressure at bypass duct (P15)",
            "unit": "psia",
            "cmapss_column": "s6",
            "group": "dependent",
            "bounds": {
              "minimum": 21.599800000000002,
              "maximum": 21.6102,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_7": {
            "name": "sensor_7",
            "label": "Total pressure at HPC outlet (P30)",
            "unit": "psia",
            "cmapss_column": "s7",
            "group": "dependent",
            "bounds": {
              "minimum": 551.0618,
              "maximum": 555.1282,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_8": {
            "name": "sensor_8",
            "label": "Physical fan speed (Nf)",
            "unit": "rpm",
            "cmapss_column": "s8",
            "group": "controllable",
            "bounds": {
              "minimum": 2387.9534,
              "maximum": 2388.2966,
              "source": "training_percentiles"
            },
            "max_rate_of_change": {
              "absolute": 0.11000000000012733,
              "fraction_of_span": null,
              "training_delta_quantile": null
            },
            "direction": "any",
            "controllable_proxy": true,
            "proxy_note": "Measured fan-speed telemetry configured as a controllable proxy; it is not a direct fan actuator command."
          },
          "sensor_9": {
            "name": "sensor_9",
            "label": "Physical core speed (Nc)",
            "unit": "rpm",
            "cmapss_column": "s9",
            "group": "controllable",
            "bounds": {
              "minimum": 9033.449096,
              "maximum": 9155.176104,
              "source": "training_percentiles"
            },
            "max_rate_of_change": {
              "absolute": 15.46000000000031,
              "fraction_of_span": null,
              "training_delta_quantile": null
            },
            "direction": "any",
            "controllable_proxy": true,
            "proxy_note": "Measured core-speed telemetry configured as a controllable proxy; it is not a direct speed or fuel command."
          },
          "sensor_10": {
            "name": "sensor_10",
            "label": "Engine pressure ratio (P50/P2)",
            "unit": "ratio",
            "cmapss_column": "s10",
            "group": "dependent",
            "bounds": {
              "minimum": null,
              "maximum": null,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_11": {
            "name": "sensor_11",
            "label": "Static pressure at HPC outlet (Ps30)",
            "unit": "psia",
            "cmapss_column": "s11",
            "group": "dependent",
            "bounds": {
              "minimum": 47.026999999999994,
              "maximum": 48.223000000000006,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_12": {
            "name": "sensor_12",
            "label": "Fuel flow to Ps30 ratio (phi)",
            "unit": "ratio",
            "cmapss_column": "s12",
            "group": "controllable",
            "bounds": {
              "minimum": 519.4752,
              "maximum": 522.8448,
              "source": "training_percentiles"
            },
            "max_rate_of_change": {
              "absolute": 1.0799999999999272,
              "fraction_of_span": null,
              "training_delta_quantile": null
            },
            "direction": "any",
            "controllable_proxy": true,
            "proxy_note": "Fuel-flow ratio derived from measured telemetry, configured as a proxy; it is not a direct fuel actuator command."
          },
          "sensor_13": {
            "name": "sensor_13",
            "label": "Corrected fan speed (NRf)",
            "unit": "rpm",
            "cmapss_column": "s13",
            "group": "dependent",
            "bounds": {
              "minimum": 2387.9534,
              "maximum": 2388.2966,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_14": {
            "name": "sensor_14",
            "label": "Corrected core speed (NRc)",
            "unit": "rpm",
            "cmapss_column": "s14",
            "group": "dependent",
            "bounds": {
              "minimum": 8111.794183999999,
              "maximum": 8220.339816,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_15": {
            "name": "sensor_15",
            "label": "Bypass ratio (BPR)",
            "unit": "ratio",
            "cmapss_column": "s15",
            "group": "controllable",
            "bounds": {
              "minimum": 8.36527224,
              "maximum": 8.53873176,
              "source": "training_percentiles"
            },
            "max_rate_of_change": {
              "absolute": 0.0751649999999995,
              "fraction_of_span": null,
              "training_delta_quantile": null
            },
            "direction": "any",
            "controllable_proxy": true,
            "proxy_note": "Measured bypass ratio configured as a synopsis proxy; it is not a verified variable-geometry actuator command."
          },
          "sensor_16": {
            "name": "sensor_16",
            "label": "Burner fuel-air ratio (farB)",
            "unit": "ratio",
            "cmapss_column": "s16",
            "group": "dependent",
            "bounds": {
              "minimum": null,
              "maximum": null,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_17": {
            "name": "sensor_17",
            "label": "Bleed enthalpy (htBleed)",
            "unit": "C-MAPSS units",
            "cmapss_column": "s17",
            "group": "controllable",
            "bounds": {
              "minimum": 389.86,
              "maximum": 397.14,
              "source": "training_percentiles"
            },
            "max_rate_of_change": {
              "absolute": 3.0,
              "fraction_of_span": null,
              "training_delta_quantile": null
            },
            "direction": "any",
            "controllable_proxy": true,
            "proxy_note": "Bleed-related enthalpy telemetry configured as a proxy; it is not a direct bleed-valve command."
          },
          "sensor_18": {
            "name": "sensor_18",
            "label": "Demanded fan speed (Nf_dmd)",
            "unit": "rpm",
            "cmapss_column": "s18",
            "group": "dependent",
            "bounds": {
              "minimum": null,
              "maximum": null,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_19": {
            "name": "sensor_19",
            "label": "Corrected fan speed demand (PCNfR_dmd)",
            "unit": "rpm",
            "cmapss_column": "s19",
            "group": "dependent",
            "bounds": {
              "minimum": null,
              "maximum": null,
              "source": "training_percentiles"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "sensor_20": {
            "name": "sensor_20",
            "label": "HPT coolant bleed (W31)",
            "unit": "lbm/s",
            "cmapss_column": "s20",
            "group": "controllable",
            "bounds": {
              "minimum": 38.3438,
              "maximum": 39.1862,
              "source": "training_percentiles"
            },
            "max_rate_of_change": {
              "absolute": 0.35999999999999943,
              "fraction_of_span": null,
              "training_delta_quantile": null
            },
            "direction": "any",
            "controllable_proxy": true,
            "proxy_note": "Measured coolant-bleed channel configured as a proxy; it is not a verified actuator command."
          },
          "sensor_21": {
            "name": "sensor_21",
            "label": "LPT coolant bleed (W32)",
            "unit": "lbm/s",
            "cmapss_column": "s21",
            "group": "controllable",
            "bounds": {
              "minimum": 23.00723016,
              "maximum": 23.51546984,
              "source": "training_percentiles"
            },
            "max_rate_of_change": {
              "absolute": 0.21499999999999986,
              "fraction_of_span": null,
              "training_delta_quantile": null
            },
            "direction": "any",
            "controllable_proxy": true,
            "proxy_note": "Measured coolant-bleed channel configured as a proxy; it is not a verified actuator command."
          },
          "engine_id": {
            "name": "engine_id",
            "label": "Engine unit identifier",
            "unit": "identifier",
            "cmapss_column": "unit_id",
            "group": "context",
            "bounds": {
              "minimum": 1.0,
              "maximum": 1000.0,
              "source": "manual"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          },
          "cycle": {
            "name": "cycle",
            "label": "Within-engine cycle index",
            "unit": "cycle",
            "cmapss_column": "cycle",
            "group": "context",
            "bounds": {
              "minimum": 1.0,
              "maximum": 10000.0,
              "source": "manual"
            },
            "max_rate_of_change": null,
            "direction": "any",
            "controllable_proxy": false,
            "proxy_note": null
          }
        },
        "scaling": {
          "feature_names": [
            "sensor_8",
            "sensor_9",
            "sensor_12",
            "sensor_15",
            "sensor_17",
            "sensor_20",
            "sensor_21",
            "op_setting_1",
            "op_setting_2",
            "op_setting_3",
            "sensor_2",
            "sensor_3",
            "sensor_4",
            "sensor_6",
            "sensor_7",
            "sensor_11",
            "sensor_13",
            "sensor_14"
          ],
          "mean": [
            2388.0997437522,
            9064.343129179866,
            521.3886617388243,
            8.442872777191129,
            393.2356212601197,
            38.81242449841605,
            23.287191918338614,
            -7.384723688841948e-06,
            1.5557902147131283e-06,
            100.0,
            642.6931664906723,
            1590.6221851460755,
            1409.1616205561422,
            21.609821893699408,
            553.3415036958818,
            47.54849208025344,
            2388.099601548751,
            8142.866206265399
          ],
          "scale": [
            0.06974881632145821,
            21.464241463059185,
            0.7295695480380889,
            0.03734831434627618,
            1.5368379437519823,
            0.18028447548133816,
            0.10768671319143475,
            0.0021886358975498873,
            0.00029284265266715716,
            1.0,
            0.49595802152649715,
            6.110300911695956,
            8.921072064440283,
            0.001322626610827966,
            0.8797325231502738,
            0.26460598115474865,
            0.07044183221540404,
            18.472666865486453
          ]
        },
        "assumptions": [
          "C-MAPSS controls, bounds, rates and K are proxies/assumptions; no RUL extension."
        ],
        "mode": "FAST",
        "authentication_enabled": false
      },
      "request_id_echo": "phase11-independent-smoke"
    },
    {
      "route": "/recommend",
      "status": 200,
      "engine": 5,
      "cycle": 241,
      "triage": "RECOVERABLE",
      "risk_before": 0.883373152081179,
      "risk_after": 0.1284214696040072,
      "evidence_level": "E3",
      "config_hash": "f5f591525e1de8b8df2b429518d3d09856d7f6381bbc498947fdb5982a57377c",
      "model_version": "xgb:artifact-3:e2792cebf7673b0720da734c7bbd52c70f51cfa96c41654ed507c104d0b33dc1",
      "request_id_echo": "phase11-independent-smoke"
    },
    {
      "route": "/recommend",
      "status": 200,
      "engine": 2,
      "cycle": 278,
      "triage": "ESCALATE",
      "risk_before": 0.997038295561199,
      "risk_after": 0.3612983062471661,
      "evidence_level": "none",
      "config_hash": "f5f591525e1de8b8df2b429518d3d09856d7f6381bbc498947fdb5982a57377c",
      "model_version": "xgb:artifact-3:e2792cebf7673b0720da734c7bbd52c70f51cfa96c41654ed507c104d0b33dc1",
      "request_id_echo": "phase11-independent-smoke"
    },
    {
      "route": "/recommend",
      "invalid": "empty state",
      "status": 422,
      "body": {
        "detail": "body: Value error, state must not be empty",
        "errors": [
          {
            "type": "value_error",
            "loc": [
              "body"
            ],
            "msg": "Value error, state must not be empty"
          }
        ],
        "error_type": "RequestValidationError",
        "mode": "THOROUGH"
      },
      "request_id_echo": "phase11-independent-smoke"
    }
  ],
  "completed_utc": "2026-10-28T13:59:52.728907+00:00",
  "passed": true
}
```

## Dashboard smoke and actual browser walkthrough

Owned Streamlit endpoint `http://127.0.0.1:8502`. Real-asset AppTest exercised the same
RECOVERABLE/ESCALATE cases,3exports per case and Fleet/Diagnostics/Evaluation/About pages.
The expected ESCALATE alert is a domain outcome; it is not an uncaught application exception.
Full independent JSON/log/exit evidence: `artifacts/phase11/dashboard-apptest*`.

```json
{
  "started_utc": "2026-10-28T14:01:26.922120+00:00",
  "runtime_source": "02f0145ad9ef75b10f3235455453cbaec0f0a9da",
  "workspace": "C:\\Users\\chira\\prescriptxai-phase11-reproduce",
  "runtime_config_sha256": "b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e",
  "cases": [
    {
      "engine": 5,
      "cycle": 241,
      "status": "RECOVERABLE",
      "risk_before": 0.883373152081179,
      "risk_after": 0.1284214696040072,
      "evidence_level": "E3",
      "exports": 3,
      "warnings": [
        "Model-based validity is not physical validity. No RUL extension is claimed on static datasets. Actuator limits are proxy assumptions on C-MAPSS. This tool does not establish real-machine safety or RUL extension.",
        "ALERT \u00b7 calibrated risk is at or above the configured alert threshold."
      ],
      "errors": []
    },
    {
      "engine": 2,
      "cycle": 278,
      "status": "ESCALATE",
      "risk_before": 0.997038295561199,
      "risk_after": 0.3612983062471661,
      "evidence_level": "none",
      "exports": 3,
      "warnings": [
        "Model-based validity is not physical validity. No RUL extension is claimed on static datasets. Actuator limits are proxy assumptions on C-MAPSS. This tool does not establish real-machine safety or RUL extension.",
        "ALERT \u00b7 calibrated risk is at or above the configured alert threshold."
      ],
      "errors": [
        "ESCALATE \u00b7 no accepted action. Schedule maintenance and obtain domain review."
      ]
    }
  ],
  "pages": [
    {
      "page": "Fleet Overview",
      "errors": [],
      "warnings": [
        "Model-based validity is not physical validity. No RUL extension is claimed on static datasets. Actuator limits are proxy assumptions on C-MAPSS. This tool does not establish real-machine safety or RUL extension."
      ],
      "dataframe_count": 1
    },
    {
      "page": "Model and Validation Diagnostics",
      "errors": [],
      "warnings": [
        "Model-based validity is not physical validity. No RUL extension is claimed on static datasets. Actuator limits are proxy assumptions on C-MAPSS. This tool does not establish real-machine safety or RUL extension."
      ],
      "dataframe_count": 1
    },
    {
      "page": "Evaluation Results",
      "errors": [],
      "warnings": [
        "Model-based validity is not physical validity. No RUL extension is claimed on static datasets. Actuator limits are proxy assumptions on C-MAPSS. This tool does not establish real-machine safety or RUL extension."
      ],
      "dataframe_count": 1
    },
    {
      "page": "About and Limitations",
      "errors": [],
      "warnings": [
        "Model-based validity is not physical validity. No RUL extension is claimed on static datasets. Actuator limits are proxy assumptions on C-MAPSS. This tool does not establish real-machine safety or RUL extension."
      ],
      "dataframe_count": 0
    }
  ],
  "completed_utc": "2026-10-28T14:02:48.751383+00:00",
  "passed": true
}
```

Real browser screenshot: [RECOVERABLE](screenshots/phase11-browser-recoverable.png).
Actual exported JSON remains `artifacts/phase11/browser-recoverable-export.json`.
Browser ESCALATE also completed; [actual ESCALATE screenshot](screenshots/phase11-browser-escalate.png),
[evaluation](screenshots/phase11-browser-evaluation.png) and [diagnostics](screenshots/phase11-browser-diagnostics.png).
API, AppTest and browser exports agree on38non-operational fields per case with0mismatches.
The actual downloaded8row metric CSV matches144saved fields exactly, including CIs, counts and provenance.
Proof `artifacts/phase11/smoke-export-reconciliation.json`.
These are real software demonstrations under assumed proxy constraints, not a field experiment.

## Docker build

Docker daemon is available (server29.4.0). Actual new package and image builds on d12dec1
completed **exit0**; Docker build elapsed326.06s. Command/artifact wrapper:
`artifacts/phase11/run_docker_build.ps1`, logs `package-build.log/.exit` and `docker-build.log/.exit`.
Wheel SHA256 `6ed2e12faefd1105760f30ffe9d35d2e85be2e3914f3c5c01203f297ae6b6da6`;
68installed source hashes match this wheel/commit with0mismatches. Image manifest-list identity
`80e3503c9b50688fa9ab2d264af9d002c762105dec7f505d93c4617b501f9b70`, tag
`prescriptxai:phase11-d12dec1`.

Real output excerpt:

```text
#14 exporting to image
#14 exporting layers
#14 exporting layers 102.7s done
#14 exporting manifest sha256:6fb8532a8c5bf73ff54724e93a5e26397cbb99ec8e82df035bc179ccb3e30dd0 0.0s done
#14 exporting config sha256:178318178a629c9c753a63b29c9ac106885bd874b1db31a27c4d4afe017e7eec 0.0s done
#14 exporting attestation manifest sha256:bce1d5a77a32919ceb7b350c245753a1ff88c87c93c241f6624fa3114fb2cbe6 0.0s done
#14 exporting manifest list sha256:80e3503c9b50688fa9ab2d264af9d002c762105dec7f505d93c4617b501f9b70 0.0s done
#14 naming to docker.io/library/prescriptxai:phase11-d12dec1
#14 naming to docker.io/library/prescriptxai:phase11-d12dec1 0.0s done
#14 unpacking to docker.io/library/prescriptxai:phase11-d12dec1
#14 unpacking to docker.io/library/prescriptxai:phase11-d12dec1 38.9s done
#14 DONE 141.9s
```

Owned API/dashboard runtime on verified-free ports8011/8511 passed bothhealthHTTP200,
invalidempty-state422, UID/GID10001:10001 and read-only config/artifact/data mount inspection.
An initial port8002attempt collided with an unrelatedtaxii-server; failure output is retained in
`docker-runtime-smoke-attempt1.log`. Only the owned failed container was removed and freeports
selected. Unrelated containers were not modified. Agent's initial assumption that no unrelated
containers were running was corrected after inventory; the actual inventory/inspection is preserved.
Only the two owned verification containers are cleaned up after checks.

Actual latest-installed Docker HTTP case outputs (Linux results are separately labeled; no
cross-platform action identity claim):

```json
{
  "runtime_source": "d12dec1a1a776d9e8416cec22d879e560498875f",
  "platform": "Linux Docker; fitted artifacts remain the Windows Phase11 reproduction",
  "timings_are_isolated_latency_measurements": false,
  "cases": [
    {
      "engine": 5,
      "cycle": 241,
      "http_status": 200,
      "status": "RECOVERABLE",
      "risk_before": 0.883373152081179,
      "risk_after": 0.10835729296287716,
      "evidence_level": "E3",
      "config_hash": "0e825c8110f59845f98dcf3ad6ecedcc058c89d7242ad1a779be658dd4de5760",
      "model_version": "xgb:artifact-3:e2792cebf7673b0720da734c7bbd52c70f51cfa96c41654ed507c104d0b33dc1",
      "schema_version": "2.0.0"
    },
    {
      "engine": 2,
      "cycle": 278,
      "http_status": 200,
      "status": "ESCALATE",
      "risk_before": 0.997038295561199,
      "risk_after": 0.3612983062471661,
      "evidence_level": "none",
      "config_hash": "0e825c8110f59845f98dcf3ad6ecedcc058c89d7242ad1a779be658dd4de5760",
      "model_version": "xgb:artifact-3:e2792cebf7673b0720da734c7bbd52c70f51cfa96c41654ed507c104d0b33dc1",
      "schema_version": "2.0.0"
    }
  ],
  "passed": true
}
```

## Protocol, metric and honesty audit

Independent protocol audit scanned all173986historical payloads and checked171490quality records:
zero fixed-threshold/tier/K/k/schema mismatches.112fitted and44diagnostic-validator hashes match;
28partition sets are disjoint. Initial preregistration commit0c0b6e1 at2026-10-20T04:16:38Z
precedes measured source63c2ed4 at10:25:25Z and run launch10:25:40.691773Z.
There is no final-evaluation change in tau_safe/tau_danger/D_max/bounds/rates relative to the
frozen profiles. Predictor selection is predictive/calibration-based; recourse-model comparisons
are separate. Strict once-ever test/fresh-engine evidence remains **Partial**, due to explicitly
recorded priorFD001 exposure and a legacy dirty-source diagnosis without a matching raw run.
A new replay cannot repair that historical provenance retroactively.

The metric audit confirms true calibrated validity, Tier2alone/both denominators, Tier3,
Tier4and joint are separate. Failures remain in all-query denominators, and conditional zero
bootstrap denominators are disclosed. The latency verdict uses p95<=upper budget, including
faster-than-lower-band passes. Every design target has its measured CI/count/gap in
[the complete appendix](final_targets.md); the current requirement map is [traceability](traceability.md).

Initial honesty scan classified237matching claim lines, each with rationale; inventory/classification
CSVs are preserved under `artifacts/phase11/`. Numeric examples in the synopsis are illustrative;
target literals are targets or confidence/histogram definitions, not achieved results. Historical
Phase4joint90% target and evidence vocabulary have a prominent erratum. The four independently
identified presentation gaps were corrected and independently rechecked; exact proof/hashes are in
`presentation-fix-independent-review.md` and `presentation-fix-review-hashes.json`.
No historical result/config/model was overwritten. New report/runtime source is explicitly distinct
from measured63c2ed4; unsupported gradient operations now raise explicit TypeError capability errors.

Independent final source rescan of65files found0 ast.Pass statements and0NotImplementedError/TODO/FIXME/placeholder/stub markers and7valid Protocol/abstract declarations; proof `source-final-independent-rescan.json`. Abstract/Protocol method signatures are contracts,
not executable pass-only implementations. Only the optional simulator interface is intentionally absent
of a validated adapter; paper TODO-VERIFY citations are explicitly permitted and remain unverified.

## Full second-seed replay and final status

Preregistration commit `02f0145ad9ef75b10f3235455453cbaec0f0a9da` precedes actual
launch2026-10-28T13:56:38.0098220Z. Run `phase11-seed1730-20261028T030707Z` executes
clean frozen source63c2ed4 in `C:/Users/chira/.codex/worktrees/phase11-frozen-replay/5thsemEL`.
Registered study `configs/experiments/phase11-seed1730-replay.yaml`, SHA256
`59b1f3c3d139dea7971eddf01f2401e520694dd804b36ad6ebb18ef6e892cd60`;
audit `configs/experiments/phase11-audit.yaml`, SHA256
`fc1ea34597768a647f59517e9675a32bd12dddd65240fb73143da88939a560e2`.
All151copied inputs/42,494,689bytes were independently checked at both roots with0hash mismatches.
Python3.13.9 and recorded core dependency versions match; Windows build changed26200→26300,
which is disclosed. The taxonomy bytehash also differs solely because Git converted8LF endings
toCRLF in the clean replay checkout; parsed YAML and newline-normalized bytes match exactly.
Both hashes and the unchanged semantic comparison are retained in `replay-manifest-audit.json`.
No running source/configuration file was edited. No cross-OS-build timing or bitwise guarantee is inferred.

An additional registration byte audit distinguishes the committed study blob from its Windows
working-file representation. In preregistration commit02f0145, the study is 2,034 bytes / 122 LF
endings, SHA256 `08b9667a1d6c257d9910349ccfa623b5e2c24cd0336a33c8613e295a21603adc`.
The unchanged runtime study is 2,156 bytes / 122 CRLF endings, SHA256
`59b1f3c3d139dea7971eddf01f2401e520694dd804b36ad6ebb18ef6e892cd60`, matching the
saved manifest and active pointer. Newline-normalized bytes and parsed YAML are exactly
equal, with no BOM or text differences. This is a Git line-ending representation difference,
not a post-registration parameter change. Both raw hashes are retained; runtime files were
not edited to force hash agreement. Proof:
`artifacts/phase11/replay-registration-study-byte-difference-peer-audit.json` and its supplement.

Full scope34298quality records/64groups is retained. Only solver seed1730 and run/output labels
change; no models/thresholds/bounds/rates/configured populations are refitted or capped.
New1730 is compared to historical1730, then separately1729. Discrete/query/verdict identities
must match exactly; numeric tolerance1e-6abs+1e-5relative; cross-seed rate tolerance0.
These are newly committed Phase11 audit criteria, not retroactive historical tolerance rules.
Timings/execution identity are the only declared comparison exclusions; timings stay saved.
The complete comparison was **pending at the following checkpoints** and has now passed.
The initial execution segment stopped after7651saved
records, last checkpoint2026-10-28T16:55:16.159869Z; discovery2026-10-29T02:38:22Z found no
live experiment process or exit marker. The process termination time and cause are unknown.
Windows had not rebooted sinceOct25; no shutdown/sleep/resource event or Python exception was
located in the inspected window. Store-update failures mentioning ChatGPT occurred near the last
checkpoint, but that correlation does not establish a cause. Host evidence is preserved in
`artifacts/phase11/interruption-host-events.json`. No causal software defect is invented.
Independent duplicate/provenance/input/checkpoint integrity checks passed before same-run
resume at2026-10-29T02:43:47.0537898Z. Segment2 has separate durable stdout/stderr/exit
metadata, preserved in `replay-active-run.json`. At02:58Z7823/34298results were saved.
Post-resume independent proof confirms all7651original results INCLUDINGtimings and7655case
payloads remain byte-identical; first20new scientific records/cases exactly match historical1730.
Four registered but uncommitted in-flight cases may be retried and are explicitly disclosed.
There is no replacement population or discarded completed timing. Proof:
`replay-segment2-independent-audit.md` and `replay-segment2-post-resume-preservation.json`. Fresh-engine generalization and isolated serial latency
are not claimed by this replay. Current process/log/checkpoint pointers:
`artifacts/phase11/replay-active-run.json`, `replay-launch-audit.json` and `replay-input-copy.json`.

Segment 2 subsequently ended with `BrokenProcessPool` after **30,729 saved results / 30,733
registered cases**; the last checkpoint was **2026-10-29T10:57:42.428547Z**. Windows recorded
shutdown-delay events seconds later and planned OS-upgrade restarts, with current boot at
11:03:54Z. This supports host shutdown as the interruption context; it does not prove the
precise worker-termination mechanism. The unknown-cause/no-reboot finding above concerns
the first segment's discovery window only. Actual traceback excerpt:

```text
concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly while the future was running or pending.
```

Independent recovery checks verified SQLite integrity, frozen source/core versions, all 151
copied inputs in both roots, every retained query/case against historical seed1730, and all
original timing hashes. **Zero exact scientific or case mismatches** were found in the 30,729
saved results. All 30,729 result payloads INCLUDING timings and 30,733 cases were separately
hashed for the next preservation check. Four registered cases had no committed result and
may be retried; no completed failure or timing is replaced. Source, configuration, workers
and declared populations remain unchanged. Evidence:
`artifacts/phase11/replay-segment3-preflight-independent.json`,
`replay-segment3-preserved-payload-hashes.json` and
`replay-segment3-host-evidence-independent.json`. The exact shutdown-delay events at
10:57:49Z and 10:57:52Z are retained separately in
`replay-segment3-shutdown-window-doc-review.json`; the host-evidence file retains the later
restart events. Post-launch independent verification found zero changes in all 30,729
completed result/timing payloads and 30,733 cases:
`replay-segment3-post-resume-preservation-independent.json`.

After a fresh zero-duplicate process inventory, the same run resumed as **segment 3 at
2026-10-29T15:37:16.7751539Z**, using the exact reviewed command and separate durable
stdout/stderr/exit paths. At resume, 62 of 64 groups were count-complete; **3,569 queries**
remained (3,361 FAST / 208 THOROUGH), both FD002/v2 grouped-OOF populations. An old value
38 in active health metadata was a stale cache, not a scientific-group count. Final acceptance
still requires all 34,298 records, all 64 groups, the source/count completion flag, an actual
successful process exit, complete comparisons against both seeds, whole-engine CIs, and
preservation of every completed payload from each prior segment. Operational replay timings
are retained and disclosed; they do not certify a new isolated serial-latency result.

Segment 3 then saved another **2,309 results** before a further host interruption, leaving
**33,038 saved results / 33,042 registered cases**. Its last checkpoint is
**2026-10-29T16:34:56.480744Z**; no exit marker exists. The host stopped returning commands
during this period. On reconnection, Windows evidence showed idle standby, a user-initiated
power-off, an unclean boot at **16:47:00Z**, and no surviving experiment process. These
events establish interruption context, not the exact worker termination time/mechanism.
Evidence: `artifacts/phase11/replay-segment4-host-evidence-independent.json`.

The next independent preflight checked every retained scientific record/case against historical
seed1730: **zero mismatches across all 33,038 results**; SQLite integrity OK. Frozen source,
core versions, manifest assets, configuration and all 151 copied inputs in both roots match.
Every prior 30,729 result/timing and 30,733 case hash remains intact. A new pinned baseline
covers all **33,038 completed results INCLUDING timings / 33,042 cases**; the independent
post-launch check again found zero payload changes. Four uncommitted cases may be retried;
they are not replacement observations. Proofs:
`replay-segment4-preflight-independent.json`, `replay-segment4-preserved-payload-hashes.json`,
`replay-segment4-inflight-case-audit.json` and
`replay-segment4-post-resume-preservation-independent.json`, with successful native exits.

Following a fresh zero-duplicate inventory and independent wrapper review, the **same run
resumed as segment 4 at 2026-10-29T16:56:04.4168125Z**, under unchanged source/study/workers.
Separate logs and exit metadata are in `replay-segment4.execution.json` and the active pointer.
At resume, **1,260 queries remained: 1,156 FAST / 104 THOROUGH**, with 62/64 groups
count-complete. Final acceptance still requires the complete registered population, successful
stage/exit markers, both historical-seed comparisons, all engine-CI checks, and full preservation
of the newest 33,038-result timing baseline. No scientific configuration or power policy changed.

The complete replay and independent comparisons subsequently passed, as recorded below.
Missing physical evidence and roadmap outputs remain explicit Partial/Not met states,
not reasons to fabricate results or add features.

## Accepted complete replay and raw preservation

Run `phase11-seed1730-20261028T030707Z`; execution source
`63c2ed445fba16c73a2771e184f635abf76b4405`; preregistration
`02f0145ad9ef75b10f3235455453cbaec0f0a9da`. Study
`configs/experiments/phase11-seed1730-replay.yaml`, measured runtime SHA256
`59b1f3c3d139dea7971eddf01f2401e520694dd804b36ad6ebb18ef6e892cd60`; audit
`configs/experiments/phase11-audit.yaml`, SHA256
`fc1ea34597768a647f59517e9675a32bd12dddd65240fb73143da88939a560e2`.
The committed/runtime study newline distinction and both raw hashes are documented above.
Scope: FD001/XGB/MLP/LSTM and FD002/XGB; protocols v1/v2; k_max3, assumed K1,
D_max5/8; internal held-out, grouped-OOF, official-test and development populations.
All 32,116 main FAST + 1,526 test THOROUGH + 480 development FAST + 176 development
THOROUGH queries are retained. No refitting, threshold/bound/rate changes or new population caps.

Actual quality command, executed in the frozen checkout in four disclosed segments:

```text
.venv/Scripts/python.exe scripts/diagnostics/phase7_experiments.py --study C:/Users/chira/OneDrive/Desktop/5thsemEL/configs/experiments/phase11-seed1730-replay.yaml --run-id phase11-seed1730-20261028T030707Z --stage quality
```

Final checkpoint: **2026-10-29T18:37:58.711939Z**. The actual segment4 exit file contains
`0`; `stages.json` contains:

```json
{
  "quality": {
    "complete": true,
    "source": "63c2ed445fba16c73a2771e184f635abf76b4405",
    "observations": 34298
  }
}
```

Independent complete-record/case/config comparison, approved helper SHA256
`f839e9bee9723075c8c95503360f0073b787c5f4372d7a56428203b520004818`, finished with
JSON `passed=true`, native exit0 and the following actual output:

```json
{
  "1730": {
    "matched_new_identities": 34298,
    "historical_quality_identities": 34298,
    "not_yet_present_or_missing": 0,
    "groups": 64,
    "historical_groups": 64,
    "verified_config_hashes": 34298,
    "mismatch_count": 0,
    "mismatch_fields": {},
    "passed": true
  },
  "1729": {
    "matched_new_identities": 34298,
    "historical_quality_identities": 34298,
    "not_yet_present_or_missing": 0,
    "groups": 64,
    "historical_groups": 64,
    "verified_config_hashes": 34298,
    "mismatch_count": 0,
    "mismatch_fields": {},
    "passed": true
  }
}
```

Numerical tolerance is absolute1e-6 / relative1e-5; query/discrete/verdict/group counts
match exactly. Timings remain saved and are excluded from scientific equality comparison.
Full proof: `artifacts/phase11/replay-complete-comparison.json/.log/.exit`.

The independently implemented whole-engine bootstrap, approved helper SHA256
`375dc54c0b4f6053bd55df93bae8750d9121245b519561ba7169184d67805ed1`, also returned
JSON `passed=true`, failures[] and native exit0. Selected actual output fields:

```json
{
  "complete_records": 34298,
  "quality_groups": 64,
  "metrics_per_group": 9,
  "independent_ci_objects": 576,
  "bootstrap_unit": "wholeengine",
  "bootstrap_seed": 1729,
  "bootstrap_replicates": 2000,
  "bootstrap_confidence": 0.95,
  "same_seed_ci_fields_checked": 5184,
  "historical_five_seed_ci_fields_checked": 4032,
  "historical_five_seed_observation_and_denominator_accounting_checked": true,
  "failures": [],
  "passed": true
}
```

All 576 saved intervals include engine counts, observations, denominators and undefined
conditional/zero-denominator information. They agree with historical1730 and the published
five-seed intervals within the registered tolerance, with exact fivefold observation and
denominator accounting. Proof: `replay-complete-engine-ci-audit.json/.log/.exit`.
The published [target appendix](final_targets.md) retains every measured target, CI and gap;
a fresh independent recheck found zero discrepancies in its 216 metric / 12 latency rows.

Final provenance returned JSONtrue/native0: frozen source clean; all 151 unique inputs at
both roots (302 file/root checks), 42,494,689 bytes per root, 28 fitted profiles, 44 diagnostic
validators, core versions and all registration guards match. Proof:
`replay-final-provenance-independent.json/.log/.exit`.

Four segments saved **7,651 + 23,078 + 2,309 + 1,260 = 34,298** results. Every completed
payload and timing survived each restart. Four registered but uncommitted cases at each
resume may have retried optimizer work; its interrupted duration is unknown. No completed
failure or timing was replaced. These operational quality timings do not establish a new
isolated serial-latency measurement. Reused engines do not establish fresh-engine generalization.

After every writer and audit reader exited, the whole unique raw run was copied to the main
checkout at `artifacts/phase11/seed-replay/phase11-seed1730-20261028T030707Z`.
Independent backup verification returned JSONtrue/errors[]/native0:

```text
5 files / 501432936 bytes; every raw byte hash identical before and after verification.
Source SQLite integrity: ok. Copy SQLite integrity: ok.
34298 result payloads and34298 case payloads at each root: identical hashes, INCLUDING timings.
64 group counts identical; all33038 prior result/timing payloads and33042 prior cases intact.
144 unique scientific model/diagnostic-asset paths have matching main-checkout counterparts.
```

The lines above summarize fields from the actual JSON, not fabricated console output.
SQLite file SHA256 is `2faec68f7dc7d7663d5c6bb34e2ade017cae12cde1c9bed4fbe7005ff0c0c32f`;
record-hash-map SHA256 is `af67c0ed72d4910f8cb32e3a2984fed37dcb2adc8e92e14991c81c4916f15d29`.
Proofs: `replay-raw-backup-bytecopy.json` and
`replay-raw-backup-independent-audit.json/.log/.exit`.

The managed archive tool refused optional cleanup with: `The task's primary checkout cannot be removed.`
The protected frozen checkout is retained intact; no manual removal or workaround was attempted.
The independently verified main-checkout copy is the canonical preserved result directory.
See `replay-worktree-retention.json` and `replay-active-run.json`; all four original segments
and execution paths remain recorded. Consolidated replay acceptance:
`replay-final-independent-acceptance.json/.md/.log/.exit`.


## Earlier documentation checkpoints

An earlier independent review confirmed all216metric rows/24config identities/
12latency rows match saved evidence, all20local links resolve and all32exception rows match
traceability (20Partial/12Notmet). Strict `uv run mkdocs build --strict` completedexit0 in5.88s
with the Final audit navigation. Evidence `artifacts/phase11/docs-strict-independent-20261029.log/.exit`
and `final-docs-independent-review-20261029.md`. Later text-only checkpoint updates retain the
same links/nav. Closure review was still pending at that checkpoint; the final accepted
requirement counts are 33 Done / 19 Partial / 12 Not met, with 31 exceptions.

The segment3 recovery checkpoint also passed a fresh independent strict build:
`.venv/Scripts/python.exe -m mkdocs build --strict --site-dir artifacts/phase11/docs-site-segment3-independent-20261029`.
Actual output: `Documentation built in 3.99 seconds`, native exit0. The reviewer verified
the root and all four audit HTML pages, navigation/content, all 20 links, and unchanged
before/after hashes for 143 source/documentation/configuration files. The 64 traceability
rows still match all 32 exceptions. Proof:
`artifacts/phase11/segment3-docs-independent-checkpoint-review.md/.json` and
`docs-strict-segment3-independent-20261029-attempt2.log/.exit`.
An earlier default-output attempt returned exit0 but stopped at cleaning with missing HTML;
it is explicitly rejected and preserved. An audit-only navigation probe initially required
an active page to link to itself; the corrected probe checks its label and other-page links,
with that first false audit retained. No product source or scientific result changed.

## Final documentation verification

The independent closing-text review passed **21 checks**: all 64 requirement rows and 31
exceptions agree, all 23 local links resolve, pasted outputs match actual evidence, source
scopes and raw-backup hashes pass, and the root plus four audit HTML pages render with the
correct navigation/statuses. All 390 tracked-file hashes were stable during that review.
The actual strict build was:

```text
.venv/Scripts/python.exe -m mkdocs build --strict --site-dir artifacts/phase11/docs-site-final-closure-independent-20261030
INFO    -  Documentation built in 4.25 seconds
```

Native exit0 and actual HTML were both verified; exit0 alone was not accepted.
Proof: `artifacts/phase11/phase11-final-closure-independent-review.json/.log/.exit` and
`docs-strict-final-closure-independent-20261030.log/.exit`, with before/after hash snapshots.
The final bounded publication check of this evidence reference is retained beside those proofs.
