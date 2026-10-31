# Appendix A. Complete measured results

Run phase7-20261020T102540Z. Measured source 63c2ed445fba16c73a2771e184f635abf76b4405. Study configs\experiments\phase7-study.yaml (SHA256 67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a). All following headline tables are FAST/full, assumed K=1, k_max=3; v1 D_max=5.0 and v2 D_max=8.0. Solver seeds [1729, 1730, 1731, 1732, 1733]; fixed predictor fits. Intervals are 95% whole-engine bootstrap intervals, 2000 requested draws, bootstrap seed1729. Engine counts apply to every interval in the row. E3 is the maximum available proxy evidence, not a universal attained level. Failed queries remain in all-query denominators.

## FD001 / XGB

Rates (%) and query / seed-observation / engine counts:

| Population | Q / observations / N | Validity | T2 all | T2 returned |
|---|---|---|---|---|
| v1/held-out | 378/1890/15 | 55.82 [49.00, 62.50] | 51.32 [44.39, 57.53] | 51.32 [44.39, 57.53] |
| v1/OOF | 2378/11890/100 | 52.52 [49.30, 55.64] | 48.70 [44.59, 52.61] | 51.04 [47.46, 54.46] |
| v1/official | 159/795/19 | 89.31 [83.57, 94.36] | 77.99 [70.42, 84.38] | 77.99 [70.42, 84.38] |
| v2/held-out | 378/1890/15 | 55.82 [49.00, 62.50] | 98.94 [98.09, 99.74] | 98.94 [98.09, 99.74] |
| v2/OOF | 2378/11890/100 | 52.52 [49.30, 55.64] | 98.07 [97.00, 98.92] | 98.98 [98.45, 99.42] |
| v2/official | 159/795/19 | 89.31 [83.57, 94.36] | 100.00 [100.00, 100.00] | 100.00 [100.00, 100.00] |

| Population | Tier 3 (%) | Tier 4 (%) | Joint (%) |
|---|---|---|---|
| v1/held-out (N=15) | 100.00 [100.00, 100.00] | 94.44 [92.02, 96.74] | 42.06 [37.92, 46.15] |
| v1/OOF (N=100) | 95.12 [92.01, 97.83] | 91.67 [89.45, 93.62] | 39.91 [36.73, 42.91] |
| v1/official (N=19) | 100.00 [100.00, 100.00] | 98.74 [96.57, 100.00] | 76.73 [68.75, 83.66] |
| v2/held-out (N=15) | 100.00 [100.00, 100.00] | 94.44 [92.02, 96.74] | 52.91 [46.13, 59.61] |
| v2/OOF (N=100) | 95.12 [92.01, 97.83] | 91.67 [89.45, 93.62] | 50.42 [47.29, 53.48] |
| v2/official (N=19) | 100.00 [100.00, 100.00] | 98.74 [96.57, 100.00] | 88.05 [82.03, 93.20] |

| Population | All / returned denominator | Mean support (all) | Mean risk drop (all) |
|---|---|---|---|
| v1/held-out (N=15) | 1890/1890 | 2.91 [2.89, 2.93] | 0.598156 [0.543098, 0.650297] |
| v1/OOF (N=100) | 11890/11245 | 2.76 [2.67, 2.85] | 0.563200 [0.535623, 0.589619] |
| v1/official (N=19) | 795/795 | 2.77 [2.64, 2.87] | 0.742415 [0.727848, 0.758047] |
| v2/held-out (N=15) | 1890/1890 | 2.87 [2.85, 2.90] | 0.599882 [0.544214, 0.651987] |
| v2/OOF (N=100) | 11890/11245 | 2.73 [2.64, 2.81] | 0.563563 [0.536285, 0.589941] |
| v2/official (N=19) | 795/795 | 2.73 [2.61, 2.84] | 0.741153 [0.727217, 0.755718] |

Distribution and coupling point diagnostics (no bootstrap CI saved for these summaries):

| Population | D_M p50 | D_M p95 | D_M p99 | Minimum coupling margin |
|---|---|---|---|---|
| v1/held-out | 4.991 | 7.188 | 8.177 | -5.691 |
| v1/OOF | 5.075 | 7.499 | 8.462 | -17.037 |
| v1/official | 4.698 | 6.239 | 7.112 | -1.234 |
| v2/held-out | 5.467 | 7.159 | 8.002 | -5.691 |
| v2/OOF | 5.486 | 7.499 | 8.429 | -17.037 |
| v2/official | 4.986 | 6.423 | 7.112 | -1.234 |

Config paths and all five effective runtime hashes for each row are retained in paper/evidence.json under the full group key. Registered profile configs: configs/experiments/phase7-FD001-xgb-v1.yaml and configs/experiments/phase7-FD001-xgb-v2.yaml. Returned denominators are explicit and may differ from all queries.

## FD001 / MLP

Rates (%) and query / seed-observation / engine counts:

