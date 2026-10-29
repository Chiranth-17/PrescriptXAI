# Complete measured targets and gaps

This is a saved-result audit appendix, not a new experiment or a pooled success claim.
Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; study `configs\experiments\phase7-study.yaml`,
SHA256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`; summary SHA256 `e0de87c06b418be761142d259ccad8870b81232217b6d75303ee7a91957082fe`.
All24 headline FAST/full model/protocol/population strata appear below. Solver seeds
`[1729, 1730, 1731, 1732, 1733]` repeat frozen predictors and are not independent engines.
Intervals are 95% whole-engine bootstrap intervals,
2000 requested draws with seed1729. Zero conditional-denominator draws
are counted in the saved summary. Failures remain in all-query denominators; conditional T2
and success-only support denominators are shown separately.

Each group states run/config/protocol/population/K/k/D_max labels; config-set identity resolves
all exact committed experiment paths and runtime hashes in [results_provenance.json](results_provenance.json).
The complete original saved report additionally retains full sensitivity/diagnostic andTHOROUGH strata.
Maximum available evidence is E3 under assumed proxy mappings/bounds/rates; each query's actual
level is retained in the raw records. Passing model validity alone establishes no physical safety.
No static result establishes a causal failure reduction, lifespan benefit or RUL extension.

Positive shortfall means a miss. No synopsis target is attached to Tier3, Tier4 or joint success.
Rate/risk-drop entries are fractions, not percentages. Support counts directly changed proxies;
propagated dependent changes are separate. The synopsis requires mean support at most3;
all-query and conditional successful support are both disclosed.


## FD001/lstm/v1/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `55573371be194b1a5f0f4e0982095b78283e1b2cc56eb846dff77fc114a77279`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-lstm-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['none']`.
Unique queries 2456; seed observations 12280; engines 100.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.000000000 [0.000000000, 0.000000000] | 100 | 12280 / 12280.0 | >=0.95 | 0.950000000 | not met |
| Tier2, all queries | 0.228827362 [0.192894166, 0.264114279] | 100 | 12280 / 12280.0 | >=0.9 | 0.671172638 | not met |
| Tier2, returned candidates | 0.237215299 [0.202864041, 0.271370341] | 100 | 12280 / 11635.0 | >=0.9 | 0.662784701 | not met |
| Tier3 | 0.952768730 [0.922692929, 0.979037478] | 100 | 12280 / 12280.0 | none | — | no target |
| Tier4 | 0.919381107 [0.897406082, 0.938243068] | 100 | 12280 / 12280.0 | none | — | no target |
| Joint success | 0.000000000 [0.000000000, 0.000000000] | 100 | 12280 / 12280.0 | none | — | no target |
| Mean support, all queries | 2.864006515 [2.772577502, 2.943092541] | 100 | 12280 / 12280.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | unmeasured [unmeasured, unmeasured] | 100 | 12280 / 0.0 | none | — | unmeasured |
| Mean model-risk drop | 0.048938918 [0.041609204, 0.056550908] | 100 | 12280 / 12280.0 | >=0.6 | 0.551061082 | not met |

## FD001/lstm/v1/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `4438e5823357266365c23eb64c22361763e33f35938691795d8004789f8f13d5`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-lstm-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['none']`.
Unique queries 350; seed observations 1750; engines 15.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.000000000 [0.000000000, 0.000000000] | 15 | 1750 / 1750.0 | >=0.95 | 0.950000000 | not met |
| Tier2, all queries | 0.217142857 [0.153417166, 0.281526515] | 15 | 1750 / 1750.0 | >=0.9 | 0.682857143 | not met |
| Tier2, returned candidates | 0.217142857 [0.153417166, 0.281526515] | 15 | 1750 / 1750.0 | >=0.9 | 0.682857143 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 15 | 1750 / 1750.0 | none | — | no target |
| Tier4 | 0.948571429 [0.923724278, 0.969703179] | 15 | 1750 / 1750.0 | none | — | no target |
| Joint success | 0.000000000 [0.000000000, 0.000000000] | 15 | 1750 / 1750.0 | none | — | no target |
| Mean support, all queries | 3.000000000 [3.000000000, 3.000000000] | 15 | 1750 / 1750.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | unmeasured [unmeasured, unmeasured] | 15 | 1750 / 0.0 | none | — | unmeasured |
| Mean model-risk drop | 0.042170111 [0.031628076, 0.052214710] | 15 | 1750 / 1750.0 | >=0.6 | 0.557829889 | not met |

