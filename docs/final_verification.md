# Final verification — Phase 11 in progress

Status at this checkpoint: **Partial**. Independent checks below are real completed checks;
post-fix full checks, Docker build and current installed reproduction have passed. The complete
34298-record seed replay was interrupted after7651saved records and has resumed as a verified second execution segment; its final comparison remains pending.
No overall final-audit completion is claimed from these partial outputs.

Main checkout: `C:/Users/chira/OneDrive/Desktop/5thsemEL`.
Release under audit: `b219041801d720f75973da24a1c5b43d5dcd0154` /0.2.0.
Reviewed report corrections: `d12dec1a1a776d9e8416cec22d879e560498875f`. Independent reviewers did not implement product code.
Schemas RecourseResult/ValidationReport remain2.0.0; frozen scientific source/YAML values and fitted
artifacts are preserved in the separate replay checkout. A disclosed Git taxonomy newline-byte
difference is detailed in the replay provenance section below. Quality replay timings are not isolated latency evidence.

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

## Fresh reproduction after report corrections

Because report/reproduction code changed, the current d12dec1 wheel was installed in a new
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

Full scope34298quality records/64groups is retained. Only solver seed1730 and run/output labels
change; no models/thresholds/bounds/rates/configured populations are refitted or capped.
New1730 is compared to historical1730, then separately1729. Discrete/query/verdict identities
must match exactly; numeric tolerance1e-6abs+1e-5relative; cross-seed rate tolerance0.
These are newly committed Phase11 audit criteria, not retroactive historical tolerance rules.
Timings/execution identity are the only declared comparison exclusions; timings stay saved.
The complete comparison is **pending**. The initial execution segment stopped after7651saved
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

Phase11 remains **in progress** until the complete replay, independent final comparison/report
review and final progress/commit have finished. Missing physical evidence and roadmap
outputs remain explicit Partial/Not met states, not reasons to fabricate or add features.


## Updated documentation checkpoint

Independent review of the current audit pages confirms all216metric rows/24config identities/
12latency rows match saved evidence, all20local links resolve and all32exception rows match
traceability (20Partial/12Notmet). Strict `uv run mkdocs build --strict` completedexit0 in5.88s
with the Final audit navigation. Evidence `artifacts/phase11/docs-strict-independent-20261029.log/.exit`
and `final-docs-independent-review-20261029.md`. Later text-only checkpoint updates retain the
same links/nav; final closure review remains required after complete replay comparison.
