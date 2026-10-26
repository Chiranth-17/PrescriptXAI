# Automatically filled experiment table

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`.

Study `configs\experiments\phase7-study.yaml`, SHA256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`; saved summary SHA256 `e0de87c06b418be761142d259ccad8870b81232217b6d75303ee7a91957082fe`.

FAST/full/all-alert populations; k_max=3, assumed K=1, D_max v1=5 and v2=8. Values are percentages with95% whole-engine bootstrap CIs (2000 draws, seed1729); the engine count beside each row applies to every interval. Five solver seeds repeat fixed predictors, not independent engines. E3 is the maximum available proxy evidence. All outcomes, including failures, remain in all-query denominators. T2 returned has its own denominator in the source data. Config-set identifiers below resolve to every exact committed config path/runtime hash in ../docs/results_provenance.json.

| Model / protocol / population | Queries / seed observations / engines | Validity | T2 all | T2 returned | T3 | T4 | Joint | Config set |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| FD001 xgb v1 internal_heldout | 378/1890/15 | 55.82 [49.00, 62.50] | 51.32 [44.39, 57.53] | 51.32 [44.39, 57.53] | 100.00 [100.00, 100.00] | 94.44 [92.02, 96.74] | 42.06 [37.92, 46.15] | f24c40c738be |
| FD001 xgb v1 grouped_oof | 2378/11890/100 | 52.52 [49.30, 55.64] | 48.70 [44.59, 52.61] | 51.04 [47.46, 54.46] | 95.12 [92.01, 97.83] | 91.67 [89.45, 93.62] | 39.91 [36.73, 42.91] | a3483e883531 |
| FD001 xgb v1 official_test | 159/795/19 | 89.31 [83.57, 94.36] | 77.99 [70.42, 84.38] | 77.99 [70.42, 84.38] | 100.00 [100.00, 100.00] | 98.74 [96.57, 100.00] | 76.73 [68.75, 83.66] | 0ad569564fa6 |
| FD001 xgb v2 internal_heldout | 378/1890/15 | 55.82 [49.00, 62.50] | 98.94 [98.09, 99.74] | 98.94 [98.09, 99.74] | 100.00 [100.00, 100.00] | 94.44 [92.02, 96.74] | 52.91 [46.13, 59.61] | dace208feedc |
| FD001 xgb v2 grouped_oof | 2378/11890/100 | 52.52 [49.30, 55.64] | 98.07 [97.00, 98.92] | 98.98 [98.45, 99.42] | 95.12 [92.01, 97.83] | 91.67 [89.45, 93.62] | 50.42 [47.29, 53.48] | 432c17f956cc |
| FD001 xgb v2 official_test | 159/795/19 | 89.31 [83.57, 94.36] | 100.00 [100.00, 100.00] | 100.00 [100.00, 100.00] | 100.00 [100.00, 100.00] | 98.74 [96.57, 100.00] | 88.05 [82.03, 93.20] | bf715a849ba3 |