## FD001/lstm/v1/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `5b74978c24b0df487b5ccf5668e533269cd79bcf018b9bcdad2dea9efc9e32cc`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-lstm-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['official_test_all_alerts']`; evidence levels observed `['none']`.
Unique queries 138; seed observations 690; engines 16.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.000000000 [0.000000000, 0.000000000] | 16 | 690 / 690.0 | >=0.95 | 0.950000000 | not met |
| Tier2, all queries | 0.311594203 [0.195400054, 0.424684660] | 16 | 690 / 690.0 | >=0.9 | 0.588405797 | not met |
| Tier2, returned candidates | 0.311594203 [0.195400054, 0.424684660] | 16 | 690 / 690.0 | >=0.9 | 0.588405797 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 16 | 690 / 690.0 | none | — | no target |
| Tier4 | 0.985507246 [0.965517241, 1.000000000] | 16 | 690 / 690.0 | none | — | no target |
| Joint success | 0.000000000 [0.000000000, 0.000000000] | 16 | 690 / 690.0 | none | — | no target |
| Mean support, all queries | 3.000000000 [3.000000000, 3.000000000] | 16 | 690 / 690.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | unmeasured [unmeasured, unmeasured] | 16 | 690 / 0.0 | none | — | unmeasured |
| Mean model-risk drop | 0.111555518 [0.091089050, 0.133671791] | 16 | 690 / 690.0 | >=0.6 | 0.488444482 | not met |

## FD001/lstm/v2/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `c2b3258f3cea1210101eab414c75f7a889b247152f7e7f740c444109bb1cfe0e`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-lstm-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['none']`.
Unique queries 2456; seed observations 12280; engines 100.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.000000000 [0.000000000, 0.000000000] | 100 | 12280 / 12280.0 | >=0.95 | 0.950000000 | not met |
| Tier2, all queries | 0.976791531 [0.965457542, 0.986684359] | 100 | 12280 / 12280.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.985388913 [0.979017336, 0.991353677] | 100 | 12280 / 11635.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 0.952768730 [0.922692929, 0.979037478] | 100 | 12280 / 12280.0 | none | — | no target |
| Tier4 | 0.919381107 [0.897406082, 0.938243068] | 100 | 12280 / 12280.0 | none | — | no target |
| Joint success | 0.000000000 [0.000000000, 0.000000000] | 100 | 12280 / 12280.0 | none | — | no target |
| Mean support, all queries | 2.864006515 [2.772577502, 2.943092541] | 100 | 12280 / 12280.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | unmeasured [unmeasured, unmeasured] | 100 | 12280 / 0.0 | none | — | unmeasured |
| Mean model-risk drop | 0.048938918 [0.041609204, 0.056550908] | 100 | 12280 / 12280.0 | >=0.6 | 0.551061082 | not met |

## FD001/lstm/v2/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `3fb276a97f70708cb7bc6f0fe6f76ecc380d719d13c27063db385d230165e696`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-lstm-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['none']`.
Unique queries 350; seed observations 1750; engines 15.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.000000000 [0.000000000, 0.000000000] | 15 | 1750 / 1750.0 | >=0.95 | 0.950000000 | not met |
| Tier2, all queries | 0.994285714 [0.985875706, 1.000000000] | 15 | 1750 / 1750.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.994285714 [0.985875706, 1.000000000] | 15 | 1750 / 1750.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 15 | 1750 / 1750.0 | none | — | no target |
| Tier4 | 0.948571429 [0.923724278, 0.969703179] | 15 | 1750 / 1750.0 | none | — | no target |
| Joint success | 0.000000000 [0.000000000, 0.000000000] | 15 | 1750 / 1750.0 | none | — | no target |
| Mean support, all queries | 3.000000000 [3.000000000, 3.000000000] | 15 | 1750 / 1750.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | unmeasured [unmeasured, unmeasured] | 15 | 1750 / 0.0 | none | — | unmeasured |
| Mean model-risk drop | 0.042170111 [0.031628076, 0.052214710] | 15 | 1750 / 1750.0 | >=0.6 | 0.557829889 | not met |

## FD001/lstm/v2/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `fd6903baf944ebfef84f3264d8e58de7490f60820eccf7004db846adc9f878e0`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-lstm-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['official_test_all_alerts']`; evidence levels observed `['none']`.
Unique queries 138; seed observations 690; engines 16.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.000000000 [0.000000000, 0.000000000] | 16 | 690 / 690.0 | >=0.95 | 0.950000000 | not met |
| Tier2, all queries | 0.978260870 [0.938593117, 1.000000000] | 16 | 690 / 690.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.978260870 [0.938593117, 1.000000000] | 16 | 690 / 690.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 16 | 690 / 690.0 | none | — | no target |
| Tier4 | 0.985507246 [0.965517241, 1.000000000] | 16 | 690 / 690.0 | none | — | no target |
| Joint success | 0.000000000 [0.000000000, 0.000000000] | 16 | 690 / 690.0 | none | — | no target |
| Mean support, all queries | 3.000000000 [3.000000000, 3.000000000] | 16 | 690 / 690.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | unmeasured [unmeasured, unmeasured] | 16 | 690 / 0.0 | none | — | unmeasured |
| Mean model-risk drop | 0.111555518 [0.091089050, 0.133671791] | 16 | 690 / 690.0 | >=0.6 | 0.488444482 | not met |