| Population | Q / observations / N | Validity | T2 all | T2 returned |
|---|---|---|---|---|
| v1/held-out | 377/1885/15 | 54.38 [47.28, 60.79] | 46.95 [37.11, 55.58] | 46.95 [37.11, 55.58] |
| v1/OOF | 2472/12360/100 | 50.04 [47.08, 53.08] | 44.74 [40.45, 49.27] | 46.78 [42.80, 51.13] |
| v1/official | 170/850/19 | 91.18 [85.80, 96.20] | 78.82 [70.55, 85.20] | 78.82 [70.55, 85.20] |
| v2/held-out | 377/1885/15 | 54.38 [47.28, 60.79] | 99.47 [98.69, 100.00] | 99.47 [98.69, 100.00] |
| v2/OOF | 2472/12360/100 | 50.04 [47.08, 53.08] | 97.94 [96.82, 98.87] | 98.80 [98.24, 99.32] |
| v2/official | 170/850/19 | 91.18 [85.80, 96.20] | 99.41 [97.96, 100.00] | 99.41 [97.96, 100.00] |

| Population | Tier 3 (%) | Tier 4 (%) | Joint (%) |
|---|---|---|---|
| v1/held-out (N=15) | 100.00 [100.00, 100.00] | 94.43 [92.00, 96.71] | 38.20 [29.95, 45.17] |
| v1/OOF (N=100) | 95.31 [92.25, 97.92] | 92.03 [89.91, 93.87] | 35.28 [32.02, 38.62] |
| v1/official (N=19) | 100.00 [100.00, 100.00] | 99.41 [97.96, 100.00] | 77.65 [69.13, 84.47] |
| v2/held-out (N=15) | 100.00 [100.00, 100.00] | 94.43 [92.00, 96.71] | 51.19 [43.61, 58.30] |
| v2/OOF (N=100) | 95.31 [92.25, 97.92] | 92.03 [89.91, 93.87] | 47.98 [45.05, 51.03] |
| v2/official (N=19) | 100.00 [100.00, 100.00] | 99.41 [97.96, 100.00] | 90.59 [85.26, 95.56] |

| Population | All / returned denominator | Mean support (all) | Mean risk drop (all) |
|---|---|---|---|
| v1/held-out (N=15) | 1885/1885 | 2.85 [2.81, 2.90] | 0.583660 [0.526925, 0.633575] |
| v1/OOF (N=100) | 12360/11715 | 2.75 [2.66, 2.83] | 0.535385 [0.509900, 0.559897] |
| v1/official (N=19) | 850/850 | 2.68 [2.61, 2.76] | 0.729392 [0.715869, 0.741870] |
| v2/held-out (N=15) | 1885/1885 | 2.79 [2.73, 2.84] | 0.582285 [0.524869, 0.632315] |
| v2/OOF (N=100) | 12360/11715 | 2.68 [2.60, 2.76] | 0.535074 [0.509465, 0.559788] |
| v2/official (N=19) | 850/850 | 2.56 [2.48, 2.64] | 0.725954 [0.713012, 0.737363] |

Distribution and coupling point diagnostics (no bootstrap CI saved for these summaries):

| Population | D_M p50 | D_M p95 | D_M p99 | Minimum coupling margin |
|---|---|---|---|---|
| v1/held-out | 5.275 | 7.171 | 7.708 | -5.691 |
| v1/OOF | 5.303 | 7.503 | 8.462 | -17.037 |
| v1/official | 4.782 | 6.647 | 7.695 | -1.234 |
| v2/held-out | 5.600 | 7.175 | 7.708 | -5.691 |
| v2/OOF | 5.631 | 7.505 | 8.462 | -17.037 |
| v2/official | 5.264 | 6.891 | 7.695 | -1.234 |

Config paths and all five effective runtime hashes for each row are retained in paper/evidence.json under the full group key. Registered profile configs: configs/experiments/phase7-FD001-mlp-v1.yaml and configs/experiments/phase7-FD001-mlp-v2.yaml. Returned denominators are explicit and may differ from all queries.

## FD001 / LSTM

Rates (%) and query / seed-observation / engine counts:

| Population | Q / observations / N | Validity | T2 all | T2 returned |
|---|---|---|---|---|
| v1/held-out | 350/1750/15 | 0.00 [0.00, 0.00] | 21.71 [15.34, 28.15] | 21.71 [15.34, 28.15] |
| v1/OOF | 2456/12280/100 | 0.00 [0.00, 0.00] | 22.88 [19.29, 26.41] | 23.72 [20.29, 27.14] |
| v1/official | 138/690/16 | 0.00 [0.00, 0.00] | 31.16 [19.54, 42.47] | 31.16 [19.54, 42.47] |
| v2/held-out | 350/1750/15 | 0.00 [0.00, 0.00] | 99.43 [98.59, 100.00] | 99.43 [98.59, 100.00] |
| v2/OOF | 2456/12280/100 | 0.00 [0.00, 0.00] | 97.68 [96.55, 98.67] | 98.54 [97.90, 99.14] |
| v2/official | 138/690/16 | 0.00 [0.00, 0.00] | 97.83 [93.86, 100.00] | 97.83 [93.86, 100.00] |