## FD001/mlp/v1/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `00ba5c6ad8918f6739a7c8f06addfcffad4726ebc8ee35be8ec8377e7052c95e`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-mlp-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3', 'none']`.
Unique queries 2472; seed observations 12360; engines 100.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.500404531 [0.470830696, 0.530829136] | 100 | 12360 / 12360.0 | >=0.95 | 0.449595469 | not met |
| Tier2, all queries | 0.447411003 [0.404464839, 0.492739412] | 100 | 12360 / 12360.0 | >=0.9 | 0.452588997 | not met |
| Tier2, returned candidates | 0.467776355 [0.427994616, 0.511308654] | 100 | 12360 / 11715.0 | >=0.9 | 0.432223645 | not met |
| Tier3 | 0.953074434 [0.922541284, 0.979228792] | 100 | 12360 / 12360.0 | none | — | no target |
| Tier4 | 0.920307443 [0.899104126, 0.938656199] | 100 | 12360 / 12360.0 | none | — | no target |
| Joint success | 0.352750809 [0.320204670, 0.386179631] | 100 | 12360 / 12360.0 | none | — | no target |
| Mean support, all queries | 2.748786408 [2.662597039, 2.826617296] | 100 | 12360 / 12360.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.727064220 [2.691913169, 2.764230803] | 100 | 12360 / 4360.0 | none | — | no target |
| Mean model-risk drop | 0.535384907 [0.509899507, 0.559896831] | 100 | 12360 / 12360.0 | >=0.6 | 0.064615093 | not met |

## FD001/mlp/v1/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `7d114224c7f650d7566309bd0eb97b4b48de04a3d033477234a101e31d74d579`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-mlp-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3', 'none']`.
Unique queries 377; seed observations 1885; engines 15.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.543766578 [0.472771152, 0.607942941] | 15 | 1885 / 1885.0 | >=0.95 | 0.406233422 | not met |
| Tier2, all queries | 0.469496021 [0.371119975, 0.555809903] | 15 | 1885 / 1885.0 | >=0.9 | 0.430503979 | not met |
| Tier2, returned candidates | 0.469496021 [0.371119975, 0.555809903] | 15 | 1885 / 1885.0 | >=0.9 | 0.430503979 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 15 | 1885 / 1885.0 | none | — | no target |
| Tier4 | 0.944297082 [0.919997416, 0.967059568] | 15 | 1885 / 1885.0 | none | — | no target |
| Joint success | 0.381962865 [0.299459906, 0.451706348] | 15 | 1885 / 1885.0 | none | — | no target |
| Mean support, all queries | 2.854111406 [2.807161513, 2.903335671] | 15 | 1885 / 1885.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.708333333 [2.643274854, 2.784618056] | 15 | 1885 / 720.0 | none | — | no target |
| Mean model-risk drop | 0.583659723 [0.526925377, 0.633574812] | 15 | 1885 / 1885.0 | >=0.6 | 0.016340277 | not met |

## FD001/mlp/v1/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `130506d4a2658fce61714f6cfb6f0607f236eb46a1c763f1604c0a4ee7a10195`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-mlp-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['official_test_all_alerts']`; evidence levels observed `['E1', 'E3', 'none']`.
Unique queries 170; seed observations 850; engines 19.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.911764706 [0.858024691, 0.962031287] | 19 | 850 / 850.0 | >=0.95 | 0.038235294 | not met |
| Tier2, all queries | 0.788235294 [0.705544872, 0.852046614] | 19 | 850 / 850.0 | >=0.9 | 0.111764706 | not met |
| Tier2, returned candidates | 0.788235294 [0.705544872, 0.852046614] | 19 | 850 / 850.0 | >=0.9 | 0.111764706 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 19 | 850 / 850.0 | none | — | no target |
| Tier4 | 0.994117647 [0.979591837, 1.000000000] | 19 | 850 / 850.0 | none | — | no target |
| Joint success | 0.776470588 [0.691335979, 0.844661702] | 19 | 850 / 850.0 | none | — | no target |
| Mean support, all queries | 2.682352941 [2.613525829, 2.758175418] | 19 | 850 / 850.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.628787879 [2.562488595, 2.708343447] | 19 | 850 / 660.0 | none | — | no target |
| Mean model-risk drop | 0.729391751 [0.715868729, 0.741869946] | 19 | 850 / 850.0 | >=0.6 | 0.000000000 | met |

## FD001/mlp/v2/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `90039fe60b7e9b4b7ed0df53ed27cdc4077d904696bed117e1240f0e1c746e86`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-mlp-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3', 'none']`.
Unique queries 2472; seed observations 12360; engines 100.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.500404531 [0.470830696, 0.530829136] | 100 | 12360 / 12360.0 | >=0.95 | 0.449595469 | not met |
| Tier2, all queries | 0.979368932 [0.968232658, 0.988743015] | 100 | 12360 / 12360.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.988049509 [0.982447901, 0.993154693] | 100 | 12360 / 11715.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 0.953074434 [0.922541284, 0.979228792] | 100 | 12360 / 12360.0 | none | — | no target |
| Tier4 | 0.920307443 [0.899104126, 0.938656199] | 100 | 12360 / 12360.0 | none | — | no target |
| Joint success | 0.479773463 [0.450502664, 0.510323699] | 100 | 12360 / 12360.0 | none | — | no target |
| Mean support, all queries | 2.680016181 [2.596711629, 2.757999480] | 100 | 12360 / 12360.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.629005059 [2.586790015, 2.673644690] | 100 | 12360 / 5930.0 | none | — | no target |
| Mean model-risk drop | 0.535074488 [0.509465344, 0.559788178] | 100 | 12360 / 12360.0 | >=0.6 | 0.064925512 | not met |

## FD001/mlp/v2/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `166e2dfcfdf70cea6f9f3e9c0bed9d403a421d7ece7fce11ce1be2482c83715c`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-mlp-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['E2', 'E3', 'none']`.
Unique queries 377; seed observations 1885; engines 15.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.543766578 [0.472771152, 0.607942941] | 15 | 1885 / 1885.0 | >=0.95 | 0.406233422 | not met |
| Tier2, all queries | 0.994694960 [0.986944315, 1.000000000] | 15 | 1885 / 1885.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.994694960 [0.986944315, 1.000000000] | 15 | 1885 / 1885.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 15 | 1885 / 1885.0 | none | — | no target |
| Tier4 | 0.944297082 [0.919997416, 0.967059568] | 15 | 1885 / 1885.0 | none | — | no target |
| Joint success | 0.511936340 [0.436099422, 0.582978530] | 15 | 1885 / 1885.0 | none | — | no target |
| Mean support, all queries | 2.785145889 [2.728325008, 2.842378436] | 15 | 1885 / 1885.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.606217617 [2.524037937, 2.695876289] | 15 | 1885 / 965.0 | none | — | no target |
| Mean model-risk drop | 0.582284674 [0.524868587, 0.632315336] | 15 | 1885 / 1885.0 | >=0.6 | 0.017715326 | not met |

## FD001/mlp/v2/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `a81ee697efa05ffa0e9b60b5931999344745440903680c09d37c303dce359d0f`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-mlp-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['official_test_all_alerts']`; evidence levels observed `['E1', 'E3', 'none']`.
Unique queries 170; seed observations 850; engines 19.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.911764706 [0.858024691, 0.962031287] | 19 | 850 / 850.0 | >=0.95 | 0.038235294 | not met |
| Tier2, all queries | 0.994117647 [0.979591837, 1.000000000] | 19 | 850 / 850.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.994117647 [0.979591837, 1.000000000] | 19 | 850 / 850.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 19 | 850 / 850.0 | none | — | no target |
| Tier4 | 0.994117647 [0.979591837, 1.000000000] | 19 | 850 / 850.0 | none | — | no target |
| Joint success | 0.905882353 [0.852551020, 0.955555556] | 19 | 850 / 850.0 | none | — | no target |
| Mean support, all queries | 2.564705882 [2.479766436, 2.644970414] | 19 | 850 / 850.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.519480519 [2.430692166, 2.605283094] | 19 | 850 / 770.0 | none | — | no target |
| Mean model-risk drop | 0.725954348 [0.713011801, 0.737363036] | 19 | 850 / 850.0 | >=0.6 | 0.000000000 | met |

## FD001/xgb/v1/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `a3483e883531d1d12b008ef5ac2c1dd5e98c2990ad40dcb0d2ca5cbedeedc2e3`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-xgb-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3', 'none']`.
Unique queries 2378; seed observations 11890; engines 100.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.525231287 [0.493042329, 0.556434093] | 100 | 11890 / 11890.0 | >=0.95 | 0.424768713 | not met |
| Tier2, all queries | 0.486963835 [0.445946048, 0.526111941] | 100 | 11890 / 11890.0 | >=0.9 | 0.413036165 | not met |
| Tier2, returned candidates | 0.510449088 [0.474595694, 0.544636191] | 100 | 11890 / 11245.0 | >=0.9 | 0.389550912 | not met |
| Tier3 | 0.951219512 [0.920096479, 0.978265210] | 100 | 11890 / 11890.0 | none | — | no target |
| Tier4 | 0.916736754 [0.894516787, 0.936155068] | 100 | 11890 / 11890.0 | none | — | no target |
| Joint success | 0.399074853 [0.367285456, 0.429127112] | 100 | 11890 / 11890.0 | none | — | no target |
| Mean support, all queries | 2.763246426 [2.668784211, 2.846641390] | 100 | 11890 / 11890.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.787144362 [2.752575764, 2.819506326] | 100 | 11890 / 4745.0 | none | — | no target |
| Mean model-risk drop | 0.563200300 [0.535622883, 0.589619100] | 100 | 11890 / 11890.0 | >=0.6 | 0.036799700 | not met |