| Population | Tier 3 (%) | Tier 4 (%) | Joint (%) |
|---|---|---|---|
| v1/held-out (N=15) | 100.00 [100.00, 100.00] | 94.86 [92.37, 96.97] | 0.00 [0.00, 0.00] |
| v1/OOF (N=100) | 95.28 [92.27, 97.90] | 91.94 [89.74, 93.82] | 0.00 [0.00, 0.00] |
| v1/official (N=16) | 100.00 [100.00, 100.00] | 98.55 [96.55, 100.00] | 0.00 [0.00, 0.00] |
| v2/held-out (N=15) | 100.00 [100.00, 100.00] | 94.86 [92.37, 96.97] | 0.00 [0.00, 0.00] |
| v2/OOF (N=100) | 95.28 [92.27, 97.90] | 91.94 [89.74, 93.82] | 0.00 [0.00, 0.00] |
| v2/official (N=16) | 100.00 [100.00, 100.00] | 98.55 [96.55, 100.00] | 0.00 [0.00, 0.00] |

| Population | All / returned denominator | Mean support (all) | Mean risk drop (all) |
|---|---|---|---|
| v1/held-out (N=15) | 1750/1750 | 3.00 [3.00, 3.00] | 0.042170 [0.031628, 0.052215] |
| v1/OOF (N=100) | 12280/11635 | 2.86 [2.77, 2.94] | 0.048939 [0.041609, 0.056551] |
| v1/official (N=16) | 690/690 | 3.00 [3.00, 3.00] | 0.111556 [0.091089, 0.133672] |
| v2/held-out (N=15) | 1750/1750 | 3.00 [3.00, 3.00] | 0.042170 [0.031628, 0.052215] |
| v2/OOF (N=100) | 12280/11635 | 2.86 [2.77, 2.94] | 0.048939 [0.041609, 0.056551] |
| v2/official (N=16) | 690/690 | 3.00 [3.00, 3.00] | 0.111556 [0.091089, 0.133672] |

Distribution and coupling point diagnostics (no bootstrap CI saved for these summaries):

| Population | D_M p50 | D_M p95 | D_M p99 | Minimum coupling margin |
|---|---|---|---|---|
| v1/held-out | 5.725 | 7.217 | 7.699 | -5.691 |
| v1/OOF | 5.729 | 7.562 | 8.476 | -17.037 |
| v1/official | 5.594 | 7.441 | 8.255 | -1.234 |
| v2/held-out | 5.725 | 7.217 | 7.699 | -5.691 |
| v2/OOF | 5.729 | 7.562 | 8.476 | -17.037 |
| v2/official | 5.594 | 7.441 | 8.255 | -1.234 |

Config paths and all five effective runtime hashes for each row are retained in paper/evidence.json under the full group key. Registered profile configs: configs/experiments/phase7-FD001-lstm-v1.yaml and configs/experiments/phase7-FD001-lstm-v2.yaml. Returned denominators are explicit and may differ from all queries.

## FD002 / XGB

Rates (%) and query / seed-observation / engine counts:

| Population | Q / observations / N | Validity | T2 all | T2 returned |
|---|---|---|---|---|
| v1/held-out | 911/4555/39 | 100.00 [100.00, 100.00] | 3.73 [2.72, 4.83] | 3.73 [2.72, 4.83] |
| v1/OOF | 5591/27955/260 | 100.00 [100.00, 100.00] | 3.13 [2.65, 3.64] | 3.13 [2.65, 3.64] |
| v1/official | 678/3390/65 | 100.00 [100.00, 100.00] | 4.57 [3.06, 6.30] | 4.57 [3.06, 6.30] |
| v2/held-out | 911/4555/39 | 100.00 [100.00, 100.00] | 10.87 [8.57, 13.21] | 10.87 [8.57, 13.21] |
| v2/OOF | 5591/27955/260 | 100.00 [100.00, 100.00] | 10.96 [10.09, 11.78] | 10.96 [10.09, 11.78] |
| v2/official | 678/3390/65 | 100.00 [100.00, 100.00] | 13.86 [11.25, 16.45] | 13.86 [11.25, 16.45] |

| Population | Tier 3 (%) | Tier 4 (%) | Joint (%) |
|---|---|---|---|
| v1/held-out (N=39) | 100.00 [100.00, 100.00] | 28.65 [20.09, 37.84] | 0.33 [0.00, 0.73] |
| v1/OOF (N=260) | 100.00 [100.00, 100.00] | 31.30 [28.21, 34.61] | 0.07 [0.02, 0.15] |
| v1/official (N=65) | 100.00 [100.00, 100.00] | 33.33 [25.84, 41.04] | 0.44 [0.00, 1.02] |
| v2/held-out (N=39) | 100.00 [100.00, 100.00] | 28.65 [20.09, 37.84] | 0.55 [0.11, 1.07] |
| v2/OOF (N=260) | 100.00 [100.00, 100.00] | 31.30 [28.21, 34.61] | 0.66 [0.45, 0.90] |
| v2/official (N=65) | 100.00 [100.00, 100.00] | 33.33 [25.84, 41.04] | 1.18 [0.48, 1.96] |