## FD001/xgb/v1/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `f24c40c738be62a62cdd859cab4f2124b6aa3c7d9d2390f3b0368d2a1926e8c3`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-xgb-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3', 'none']`.
Unique queries 378; seed observations 1890; engines 15.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.558201058 [0.489982620, 0.625008075] | 15 | 1890 / 1890.0 | >=0.95 | 0.391798942 | not met |
| Tier2, all queries | 0.513227513 [0.443888908, 0.575345093] | 15 | 1890 / 1890.0 | >=0.9 | 0.386772487 | not met |
| Tier2, returned candidates | 0.513227513 [0.443888908, 0.575345093] | 15 | 1890 / 1890.0 | >=0.9 | 0.386772487 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 15 | 1890 / 1890.0 | none | — | no target |
| Tier4 | 0.944444444 [0.920244251, 0.967443314] | 15 | 1890 / 1890.0 | none | — | no target |
| Joint success | 0.420634921 [0.379208365, 0.461538462] | 15 | 1890 / 1890.0 | none | — | no target |
| Mean support, all queries | 2.910052910 [2.885116696, 2.932039495] | 15 | 1890 / 1890.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.798742138 [2.738333843, 2.847237319] | 15 | 1890 / 795.0 | none | — | no target |
| Mean model-risk drop | 0.598155798 [0.543098496, 0.650297146] | 15 | 1890 / 1890.0 | >=0.6 | 0.001844202 | not met |

## FD001/xgb/v1/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `0ad569564fa6edd51af24059ee4e59effd239da21231dc9088222f5a3fb7974b`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-xgb-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['official_test_all_alerts']`; evidence levels observed `['E1', 'E3', 'none']`.
Unique queries 159; seed observations 795; engines 19.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.893081761 [0.835714286, 0.943551227] | 19 | 795 / 795.0 | >=0.95 | 0.056918239 | not met |
| Tier2, all queries | 0.779874214 [0.704223269, 0.843753811] | 19 | 795 / 795.0 | >=0.9 | 0.120125786 | not met |
| Tier2, returned candidates | 0.779874214 [0.704223269, 0.843753811] | 19 | 795 / 795.0 | >=0.9 | 0.120125786 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 19 | 795 / 795.0 | none | — | no target |
| Tier4 | 0.987421384 [0.965709360, 1.000000000] | 19 | 795 / 795.0 | none | — | no target |
| Joint success | 0.767295597 [0.687488073, 0.836604642] | 19 | 795 / 795.0 | none | — | no target |
| Mean support, all queries | 2.773584906 [2.643264411, 2.870753785] | 19 | 795 / 795.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.770491803 [2.663716814, 2.864411194] | 19 | 795 / 610.0 | none | — | no target |
| Mean model-risk drop | 0.742415050 [0.727847825, 0.758046816] | 19 | 795 / 795.0 | >=0.6 | 0.000000000 | met |

## FD001/xgb/v2/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `432c17f956ccfcdfdabd9b073cb74b26c6d7e8877746630065d66b6a5329c61e`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-xgb-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3', 'none']`.
Unique queries 2378; seed observations 11890; engines 100.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.525231287 [0.493042329, 0.556434093] | 100 | 11890 / 11890.0 | >=0.95 | 0.424768713 | not met |
| Tier2, all queries | 0.980656013 [0.970024248, 0.989206108] | 100 | 11890 / 11890.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.989773233 [0.984546844, 0.994230235] | 100 | 11890 / 11245.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 0.951219512 [0.920096479, 0.978265210] | 100 | 11890 / 11890.0 | none | — | no target |
| Tier4 | 0.916736754 [0.894516787, 0.936155068] | 100 | 11890 / 11890.0 | none | — | no target |
| Joint success | 0.504205214 [0.472895721, 0.534791723] | 100 | 11890 / 11890.0 | none | — | no target |
| Mean support, all queries | 2.725399495 [2.636106801, 2.807423475] | 100 | 11890 / 11890.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.744787323 [2.715871578, 2.771085538] | 100 | 11890 / 5995.0 | none | — | no target |
| Mean model-risk drop | 0.563562600 [0.536284555, 0.589941016] | 100 | 11890 / 11890.0 | >=0.6 | 0.036437400 | not met |

## FD001/xgb/v2/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `dace208feedc8ab0fade66b4d4b62c45f0d84dc5510bce68252305f627797599`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-xgb-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['E2', 'E3', 'none']`.
Unique queries 378; seed observations 1890; engines 15.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.558201058 [0.489982620, 0.625008075] | 15 | 1890 / 1890.0 | >=0.95 | 0.391798942 | not met |
| Tier2, all queries | 0.989417989 [0.980906106, 0.997361651] | 15 | 1890 / 1890.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 0.989417989 [0.980906106, 0.997361651] | 15 | 1890 / 1890.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 15 | 1890 / 1890.0 | none | — | no target |
| Tier4 | 0.944444444 [0.920244251, 0.967443314] | 15 | 1890 / 1890.0 | none | — | no target |
| Joint success | 0.529100529 [0.461345919, 0.596057434] | 15 | 1890 / 1890.0 | none | — | no target |
| Mean support, all queries | 2.873015873 [2.849008910, 2.899666750] | 15 | 1890 / 1890.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.770000000 [2.725581395, 2.815797036] | 15 | 1890 / 1000.0 | none | — | no target |
| Mean model-risk drop | 0.599881699 [0.544213951, 0.651986600] | 15 | 1890 / 1890.0 | >=0.6 | 0.000118301 | not met |