| Population | All / returned denominator | Mean support (all) | Mean risk drop (all) |
|---|---|---|---|
| v1/held-out (N=39) | 4555/4555 | 1.62 [1.57, 1.67] | 0.838121 [0.832636, 0.843150] |
| v1/OOF (N=260) | 27955/27955 | 1.59 [1.56, 1.61] | 0.835903 [0.833143, 0.838834] |
| v1/official (N=65) | 3390/3390 | 1.51 [1.46, 1.56] | 0.821258 [0.814287, 0.827573] |
| v2/held-out (N=39) | 4555/4555 | 1.70 [1.65, 1.75] | 0.839365 [0.834412, 0.843931] |
| v2/OOF (N=260) | 27955/27955 | 1.64 [1.62, 1.66] | 0.836746 [0.833820, 0.839684] |
| v2/official (N=65) | 3390/3390 | 1.60 [1.55, 1.66] | 0.820838 [0.813636, 0.827506] |

Distribution and coupling point diagnostics (no bootstrap CI saved for these summaries):

| Population | D_M p50 | D_M p95 | D_M p99 | Minimum coupling margin |
|---|---|---|---|---|
| v1/held-out | 85.856 | 239.096 | 311.854 | -12.473 |
| v1/OOF | 78.179 | 243.927 | 613.082 | -12.156 |
| v1/official | 64.186 | 237.903 | 311.968 | -6.003 |
| v2/held-out | 85.139 | 240.789 | 311.854 | -12.473 |
| v2/OOF | 74.974 | 244.251 | 611.599 | -12.156 |
| v2/official | 62.475 | 237.312 | 310.509 | -6.003 |

Config paths and all five effective runtime hashes for each row are retained in paper/evidence.json under the full group key. Registered profile configs: configs/experiments/phase7-FD002-xgb-v1.yaml and configs/experiments/phase7-FD002-xgb-v2.yaml. Returned denominators are explicit and may differ from all queries.

# Appendix B. Design targets and measured gaps

The following gaps are signed shortfalls: positive means the target is missed; negative means the estimate is beyond the target in the favorable direction. A point-estimate pass does not imply its entire CI passes. Rate gaps are percentage points. All intervals and engine counts are in Appendix A. Simulated trajectory health is unmeasured.

| Population | Validity 95% | T2 all 90% | T2 returned 90% | Support <=3 | Risk drop >=0.60 |
|---|---|---|---|---|---|
| FD001/xgb/v1/held-out | +39.18 miss | +38.68 miss | +38.68 miss | -0.09 pass | +0.001844 miss |
| FD001/xgb/v1/OOF | +42.48 miss | +41.30 miss | +38.96 miss | -0.24 pass | +0.036800 miss |
| FD001/xgb/v1/official | +5.69 miss | +12.01 miss | +12.01 miss | -0.23 pass | -0.142415 pass |
| FD001/xgb/v2/held-out | +39.18 miss | -8.94 pass | -8.94 pass | -0.13 pass | +0.000118 miss |
| FD001/xgb/v2/OOF | +42.48 miss | -8.07 pass | -8.98 pass | -0.27 pass | +0.036437 miss |
| FD001/xgb/v2/official | +5.69 miss | -10.00 pass | -10.00 pass | -0.27 pass | -0.141153 pass |
| FD001/mlp/v1/held-out | +40.62 miss | +43.05 miss | +43.05 miss | -0.15 pass | +0.016340 miss |
| FD001/mlp/v1/OOF | +44.96 miss | +45.26 miss | +43.22 miss | -0.25 pass | +0.064615 miss |
| FD001/mlp/v1/official | +3.82 miss | +11.18 miss | +11.18 miss | -0.32 pass | -0.129392 pass |
| FD001/mlp/v2/held-out | +40.62 miss | -9.47 pass | -9.47 pass | -0.21 pass | +0.017715 miss |
| FD001/mlp/v2/OOF | +44.96 miss | -7.94 pass | -8.80 pass | -0.32 pass | +0.064926 miss |
| FD001/mlp/v2/official | +3.82 miss | -9.41 pass | -9.41 pass | -0.44 pass | -0.125954 pass |
| FD001/lstm/v1/held-out | +95.00 miss | +68.29 miss | +68.29 miss | +0.00 pass | +0.557830 miss |
| FD001/lstm/v1/OOF | +95.00 miss | +67.12 miss | +66.28 miss | -0.14 pass | +0.551061 miss |
| FD001/lstm/v1/official | +95.00 miss | +58.84 miss | +58.84 miss | +0.00 pass | +0.488444 miss |
| FD001/lstm/v2/held-out | +95.00 miss | -9.43 pass | -9.43 pass | +0.00 pass | +0.557830 miss |
| FD001/lstm/v2/OOF | +95.00 miss | -7.68 pass | -8.54 pass | -0.14 pass | +0.551061 miss |
| FD001/lstm/v2/official | +95.00 miss | -7.83 pass | -7.83 pass | +0.00 pass | +0.488444 miss |
| FD002/xgb/v1/held-out | -5.00 pass | +86.27 miss | +86.27 miss | -1.38 pass | -0.238121 pass |
| FD002/xgb/v1/OOF | -5.00 pass | +86.87 miss | +86.87 miss | -1.41 pass | -0.235903 pass |
| FD002/xgb/v1/official | -5.00 pass | +85.43 miss | +85.43 miss | -1.49 pass | -0.221258 pass |
| FD002/xgb/v2/held-out | -5.00 pass | +79.13 miss | +79.13 miss | -1.30 pass | -0.239365 pass |
| FD002/xgb/v2/OOF | -5.00 pass | +79.04 miss | +79.04 miss | -1.36 pass | -0.236746 pass |
| FD002/xgb/v2/official | -5.00 pass | +76.14 miss | +76.14 miss | -1.40 pass | -0.220838 pass |