## FD001/xgb/v2/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `bf715a849ba303ec345c22157f46ed3d6ad2f5e41bf15972c9a04a560a039e22`.
Committed model profile(s): `['configs\\experiments\\phase7-FD001-xgb-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['official_test_all_alerts']`; evidence levels observed `['E2', 'E3', 'none']`.
Unique queries 159; seed observations 795; engines 19.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 0.893081761 [0.835714286, 0.943551227] | 19 | 795 / 795.0 | >=0.95 | 0.056918239 | not met |
| Tier2, all queries | 1.000000000 [1.000000000, 1.000000000] | 19 | 795 / 795.0 | >=0.9 | 0.000000000 | met |
| Tier2, returned candidates | 1.000000000 [1.000000000, 1.000000000] | 19 | 795 / 795.0 | >=0.9 | 0.000000000 | met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 19 | 795 / 795.0 | none | — | no target |
| Tier4 | 0.987421384 [0.965709360, 1.000000000] | 19 | 795 / 795.0 | none | — | no target |
| Joint success | 0.880503145 [0.820339021, 0.931975939] | 19 | 795 / 795.0 | none | — | no target |
| Mean support, all queries | 2.729559748 [2.614006791, 2.836488024] | 19 | 795 / 795.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.707142857 [2.586925466, 2.822231183] | 19 | 795 / 700.0 | none | — | no target |
| Mean model-risk drop | 0.741152642 [0.727216568, 0.755718068] | 19 | 795 / 795.0 | >=0.6 | 0.000000000 | met |

## FD002/xgb/v1/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `7fdfd01db0aaca0b5ddfe6bda8b269bf0b04f85287bf1188c5e7f5153a8de46b`.
Committed model profile(s): `['configs\\experiments\\phase7-FD002-xgb-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3']`.
Unique queries 5591; seed observations 27955; engines 260.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 1.000000000 [1.000000000, 1.000000000] | 260 | 27955 / 27955.0 | >=0.95 | 0.000000000 | met |
| Tier2, all queries | 0.031300304 [0.026538854, 0.036373632] | 260 | 27955 / 27955.0 | >=0.9 | 0.868699696 | not met |
| Tier2, returned candidates | 0.031300304 [0.026538854, 0.036373632] | 260 | 27955 / 27955.0 | >=0.9 | 0.868699696 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 260 | 27955 / 27955.0 | none | — | no target |
| Tier4 | 0.313003041 [0.282128977, 0.346051437] | 260 | 27955 / 27955.0 | none | — | no target |
| Joint success | 0.000715436 [0.000174092, 0.001451662] | 260 | 27955 / 27955.0 | none | — | no target |
| Mean support, all queries | 1.585405115 [1.561433120, 1.608971180] | 260 | 27955 / 27955.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.250000000 [1.000000000, 3.000000000] | 260 | 27955 / 20.0 | none | — | no target |
| Mean model-risk drop | 0.835903371 [0.833142640, 0.838834363] | 260 | 27955 / 27955.0 | >=0.6 | 0.000000000 | met |

## FD002/xgb/v1/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `a7522879e1bd8eba8836d5f637ddfdb5e3d746ccd5c38f439bcf84a00234cc80`.
Committed model profile(s): `['configs\\experiments\\phase7-FD002-xgb-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3']`.
Unique queries 911; seed observations 4555; engines 39.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 1.000000000 [1.000000000, 1.000000000] | 39 | 4555 / 4555.0 | >=0.95 | 0.000000000 | met |
| Tier2, all queries | 0.037321625 [0.027172531, 0.048299487] | 39 | 4555 / 4555.0 | >=0.9 | 0.862678375 | not met |
| Tier2, returned candidates | 0.037321625 [0.027172531, 0.048299487] | 39 | 4555 / 4555.0 | >=0.9 | 0.862678375 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 39 | 4555 / 4555.0 | none | — | no target |
| Tier4 | 0.286498353 [0.200858406, 0.378412691] | 39 | 4555 / 4555.0 | none | — | no target |
| Joint success | 0.003293085 [0.000000000, 0.007344553] | 39 | 4555 / 4555.0 | none | — | no target |
| Mean support, all queries | 1.624588364 [1.572616750, 1.673509454] | 39 | 4555 / 4555.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.000000000 [1.000000000, 3.000000000] | 39 | 4555 / 15.0 | none | — | no target |
| Mean model-risk drop | 0.838121260 [0.832635543, 0.843150224] | 39 | 4555 / 4555.0 | >=0.6 | 0.000000000 | met |

## FD002/xgb/v1/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `2bcd60ad093c45a6bd19c027719ee1dc004b6239f31013c28806f9af3f52cbae`.
Committed model profile(s): `['configs\\experiments\\phase7-FD002-xgb-v1.yaml']`. Protocol `['v1']`, k_max `['3']`, assumed K `['1']`, D_max `['5.0']`, population `['official_test_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3']`.
Unique queries 678; seed observations 3390; engines 65.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 1.000000000 [1.000000000, 1.000000000] | 65 | 3390 / 3390.0 | >=0.95 | 0.000000000 | met |
| Tier2, all queries | 0.045722714 [0.030612245, 0.062992444] | 65 | 3390 / 3390.0 | >=0.9 | 0.854277286 | not met |
| Tier2, returned candidates | 0.045722714 [0.030612245, 0.062992444] | 65 | 3390 / 3390.0 | >=0.9 | 0.854277286 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 65 | 3390 / 3390.0 | none | — | no target |
| Tier4 | 0.333333333 [0.258401154, 0.410441481] | 65 | 3390 / 3390.0 | none | — | no target |
| Joint success | 0.004424779 [0.000000000, 0.010221901] | 65 | 3390 / 3390.0 | none | — | no target |
| Mean support, all queries | 1.513274336 [1.461632766, 1.564653579] | 65 | 3390 / 3390.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.000000000 [1.000000000, 3.000000000] | 65 | 3390 / 15.0 | none | — | no target |
| Mean model-risk drop | 0.821257603 [0.814287157, 0.827572854] | 65 | 3390 / 3390.0 | >=0.6 | 0.000000000 | met |

## FD002/xgb/v2/grouped_oof_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `9eb007b33342f1e209b03a2b08aa93f462f02a20e65056c9219585134e56f75a`.
Committed model profile(s): `['configs\\experiments\\phase7-FD002-xgb-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['grouped_oof_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3']`.
Unique queries 5591; seed observations 27955; engines 260.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 1.000000000 [1.000000000, 1.000000000] | 260 | 27955 / 27955.0 | >=0.95 | 0.000000000 | met |
| Tier2, all queries | 0.109640494 [0.100900621, 0.117758016] | 260 | 27955 / 27955.0 | >=0.9 | 0.790359506 | not met |
| Tier2, returned candidates | 0.109640494 [0.100900621, 0.117758016] | 260 | 27955 / 27955.0 | >=0.9 | 0.790359506 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 260 | 27955 / 27955.0 | none | — | no target |
| Tier4 | 0.313003041 [0.282128977, 0.346051437] | 260 | 27955 / 27955.0 | none | — | no target |
| Joint success | 0.006617779 [0.004479986, 0.008977307] | 260 | 27955 / 27955.0 | none | — | no target |
| Mean support, all queries | 1.639062779 [1.618892432, 1.658932337] | 260 | 27955 / 27955.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.297297297 [2.076923077, 2.514307359] | 260 | 27955 / 185.0 | none | — | no target |
| Mean model-risk drop | 0.836746459 [0.833819768, 0.839684357] | 260 | 27955 / 27955.0 | >=0.6 | 0.000000000 | met |

## FD002/xgb/v2/internal_heldout_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `3e5abf5100175d285c43e9926225b5ae8e193b7a01c6a93505a4c741c57aceb1`.
Committed model profile(s): `['configs\\experiments\\phase7-FD002-xgb-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['internal_heldout_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3']`.
Unique queries 911; seed observations 4555; engines 39.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 1.000000000 [1.000000000, 1.000000000] | 39 | 4555 / 4555.0 | >=0.95 | 0.000000000 | met |
| Tier2, all queries | 0.108671789 [0.085712811, 0.132075472] | 39 | 4555 / 4555.0 | >=0.9 | 0.791328211 | not met |
| Tier2, returned candidates | 0.108671789 [0.085712811, 0.132075472] | 39 | 4555 / 4555.0 | >=0.9 | 0.791328211 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 39 | 4555 / 4555.0 | none | — | no target |
| Tier4 | 0.286498353 [0.200858406, 0.378412691] | 39 | 4555 / 4555.0 | none | — | no target |
| Joint success | 0.005488474 [0.001127238, 0.010707149] | 39 | 4555 / 4555.0 | none | — | no target |
| Mean support, all queries | 1.699231614 [1.645876940, 1.752038785] | 39 | 4555 / 4555.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.200000000 [1.500000000, 3.000000000] | 39 | 4555 / 25.0 | none | — | no target |
| Mean model-risk drop | 0.839364597 [0.834411908, 0.843931433] | 39 | 4555 / 4555.0 | >=0.6 | 0.000000000 | met |

## FD002/xgb/v2/official_test_all_alerts/fast/full

Run `phase7-20261020T102540Z`; source `63c2ed445fba16c73a2771e184f635abf76b4405`; config set `58da936f3c43d38ccb289716fa8f4fa719faa2e790b14ce665ba48ff27895737`.
Committed model profile(s): `['configs\\experiments\\phase7-FD002-xgb-v2.yaml']`. Protocol `['v2']`, k_max `['3']`, assumed K `['1']`, D_max `['8.0']`, population `['official_test_all_alerts']`; evidence levels observed `['E1', 'E2', 'E3']`.
Unique queries 678; seed observations 3390; engines 65.