## Historical warm serial backend latency

Same run/source as Appendix A. Exact latency labels: {"D_max": 5.0, "D_max_version": "v1", "K": 1, "config_hash": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271", "git_hash": "63c2ed445fba16c73a2771e184f635abf76b4405", "k_max": 3, "population": "development_all_alerts_repeated_fixed_order", "protocol": "v1"}. Startup, network, attribution and browser paint are excluded. Faster than a band's lower endpoint passes.

| Mode / stage | Calls / N | p95 ms [engine CI] | Upper budget | Signed gap ms | Pass |
|---|---|---|---|---|---|
| FAST/ingestion | 1000/16 | 0.18 [0.17, 0.18] | 10 | -9.82 | True |
| FAST/inference | 1000/16 | 3.05 [3.02, 3.12] | 15 | -11.95 | True |
| FAST/optimization | 1000/16 | 2339.07 [2256.87, 2403.27] | 1800 | 539.07 | False |
| FAST/validation | 1000/16 | 5.49 [5.21, 5.68] | 100 | -94.51 | True |
| FAST/pipeline | 1000/16 | 2348.23 [2265.85, 2414.08] | 2200 | 148.23 | False |
| THOROUGH/ingestion | 1000/16 | 0.18 [0.18, 0.20] | 10 | -9.82 | True |
| THOROUGH/inference | 1000/16 | 3.11 [3.00, 3.21] | 15 | -11.89 | True |
| THOROUGH/optimization | 1000/16 | 2080.23 [2029.10, 2171.67] | 1800 | 280.23 | False |
| THOROUGH/validation | 1000/16 | 5.77 [5.57, 6.10] | 100 | -94.23 | True |
| THOROUGH/pipeline | 1000/16 | 2089.85 [2039.34, 2181.37] | 2200 | -110.15 | True |

UI <250ms and full UI/network total <=2200ms remain unmeasured at browser-interaction scope. The separately saved server-construction timing must not be relabeled as browser paint. Historical latency is not a measurement of the post-audit implementation.

# Appendix C. Predictor, calibration and coupling evidence

Predictive and calibration entries below are saved point diagnostics without engine CIs. No interval is invented.

| Profile | Rows | AUROC | AUPRC | Brier before -> after | ECE before -> after |
|---|---|---|---|---|---|
| FD001/xgb | 3281 | 0.9907 | 0.9554 | 0.03527 -> 0.02607 | 0.03636 -> 0.00986 |
| FD001/mlp | 3281 | 0.9913 | 0.9572 | 0.02509 -> 0.02527 | 0.00723 -> 0.00748 |
| FD001/lstm | 3281 | 0.9930 | 0.9654 | 0.02251 -> 0.02204 | 0.01364 -> 0.01070 |
| FD002/xgb | 8258 | 0.9858 | 0.9327 | 0.04929 -> 0.03209 | 0.06503 -> 0.01050 |

Calibration is not uniformly better. Training provenance and fit/calibration/test engine identities:

## FD001/xgb/base

Training source fa5adcbe914f95e6efe25f4edc8f8f50a234881a; training config SHA256 8020233c4fbafc4d6124aa9f128d022e9b04ea81b6f526ce969e5b17e1888238; actual training seed 1729. Engine counts by split: {"test_holdout": 15, "train": 69, "validation": 16}. Calibration-fit engines: 16. All engine identities, overlap checks, metadata and committed experiment config paths are copied unchanged to paper/evidence.json.

Surrogate on observed held-out states: {"agreement_at_tau_danger": 0.9896373056994818, "agreement_at_tau_safe": 0.9850655288021944, "mae": 0.013378545890953901, "rank_correlation": 0.9674176955074236, "sample_count": 3281, "tau_danger": 0.8, "tau_safe": 0.2}. These states differ from optimized counterfactual candidates.

v1/internal_heldout_all_alerts, 15 engines: candidate surrogate MAE 0.15 [0.13, 0.16]; false-safe share over all queries (%) 1.06 [0.00, 2.45]. v1/grouped_oof_all_alerts, 100 engines: candidate surrogate MAE 0.13 [0.12, 0.14]; false-safe share over all queries (%) 0.71 [0.36, 1.13]. v1/official_test_all_alerts, 19 engines: candidate surrogate MAE 0.15 [0.14, 0.17]; false-safe share over all queries (%) 3.14 [1.12, 5.48].

Learned coupling residual calibration: 2649 rows / 16 engines, reference distribution healthy_to_moderate, RUL > 30, sigma multiplier 3.0. These validation engines are disjoint from coupling training but also determine residual thresholds; they are not untouched coupling test units.

| Sensor | R2 | Residual mean | Residual std | Threshold | Share beyond |
|---|---|---|---|---|---|
| sensor_11 | 0.695448 | -0.00283335 | 0.114326 | 0.342978 | 0.00264251 |
| sensor_13 | 0.699543 | -0.00110905 | 0.0352023 | 0.105607 | 0.00264251 |
| sensor_14 | 0.895774 | 0.247751 | 4.72452 | 14.1736 | 0.00377501 |
| sensor_2 | 0.432981 | -0.00989393 | 0.311562 | 0.934687 | 0.00339751 |
| sensor_3 | 0.35313 | 0.0483685 | 4.11105 | 12.3332 | 0.00302001 |
| sensor_4 | 0.608206 | -0.199181 | 4.44748 | 13.3424 | 0.00302001 |
| sensor_6 | 0.0319621 | -3.9666e-05 | 0.00165273 | 0.00495819 | 0.0290676 |
| sensor_7 | 0.597431 | 0.00419682 | 0.458173 | 1.37452 | 0.00151 |

## FD001/mlp/base

Training source 473672b1b8103fb4468184145aa3bc2d82f63e8e; training config SHA256 d75bd63bbd3fbfbd89749f18d4a3a74738a08b395f58a4a84b2f90f0fe678fe0; actual training seed 1729. Engine counts by split: {"test_holdout": 15, "train": 69, "validation": 16}. Calibration-fit engines: 16. All engine identities, overlap checks, metadata and committed experiment config paths are copied unchanged to paper/evidence.json.

No distillation surrogate is used for this differentiable predictor; surrogate fidelity is not applicable.

v1/internal_heldout_all_alerts, 15 engines: candidate surrogate MAE 0.00 [0.00, 0.00]; false-safe share over all queries (%) 0.00 [0.00, 0.00]. v1/grouped_oof_all_alerts, 100 engines: candidate surrogate MAE 0.00 [0.00, 0.00]; false-safe share over all queries (%) 0.00 [0.00, 0.00]. v1/official_test_all_alerts, 19 engines: candidate surrogate MAE 0.00 [0.00, 0.00]; false-safe share over all queries (%) 0.00 [0.00, 0.00].

Learned coupling residual calibration: 2649 rows / 16 engines, reference distribution healthy_to_moderate, RUL > 30, sigma multiplier 3.0. These validation engines are disjoint from coupling training but also determine residual thresholds; they are not untouched coupling test units.

| Sensor | R2 | Residual mean | Residual std | Threshold | Share beyond |
|---|---|---|---|---|---|
| sensor_11 | 0.695448 | -0.00283335 | 0.114326 | 0.342978 | 0.00264251 |
| sensor_13 | 0.699543 | -0.00110905 | 0.0352023 | 0.105607 | 0.00264251 |
| sensor_14 | 0.895774 | 0.247751 | 4.72452 | 14.1736 | 0.00377501 |
| sensor_2 | 0.432981 | -0.00989393 | 0.311562 | 0.934687 | 0.00339751 |
| sensor_3 | 0.35313 | 0.0483685 | 4.11105 | 12.3332 | 0.00302001 |
| sensor_4 | 0.608206 | -0.199181 | 4.44748 | 13.3424 | 0.00302001 |
| sensor_6 | 0.0319621 | -3.9666e-05 | 0.00165273 | 0.00495819 | 0.0290676 |
| sensor_7 | 0.597431 | 0.00419682 | 0.458173 | 1.37452 | 0.00151 |

## FD001/lstm/base

Training source 473672b1b8103fb4468184145aa3bc2d82f63e8e; training config SHA256 05a14f264d6a411d8bb030bad5404bebb5193d91419b4dd00afa86d7e38c3a80; actual training seed 1729. Engine counts by split: {"test_holdout": 15, "train": 69, "validation": 16}. Calibration-fit engines: 16. All engine identities, overlap checks, metadata and committed experiment config paths are copied unchanged to paper/evidence.json.

No distillation surrogate is used for this differentiable predictor; surrogate fidelity is not applicable.

v1/internal_heldout_all_alerts, 15 engines: candidate surrogate MAE 0.00 [0.00, 0.00]; false-safe share over all queries (%) 0.00 [0.00, 0.00]. v1/grouped_oof_all_alerts, 100 engines: candidate surrogate MAE 0.00 [0.00, 0.00]; false-safe share over all queries (%) 0.00 [0.00, 0.00]. v1/official_test_all_alerts, 16 engines: candidate surrogate MAE 0.00 [0.00, 0.00]; false-safe share over all queries (%) 0.00 [0.00, 0.00].

Learned coupling residual calibration: 2649 rows / 16 engines, reference distribution healthy_to_moderate, RUL > 30, sigma multiplier 3.0. These validation engines are disjoint from coupling training but also determine residual thresholds; they are not untouched coupling test units.

| Sensor | R2 | Residual mean | Residual std | Threshold | Share beyond |
|---|---|---|---|---|---|
| sensor_11 | 0.695448 | -0.00283335 | 0.114326 | 0.342978 | 0.00264251 |
| sensor_13 | 0.699543 | -0.00110905 | 0.0352023 | 0.105607 | 0.00264251 |
| sensor_14 | 0.895774 | 0.247751 | 4.72452 | 14.1736 | 0.00377501 |
| sensor_2 | 0.432981 | -0.00989393 | 0.311562 | 0.934687 | 0.00339751 |
| sensor_3 | 0.35313 | 0.0483685 | 4.11105 | 12.3332 | 0.00302001 |
| sensor_4 | 0.608206 | -0.199181 | 4.44748 | 13.3424 | 0.00302001 |
| sensor_6 | 0.0319621 | -3.9666e-05 | 0.00165273 | 0.00495819 | 0.0290676 |
| sensor_7 | 0.597431 | 0.00419682 | 0.458173 | 1.37452 | 0.00151 |

## FD002/xgb/base

Training source 0c0b6e1d37aafaed66cc61d9ac23f768c0529442; training config SHA256 6f0bc56488a4635426b2a047ac1f791a54c696c00178aab8edf5d4c6bcc0eefa; actual training seed 1729. Engine counts by split: {"test_holdout": 39, "train": 181, "validation": 40}. Calibration-fit engines: 40. All engine identities, overlap checks, metadata and committed experiment config paths are copied unchanged to paper/evidence.json.

Surrogate on observed held-out states: {"agreement_at_tau_danger": 0.9778396706224267, "agreement_at_tau_safe": 0.9796560910632114, "mae": 0.023030330923476117, "rank_correlation": 0.9420333250312036, "sample_count": 8258, "tau_danger": 0.8, "tau_safe": 0.2}. These states differ from optimized counterfactual candidates.

v1/internal_heldout_all_alerts, 39 engines: candidate surrogate MAE 0.15 [0.14, 0.17]; false-safe share over all queries (%) 0.00 [0.00, 0.00]. v1/grouped_oof_all_alerts, 260 engines: candidate surrogate MAE 0.20 [0.19, 0.21]; false-safe share over all queries (%) 0.00 [0.00, 0.00]. v1/official_test_all_alerts, 65 engines: candidate surrogate MAE 0.12 [0.11, 0.14]; false-safe share over all queries (%) 0.00 [0.00, 0.00].

Learned coupling residual calibration: 6879 rows / 40 engines, reference distribution healthy_to_moderate, RUL > 30, sigma multiplier 3.0. These validation engines are disjoint from coupling training but also determine residual thresholds; they are not untouched coupling test units.

| Sensor | R2 | Residual mean | Residual std | Threshold | Share beyond |
|---|---|---|---|---|---|
| sensor_1 | 0.999997 | -0.000293231 | 0.0457972 | 0.137392 | 0.0087222 |
| sensor_10 | 0.999807 | 3.29791e-06 | 0.00176754 | 0.00530263 | 0.0287833 |
| sensor_11 | 0.998324 | 0.00418622 | 0.131597 | 0.394791 | 0.00218055 |
| sensor_13 | 0.999999 | 4.06424e-05 | 0.118248 | 0.354745 | 0.00915831 |
| sensor_14 | 0.99678 | -0.112809 | 4.75272 | 14.2582 | 0.00334351 |
| sensor_16 | 0.934065 | 6.45216e-06 | 0.00119151 | 0.00357454 | 0.0162814 |
| sensor_18 | 0.999999 | -0.000957428 | 0.111772 | 0.335316 | 0.00843146 |
| sensor_19 | 1 | 1.12053e-06 | 3.175e-05 | 9.52499e-05 | 0.0101759 |
| sensor_2 | 0.99992 | 0.00879959 | 0.332113 | 0.996339 | 0.00203518 |
| sensor_3 | 0.998374 | 0.147795 | 4.25425 | 12.7628 | 0.00232592 |
| sensor_4 | 0.998375 | 0.177272 | 4.76815 | 14.3045 | 0.00348888 |
| sensor_5 | 0.999993 | 0.0001223 | 0.00972713 | 0.0291814 | 0.00348888 |
| sensor_6 | 0.999992 | 0.000214893 | 0.0153615 | 0.0460844 | 0.00319814 |
| sensor_7 | 0.999988 | 0.00136401 | 0.510288 | 1.53086 | 0.00261666 |

# Appendix D. Diagnostics, reproducibility and provenance

## Paired K sensitivity beside the K=1 headline assumption

This is the preregistered paired FD001/XGB/v1 diagnostic population, not the all-alert headline cohort. K changes assumed cumulative rate allowance only. It is not a dynamic trajectory or a physical response measurement. Each row retains its exact config path/hash and effective labels in paper/evidence.json, diagnostic_groups.

| K | Observations / engines | Validity (%) | T2 all (%) | Joint (%) |
|---|---|---|---|---|
| 1 | 12/10 | 33.33 [8.33, 60.00] | 50.00 [23.08, 80.00] | 33.33 [8.33, 60.00] |
| 2 | 12/10 | 91.67 [72.73, 100.00] | 58.33 [36.36, 81.82] | 58.33 [36.36, 81.82] |
| 3 | 12/10 | 91.67 [72.73, 100.00] | 58.33 [30.00, 84.62] | 58.33 [30.00, 84.62] |
| 5 | 12/10 | 100.00 [100.00, 100.00] | 66.67 [40.00, 91.67] | 66.67 [40.00, 91.67] |
| 10 | 12/10 | 100.00 [100.00, 100.00] | 66.67 [40.00, 91.67] | 66.67 [40.00, 91.67] |

## Paired constraint ladder and baseline comparisons

| Variant | Observations / engines | Validity (%) | T2 all (%) | Joint (%) |
|---|---|---|---|---|
| L0 all free | 12/10 | 75.00 [56.25, 91.14] | 8.33 [0.00, 23.08] | 8.33 [0.00, 23.08] |
| L1 immutable | 12/10 | 75.00 [56.25, 91.14] | 8.33 [0.00, 23.08] | 8.33 [0.00, 23.08] |
| L2 bounds | 12/10 | 66.67 [45.45, 90.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| L3 rates | 12/10 | 50.00 [23.08, 80.00] | 8.33 [0.00, 27.27] | 8.33 [0.00, 27.27] |
| L4 propagation | 12/10 | 50.00 [23.08, 80.00] | 33.33 [9.09, 60.00] | 25.00 [6.67, 50.00] |
| L5 sparsity | 12/10 | 33.33 [8.33, 60.00] | 33.33 [9.09, 60.00] | 16.67 [0.00, 36.36] |
| L6 mahalanobis | 12/10 | 33.33 [8.33, 60.00] | 50.00 [23.08, 80.00] | 33.33 [8.33, 60.00] |
| L7 coupling | 12/10 | 33.33 [8.33, 60.00] | 50.00 [23.08, 80.00] | 33.33 [8.33, 60.00] |
| unconstrained | 12/10 | 0.00 [0.00, 0.00] | 50.00 [25.00, 75.00] | 0.00 [0.00, 0.00] |
| bounded without plausibility | 12/10 | 33.33 [8.33, 60.00] | 33.33 [9.09, 60.00] | 16.67 [0.00, 36.36] |
| dice | 12/10 | 100.00 [100.00, 100.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| full | 12/10 | 33.33 [8.33, 60.00] | 50.00 [23.08, 80.00] | 33.33 [8.33, 60.00] |

Ladder variants progressively activate constraints; baselines use the saved configured implementations. Their permitted spaces differ. This is not evidence that every DiCE configuration is unconstrained or that a finite baseline failed to find a globally feasible action.

## Headline acceptance funnel

| Sequential stage | Count | Engines | All-query share (%) [engine CI] |
|---|---|---|---|
| alerts | 1890 | 15 | 100.00 [100.00, 100.00] |
| nonzero feasible counterfactual returned | 1890 | 15 | 100.00 [100.00, 100.00] |
| tier1 | 1055 | 15 | 55.82 [49.00, 62.50] |
| tier2 | 800 | 15 | 42.33 [38.05, 46.52] |
| tier3 | 800 | 15 | 42.33 [38.05, 46.52] |
| tier4 | 795 | 15 | 42.06 [37.92, 46.15] |
| joint | 795 | 15 | 42.06 [37.92, 46.15] |

Funnel stages are cumulative acceptance steps, whereas Appendix A tier pass rates are independent checks. Do not substitute a cumulative funnel numerator for an independent tier metric.

## LSTM scorable-history accounting

| Cohort | Input rows | Insufficient history | Scorable | Selected alerts |
|---|---|---|---|---|
| base/internal_heldout | 3281 | 135 | 3146 | 350 |
| base/official_test | 13096 | 900 | 12196 | 138 |
| fold-1/grouped_oof | 4012 | 180 | 3832 | 546 |
| fold-2/grouped_oof | 4106 | 180 | 3926 | 403 |
| fold-3/grouped_oof | 4325 | 180 | 4145 | 533 |
| fold-4/grouped_oof | 4027 | 180 | 3847 | 456 |
| fold-5/grouped_oof | 4161 | 180 | 3981 | 518 |

Early rows without the required real-history prefix are excluded before alert scoring, with counts disclosed above. This makes LSTM populations differ from snapshot models. Queries that enter the registered scorable-alert cohort remain in its result denominators.

The full paired constraint ladder, K curves, ablations, baselines and first-alert strata remain in docs/phase7_changes.md and all 272 saved summary groups. They are separate diagnostic or sensitivity populations, not replacements for the 24 headline rows. Exact selected-group funnel counts, failure reasons and D_M distributions are preserved in paper/evidence.json.

Reference classifications remain unresolved finite searches, not certified infeasibility:

| Profile / protocol | Failed cases | Engines | Unresolved (%) [engine CI] |
|---|---|---|---|
| FD002/xgb/v2 | 12 | 10 | 100.0 [100.0, 100.0] |
| FD002/xgb/v1 | 12 | 10 | 100.0 [100.0, 100.0] |
| FD001/xgb/v1 | 8 | 7 | 100.0 [100.0, 100.0] |
| FD001/xgb/v2 | 8 | 7 | 100.0 [100.0, 100.0] |

The frozen second-seed replay is documented in docs/final_verification.md under run phase11-seed1730-20261028T030707Z and source63c2ed445fba16c73a2771e184f635abf76b4405. It completed 34,298 records / 64 groups. Comparisons against historical 1730 and 1729 each found zero mismatches at absolute tolerance 1e-6 / relative tolerance 1e-5, with discrete verdicts exact. All 576 whole-engine CI objects passed independent checks. This reused-engine replay is reproducibility evidence, not an independent generalization sample. Execution segments and host interruptions are disclosed in that verification record.