| Metric | Measured [engine CI] | Engines | Observations / denominator | Target | Shortfall | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Validity | 1.000000000 [1.000000000, 1.000000000] | 65 | 3390 / 3390.0 | >=0.95 | 0.000000000 | met |
| Tier2, all queries | 0.138643068 [0.112533972, 0.164534965] | 65 | 3390 / 3390.0 | >=0.9 | 0.761356932 | not met |
| Tier2, returned candidates | 0.138643068 [0.112533972, 0.164534965] | 65 | 3390 / 3390.0 | >=0.9 | 0.761356932 | not met |
| Tier3 | 1.000000000 [1.000000000, 1.000000000] | 65 | 3390 / 3390.0 | none | — | no target |
| Tier4 | 0.333333333 [0.258401154, 0.410441481] | 65 | 3390 / 3390.0 | none | — | no target |
| Joint success | 0.011799410 [0.004805983, 0.019551723] | 65 | 3390 / 3390.0 | none | — | no target |
| Mean support, all queries | 1.604719764 [1.546679450, 1.660828773] | 65 | 3390 / 3390.0 | <=3 | 0.000000000 | met |
| Mean support, joint successes | 2.125000000 [1.666666667, 2.600000000] | 65 | 3390 / 40.0 | none | — | no target |
| Mean model-risk drop | 0.820837974 [0.813635573, 0.827505721] | 65 | 3390 / 3390.0 | >=0.6 | 0.000000000 | met |

## All six latency budget rows

Run `phase7-20261020T102540Z`, source `63c2ed445fba16c73a2771e184f635abf76b4405`, study/config identities above. Runtime labels `{"D_max": 5.0, "D_max_version": "v1", "K": 1, "config_hash": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271", "git_hash": "63c2ed445fba16c73a2771e184f635abf76b4405", "k_max": 3, "population": "development_all_alerts_repeated_fixed_order", "protocol": "v1"}`.
Workload `all validation alerts, fixed engine/cycle order, cycled`; scope `warm serial backend; UI/startup unmeasured`; warmups excluded per invocation/mode 10. All measured calls and outliers retained. The verdict uses p95<=upper budget; faster passes.

| Mode / stage | p95 ms [95% engine CI] | Engines / calls | Upper budget ms | Shortfall ms | Verdict |
|---|---:|---:|---:|---:|---|
| FAST / ingestion_ms | 0.178500000 [0.170849625, 0.184795125] | 16 / 1000 | 10 | 0.000000000 | met |
| FAST / inference_ms | 3.048205000 [3.018351750, 3.116000000] | 16 / 1000 | 15 | 0.000000000 | met |
| FAST / optimization_ms | 2339.074780000 [2256.866225250, 2403.271553500] | 16 / 1000 | 1800 | 539.074780000 | not met |
| FAST / validation_ms | 5.493640000 [5.208800000, 5.684600000] | 16 / 1000 | 100 | 0.000000000 | met |
| FAST / pipeline_ms | 2348.233290000 [2265.848789375, 2414.081649500] | 16 / 1000 | 2200 | 148.233290000 | not met |
| FAST / dashboard_ms | unmeasured | 0 / 0 | 250 | unmeasured | unmeasured |
| THOROUGH / ingestion_ms | 0.183035000 [0.178704875, 0.195700000] | 16 / 1000 | 10 | 0.000000000 | met |
| THOROUGH / inference_ms | 3.108680000 [3.001819500, 3.215000000] | 16 / 1000 | 15 | 0.000000000 | met |
| THOROUGH / optimization_ms | 2080.227280000 [2029.095379500, 2171.670846500] | 16 / 1000 | 1800 | 280.227280000 | not met |
| THOROUGH / validation_ms | 5.771035000 [5.569000000, 6.103672375] | 16 / 1000 | 100 | 0.000000000 | met |
| THOROUGH / pipeline_ms | 2089.845030000 [2039.342303625, 2181.370566500] | 16 / 1000 | 2200 | 0.000000000 | met |
| THOROUGH / dashboard_ms | unmeasured | 0 / 0 | 250 | unmeasured | unmeasured |

The backend pipeline total is measured per call, not obtained by summing stage percentiles.
FAST total and both optimization modes miss their budgets. THOROUGH backend total passes.
The actual full UI-inclusive system total is **unmeasured**: backend and UI studies cannot be
added to manufacture its p95.

The separate Phase8 server-construction measurement passes the250ms budget within its scope:
p95 **115.3545ms [108.8,120.46]**, **8engines/32callbacks**, shortfall0ms. Run
`phase8-ui-render-20261024-v1`, source `52affd06d39b03f76a0dd70417c3a75bd76f55c4`, config
`configs/experiments/phase8-ui-render.yaml`, SHA256
`05f692de6b78fa6c9ca3477de8e3c4dd7454cfccff7d9259ef43909d5b4c6f5b`;
FD001/XGB/v1, FAST, k_max3, assumedK1, D_max5, official-test last-observed-cycle UI population.
Saved raw samples and summary: `artifacts/phase8/ui-render-20261024-v1/`.
Browser paint/network/loading/scoring/solve/attribution are excluded; full browser UI latency
remains **Not met / unmeasured** as a complete end-to-end requirement.

## Optional trajectory health

**Not met / not evaluated**. No validated emulator or physics simulator exists. The optional
interface is disabled; static benchmark labels and E3 proxy checks do not establish a dynamic
trajectory, causal health improvement or additional RUL cycles.
