# Phase 7 — measured results and closure evidence

This document is generated from saved real measurements by the ignored review renderer `artifacts/phase7-final-audit/render_summary.py`. It supplements the complete saved Markdown, HTML, CSV and JSON report; it does not replace records, failures or earlier protocol versions.

## Scope and interpretation

- Validity is the true calibrated predictor probability **f(x') <= 0.20**. Tier 2 is Mahalanobis plausibility, reported over all queries and over returned counterfactuals.
- Tiers 3 and 4 are separate proxy engineering/coupling checks. Joint success is stricter and is not compared with the 90% Tier 2 plausibility design target.
- All bracketed intervals below are 95% whole-engine bootstrap intervals with engine counts beside them (2000 replicates, bootstrap seed 1729). All states and solver repetitions belonging to a sampled engine stay together. Zero-return engines remain in the conditional bootstrap; undefined denominators remain explicit.
- Solver seeds are [1729, 1730, 1731, 1732, 1733]; they repeat fixed predictors. Their standard deviation does not measure predictor training uncertainty. Training seeds/hashes differ and remain recorded in model_metadata.json.
- C-MAPSS sensor channels are controllable **proxies**. Bounds, rates and K are assumptions; K sensitivity is not engine dynamics. E3 is the highest available evidence. No validated emulator/physics simulator, real actuator response or RUL extension is established.
- Internal test, grouped outer-fold and official test populations are shown side by side. Validation-engine development results remain in the complete saved report, separately labeled.
- Optional FD003/FD004 were not scheduled. Early LSTM windows without genuine history are excluded with their counts in the manifest; they are not replaced by duplicated states.

## Provenance and completed measurements

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: preregistered diagnostics, full quality, declared references, serial latency. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Stage | Saved observations | Frozen source |
|---|---|---|
| diagnostics | 2496 | 63c2ed445fba16c73a2771e184f635abf76b4405 |
| quality | 171490 | 63c2ed445fba16c73a2771e184f635abf76b4405 |
| reference | 48 | 63c2ed445fba16c73a2771e184f635abf76b4405 |
| latency | 2000 | 63c2ed445fba16c73a2771e184f635abf76b4405 |

The original process stopped after 122,821 quality results at 2026-10-23 18:34 UTC; its termination cause is **unknown**. Source/runtime/config/artifact compatibility and SQLite integrity were independently verified before resuming the same run at 2026-10-23T18:39:57.350409+00:00. The resumed segment added 48,669 quality results. Completed IDs were reused, four registered but uncommitted cases were retried, and no saved result or timing was replaced. The resumed process exited with code 0 at 2026-10-24T04:26:44.177897+00:00.

Historical quality-run timings include documented power interruptions and competing experiment worker overhead; every outlier is retained. The warm serial latency stage began only after quality workers stopped. UI, network and cold startup remain unmeasured in Phase 7.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: base/internal FAST registry only; OOF folds and THOROUGH have distinct recorded runtime hashes. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile | Committed cohort config | Base/internal FAST config hashes across solver seeds |
|---|---|---|
| FD001/lstm/v1 | configs\experiments\phase7-FD001-lstm-v1.yaml | 375acd296ef2ef253dd869ef84df70973346c7137265d89a0eedffc05a81cec0; 41296e94f9a3b9fc7ac4e7a0cd0b832324cc8a47b6fdb7665e5d5892b3a70847; 78cd7e7d9c4845cd7803c83a5c73b38f5580c23d99cdddd3e3705ba8f5bb7685; 943989e0e7b5b8c1efbda678b5e1532d862a2036fd37f694521529dbadc89e4e; c830fd1d503114ac41c6d8d2ad390ae3f8d47835113878d72c9db8c1a21ba1d9 |
| FD001/lstm/v2 | configs\experiments\phase7-FD001-lstm-v2.yaml | 70f7b33fb185b281c4430ad928be7ce5485544ea50f9db122a062d2c0bd044ba; 81ac3078a851f514b516dae67beb95e4a5e946b5093c18cbb14fb71410e4f5f1; b325d3b8132e0d754d5e90b9ffa8adf62b66dc40843d7592926b7437fff59d9b; be07c4b93e23c534ddcc729420dac5fcd0af2d60a336aced4e08d3cfb897f0ff; d70a6ebc267dcfb98e9292c7568b9515d5bd049631319156ea32a0097e8d869a |
| FD001/mlp/v1 | configs\experiments\phase7-FD001-mlp-v1.yaml | 055449ac85ff54bc6b7793b41849f5e22f5fc642c2613e5ba953e15cfb686248; 27ae03b9319734aba94d6d04cee39319bfd8446d5a696ccbfea98492c0e7cae5; 2b359080157153d651f565ba9a04b0973f6f7dc6089bf5ae953dfb7345b1cc62; 36cdf14132b8ecee904622fe8f78ae845401f95ce82c7ac83e4ca4c6f530ef82; d8a823c94f8b21215719b9a5ec58902f6dbfa7c239b97cf018b949341f00dfd7 |
| FD001/mlp/v2 | configs\experiments\phase7-FD001-mlp-v2.yaml | 0f4b8ffe8ac75937f0e96e2249fb8da274d1c60972bc36f6a7625e5eb17aec76; 97cae065f37ffa6e0a8afb66f069ce34870435cc74dea3293e40219c1c0017cb; a10a683c769e1673d383da56ce2cffb53df5a48134895de641ebf9d624888c1d; e0710ee0ead8d5a1347579316bc127d6c380a1bd4895955639716e09b2b88b18; f3b86bf09a48a0777b400ed0e9f48d1e9d6f514cdad5e70a0d910787f694131c |
| FD001/xgb/v1 | configs\experiments\phase7-FD001-xgb-v1.yaml | 387710b067719302aba415b8bbdbb9ba32c609364e27e5f6290008815b0966cb; 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271; b7670ffb756389ed13c6724024713341ee0c0f83248fa3466e95bdd9297c6671; b8a56224aaeb156f53936e8c46e3bd9188bbc9f29cf308158de1f91ec76123f6; d008252a3892855e1806034bb2c3b52cfaba58e150b2ef32dd7add4989ed6029 |
| FD001/xgb/v2 | configs\experiments\phase7-FD001-xgb-v2.yaml | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a; 4807060124d9fb65e68fb02317f1e240d97f6954b66ba3e56c6e95f955aa04e1; 76b79302ffe7581df1453bedceaabfb11aaf25a07e68af9a0c7f9d879c5fdf32; a6dc02c11b6a18fb41880b8521421ccff47f96aa0102cca0648ca34525d91d7b; de084dfd83722c4a167f4959e29bd0eb455400ae9166d806ccf818096d345689 |
| FD002/xgb/v1 | configs\experiments\phase7-FD002-xgb-v1.yaml | 30723add36f39d26d4b763cf3cebaa09b501d4a67b76a492dff8b21926b0bfe2; 815827b3ad6c76124d04ff379827d857d43faa01a68c8c14093b328b8f40e20d; b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264; e98b73cd3a09ad87f6b92efb197f6ea1d960609eb5c88333e6cd569b41e88721; f2a9450bcf9f410b67f1a07a49ce8c4813ac83fcb6b010a98b06f556339c3af9 |
| FD002/xgb/v2 | configs\experiments\phase7-FD002-xgb-v2.yaml | 13d21a7011a50df267af7164339f8bb084fcb787336ccead420be664dba8613e; 51c6e6ce660f55c07751841bc440a7c89960877e68cef88424bf2c17e4c10117; 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd; 849c855930d3860b8f46b07e06c5973decebf43b2ddf68c26ef8fed5b860e159; 99da2824405680895045224703f32ed00c6e5be99cccfca388b64c5d6d483ca5 |

## FAST all-alert results, side by side

Values in rate tables are percentages; intervals are over engines. A query is an engine/cycle, and each has five solver-seed observations. Denominators include failed queries.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; five solver seeds. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile | Internal held-out queries / observations / engines | Grouped OOF queries / observations / engines | Official test queries / observations / engines |
|---|---|---|---|
| FD001/lstm/v1 | 350 / 1750 / 15 | 2456 / 12280 / 100 | 138 / 690 / 16 |
| FD001/lstm/v2 | 350 / 1750 / 15 | 2456 / 12280 / 100 | 138 / 690 / 16 |
| FD001/mlp/v1 | 377 / 1885 / 15 | 2472 / 12360 / 100 | 170 / 850 / 19 |
| FD001/mlp/v2 | 377 / 1885 / 15 | 2472 / 12360 / 100 | 170 / 850 / 19 |
| FD001/xgb/v1 | 378 / 1890 / 15 | 2378 / 11890 / 100 | 159 / 795 / 19 |
| FD001/xgb/v2 | 378 / 1890 / 15 | 2378 / 11890 / 100 | 159 / 795 / 19 |
| FD002/xgb/v1 | 911 / 4555 / 39 | 5591 / 27955 / 260 | 678 / 3390 / 65 |
| FD002/xgb/v2 | 911 / 4555 / 39 | 5591 / 27955 / 260 | 678 / 3390 / 65 |

### True model validity

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; True model validity. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile | Internal held-out | Grouped OOF | Official test |
|---|---|---|---|
| FD001/lstm/v1 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=16 |
| FD001/lstm/v2 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=16 |
| FD001/mlp/v1 | 54.38 [47.28, 60.79]; n=15 | 50.04 [47.08, 53.08]; n=100 | 91.18 [85.80, 96.20]; n=19 |
| FD001/mlp/v2 | 54.38 [47.28, 60.79]; n=15 | 50.04 [47.08, 53.08]; n=100 | 91.18 [85.80, 96.20]; n=19 |
| FD001/xgb/v1 | 55.82 [49.00, 62.50]; n=15 | 52.52 [49.30, 55.64]; n=100 | 89.31 [83.57, 94.36]; n=19 |
| FD001/xgb/v2 | 55.82 [49.00, 62.50]; n=15 | 52.52 [49.30, 55.64]; n=100 | 89.31 [83.57, 94.36]; n=19 |
| FD002/xgb/v1 | 100.00 [100.00, 100.00]; n=39 | 100.00 [100.00, 100.00]; n=260 | 100.00 [100.00, 100.00]; n=65 |
| FD002/xgb/v2 | 100.00 [100.00, 100.00]; n=39 | 100.00 [100.00, 100.00]; n=260 | 100.00 [100.00, 100.00]; n=65 |

### Tier 2 over all queries

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; Tier 2 over all queries. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile | Internal held-out | Grouped OOF | Official test |
|---|---|---|---|
| FD001/lstm/v1 | 21.71 [15.34, 28.15]; n=15 | 22.88 [19.29, 26.41]; n=100 | 31.16 [19.54, 42.47]; n=16 |
| FD001/lstm/v2 | 99.43 [98.59, 100.00]; n=15 | 97.68 [96.55, 98.67]; n=100 | 97.83 [93.86, 100.00]; n=16 |
| FD001/mlp/v1 | 46.95 [37.11, 55.58]; n=15 | 44.74 [40.45, 49.27]; n=100 | 78.82 [70.55, 85.20]; n=19 |
| FD001/mlp/v2 | 99.47 [98.69, 100.00]; n=15 | 97.94 [96.82, 98.87]; n=100 | 99.41 [97.96, 100.00]; n=19 |
| FD001/xgb/v1 | 51.32 [44.39, 57.53]; n=15 | 48.70 [44.59, 52.61]; n=100 | 77.99 [70.42, 84.38]; n=19 |
| FD001/xgb/v2 | 98.94 [98.09, 99.74]; n=15 | 98.07 [97.00, 98.92]; n=100 | 100.00 [100.00, 100.00]; n=19 |
| FD002/xgb/v1 | 3.73 [2.72, 4.83]; n=39 | 3.13 [2.65, 3.64]; n=260 | 4.57 [3.06, 6.30]; n=65 |
| FD002/xgb/v2 | 10.87 [8.57, 13.21]; n=39 | 10.96 [10.09, 11.78]; n=260 | 13.86 [11.25, 16.45]; n=65 |

### Tier 2 over returned counterfactuals

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; Tier 2 over returned counterfactuals. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile | Internal held-out | Grouped OOF | Official test |
|---|---|---|---|
| FD001/lstm/v1 | 21.71 [15.34, 28.15]; n=15 | 23.72 [20.29, 27.14]; n=100 | 31.16 [19.54, 42.47]; n=16 |
| FD001/lstm/v2 | 99.43 [98.59, 100.00]; n=15 | 98.54 [97.90, 99.14]; n=100 | 97.83 [93.86, 100.00]; n=16 |
| FD001/mlp/v1 | 46.95 [37.11, 55.58]; n=15 | 46.78 [42.80, 51.13]; n=100 | 78.82 [70.55, 85.20]; n=19 |
| FD001/mlp/v2 | 99.47 [98.69, 100.00]; n=15 | 98.80 [98.24, 99.32]; n=100 | 99.41 [97.96, 100.00]; n=19 |
| FD001/xgb/v1 | 51.32 [44.39, 57.53]; n=15 | 51.04 [47.46, 54.46]; n=100 | 77.99 [70.42, 84.38]; n=19 |
| FD001/xgb/v2 | 98.94 [98.09, 99.74]; n=15 | 98.98 [98.45, 99.42]; n=100 | 100.00 [100.00, 100.00]; n=19 |
| FD002/xgb/v1 | 3.73 [2.72, 4.83]; n=39 | 3.13 [2.65, 3.64]; n=260 | 4.57 [3.06, 6.30]; n=65 |
| FD002/xgb/v2 | 10.87 [8.57, 13.21]; n=39 | 10.96 [10.09, 11.78]; n=260 | 13.86 [11.25, 16.45]; n=65 |

### Joint success

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; Joint success. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile | Internal held-out | Grouped OOF | Official test |
|---|---|---|---|
| FD001/lstm/v1 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=16 |
| FD001/lstm/v2 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=16 |
| FD001/mlp/v1 | 38.20 [29.95, 45.17]; n=15 | 35.28 [32.02, 38.62]; n=100 | 77.65 [69.13, 84.47]; n=19 |
| FD001/mlp/v2 | 51.19 [43.61, 58.30]; n=15 | 47.98 [45.05, 51.03]; n=100 | 90.59 [85.26, 95.56]; n=19 |
| FD001/xgb/v1 | 42.06 [37.92, 46.15]; n=15 | 39.91 [36.73, 42.91]; n=100 | 76.73 [68.75, 83.66]; n=19 |
| FD001/xgb/v2 | 52.91 [46.13, 59.61]; n=15 | 50.42 [47.29, 53.48]; n=100 | 88.05 [82.03, 93.20]; n=19 |
| FD002/xgb/v1 | 0.33 [0.00, 0.73]; n=39 | 0.07 [0.02, 0.15]; n=260 | 0.44 [0.00, 1.02]; n=65 |
| FD002/xgb/v2 | 0.55 [0.11, 1.07]; n=39 | 0.66 [0.45, 0.90]; n=260 | 1.18 [0.48, 1.96]; n=65 |

### Independent tiers, proximity and risk reduction

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; mixed-unit raw L1 is descriptive, scaled L1 is dimensionless. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | Tier 3 % | Tier 4 % | Risk drop (probability) | Mean support | Raw L1 | Scaled L1 |
|---|---|---|---|---|---|---|
| FD001/lstm/v1/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 94.86 [92.37, 96.97]; n=15 | 0.04 [0.03, 0.05]; n=15 | 3.00 [3.00, 3.00]; n=15 | 19.47 [19.18, 19.75]; n=15 | 10.95 [10.88, 11.03]; n=15 |
| FD001/lstm/v1/grouped_oof | 95.28 [92.27, 97.90]; n=100 | 91.94 [89.74, 93.82]; n=100 | 0.05 [0.04, 0.06]; n=100 | 2.86 [2.77, 2.94]; n=100 | 19.07 [18.66, 19.46]; n=100 | 10.04 [9.67, 10.38]; n=100 |
| FD001/lstm/v1/official_test | 100.00 [100.00, 100.00]; n=16 | 98.55 [96.55, 100.00]; n=16 | 0.11 [0.09, 0.13]; n=16 | 3.00 [3.00, 3.00]; n=16 | 19.70 [18.96, 20.22]; n=16 | 11.06 [10.96, 11.13]; n=16 |
| FD001/lstm/v2/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 94.86 [92.37, 96.97]; n=15 | 0.04 [0.03, 0.05]; n=15 | 3.00 [3.00, 3.00]; n=15 | 19.47 [19.18, 19.75]; n=15 | 10.95 [10.88, 11.03]; n=15 |
| FD001/lstm/v2/grouped_oof | 95.28 [92.27, 97.90]; n=100 | 91.94 [89.74, 93.82]; n=100 | 0.05 [0.04, 0.06]; n=100 | 2.86 [2.77, 2.94]; n=100 | 19.07 [18.66, 19.46]; n=100 | 10.04 [9.67, 10.38]; n=100 |
| FD001/lstm/v2/official_test | 100.00 [100.00, 100.00]; n=16 | 98.55 [96.55, 100.00]; n=16 | 0.11 [0.09, 0.13]; n=16 | 3.00 [3.00, 3.00]; n=16 | 19.70 [18.96, 20.22]; n=16 | 11.06 [10.96, 11.13]; n=16 |
| FD001/mlp/v1/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 94.43 [92.00, 96.71]; n=15 | 0.58 [0.53, 0.63]; n=15 | 2.85 [2.81, 2.90]; n=15 | 23.01 [19.43, 27.23]; n=15 | 8.82 [8.49, 9.12]; n=15 |
| FD001/mlp/v1/grouped_oof | 95.31 [92.25, 97.92]; n=100 | 92.03 [89.91, 93.87]; n=100 | 0.54 [0.51, 0.56]; n=100 | 2.75 [2.66, 2.83]; n=100 | 21.73 [20.59, 22.98]; n=100 | 8.40 [8.09, 8.67]; n=100 |
| FD001/mlp/v1/official_test | 100.00 [100.00, 100.00]; n=19 | 99.41 [97.96, 100.00]; n=19 | 0.73 [0.72, 0.74]; n=19 | 2.68 [2.61, 2.76]; n=19 | 19.72 [17.34, 22.84]; n=19 | 7.26 [6.87, 7.57]; n=19 |
| FD001/mlp/v2/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 94.43 [92.00, 96.71]; n=15 | 0.58 [0.52, 0.63]; n=15 | 2.79 [2.73, 2.84]; n=15 | 22.72 [19.17, 26.95]; n=15 | 8.60 [8.31, 8.87]; n=15 |
| FD001/mlp/v2/grouped_oof | 95.31 [92.25, 97.92]; n=100 | 92.03 [89.91, 93.87]; n=100 | 0.54 [0.51, 0.56]; n=100 | 2.68 [2.60, 2.76]; n=100 | 21.87 [20.76, 23.10]; n=100 | 8.21 [7.91, 8.48]; n=100 |
| FD001/mlp/v2/official_test | 100.00 [100.00, 100.00]; n=19 | 99.41 [97.96, 100.00]; n=19 | 0.73 [0.71, 0.74]; n=19 | 2.56 [2.48, 2.64]; n=19 | 19.28 [17.15, 22.03]; n=19 | 6.82 [6.42, 7.14]; n=19 |
| FD001/xgb/v1/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 94.44 [92.02, 96.74]; n=15 | 0.60 [0.54, 0.65]; n=15 | 2.91 [2.89, 2.93]; n=15 | 21.76 [19.03, 24.95]; n=15 | 8.60 [8.23, 8.94]; n=15 |
| FD001/xgb/v1/grouped_oof | 95.12 [92.01, 97.83]; n=100 | 91.67 [89.45, 93.62]; n=100 | 0.56 [0.54, 0.59]; n=100 | 2.76 [2.67, 2.85]; n=100 | 20.26 [19.36, 21.22]; n=100 | 7.94 [7.61, 8.25]; n=100 |
| FD001/xgb/v1/official_test | 100.00 [100.00, 100.00]; n=19 | 98.74 [96.57, 100.00]; n=19 | 0.74 [0.73, 0.76]; n=19 | 2.77 [2.64, 2.87]; n=19 | 20.93 [18.91, 23.40]; n=19 | 6.75 [6.16, 7.20]; n=19 |
| FD001/xgb/v2/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 94.44 [92.02, 96.74]; n=15 | 0.60 [0.54, 0.65]; n=15 | 2.87 [2.85, 2.90]; n=15 | 22.00 [19.44, 24.91]; n=15 | 8.53 [8.18, 8.86]; n=15 |
| FD001/xgb/v2/grouped_oof | 95.12 [92.01, 97.83]; n=100 | 91.67 [89.45, 93.62]; n=100 | 0.56 [0.54, 0.59]; n=100 | 2.73 [2.64, 2.81]; n=100 | 20.36 [19.46, 21.31]; n=100 | 7.84 [7.52, 8.14]; n=100 |
| FD001/xgb/v2/official_test | 100.00 [100.00, 100.00]; n=19 | 98.74 [96.57, 100.00]; n=19 | 0.74 [0.73, 0.76]; n=19 | 2.73 [2.61, 2.84]; n=19 | 21.09 [19.01, 23.72]; n=19 | 6.62 [5.98, 7.12]; n=19 |
| FD002/xgb/v1/internal_heldout | 100.00 [100.00, 100.00]; n=39 | 28.65 [20.09, 37.84]; n=39 | 0.84 [0.83, 0.84]; n=39 | 1.62 [1.57, 1.67]; n=39 | 82.40 [74.20, 91.94]; n=39 | 1.42 [1.34, 1.51]; n=39 |
| FD002/xgb/v1/grouped_oof | 100.00 [100.00, 100.00]; n=260 | 31.30 [28.21, 34.61]; n=260 | 0.84 [0.83, 0.84]; n=260 | 1.59 [1.56, 1.61]; n=260 | 82.72 [79.98, 85.62]; n=260 | 1.42 [1.38, 1.45]; n=260 |
| FD002/xgb/v1/official_test | 100.00 [100.00, 100.00]; n=65 | 33.33 [25.84, 41.04]; n=65 | 0.82 [0.81, 0.83]; n=65 | 1.51 [1.46, 1.56]; n=65 | 62.74 [56.51, 69.34]; n=65 | 1.16 [1.07, 1.25]; n=65 |
| FD002/xgb/v2/internal_heldout | 100.00 [100.00, 100.00]; n=39 | 28.65 [20.09, 37.84]; n=39 | 0.84 [0.83, 0.84]; n=39 | 1.70 [1.65, 1.75]; n=39 | 82.88 [73.55, 93.49]; n=39 | 1.43 [1.33, 1.54]; n=39 |
| FD002/xgb/v2/grouped_oof | 100.00 [100.00, 100.00]; n=260 | 31.30 [28.21, 34.61]; n=260 | 0.84 [0.83, 0.84]; n=260 | 1.64 [1.62, 1.66]; n=260 | 82.21 [79.24, 85.29]; n=260 | 1.40 [1.36, 1.44]; n=260 |
| FD002/xgb/v2/official_test | 100.00 [100.00, 100.00]; n=65 | 33.33 [25.84, 41.04]; n=65 | 0.82 [0.81, 0.83]; n=65 | 1.60 [1.55, 1.66]; n=65 | 59.19 [52.80, 65.94]; n=65 | 1.09 [1.00, 1.18]; n=65 |

### Target / measured / gap

The full report gives every target, measured estimate, CI, gap and comparison. The table below shows the primary XGBoost profiles. Gaps are percentage points except mean support. No threshold, D_max, bound, rate or solver setting was changed after these outcomes.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; primary XGBoost, both protocols. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | Metric | Design target | Measured (engine CI) | Gap |
|---|---|---|---|---|
| FD001/xgb/v1/internal_heldout | validity | 95.00 | 55.82 [49.00, 62.50]; n=15 | 39.18 |
| FD001/xgb/v1/internal_heldout | plausibility_all | 90.00 | 51.32 [44.39, 57.53]; n=15 | 38.68 |
| FD001/xgb/v1/internal_heldout | plausibility_returned | 90.00 | 51.32 [44.39, 57.53]; n=15 | 38.68 |
| FD001/xgb/v1/internal_heldout | risk_reduction | 60.00 | 59.82 [54.31, 65.03]; n=15 | 0.18 |
| FD001/xgb/v1/internal_heldout | sparsity_all | 3.00 | 2.91 [2.89, 2.93]; n=15 | 0.00 |
| FD001/xgb/v1/grouped_oof | validity | 95.00 | 52.52 [49.30, 55.64]; n=100 | 42.48 |
| FD001/xgb/v1/grouped_oof | plausibility_all | 90.00 | 48.70 [44.59, 52.61]; n=100 | 41.30 |
| FD001/xgb/v1/grouped_oof | plausibility_returned | 90.00 | 51.04 [47.46, 54.46]; n=100 | 38.96 |
| FD001/xgb/v1/grouped_oof | risk_reduction | 60.00 | 56.32 [53.56, 58.96]; n=100 | 3.68 |
| FD001/xgb/v1/grouped_oof | sparsity_all | 3.00 | 2.76 [2.67, 2.85]; n=100 | 0.00 |
| FD001/xgb/v1/official_test | validity | 95.00 | 89.31 [83.57, 94.36]; n=19 | 5.69 |
| FD001/xgb/v1/official_test | plausibility_all | 90.00 | 77.99 [70.42, 84.38]; n=19 | 12.01 |
| FD001/xgb/v1/official_test | plausibility_returned | 90.00 | 77.99 [70.42, 84.38]; n=19 | 12.01 |
| FD001/xgb/v1/official_test | risk_reduction | 60.00 | 74.24 [72.78, 75.80]; n=19 | 0.00 |
| FD001/xgb/v1/official_test | sparsity_all | 3.00 | 2.77 [2.64, 2.87]; n=19 | 0.00 |
| FD001/xgb/v2/internal_heldout | validity | 95.00 | 55.82 [49.00, 62.50]; n=15 | 39.18 |
| FD001/xgb/v2/internal_heldout | plausibility_all | 90.00 | 98.94 [98.09, 99.74]; n=15 | 0.00 |
| FD001/xgb/v2/internal_heldout | plausibility_returned | 90.00 | 98.94 [98.09, 99.74]; n=15 | 0.00 |
| FD001/xgb/v2/internal_heldout | risk_reduction | 60.00 | 59.99 [54.42, 65.20]; n=15 | 0.01 |
| FD001/xgb/v2/internal_heldout | sparsity_all | 3.00 | 2.87 [2.85, 2.90]; n=15 | 0.00 |
| FD001/xgb/v2/grouped_oof | validity | 95.00 | 52.52 [49.30, 55.64]; n=100 | 42.48 |
| FD001/xgb/v2/grouped_oof | plausibility_all | 90.00 | 98.07 [97.00, 98.92]; n=100 | 0.00 |
| FD001/xgb/v2/grouped_oof | plausibility_returned | 90.00 | 98.98 [98.45, 99.42]; n=100 | 0.00 |
| FD001/xgb/v2/grouped_oof | risk_reduction | 60.00 | 56.36 [53.63, 58.99]; n=100 | 3.64 |
| FD001/xgb/v2/grouped_oof | sparsity_all | 3.00 | 2.73 [2.64, 2.81]; n=100 | 0.00 |
| FD001/xgb/v2/official_test | validity | 95.00 | 89.31 [83.57, 94.36]; n=19 | 5.69 |
| FD001/xgb/v2/official_test | plausibility_all | 90.00 | 100.00 [100.00, 100.00]; n=19 | 0.00 |
| FD001/xgb/v2/official_test | plausibility_returned | 90.00 | 100.00 [100.00, 100.00]; n=19 | 0.00 |
| FD001/xgb/v2/official_test | risk_reduction | 60.00 | 74.12 [72.72, 75.57]; n=19 | 0.00 |
| FD001/xgb/v2/official_test | sparsity_all | 3.00 | 2.73 [2.61, 2.84]; n=19 | 0.00 |
| FD002/xgb/v1/internal_heldout | validity | 95.00 | 100.00 [100.00, 100.00]; n=39 | 0.00 |
| FD002/xgb/v1/internal_heldout | plausibility_all | 90.00 | 3.73 [2.72, 4.83]; n=39 | 86.27 |
| FD002/xgb/v1/internal_heldout | plausibility_returned | 90.00 | 3.73 [2.72, 4.83]; n=39 | 86.27 |
| FD002/xgb/v1/internal_heldout | risk_reduction | 60.00 | 83.81 [83.26, 84.32]; n=39 | 0.00 |
| FD002/xgb/v1/internal_heldout | sparsity_all | 3.00 | 1.62 [1.57, 1.67]; n=39 | 0.00 |
| FD002/xgb/v1/grouped_oof | validity | 95.00 | 100.00 [100.00, 100.00]; n=260 | 0.00 |
| FD002/xgb/v1/grouped_oof | plausibility_all | 90.00 | 3.13 [2.65, 3.64]; n=260 | 86.87 |
| FD002/xgb/v1/grouped_oof | plausibility_returned | 90.00 | 3.13 [2.65, 3.64]; n=260 | 86.87 |
| FD002/xgb/v1/grouped_oof | risk_reduction | 60.00 | 83.59 [83.31, 83.88]; n=260 | 0.00 |
| FD002/xgb/v1/grouped_oof | sparsity_all | 3.00 | 1.59 [1.56, 1.61]; n=260 | 0.00 |
| FD002/xgb/v1/official_test | validity | 95.00 | 100.00 [100.00, 100.00]; n=65 | 0.00 |
| FD002/xgb/v1/official_test | plausibility_all | 90.00 | 4.57 [3.06, 6.30]; n=65 | 85.43 |
| FD002/xgb/v1/official_test | plausibility_returned | 90.00 | 4.57 [3.06, 6.30]; n=65 | 85.43 |
| FD002/xgb/v1/official_test | risk_reduction | 60.00 | 82.13 [81.43, 82.76]; n=65 | 0.00 |
| FD002/xgb/v1/official_test | sparsity_all | 3.00 | 1.51 [1.46, 1.56]; n=65 | 0.00 |
| FD002/xgb/v2/internal_heldout | validity | 95.00 | 100.00 [100.00, 100.00]; n=39 | 0.00 |
| FD002/xgb/v2/internal_heldout | plausibility_all | 90.00 | 10.87 [8.57, 13.21]; n=39 | 79.13 |
| FD002/xgb/v2/internal_heldout | plausibility_returned | 90.00 | 10.87 [8.57, 13.21]; n=39 | 79.13 |
| FD002/xgb/v2/internal_heldout | risk_reduction | 60.00 | 83.94 [83.44, 84.39]; n=39 | 0.00 |
| FD002/xgb/v2/internal_heldout | sparsity_all | 3.00 | 1.70 [1.65, 1.75]; n=39 | 0.00 |
| FD002/xgb/v2/grouped_oof | validity | 95.00 | 100.00 [100.00, 100.00]; n=260 | 0.00 |
| FD002/xgb/v2/grouped_oof | plausibility_all | 90.00 | 10.96 [10.09, 11.78]; n=260 | 79.04 |
| FD002/xgb/v2/grouped_oof | plausibility_returned | 90.00 | 10.96 [10.09, 11.78]; n=260 | 79.04 |
| FD002/xgb/v2/grouped_oof | risk_reduction | 60.00 | 83.67 [83.38, 83.97]; n=260 | 0.00 |
| FD002/xgb/v2/grouped_oof | sparsity_all | 3.00 | 1.64 [1.62, 1.66]; n=260 | 0.00 |
| FD002/xgb/v2/official_test | validity | 95.00 | 100.00 [100.00, 100.00]; n=65 | 0.00 |
| FD002/xgb/v2/official_test | plausibility_all | 90.00 | 13.86 [11.25, 16.45]; n=65 | 76.14 |
| FD002/xgb/v2/official_test | plausibility_returned | 90.00 | 13.86 [11.25, 16.45]; n=65 | 76.14 |
| FD002/xgb/v2/official_test | risk_reduction | 60.00 | 82.08 [81.36, 82.75]; n=65 | 0.00 |
| FD002/xgb/v2/official_test | sparsity_all | 3.00 | 1.60 [1.55, 1.66]; n=65 | 0.00 |

### Gap diagnosis

Tier 1 alone can be driven low by proxy-sensor movement. Safe-model candidates can still lie outside the fitted operating distribution or violate the learned residual envelope. The next table exposes D_M and surrogate errors rather than inferring consistency from small changes. The frozen propagation preserves the original observed residual; a pre-existing Tier 4 violation can therefore survive every propagated candidate. This is a model/assumption limitation, not proof of a physically impossible intervention.

For the frozen LSTM, the highest validity estimate across the reported population/protocol groups is 0.00%. Its recourse preserves the genuine observed history prefix and changes only the latest timestep under the frozen sparse proxy constraints. This is an observed failure of this model/search/intervention setup to cross the risk gate; it does not certify global or trajectory infeasibility. Predictor selection remains based on predictive/calibration metrics and was not retuned on these recourse outcomes.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; fixed predictors. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | Surrogate MAE (engine CI) | Surrogate false-safe % (engine CI) | D_M p50 / p95 / p99 | Minimum coupling margin |
|---|---|---|---|---|
| FD001/lstm/v1/internal_heldout | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 5.725 / 7.217 / 7.699 | -5.691 |
| FD001/lstm/v1/grouped_oof | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 5.729 / 7.562 / 8.476 | -17.037 |
| FD001/lstm/v1/official_test | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 5.594 / 7.441 / 8.255 | -1.234 |
| FD001/lstm/v2/internal_heldout | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 5.725 / 7.217 / 7.699 | -5.691 |
| FD001/lstm/v2/grouped_oof | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 5.729 / 7.562 / 8.476 | -17.037 |
| FD001/lstm/v2/official_test | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 5.594 / 7.441 / 8.255 | -1.234 |
| FD001/mlp/v1/internal_heldout | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 5.275 / 7.171 / 7.708 | -5.691 |
| FD001/mlp/v1/grouped_oof | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 5.303 / 7.503 / 8.462 | -17.037 |
| FD001/mlp/v1/official_test | 0.00 [0.00, 0.00]; n=19 | 0.00 [0.00, 0.00]; n=19 | 4.782 / 6.647 / 7.695 | -1.234 |
| FD001/mlp/v2/internal_heldout | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 5.600 / 7.175 / 7.708 | -5.691 |
| FD001/mlp/v2/grouped_oof | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 5.631 / 7.505 / 8.462 | -17.037 |
| FD001/mlp/v2/official_test | 0.00 [0.00, 0.00]; n=19 | 0.00 [0.00, 0.00]; n=19 | 5.264 / 6.891 / 7.695 | -1.234 |
| FD001/xgb/v1/internal_heldout | 0.15 [0.13, 0.16]; n=15 | 1.06 [0.00, 2.45]; n=15 | 4.991 / 7.188 / 8.177 | -5.691 |
| FD001/xgb/v1/grouped_oof | 0.13 [0.12, 0.14]; n=100 | 0.71 [0.36, 1.13]; n=100 | 5.075 / 7.499 / 8.462 | -17.037 |
| FD001/xgb/v1/official_test | 0.15 [0.14, 0.17]; n=19 | 3.14 [1.12, 5.48]; n=19 | 4.698 / 6.239 / 7.112 | -1.234 |
| FD001/xgb/v2/internal_heldout | 0.14 [0.12, 0.15]; n=15 | 1.06 [0.00, 2.45]; n=15 | 5.467 / 7.159 / 8.002 | -5.691 |
| FD001/xgb/v2/grouped_oof | 0.13 [0.12, 0.13]; n=100 | 0.67 [0.35, 1.04]; n=100 | 5.486 / 7.499 / 8.429 | -17.037 |
| FD001/xgb/v2/official_test | 0.14 [0.13, 0.16]; n=19 | 3.14 [1.12, 5.48]; n=19 | 4.986 / 6.423 / 7.112 | -1.234 |
| FD002/xgb/v1/internal_heldout | 0.15 [0.14, 0.17]; n=39 | 0.00 [0.00, 0.00]; n=39 | 85.856 / 239.096 / 311.854 | -12.473 |
| FD002/xgb/v1/grouped_oof | 0.20 [0.19, 0.21]; n=260 | 0.00 [0.00, 0.00]; n=260 | 78.179 / 243.927 / 613.082 | -12.156 |
| FD002/xgb/v1/official_test | 0.12 [0.11, 0.14]; n=65 | 0.00 [0.00, 0.00]; n=65 | 64.186 / 237.903 / 311.968 | -6.003 |
| FD002/xgb/v2/internal_heldout | 0.14 [0.13, 0.15]; n=39 | 0.00 [0.00, 0.00]; n=39 | 85.139 / 240.789 / 311.854 | -12.473 |
| FD002/xgb/v2/grouped_oof | 0.19 [0.18, 0.20]; n=260 | 0.00 [0.00, 0.00]; n=260 | 74.974 / 244.251 / 611.599 | -12.156 |
| FD002/xgb/v2/official_test | 0.11 [0.10, 0.12]; n=65 | 0.00 [0.00, 0.00]; n=65 | 62.475 / 237.312 / 310.509 | -6.003 |

## THOROUGH and matched first-alert FAST results

THOROUGH uses the true first alert per engine, selected before development sampling. The matched FAST column uses first-alert records already present in the FAST cohort, so a change of mode is not confused with all-alert versus first-alert sampling.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: true first alerts per engine; FAST matched versus THOROUGH. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | First-alert queries / engines | FAST validity % | THOROUGH validity % | THOROUGH Tier 2 all % | THOROUGH joint % |
|---|---|---|---|---|---|
| FD001/lstm/v1/internal_heldout | 15 / 15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 13.33 [0.00, 33.33]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/grouped_oof | 100 / 100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 23.00 [16.00, 31.00]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v1/official_test | 16 / 16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 50.00 [25.00, 75.00]; n=16 | 0.00 [0.00, 0.00]; n=16 |
| FD001/lstm/v2/internal_heldout | 15 / 15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/grouped_oof | 100 / 100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 100.00 [100.00, 100.00]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v2/official_test | 16 / 16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 93.75 [81.25, 100.00]; n=16 | 0.00 [0.00, 0.00]; n=16 |
| FD001/mlp/v1/internal_heldout | 15 / 15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.33 [80.00, 100.00]; n=15 | 93.33 [80.00, 100.00]; n=15 |
| FD001/mlp/v1/grouped_oof | 100 / 100 | 100.00 [100.00, 100.00]; n=100 | 100.00 [100.00, 100.00]; n=100 | 91.00 [85.00, 96.00]; n=100 | 90.00 [84.00, 96.00]; n=100 |
| FD001/mlp/v1/official_test | 19 / 19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 |
| FD001/mlp/v2/internal_heldout | 15 / 15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.33 [80.00, 100.00]; n=15 |
| FD001/mlp/v2/grouped_oof | 100 / 100 | 100.00 [100.00, 100.00]; n=100 | 100.00 [100.00, 100.00]; n=100 | 100.00 [100.00, 100.00]; n=100 | 95.00 [90.00, 99.00]; n=100 |
| FD001/mlp/v2/official_test | 19 / 19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 |
| FD001/xgb/v1/internal_heldout | 15 / 15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 |
| FD001/xgb/v1/grouped_oof | 100 / 100 | 99.00 [97.00, 100.00]; n=100 | 99.00 [97.00, 100.00]; n=100 | 90.00 [84.00, 95.00]; n=100 | 90.00 [84.00, 95.00]; n=100 |
| FD001/xgb/v1/official_test | 19 / 19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 | 94.74 [84.21, 100.00]; n=19 | 94.74 [84.21, 100.00]; n=19 |
| FD001/xgb/v2/internal_heldout | 15 / 15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 |
| FD001/xgb/v2/grouped_oof | 100 / 100 | 99.00 [97.00, 100.00]; n=100 | 99.00 [97.00, 100.00]; n=100 | 100.00 [100.00, 100.00]; n=100 | 95.00 [90.00, 99.00]; n=100 |
| FD001/xgb/v2/official_test | 19 / 19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 | 100.00 [100.00, 100.00]; n=19 | 94.74 [84.21, 100.00]; n=19 |
| FD002/xgb/v1/internal_heldout | 39 / 39 | 100.00 [100.00, 100.00]; n=39 | 100.00 [100.00, 100.00]; n=39 | 15.38 [5.13, 28.21]; n=39 | 5.13 [0.00, 12.82]; n=39 |
| FD002/xgb/v1/grouped_oof | 260 / 260 | 100.00 [100.00, 100.00]; n=260 | 100.00 [100.00, 100.00]; n=260 | 8.46 [5.38, 11.92]; n=260 | 1.15 [0.00, 2.69]; n=260 |
| FD002/xgb/v1/official_test | 65 / 65 | 100.00 [100.00, 100.00]; n=65 | 100.00 [100.00, 100.00]; n=65 | 10.77 [4.62, 18.46]; n=65 | 3.08 [0.00, 7.69]; n=65 |
| FD002/xgb/v2/internal_heldout | 39 / 39 | 100.00 [100.00, 100.00]; n=39 | 100.00 [100.00, 100.00]; n=39 | 20.51 [7.69, 33.33]; n=39 | 2.56 [0.00, 7.69]; n=39 |
| FD002/xgb/v2/grouped_oof | 260 / 260 | 100.00 [100.00, 100.00]; n=260 | 100.00 [100.00, 100.00]; n=260 | 19.62 [15.00, 24.62]; n=260 | 1.92 [0.38, 3.85]; n=260 |
| FD002/xgb/v2/official_test | 65 / 65 | 100.00 [100.00, 100.00]; n=65 | 100.00 [100.00, 100.00]; n=65 | 20.00 [10.77, 29.23]; n=65 | 0.00 [0.00, 0.00]; n=65 |

## Funnel and triage

Counts below are query-seed observations. The cumulative funnel in the full report includes engine CIs at every step. The four independent tier rates above retain their own definitions.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; cumulative funnel. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | Alerts → returned → T1 → T2 → T3 → T4 → joint | REC / PART / ESC |
|---|---|---|
| FD001/lstm/v1/internal_heldout | 1750 → 1750 → 0 → 0 → 0 → 0 → 0 | 0 / 0 / 1750 |
| FD001/lstm/v1/grouped_oof | 12280 → 11635 → 0 → 0 → 0 → 0 → 0 | 0 / 235 / 12045 |
| FD001/lstm/v1/official_test | 690 → 690 → 0 → 0 → 0 → 0 → 0 | 0 / 0 / 690 |
| FD001/lstm/v2/internal_heldout | 1750 → 1750 → 0 → 0 → 0 → 0 → 0 | 0 / 0 / 1750 |
| FD001/lstm/v2/grouped_oof | 12280 → 11635 → 0 → 0 → 0 → 0 → 0 | 0 / 520 / 11760 |
| FD001/lstm/v2/official_test | 690 → 690 → 0 → 0 → 0 → 0 → 0 | 0 / 0 / 690 |
| FD001/mlp/v1/internal_heldout | 1885 → 1885 → 1025 → 725 → 725 → 720 → 720 | 720 / 75 / 1090 |
| FD001/mlp/v1/grouped_oof | 12360 → 11715 → 6185 → 4375 → 4375 → 4360 → 4360 | 4360 / 545 / 7455 |
| FD001/mlp/v1/official_test | 850 → 850 → 775 → 660 → 660 → 660 → 660 | 660 / 10 / 180 |
| FD001/mlp/v2/internal_heldout | 1885 → 1885 → 1025 → 1025 → 1025 → 965 → 965 | 965 / 430 / 490 |
| FD001/mlp/v2/grouped_oof | 12360 → 11715 → 6185 → 6165 → 6165 → 5930 → 5930 | 5930 / 2740 / 3690 |
| FD001/mlp/v2/official_test | 850 → 850 → 775 → 770 → 770 → 770 → 770 | 770 / 75 / 5 |
| FD001/xgb/v1/internal_heldout | 1890 → 1890 → 1055 → 800 → 800 → 795 → 795 | 795 / 110 / 985 |
| FD001/xgb/v1/grouped_oof | 11890 → 11245 → 6245 → 4775 → 4775 → 4745 → 4745 | 4745 / 610 / 6535 |
| FD001/xgb/v1/official_test | 795 → 795 → 710 → 610 → 610 → 610 → 610 | 610 / 10 / 175 |
| FD001/xgb/v2/internal_heldout | 1890 → 1890 → 1055 → 1055 → 1055 → 1000 → 1000 | 1000 / 465 / 425 |
| FD001/xgb/v2/grouped_oof | 11890 → 11245 → 6245 → 6240 → 6240 → 5995 → 5995 | 5995 / 2785 / 3110 |
| FD001/xgb/v2/official_test | 795 → 795 → 710 → 710 → 710 → 700 → 700 | 700 / 85 / 10 |
| FD002/xgb/v1/internal_heldout | 4555 → 4555 → 4555 → 170 → 170 → 15 → 15 | 15 / 0 / 4540 |
| FD002/xgb/v1/grouped_oof | 27955 → 27955 → 27955 → 875 → 875 → 20 → 20 | 20 / 0 / 27935 |
| FD002/xgb/v1/official_test | 3390 → 3390 → 3390 → 155 → 155 → 15 → 15 | 15 / 0 / 3375 |
| FD002/xgb/v2/internal_heldout | 4555 → 4555 → 4555 → 495 → 495 → 25 → 25 | 25 / 0 / 4530 |
| FD002/xgb/v2/grouped_oof | 27955 → 27955 → 27955 → 3065 → 3065 → 185 → 185 | 185 / 0 / 27770 |
| FD002/xgb/v2/official_test | 3390 → 3390 → 3390 → 470 → 470 → 40 → 40 | 40 / 0 / 3350 |

### Cumulative funnel engine intervals

These are cumulative shares of all query-seed observations, not independent tier pass rates.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; cumulative funnel. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | Returned % | Then T1 % | Then T2 % | Then T3 % | Then T4 % | Joint % |
|---|---|---|---|---|---|---|
| FD001/lstm/v1/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/grouped_oof | 94.75 [91.75, 97.36]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v1/official_test | 100.00 [100.00, 100.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 |
| FD001/lstm/v2/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/grouped_oof | 94.75 [91.75, 97.36]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v2/official_test | 100.00 [100.00, 100.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 | 0.00 [0.00, 0.00]; n=16 |
| FD001/mlp/v1/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 54.38 [47.28, 60.79]; n=15 | 38.46 [30.16, 45.48]; n=15 | 38.46 [30.16, 45.48]; n=15 | 38.20 [29.95, 45.17]; n=15 | 38.20 [29.95, 45.17]; n=15 |
| FD001/mlp/v1/grouped_oof | 94.78 [91.78, 97.40]; n=100 | 50.04 [47.08, 53.08]; n=100 | 35.40 [32.12, 38.79]; n=100 | 35.40 [32.12, 38.79]; n=100 | 35.28 [32.02, 38.62]; n=100 | 35.28 [32.02, 38.62]; n=100 |
| FD001/mlp/v1/official_test | 100.00 [100.00, 100.00]; n=19 | 91.18 [85.80, 96.20]; n=19 | 77.65 [69.13, 84.47]; n=19 | 77.65 [69.13, 84.47]; n=19 | 77.65 [69.13, 84.47]; n=19 | 77.65 [69.13, 84.47]; n=19 |
| FD001/mlp/v2/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 54.38 [47.28, 60.79]; n=15 | 54.38 [47.28, 60.79]; n=15 | 54.38 [47.28, 60.79]; n=15 | 51.19 [43.61, 58.30]; n=15 | 51.19 [43.61, 58.30]; n=15 |
| FD001/mlp/v2/grouped_oof | 94.78 [91.78, 97.40]; n=100 | 50.04 [47.08, 53.08]; n=100 | 49.88 [46.88, 52.93]; n=100 | 49.88 [46.88, 52.93]; n=100 | 47.98 [45.05, 51.03]; n=100 | 47.98 [45.05, 51.03]; n=100 |
| FD001/mlp/v2/official_test | 100.00 [100.00, 100.00]; n=19 | 91.18 [85.80, 96.20]; n=19 | 90.59 [85.26, 95.56]; n=19 | 90.59 [85.26, 95.56]; n=19 | 90.59 [85.26, 95.56]; n=19 | 90.59 [85.26, 95.56]; n=19 |
| FD001/xgb/v1/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 55.82 [49.00, 62.50]; n=15 | 42.33 [38.05, 46.52]; n=15 | 42.33 [38.05, 46.52]; n=15 | 42.06 [37.92, 46.15]; n=15 | 42.06 [37.92, 46.15]; n=15 |
| FD001/xgb/v1/grouped_oof | 94.58 [91.49, 97.28]; n=100 | 52.52 [49.30, 55.64]; n=100 | 40.16 [36.95, 43.21]; n=100 | 40.16 [36.95, 43.21]; n=100 | 39.91 [36.73, 42.91]; n=100 | 39.91 [36.73, 42.91]; n=100 |
| FD001/xgb/v1/official_test | 100.00 [100.00, 100.00]; n=19 | 89.31 [83.57, 94.36]; n=19 | 76.73 [68.75, 83.66]; n=19 | 76.73 [68.75, 83.66]; n=19 | 76.73 [68.75, 83.66]; n=19 | 76.73 [68.75, 83.66]; n=19 |
| FD001/xgb/v2/internal_heldout | 100.00 [100.00, 100.00]; n=15 | 55.82 [49.00, 62.50]; n=15 | 55.82 [49.00, 62.50]; n=15 | 55.82 [49.00, 62.50]; n=15 | 52.91 [46.13, 59.61]; n=15 | 52.91 [46.13, 59.61]; n=15 |
| FD001/xgb/v2/grouped_oof | 94.58 [91.49, 97.28]; n=100 | 52.52 [49.30, 55.64]; n=100 | 52.48 [49.23, 55.60]; n=100 | 52.48 [49.23, 55.60]; n=100 | 50.42 [47.29, 53.48]; n=100 | 50.42 [47.29, 53.48]; n=100 |
| FD001/xgb/v2/official_test | 100.00 [100.00, 100.00]; n=19 | 89.31 [83.57, 94.36]; n=19 | 89.31 [83.57, 94.36]; n=19 | 89.31 [83.57, 94.36]; n=19 | 88.05 [82.03, 93.20]; n=19 | 88.05 [82.03, 93.20]; n=19 |
| FD002/xgb/v1/internal_heldout | 100.00 [100.00, 100.00]; n=39 | 100.00 [100.00, 100.00]; n=39 | 3.73 [2.72, 4.83]; n=39 | 3.73 [2.72, 4.83]; n=39 | 0.33 [0.00, 0.73]; n=39 | 0.33 [0.00, 0.73]; n=39 |
| FD002/xgb/v1/grouped_oof | 100.00 [100.00, 100.00]; n=260 | 100.00 [100.00, 100.00]; n=260 | 3.13 [2.65, 3.64]; n=260 | 3.13 [2.65, 3.64]; n=260 | 0.07 [0.02, 0.15]; n=260 | 0.07 [0.02, 0.15]; n=260 |
| FD002/xgb/v1/official_test | 100.00 [100.00, 100.00]; n=65 | 100.00 [100.00, 100.00]; n=65 | 4.57 [3.06, 6.30]; n=65 | 4.57 [3.06, 6.30]; n=65 | 0.44 [0.00, 1.02]; n=65 | 0.44 [0.00, 1.02]; n=65 |
| FD002/xgb/v2/internal_heldout | 100.00 [100.00, 100.00]; n=39 | 100.00 [100.00, 100.00]; n=39 | 10.87 [8.57, 13.21]; n=39 | 10.87 [8.57, 13.21]; n=39 | 0.55 [0.11, 1.07]; n=39 | 0.55 [0.11, 1.07]; n=39 |
| FD002/xgb/v2/grouped_oof | 100.00 [100.00, 100.00]; n=260 | 100.00 [100.00, 100.00]; n=260 | 10.96 [10.09, 11.78]; n=260 | 10.96 [10.09, 11.78]; n=260 | 0.66 [0.45, 0.90]; n=260 | 0.66 [0.45, 0.90]; n=260 |
| FD002/xgb/v2/official_test | 100.00 [100.00, 100.00]; n=65 | 100.00 [100.00, 100.00]; n=65 | 13.86 [11.25, 16.45]; n=65 | 13.86 [11.25, 16.45]; n=65 | 1.18 [0.48, 1.96]; n=65 | 1.18 [0.48, 1.96]; n=65 |

### Risk, RUL and engine-life strata

Bins are left-closed/right-open and fixed in the committed study. The table reports observed strata only; an absent bin has no observations and is not a successful query. The last risk/life upper edge is the next representable float above 1, so exact 1.0 is included. RUL is a dataset label used for evaluation strata, never a predictor input or an extension claim.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; fixed risk/RUL/life bins. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | Stratum | Bin | Observations | Validity % | Tier 2 all % | Tier 3 % | Tier 4 % | Joint % |
|---|---|---|---|---|---|---|---|---|
| FD001/lstm/v1/internal_heldout | risk_before | [0.8, 0.85) | 95 | 0.00 [0.00, 0.00]; n=9 | 15.79 [0.00, 25.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v1/internal_heldout | risk_before | [0.85, 0.9) | 105 | 0.00 [0.00, 0.00]; n=12 | 23.81 [6.25, 39.13]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 0.00 [0.00, 0.00]; n=12 |
| FD001/lstm/v1/internal_heldout | risk_before | [0.9, 0.95) | 110 | 0.00 [0.00, 0.00]; n=15 | 36.36 [13.64, 60.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 86.36 [71.43, 96.55]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 1440 | 0.00 [0.00, 0.00]; n=15 | 20.83 [14.74, 27.56]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.79 [91.73, 97.39]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/internal_heldout | rul | [0.0, 11.0) | 825 | 0.00 [0.00, 0.00]; n=15 | 19.39 [12.73, 26.06]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.94 [90.30, 96.97]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/internal_heldout | rul | [11.0, 21.0) | 610 | 0.00 [0.00, 0.00]; n=15 | 26.23 [16.07, 37.23]; n=15 | 100.00 [100.00, 100.00]; n=15 | 95.08 [90.91, 98.35]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/internal_heldout | rul | [21.0, 31.0) | 265 | 0.00 [0.00, 0.00]; n=8 | 18.87 [6.97, 30.51]; n=8 | 100.00 [100.00, 100.00]; n=8 | 96.23 [89.58, 100.00]; n=8 | 0.00 [0.00, 0.00]; n=8 |
| FD001/lstm/v1/internal_heldout | rul | [31.0, 1000000.0) | 50 | 0.00 [0.00, 0.00]; n=1 | 20.00 [20.00, 20.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 |
| FD001/lstm/v1/internal_heldout | life_fraction | [0.8, 0.9) | 230 | 0.00 [0.00, 0.00]; n=9 | 28.26 [15.79, 38.30]; n=9 | 100.00 [100.00, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v1/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 1520 | 0.00 [0.00, 0.00]; n=15 | 20.72 [14.60, 27.27]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.08 [91.16, 96.56]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/grouped_oof | risk_before | [0.8, 0.85) | 600 | 0.00 [0.00, 0.00]; n=71 | 37.50 [28.70, 46.03]; n=71 | 100.00 [100.00, 100.00]; n=71 | 98.33 [95.71, 100.00]; n=71 | 0.00 [0.00, 0.00]; n=71 |
| FD001/lstm/v1/grouped_oof | risk_before | [0.85, 0.9) | 675 | 0.00 [0.00, 0.00]; n=79 | 34.07 [25.18, 42.86]; n=79 | 100.00 [100.00, 100.00]; n=79 | 97.78 [95.18, 100.00]; n=79 | 0.00 [0.00, 0.00]; n=79 |
| FD001/lstm/v1/grouped_oof | risk_before | [0.9, 0.95) | 1125 | 0.00 [0.00, 0.00]; n=97 | 24.44 [19.28, 29.76]; n=97 | 100.00 [100.00, 100.00]; n=97 | 94.67 [91.27, 97.52]; n=97 | 0.00 [0.00, 0.00]; n=97 |
| FD001/lstm/v1/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 9880 | 0.00 [0.00, 0.00]; n=100 | 21.05 [17.50, 24.85]; n=100 | 94.13 [90.39, 97.41]; n=100 | 90.84 [88.31, 93.07]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v1/grouped_oof | rul | [0.0, 11.0) | 5485 | 0.00 [0.00, 0.00]; n=100 | 22.79 [18.96, 26.97]; n=100 | 91.07 [85.48, 95.99]; n=100 | 88.33 [84.78, 91.59]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v1/grouped_oof | rul | [11.0, 21.0) | 4030 | 0.00 [0.00, 0.00]; n=97 | 23.33 [19.21, 27.53]; n=97 | 97.77 [95.59, 99.40]; n=97 | 93.92 [91.87, 95.76]; n=97 | 0.00 [0.00, 0.00]; n=97 |
| FD001/lstm/v1/grouped_oof | rul | [21.0, 31.0) | 1960 | 0.00 [0.00, 0.00]; n=60 | 18.37 [13.69, 23.49]; n=60 | 100.00 [100.00, 100.00]; n=60 | 95.66 [93.90, 97.40]; n=60 | 0.00 [0.00, 0.00]; n=60 |
| FD001/lstm/v1/grouped_oof | rul | [31.0, 1000000.0) | 805 | 0.00 [0.00, 0.00]; n=24 | 32.30 [23.12, 41.56]; n=24 | 100.00 [100.00, 100.00]; n=24 | 97.52 [95.08, 99.39]; n=24 | 0.00 [0.00, 0.00]; n=24 |
| FD001/lstm/v1/grouped_oof | life_fraction | [0.7, 0.8) | 45 | 0.00 [0.00, 0.00]; n=4 | 44.44 [0.00, 57.14]; n=4 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 0.00 [0.00, 0.00]; n=4 |
| FD001/lstm/v1/grouped_oof | life_fraction | [0.8, 0.9) | 2420 | 0.00 [0.00, 0.00]; n=67 | 24.59 [19.48, 29.53]; n=67 | 100.00 [100.00, 100.00]; n=67 | 97.11 [95.18, 98.77]; n=67 | 0.00 [0.00, 0.00]; n=67 |
| FD001/lstm/v1/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 9815 | 0.00 [0.00, 0.00]; n=100 | 22.36 [18.74, 26.15]; n=100 | 94.09 [90.34, 97.37]; n=100 | 90.63 [88.10, 92.93]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v1/official_test | risk_before | [0.8, 0.85) | 80 | 0.00 [0.00, 0.00]; n=10 | 43.75 [15.38, 68.75]; n=10 | 100.00 [100.00, 100.00]; n=10 | 93.75 [76.92, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 |
| FD001/lstm/v1/official_test | risk_before | [0.85, 0.9) | 145 | 0.00 [0.00, 0.00]; n=16 | 51.72 [34.78, 71.43]; n=16 | 100.00 [100.00, 100.00]; n=16 | 100.00 [100.00, 100.00]; n=16 | 0.00 [0.00, 0.00]; n=16 |
| FD001/lstm/v1/official_test | risk_before | [0.9, 0.95) | 125 | 0.00 [0.00, 0.00]; n=13 | 20.00 [5.26, 33.36]; n=13 | 100.00 [100.00, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 0.00 [0.00, 0.00]; n=13 |
| FD001/lstm/v1/official_test | risk_before | [0.95, 1.0000000000000002) | 340 | 0.00 [0.00, 0.00]; n=12 | 23.53 [7.27, 40.63]; n=12 | 100.00 [100.00, 100.00]; n=12 | 98.53 [94.64, 100.00]; n=12 | 0.00 [0.00, 0.00]; n=12 |
| FD001/lstm/v1/official_test | rul | [0.0, 11.0) | 85 | 0.00 [0.00, 0.00]; n=7 | 35.29 [13.33, 56.25]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 0.00 [0.00, 0.00]; n=7 |
| FD001/lstm/v1/official_test | rul | [11.0, 21.0) | 395 | 0.00 [0.00, 0.00]; n=15 | 30.38 [19.64, 41.47]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v1/official_test | rul | [21.0, 31.0) | 195 | 0.00 [0.00, 0.00]; n=9 | 28.21 [11.63, 51.85]; n=9 | 100.00 [100.00, 100.00]; n=9 | 94.87 [87.80, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v1/official_test | rul | [31.0, 1000000.0) | 15 | 0.00 [0.00, 0.00]; n=2 | 66.67 [50.00, 100.00]; n=2 | 100.00 [100.00, 100.00]; n=2 | 100.00 [100.00, 100.00]; n=2 | 0.00 [0.00, 0.00]; n=2 |
| FD001/lstm/v1/official_test | life_fraction | [0.7, 0.8) | 5 | 0.00 [0.00, 0.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 |
| FD001/lstm/v1/official_test | life_fraction | [0.8, 0.9) | 225 | 0.00 [0.00, 0.00]; n=9 | 24.44 [9.30, 39.39]; n=9 | 100.00 [100.00, 100.00]; n=9 | 95.56 [85.71, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v1/official_test | life_fraction | [0.9, 1.0000000000000002) | 460 | 0.00 [0.00, 0.00]; n=14 | 33.70 [18.64, 44.71]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 0.00 [0.00, 0.00]; n=14 |
| FD001/lstm/v2/internal_heldout | risk_before | [0.8, 0.85) | 95 | 0.00 [0.00, 0.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v2/internal_heldout | risk_before | [0.85, 0.9) | 105 | 0.00 [0.00, 0.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 0.00 [0.00, 0.00]; n=12 |
| FD001/lstm/v2/internal_heldout | risk_before | [0.9, 0.95) | 110 | 0.00 [0.00, 0.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 86.36 [71.43, 96.55]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 1440 | 0.00 [0.00, 0.00]; n=15 | 99.31 [98.31, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.79 [91.73, 97.39]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/internal_heldout | rul | [0.0, 11.0) | 825 | 0.00 [0.00, 0.00]; n=15 | 99.39 [98.18, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.94 [90.30, 96.97]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/internal_heldout | rul | [11.0, 21.0) | 610 | 0.00 [0.00, 0.00]; n=15 | 99.18 [97.41, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 95.08 [90.91, 98.35]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/internal_heldout | rul | [21.0, 31.0) | 265 | 0.00 [0.00, 0.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 96.23 [89.58, 100.00]; n=8 | 0.00 [0.00, 0.00]; n=8 |
| FD001/lstm/v2/internal_heldout | rul | [31.0, 1000000.0) | 50 | 0.00 [0.00, 0.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 |
| FD001/lstm/v2/internal_heldout | life_fraction | [0.8, 0.9) | 230 | 0.00 [0.00, 0.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v2/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 1520 | 0.00 [0.00, 0.00]; n=15 | 99.34 [98.38, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.08 [91.16, 96.56]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/grouped_oof | risk_before | [0.8, 0.85) | 600 | 0.00 [0.00, 0.00]; n=71 | 100.00 [100.00, 100.00]; n=71 | 100.00 [100.00, 100.00]; n=71 | 98.33 [95.71, 100.00]; n=71 | 0.00 [0.00, 0.00]; n=71 |
| FD001/lstm/v2/grouped_oof | risk_before | [0.85, 0.9) | 675 | 0.00 [0.00, 0.00]; n=79 | 100.00 [100.00, 100.00]; n=79 | 100.00 [100.00, 100.00]; n=79 | 97.78 [95.18, 100.00]; n=79 | 0.00 [0.00, 0.00]; n=79 |
| FD001/lstm/v2/grouped_oof | risk_before | [0.9, 0.95) | 1125 | 0.00 [0.00, 0.00]; n=97 | 99.56 [98.50, 100.00]; n=97 | 100.00 [100.00, 100.00]; n=97 | 94.67 [91.27, 97.52]; n=97 | 0.00 [0.00, 0.00]; n=97 |
| FD001/lstm/v2/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 9880 | 0.00 [0.00, 0.00]; n=100 | 97.17 [95.75, 98.41]; n=100 | 94.13 [90.39, 97.41]; n=100 | 90.84 [88.31, 93.07]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v2/grouped_oof | rul | [0.0, 11.0) | 5485 | 0.00 [0.00, 0.00]; n=100 | 96.72 [94.62, 98.35]; n=100 | 91.07 [85.48, 95.99]; n=100 | 88.33 [84.78, 91.59]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v2/grouped_oof | rul | [11.0, 21.0) | 4030 | 0.00 [0.00, 0.00]; n=97 | 98.26 [97.13, 99.26]; n=97 | 97.77 [95.59, 99.40]; n=97 | 93.92 [91.87, 95.76]; n=97 | 0.00 [0.00, 0.00]; n=97 |
| FD001/lstm/v2/grouped_oof | rul | [21.0, 31.0) | 1960 | 0.00 [0.00, 0.00]; n=60 | 98.47 [96.95, 99.71]; n=60 | 100.00 [100.00, 100.00]; n=60 | 95.66 [93.90, 97.40]; n=60 | 0.00 [0.00, 0.00]; n=60 |
| FD001/lstm/v2/grouped_oof | rul | [31.0, 1000000.0) | 805 | 0.00 [0.00, 0.00]; n=24 | 99.38 [98.15, 100.00]; n=24 | 100.00 [100.00, 100.00]; n=24 | 97.52 [95.08, 99.39]; n=24 | 0.00 [0.00, 0.00]; n=24 |
| FD001/lstm/v2/grouped_oof | life_fraction | [0.7, 0.8) | 45 | 0.00 [0.00, 0.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 0.00 [0.00, 0.00]; n=4 |
| FD001/lstm/v2/grouped_oof | life_fraction | [0.8, 0.9) | 2420 | 0.00 [0.00, 0.00]; n=67 | 98.76 [97.44, 99.77]; n=67 | 100.00 [100.00, 100.00]; n=67 | 97.11 [95.18, 98.77]; n=67 | 0.00 [0.00, 0.00]; n=67 |
| FD001/lstm/v2/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 9815 | 0.00 [0.00, 0.00]; n=100 | 97.40 [96.14, 98.53]; n=100 | 94.09 [90.34, 97.37]; n=100 | 90.63 [88.10, 92.93]; n=100 | 0.00 [0.00, 0.00]; n=100 |
| FD001/lstm/v2/official_test | risk_before | [0.8, 0.85) | 80 | 0.00 [0.00, 0.00]; n=10 | 93.75 [76.92, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 93.75 [76.92, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 |
| FD001/lstm/v2/official_test | risk_before | [0.85, 0.9) | 145 | 0.00 [0.00, 0.00]; n=16 | 100.00 [100.00, 100.00]; n=16 | 100.00 [100.00, 100.00]; n=16 | 100.00 [100.00, 100.00]; n=16 | 0.00 [0.00, 0.00]; n=16 |
| FD001/lstm/v2/official_test | risk_before | [0.9, 0.95) | 125 | 0.00 [0.00, 0.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 0.00 [0.00, 0.00]; n=13 |
| FD001/lstm/v2/official_test | risk_before | [0.95, 1.0000000000000002) | 340 | 0.00 [0.00, 0.00]; n=12 | 97.06 [91.23, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 98.53 [94.64, 100.00]; n=12 | 0.00 [0.00, 0.00]; n=12 |
| FD001/lstm/v2/official_test | rul | [0.0, 11.0) | 85 | 0.00 [0.00, 0.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 0.00 [0.00, 0.00]; n=7 |
| FD001/lstm/v2/official_test | rul | [11.0, 21.0) | 395 | 0.00 [0.00, 0.00]; n=15 | 98.73 [95.35, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD001/lstm/v2/official_test | rul | [21.0, 31.0) | 195 | 0.00 [0.00, 0.00]; n=9 | 94.87 [84.00, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 94.87 [87.80, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v2/official_test | rul | [31.0, 1000000.0) | 15 | 0.00 [0.00, 0.00]; n=2 | 100.00 [100.00, 100.00]; n=2 | 100.00 [100.00, 100.00]; n=2 | 100.00 [100.00, 100.00]; n=2 | 0.00 [0.00, 0.00]; n=2 |
| FD001/lstm/v2/official_test | life_fraction | [0.7, 0.8) | 5 | 0.00 [0.00, 0.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 |
| FD001/lstm/v2/official_test | life_fraction | [0.8, 0.9) | 225 | 0.00 [0.00, 0.00]; n=9 | 95.56 [84.62, 100.00]; n=9 | 100.00 [100.00, 100.00]; n=9 | 95.56 [85.71, 100.00]; n=9 | 0.00 [0.00, 0.00]; n=9 |
| FD001/lstm/v2/official_test | life_fraction | [0.9, 1.0000000000000002) | 460 | 0.00 [0.00, 0.00]; n=14 | 98.91 [95.71, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 0.00 [0.00, 0.00]; n=14 |
| FD001/mlp/v1/internal_heldout | risk_before | [0.8, 0.85) | 110 | 100.00 [100.00, 100.00]; n=12 | 81.82 [68.75, 94.44]; n=12 | 100.00 [100.00, 100.00]; n=12 | 90.91 [78.95, 100.00]; n=12 | 81.82 [68.75, 94.44]; n=12 |
| FD001/mlp/v1/internal_heldout | risk_before | [0.85, 0.9) | 140 | 100.00 [100.00, 100.00]; n=13 | 92.86 [80.95, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 96.43 [85.71, 100.00]; n=13 | 92.86 [80.95, 100.00]; n=13 |
| FD001/mlp/v1/internal_heldout | risk_before | [0.9, 0.95) | 280 | 100.00 [100.00, 100.00]; n=15 | 82.14 [62.96, 95.46]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.64 [87.93, 100.00]; n=15 | 82.14 [62.96, 95.46]; n=15 |
| FD001/mlp/v1/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 1355 | 36.53 [27.65, 45.13]; n=15 | 32.10 [21.97, 42.28]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.46 [92.23, 96.63]; n=15 | 19.93 [12.12, 27.52]; n=15 |
| FD001/mlp/v1/internal_heldout | rul | [0.0, 11.0) | 820 | 20.12 [12.19, 28.22]; n=15 | 23.17 [14.02, 32.52]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.90 [90.30, 96.95]; n=15 | 9.15 [4.27, 14.21]; n=15 |
| FD001/mlp/v1/internal_heldout | rul | [11.0, 21.0) | 650 | 69.23 [58.57, 81.60]; n=15 | 56.15 [40.74, 72.31]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.62 [90.08, 98.43]; n=15 | 49.23 [35.46, 65.30]; n=15 |
| FD001/mlp/v1/internal_heldout | rul | [21.0, 31.0) | 330 | 98.48 [95.31, 100.00]; n=12 | 75.76 [63.15, 84.91]; n=12 | 100.00 [100.00, 100.00]; n=12 | 93.94 [88.14, 98.46]; n=12 | 74.24 [58.49, 84.91]; n=12 |
| FD001/mlp/v1/internal_heldout | rul | [31.0, 1000000.0) | 85 | 100.00 [100.00, 100.00]; n=4 | 94.12 [87.50, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 94.12 [87.50, 100.00]; n=4 |
| FD001/mlp/v1/internal_heldout | life_fraction | [0.8, 0.9) | 320 | 100.00 [100.00, 100.00]; n=12 | 92.19 [87.01, 97.62]; n=12 | 100.00 [100.00, 100.00]; n=12 | 98.44 [96.05, 100.00]; n=12 | 92.19 [87.01, 97.62]; n=12 |
| FD001/mlp/v1/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 1565 | 45.05 [37.63, 52.56]; n=15 | 37.70 [26.79, 48.12]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.61 [90.68, 96.13]; n=15 | 27.16 [18.65, 35.06]; n=15 |
| FD001/mlp/v1/grouped_oof | risk_before | [0.8, 0.85) | 860 | 100.00 [100.00, 100.00]; n=80 | 90.12 [85.55, 94.38]; n=80 | 100.00 [100.00, 100.00]; n=80 | 95.93 [92.90, 98.75]; n=80 | 88.95 [84.18, 93.57]; n=80 |
| FD001/mlp/v1/grouped_oof | risk_before | [0.85, 0.9) | 1015 | 100.00 [100.00, 100.00]; n=84 | 85.71 [80.10, 90.86]; n=84 | 100.00 [100.00, 100.00]; n=84 | 95.57 [92.72, 98.43]; n=84 | 85.22 [79.57, 90.36]; n=84 |
| FD001/mlp/v1/grouped_oof | risk_before | [0.9, 0.95) | 1790 | 97.21 [94.80, 99.12]; n=97 | 75.70 [69.65, 81.06]; n=97 | 100.00 [100.00, 100.00]; n=97 | 97.21 [95.26, 98.88]; n=97 | 75.70 [69.65, 81.06]; n=97 |
| FD001/mlp/v1/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 8695 | 29.56 [25.83, 33.51]; n=100 | 29.10 [24.43, 34.37]; n=100 | 93.33 [89.15, 97.02]; n=100 | 90.17 [87.44, 92.62]; n=100 | 15.81 [12.70, 19.30]; n=100 |
| FD001/mlp/v1/grouped_oof | rul | [0.0, 11.0) | 5465 | 19.12 [15.24, 23.31]; n=100 | 27.45 [23.08, 32.48]; n=100 | 91.03 [85.43, 95.98]; n=100 | 88.29 [84.73, 91.57]; n=100 | 10.43 [7.75, 13.47]; n=100 |
| FD001/mlp/v1/grouped_oof | rul | [11.0, 21.0) | 4145 | 61.16 [55.16, 67.59]; n=100 | 45.24 [38.52, 52.12]; n=100 | 97.83 [95.82, 99.41]; n=100 | 93.61 [91.56, 95.47]; n=100 | 39.69 [33.15, 46.44]; n=100 |
| FD001/mlp/v1/grouped_oof | rul | [21.0, 31.0) | 1950 | 92.82 [88.61, 96.56]; n=77 | 73.08 [65.94, 80.11]; n=77 | 100.00 [100.00, 100.00]; n=77 | 96.41 [94.64, 97.92]; n=77 | 72.56 [65.43, 79.59]; n=77 |
| FD001/mlp/v1/grouped_oof | rul | [31.0, 1000000.0) | 800 | 99.38 [98.24, 100.00]; n=31 | 91.25 [85.94, 96.75]; n=31 | 100.00 [100.00, 100.00]; n=31 | 98.75 [97.35, 100.00]; n=31 | 91.25 [85.94, 96.75]; n=31 |
| FD001/mlp/v1/grouped_oof | life_fraction | [0.7, 0.8) | 80 | 100.00 [100.00, 100.00]; n=8 | 93.75 [85.71, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 93.75 [85.71, 100.00]; n=8 |
| FD001/mlp/v1/grouped_oof | life_fraction | [0.8, 0.9) | 2400 | 96.67 [94.74, 98.36]; n=79 | 82.71 [78.03, 87.07]; n=79 | 100.00 [100.00, 100.00]; n=79 | 97.92 [96.55, 99.10]; n=79 | 81.88 [77.15, 86.32]; n=79 |
| FD001/mlp/v1/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 9880 | 38.31 [34.27, 42.65]; n=100 | 35.12 [30.03, 40.38]; n=100 | 94.13 [90.39, 97.39]; n=100 | 90.54 [88.02, 92.81]; n=100 | 23.48 [19.70, 27.55]; n=100 |
| FD001/mlp/v1/official_test | risk_before | [0.8, 0.85) | 135 | 100.00 [100.00, 100.00]; n=15 | 96.30 [86.96, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 96.30 [86.96, 100.00]; n=15 |
| FD001/mlp/v1/official_test | risk_before | [0.85, 0.9) | 170 | 100.00 [100.00, 100.00]; n=14 | 97.06 [91.89, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 97.06 [91.89, 100.00]; n=14 |
| FD001/mlp/v1/official_test | risk_before | [0.9, 0.95) | 220 | 100.00 [100.00, 100.00]; n=18 | 88.64 [75.00, 98.04]; n=18 | 100.00 [100.00, 100.00]; n=18 | 100.00 [100.00, 100.00]; n=18 | 88.64 [75.00, 98.04]; n=18 |
| FD001/mlp/v1/official_test | risk_before | [0.95, 1.0000000000000002) | 325 | 76.92 [65.08, 89.09]; n=16 | 55.38 [41.27, 68.18]; n=16 | 100.00 [100.00, 100.00]; n=16 | 98.46 [94.87, 100.00]; n=16 | 52.31 [37.50, 66.67]; n=16 |
| FD001/mlp/v1/official_test | rul | [0.0, 11.0) | 85 | 52.94 [21.73, 87.50]; n=7 | 52.94 [31.25, 78.95]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 41.18 [13.33, 71.43]; n=7 |
| FD001/mlp/v1/official_test | rul | [11.0, 21.0) | 405 | 91.36 [83.33, 97.62]; n=15 | 74.07 [62.33, 83.15]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 74.07 [62.33, 83.15]; n=15 |
| FD001/mlp/v1/official_test | rul | [21.0, 31.0) | 275 | 100.00 [100.00, 100.00]; n=14 | 87.27 [74.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 98.18 [94.34, 100.00]; n=14 | 87.27 [74.00, 100.00]; n=14 |
| FD001/mlp/v1/official_test | rul | [31.0, 1000000.0) | 85 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 |
| FD001/mlp/v1/official_test | life_fraction | [0.7, 0.8) | 15 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 |
| FD001/mlp/v1/official_test | life_fraction | [0.8, 0.9) | 350 | 98.57 [94.59, 100.00]; n=14 | 88.57 [78.12, 96.74]; n=14 | 100.00 [100.00, 100.00]; n=14 | 98.57 [95.45, 100.00]; n=14 | 88.57 [78.12, 96.74]; n=14 |
| FD001/mlp/v1/official_test | life_fraction | [0.9, 1.0000000000000002) | 485 | 85.57 [78.38, 93.10]; n=14 | 71.13 [61.76, 78.10]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 69.07 [59.30, 76.60]; n=14 |
| FD001/mlp/v2/internal_heldout | risk_before | [0.8, 0.85) | 110 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 90.91 [78.95, 100.00]; n=12 | 90.91 [78.95, 100.00]; n=12 |
| FD001/mlp/v2/internal_heldout | risk_before | [0.85, 0.9) | 140 | 100.00 [100.00, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 96.43 [85.71, 100.00]; n=13 | 96.43 [85.71, 100.00]; n=13 |
| FD001/mlp/v2/internal_heldout | risk_before | [0.9, 0.95) | 280 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.64 [87.93, 100.00]; n=15 | 94.64 [87.93, 100.00]; n=15 |
| FD001/mlp/v2/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 1355 | 36.53 [27.65, 45.13]; n=15 | 99.26 [98.17, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.46 [92.23, 96.63]; n=15 | 34.32 [25.63, 42.86]; n=15 |
| FD001/mlp/v2/internal_heldout | rul | [0.0, 11.0) | 820 | 20.12 [12.19, 28.22]; n=15 | 99.39 [98.16, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.90 [90.30, 96.95]; n=15 | 18.90 [11.58, 26.67]; n=15 |
| FD001/mlp/v2/internal_heldout | rul | [11.0, 21.0) | 650 | 69.23 [58.57, 81.60]; n=15 | 99.23 [97.62, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.62 [90.08, 98.43]; n=15 | 64.62 [53.17, 77.31]; n=15 |
| FD001/mlp/v2/internal_heldout | rul | [21.0, 31.0) | 330 | 98.48 [95.31, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 93.94 [88.14, 98.46]; n=12 | 92.42 [85.00, 98.25]; n=12 |
| FD001/mlp/v2/internal_heldout | rul | [31.0, 1000000.0) | 85 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 | 100.00 [100.00, 100.00]; n=4 |
| FD001/mlp/v2/internal_heldout | life_fraction | [0.8, 0.9) | 320 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 98.44 [96.05, 100.00]; n=12 | 98.44 [96.05, 100.00]; n=12 |
| FD001/mlp/v2/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 1565 | 45.05 [37.63, 52.56]; n=15 | 99.36 [98.43, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.61 [90.68, 96.13]; n=15 | 41.53 [33.43, 49.69]; n=15 |
| FD001/mlp/v2/grouped_oof | risk_before | [0.8, 0.85) | 860 | 100.00 [100.00, 100.00]; n=80 | 100.00 [100.00, 100.00]; n=80 | 100.00 [100.00, 100.00]; n=80 | 95.93 [92.90, 98.75]; n=80 | 95.93 [92.90, 98.75]; n=80 |
| FD001/mlp/v2/grouped_oof | risk_before | [0.85, 0.9) | 1015 | 100.00 [100.00, 100.00]; n=84 | 100.00 [100.00, 100.00]; n=84 | 100.00 [100.00, 100.00]; n=84 | 95.57 [92.72, 98.43]; n=84 | 95.57 [92.72, 98.43]; n=84 |
| FD001/mlp/v2/grouped_oof | risk_before | [0.9, 0.95) | 1790 | 97.21 [94.80, 99.12]; n=97 | 99.72 [99.11, 100.00]; n=97 | 100.00 [100.00, 100.00]; n=97 | 97.21 [95.26, 98.88]; n=97 | 94.41 [91.56, 97.04]; n=97 |
| FD001/mlp/v2/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 8695 | 29.56 [25.83, 33.51]; n=100 | 97.12 [95.61, 98.44]; n=100 | 93.33 [89.15, 97.02]; n=100 | 90.17 [87.44, 92.62]; n=100 | 28.12 [24.47, 31.95]; n=100 |
| FD001/mlp/v2/grouped_oof | rul | [0.0, 11.0) | 5465 | 19.12 [15.24, 23.31]; n=100 | 96.89 [94.70, 98.54]; n=100 | 91.03 [85.43, 95.98]; n=100 | 88.29 [84.73, 91.57]; n=100 | 18.39 [14.68, 22.50]; n=100 |
| FD001/mlp/v2/grouped_oof | rul | [11.0, 21.0) | 4145 | 61.16 [55.16, 67.59]; n=100 | 98.19 [96.99, 99.26]; n=100 | 97.83 [95.82, 99.41]; n=100 | 93.61 [91.56, 95.47]; n=100 | 57.66 [51.64, 63.94]; n=100 |
| FD001/mlp/v2/grouped_oof | rul | [21.0, 31.0) | 1950 | 92.82 [88.61, 96.56]; n=77 | 99.49 [98.71, 100.00]; n=77 | 100.00 [100.00, 100.00]; n=77 | 96.41 [94.64, 97.92]; n=77 | 89.49 [85.23, 93.56]; n=77 |
| FD001/mlp/v2/grouped_oof | rul | [31.0, 1000000.0) | 800 | 99.38 [98.24, 100.00]; n=31 | 100.00 [100.00, 100.00]; n=31 | 100.00 [100.00, 100.00]; n=31 | 98.75 [97.35, 100.00]; n=31 | 98.75 [97.35, 100.00]; n=31 |
| FD001/mlp/v2/grouped_oof | life_fraction | [0.7, 0.8) | 80 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 |
| FD001/mlp/v2/grouped_oof | life_fraction | [0.8, 0.9) | 2400 | 96.67 [94.74, 98.36]; n=79 | 99.58 [98.93, 100.00]; n=79 | 100.00 [100.00, 100.00]; n=79 | 97.92 [96.55, 99.10]; n=79 | 95.00 [92.69, 97.08]; n=79 |
| FD001/mlp/v2/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 9880 | 38.31 [34.27, 42.65]; n=100 | 97.52 [96.15, 98.68]; n=100 | 94.13 [90.39, 97.39]; n=100 | 90.54 [88.02, 92.81]; n=100 | 36.13 [32.15, 40.27]; n=100 |
| FD001/mlp/v2/official_test | risk_before | [0.8, 0.85) | 135 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 |
| FD001/mlp/v2/official_test | risk_before | [0.85, 0.9) | 170 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 |
| FD001/mlp/v2/official_test | risk_before | [0.9, 0.95) | 220 | 100.00 [100.00, 100.00]; n=18 | 100.00 [100.00, 100.00]; n=18 | 100.00 [100.00, 100.00]; n=18 | 100.00 [100.00, 100.00]; n=18 | 100.00 [100.00, 100.00]; n=18 |
| FD001/mlp/v2/official_test | risk_before | [0.95, 1.0000000000000002) | 325 | 76.92 [65.08, 89.09]; n=16 | 98.46 [94.87, 100.00]; n=16 | 100.00 [100.00, 100.00]; n=16 | 98.46 [94.87, 100.00]; n=16 | 75.38 [64.15, 87.69]; n=16 |
| FD001/mlp/v2/official_test | rul | [0.0, 11.0) | 85 | 52.94 [21.73, 87.50]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 52.94 [21.73, 87.50]; n=7 |
| FD001/mlp/v2/official_test | rul | [11.0, 21.0) | 405 | 91.36 [83.33, 97.62]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 91.36 [83.33, 97.62]; n=15 |
| FD001/mlp/v2/official_test | rul | [21.0, 31.0) | 275 | 100.00 [100.00, 100.00]; n=14 | 98.18 [94.34, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 98.18 [94.34, 100.00]; n=14 | 98.18 [94.34, 100.00]; n=14 |
| FD001/mlp/v2/official_test | rul | [31.0, 1000000.0) | 85 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 |
| FD001/mlp/v2/official_test | life_fraction | [0.7, 0.8) | 15 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 |
| FD001/mlp/v2/official_test | life_fraction | [0.8, 0.9) | 350 | 98.57 [94.59, 100.00]; n=14 | 98.57 [95.45, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 98.57 [95.45, 100.00]; n=14 | 97.14 [92.59, 100.00]; n=14 |
| FD001/mlp/v2/official_test | life_fraction | [0.9, 1.0000000000000002) | 485 | 85.57 [78.38, 93.10]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 85.57 [78.38, 93.10]; n=14 |
| FD001/xgb/v1/internal_heldout | risk_before | [0.8, 0.85) | 95 | 100.00 [100.00, 100.00]; n=12 | 84.21 [64.71, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 89.47 [72.22, 100.00]; n=12 | 84.21 [64.71, 100.00]; n=12 |
| FD001/xgb/v1/internal_heldout | risk_before | [0.85, 0.9) | 150 | 100.00 [100.00, 100.00]; n=14 | 93.33 [86.84, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 93.33 [86.84, 100.00]; n=14 |
| FD001/xgb/v1/internal_heldout | risk_before | [0.9, 0.95) | 280 | 98.21 [94.23, 100.00]; n=15 | 89.29 [82.26, 95.75]; n=15 | 100.00 [100.00, 100.00]; n=15 | 96.43 [90.91, 100.00]; n=15 | 89.29 [82.26, 95.75]; n=15 |
| FD001/xgb/v1/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 1365 | 39.19 [32.29, 46.60]; n=15 | 36.63 [28.57, 44.68]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.77 [91.47, 96.03]; n=15 | 23.81 [19.23, 28.62]; n=15 |
| FD001/xgb/v1/internal_heldout | rul | [0.0, 11.0) | 820 | 24.39 [15.24, 33.74]; n=15 | 25.61 [15.85, 35.19]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.90 [90.30, 96.97]; n=15 | 10.37 [4.85, 16.56]; n=15 |
| FD001/xgb/v1/internal_heldout | rul | [11.0, 21.0) | 635 | 67.72 [54.92, 81.08]; n=15 | 61.42 [48.69, 74.14]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.49 [89.84, 98.36]; n=15 | 53.54 [42.19, 66.00]; n=15 |
| FD001/xgb/v1/internal_heldout | rul | [21.0, 31.0) | 355 | 97.18 [91.67, 100.00]; n=13 | 83.10 [77.77, 88.89]; n=13 | 100.00 [100.00, 100.00]; n=13 | 94.37 [89.23, 98.63]; n=13 | 83.10 [77.77, 88.89]; n=13 |
| FD001/xgb/v1/internal_heldout | rul | [31.0, 1000000.0) | 80 | 100.00 [100.00, 100.00]; n=5 | 93.75 [85.71, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 93.75 [85.71, 100.00]; n=5 |
| FD001/xgb/v1/internal_heldout | life_fraction | [0.8, 0.9) | 340 | 100.00 [100.00, 100.00]; n=12 | 92.65 [87.32, 98.21]; n=12 | 100.00 [100.00, 100.00]; n=12 | 98.53 [95.94, 100.00]; n=12 | 92.65 [87.32, 98.21]; n=12 |
| FD001/xgb/v1/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 1550 | 46.13 [37.50, 54.68]; n=15 | 42.26 [32.26, 51.59]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.55 [90.64, 96.10]; n=15 | 30.97 [24.54, 37.38]; n=15 |
| FD001/xgb/v1/grouped_oof | risk_before | [0.8, 0.85) | 810 | 98.77 [95.92, 100.00]; n=75 | 92.59 [87.50, 96.41]; n=75 | 100.00 [100.00, 100.00]; n=75 | 95.68 [92.09, 98.25]; n=75 | 92.59 [87.50, 96.41]; n=75 |
| FD001/xgb/v1/grouped_oof | risk_before | [0.85, 0.9) | 1040 | 97.60 [93.37, 100.00]; n=89 | 85.58 [78.61, 91.43]; n=89 | 99.04 [96.97, 100.00]; n=89 | 93.75 [90.34, 96.74]; n=89 | 84.13 [76.96, 90.23]; n=89 |
| FD001/xgb/v1/grouped_oof | risk_before | [0.9, 0.95) | 1730 | 91.33 [85.33, 95.66]; n=95 | 77.75 [71.39, 83.55]; n=95 | 98.84 [96.35, 100.00]; n=95 | 94.80 [92.09, 97.30]; n=95 | 76.30 [69.69, 82.10]; n=95 |
| FD001/xgb/v1/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 8310 | 34.30 [30.39, 38.44]; n=100 | 33.75 [29.07, 38.63]; n=100 | 93.38 [89.36, 97.09]; n=100 | 90.37 [87.59, 92.88]; n=100 | 21.66 [17.98, 25.35]; n=100 |
| FD001/xgb/v1/grouped_oof | rul | [0.0, 11.0) | 5440 | 23.71 [19.20, 28.23]; n=100 | 28.86 [23.97, 34.04]; n=100 | 90.99 [85.35, 95.96]; n=100 | 88.24 [84.66, 91.52]; n=100 | 14.34 [10.92, 18.04]; n=100 |
| FD001/xgb/v1/grouped_oof | rul | [11.0, 21.0) | 3940 | 65.99 [59.37, 72.34]; n=99 | 54.70 [47.64, 61.48]; n=99 | 97.72 [95.61, 99.47]; n=99 | 93.65 [91.63, 95.54]; n=99 | 48.73 [41.92, 55.26]; n=99 |
| FD001/xgb/v1/grouped_oof | rul | [21.0, 31.0) | 1800 | 91.67 [86.61, 96.52]; n=67 | 77.50 [71.05, 83.97]; n=67 | 100.00 [100.00, 100.00]; n=67 | 95.56 [93.75, 97.41]; n=67 | 76.39 [69.74, 83.09]; n=67 |
| FD001/xgb/v1/grouped_oof | rul | [31.0, 1000000.0) | 710 | 99.30 [97.95, 100.00]; n=29 | 94.37 [89.57, 98.10]; n=29 | 100.00 [100.00, 100.00]; n=29 | 97.18 [93.08, 100.00]; n=29 | 94.37 [89.57, 98.10]; n=29 |
| FD001/xgb/v1/grouped_oof | life_fraction | [0.0, 0.7) | 15 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 |
| FD001/xgb/v1/grouped_oof | life_fraction | [0.7, 0.8) | 90 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 |
| FD001/xgb/v1/grouped_oof | life_fraction | [0.8, 0.9) | 2155 | 95.13 [91.75, 98.10]; n=70 | 84.69 [79.27, 89.76]; n=70 | 100.00 [100.00, 100.00]; n=70 | 96.75 [94.68, 98.54]; n=70 | 83.76 [77.80, 89.30]; n=70 |
| FD001/xgb/v1/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 9630 | 42.47 [38.20, 46.91]; n=100 | 40.08 [35.13, 45.00]; n=100 | 93.98 [90.19, 97.31]; n=100 | 90.45 [87.88, 92.73]; n=100 | 29.44 [25.54, 33.40]; n=100 |
| FD001/xgb/v1/official_test | risk_before | [0.8, 0.85) | 85 | 100.00 [100.00, 100.00]; n=8 | 94.12 [76.92, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 94.12 [76.92, 100.00]; n=8 | 94.12 [76.92, 100.00]; n=8 |
| FD001/xgb/v1/official_test | risk_before | [0.85, 0.9) | 165 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 |
| FD001/xgb/v1/official_test | risk_before | [0.9, 0.95) | 195 | 100.00 [100.00, 100.00]; n=17 | 84.62 [73.17, 95.00]; n=17 | 100.00 [100.00, 100.00]; n=17 | 100.00 [100.00, 100.00]; n=17 | 84.62 [73.17, 95.00]; n=17 |
| FD001/xgb/v1/official_test | risk_before | [0.95, 1.0000000000000002) | 350 | 75.71 [64.71, 86.27]; n=15 | 60.00 [46.48, 72.60]; n=15 | 100.00 [100.00, 100.00]; n=15 | 98.57 [95.24, 100.00]; n=15 | 57.14 [42.53, 71.02]; n=15 |
| FD001/xgb/v1/official_test | rul | [0.0, 11.0) | 85 | 64.71 [33.30, 94.44]; n=7 | 52.94 [31.25, 78.95]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 41.18 [13.33, 71.43]; n=7 |
| FD001/xgb/v1/official_test | rul | [11.0, 21.0) | 370 | 86.49 [77.19, 94.45]; n=15 | 74.32 [62.50, 83.05]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 74.32 [62.50, 83.05]; n=15 |
| FD001/xgb/v1/official_test | rul | [21.0, 31.0) | 265 | 98.11 [94.20, 100.00]; n=14 | 86.79 [74.60, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 98.11 [94.20, 100.00]; n=14 | 86.79 [74.60, 100.00]; n=14 |
| FD001/xgb/v1/official_test | rul | [31.0, 1000000.0) | 75 | 100.00 [100.00, 100.00]; n=7 | 93.33 [70.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 93.33 [70.00, 100.00]; n=7 | 93.33 [70.00, 100.00]; n=7 |
| FD001/xgb/v1/official_test | life_fraction | [0.7, 0.8) | 15 | 100.00 [100.00, 100.00]; n=3 | 66.67 [0.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 66.67 [0.00, 100.00]; n=3 | 66.67 [0.00, 100.00]; n=3 |
| FD001/xgb/v1/official_test | life_fraction | [0.8, 0.9) | 330 | 96.97 [92.86, 100.00]; n=15 | 87.88 [79.31, 96.55]; n=15 | 100.00 [100.00, 100.00]; n=15 | 98.48 [95.40, 100.00]; n=15 | 87.88 [79.31, 96.55]; n=15 |
| FD001/xgb/v1/official_test | life_fraction | [0.9, 1.0000000000000002) | 450 | 83.33 [75.41, 91.51]; n=14 | 71.11 [60.32, 78.10]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 68.89 [58.00, 76.83]; n=14 |
| FD001/xgb/v2/internal_heldout | risk_before | [0.8, 0.85) | 95 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 89.47 [72.22, 100.00]; n=12 | 89.47 [72.22, 100.00]; n=12 |
| FD001/xgb/v2/internal_heldout | risk_before | [0.85, 0.9) | 150 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 |
| FD001/xgb/v2/internal_heldout | risk_before | [0.9, 0.95) | 280 | 98.21 [94.23, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 96.43 [90.91, 100.00]; n=15 | 96.43 [90.91, 100.00]; n=15 |
| FD001/xgb/v2/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 1365 | 39.19 [32.29, 46.60]; n=15 | 98.53 [97.40, 99.62]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.77 [91.47, 96.03]; n=15 | 36.26 [29.84, 43.21]; n=15 |
| FD001/xgb/v2/internal_heldout | rul | [0.0, 11.0) | 820 | 24.39 [15.24, 33.74]; n=15 | 98.17 [96.32, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.90 [90.30, 96.97]; n=15 | 22.56 [14.11, 31.68]; n=15 |
| FD001/xgb/v2/internal_heldout | rul | [11.0, 21.0) | 635 | 67.72 [54.92, 81.08]; n=15 | 99.21 [97.62, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 94.49 [89.84, 98.36]; n=15 | 64.57 [51.56, 77.44]; n=15 |
| FD001/xgb/v2/internal_heldout | rul | [21.0, 31.0) | 355 | 97.18 [91.67, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 100.00 [100.00, 100.00]; n=13 | 94.37 [89.23, 98.63]; n=13 | 91.55 [85.45, 97.10]; n=13 |
| FD001/xgb/v2/internal_heldout | rul | [31.0, 1000000.0) | 80 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 | 100.00 [100.00, 100.00]; n=5 |
| FD001/xgb/v2/internal_heldout | life_fraction | [0.8, 0.9) | 340 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 100.00 [100.00, 100.00]; n=12 | 98.53 [95.94, 100.00]; n=12 | 98.53 [95.94, 100.00]; n=12 |
| FD001/xgb/v2/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 1550 | 46.13 [37.50, 54.68]; n=15 | 98.71 [97.67, 99.67]; n=15 | 100.00 [100.00, 100.00]; n=15 | 93.55 [90.64, 96.10]; n=15 | 42.90 [34.17, 51.61]; n=15 |
| FD001/xgb/v2/grouped_oof | risk_before | [0.8, 0.85) | 810 | 98.77 [95.92, 100.00]; n=75 | 100.00 [100.00, 100.00]; n=75 | 100.00 [100.00, 100.00]; n=75 | 95.68 [92.09, 98.25]; n=75 | 94.44 [90.12, 97.78]; n=75 |
| FD001/xgb/v2/grouped_oof | risk_before | [0.85, 0.9) | 1040 | 97.60 [93.37, 100.00]; n=89 | 100.00 [100.00, 100.00]; n=89 | 99.04 [96.97, 100.00]; n=89 | 93.75 [90.34, 96.74]; n=89 | 92.31 [86.60, 96.67]; n=89 |
| FD001/xgb/v2/grouped_oof | risk_before | [0.9, 0.95) | 1730 | 91.33 [85.33, 95.66]; n=95 | 100.00 [100.00, 100.00]; n=95 | 98.84 [96.35, 100.00]; n=95 | 94.80 [92.09, 97.30]; n=95 | 87.57 [81.59, 92.49]; n=95 |
| FD001/xgb/v2/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 8310 | 34.30 [30.39, 38.44]; n=100 | 97.23 [95.69, 98.46]; n=100 | 93.38 [89.36, 97.09]; n=100 | 90.37 [87.59, 92.88]; n=100 | 33.15 [29.32, 37.21]; n=100 |
| FD001/xgb/v2/grouped_oof | rul | [0.0, 11.0) | 5440 | 23.71 [19.20, 28.23]; n=100 | 96.51 [94.31, 98.17]; n=100 | 90.99 [85.35, 95.96]; n=100 | 88.24 [84.66, 91.52]; n=100 | 22.79 [18.41, 27.20]; n=100 |
| FD001/xgb/v2/grouped_oof | rul | [11.0, 21.0) | 3940 | 65.99 [59.37, 72.34]; n=99 | 98.98 [98.11, 99.63]; n=99 | 97.72 [95.61, 99.47]; n=99 | 93.65 [91.63, 95.54]; n=99 | 63.07 [56.80, 69.08]; n=99 |
| FD001/xgb/v2/grouped_oof | rul | [21.0, 31.0) | 1800 | 91.67 [86.61, 96.52]; n=67 | 100.00 [100.00, 100.00]; n=67 | 100.00 [100.00, 100.00]; n=67 | 95.56 [93.75, 97.41]; n=67 | 87.78 [82.68, 92.60]; n=67 |
| FD001/xgb/v2/grouped_oof | rul | [31.0, 1000000.0) | 710 | 99.30 [97.95, 100.00]; n=29 | 100.00 [100.00, 100.00]; n=29 | 100.00 [100.00, 100.00]; n=29 | 97.18 [93.08, 100.00]; n=29 | 97.18 [93.08, 100.00]; n=29 |
| FD001/xgb/v2/grouped_oof | life_fraction | [0.0, 0.7) | 15 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 |
| FD001/xgb/v2/grouped_oof | life_fraction | [0.7, 0.8) | 90 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 |
| FD001/xgb/v2/grouped_oof | life_fraction | [0.8, 0.9) | 2155 | 95.13 [91.75, 98.10]; n=70 | 100.00 [100.00, 100.00]; n=70 | 100.00 [100.00, 100.00]; n=70 | 96.75 [94.68, 98.54]; n=70 | 92.81 [89.08, 96.35]; n=70 |
| FD001/xgb/v2/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 9630 | 42.47 [38.20, 46.91]; n=100 | 97.61 [96.31, 98.67]; n=100 | 93.98 [90.19, 97.31]; n=100 | 90.45 [87.88, 92.73]; n=100 | 40.39 [36.23, 44.64]; n=100 |
| FD001/xgb/v2/official_test | risk_before | [0.8, 0.85) | 85 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 100.00 [100.00, 100.00]; n=8 | 94.12 [76.92, 100.00]; n=8 | 94.12 [76.92, 100.00]; n=8 |
| FD001/xgb/v2/official_test | risk_before | [0.85, 0.9) | 165 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 |
| FD001/xgb/v2/official_test | risk_before | [0.9, 0.95) | 195 | 100.00 [100.00, 100.00]; n=17 | 100.00 [100.00, 100.00]; n=17 | 100.00 [100.00, 100.00]; n=17 | 100.00 [100.00, 100.00]; n=17 | 100.00 [100.00, 100.00]; n=17 |
| FD001/xgb/v2/official_test | risk_before | [0.95, 1.0000000000000002) | 350 | 75.71 [64.71, 86.27]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 98.57 [95.24, 100.00]; n=15 | 74.29 [63.23, 85.71]; n=15 |
| FD001/xgb/v2/official_test | rul | [0.0, 11.0) | 85 | 64.71 [33.30, 94.44]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 64.71 [33.30, 94.44]; n=7 |
| FD001/xgb/v2/official_test | rul | [11.0, 21.0) | 370 | 86.49 [77.19, 94.45]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 86.49 [77.19, 94.45]; n=15 |
| FD001/xgb/v2/official_test | rul | [21.0, 31.0) | 265 | 98.11 [94.20, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 98.11 [94.20, 100.00]; n=14 | 96.23 [88.40, 100.00]; n=14 |
| FD001/xgb/v2/official_test | rul | [31.0, 1000000.0) | 75 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 100.00 [100.00, 100.00]; n=7 | 93.33 [70.00, 100.00]; n=7 | 93.33 [70.00, 100.00]; n=7 |
| FD001/xgb/v2/official_test | life_fraction | [0.7, 0.8) | 15 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 100.00 [100.00, 100.00]; n=3 | 66.67 [0.00, 100.00]; n=3 | 66.67 [0.00, 100.00]; n=3 |
| FD001/xgb/v2/official_test | life_fraction | [0.8, 0.9) | 330 | 96.97 [92.86, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 100.00 [100.00, 100.00]; n=15 | 98.48 [95.40, 100.00]; n=15 | 95.45 [88.89, 100.00]; n=15 |
| FD001/xgb/v2/official_test | life_fraction | [0.9, 1.0000000000000002) | 450 | 83.33 [75.41, 91.51]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 100.00 [100.00, 100.00]; n=14 | 83.33 [75.41, 91.51]; n=14 |
| FD002/xgb/v1/internal_heldout | risk_before | [0.8, 0.85) | 515 | 100.00 [100.00, 100.00]; n=36 | 6.80 [2.78, 11.21]; n=36 | 100.00 [100.00, 100.00]; n=36 | 44.66 [31.37, 56.96]; n=36 | 1.94 [0.00, 5.00]; n=36 |
| FD002/xgb/v1/internal_heldout | risk_before | [0.85, 0.9) | 580 | 100.00 [100.00, 100.00]; n=36 | 6.03 [2.13, 10.40]; n=36 | 100.00 [100.00, 100.00]; n=36 | 49.14 [35.71, 61.29]; n=36 | 0.00 [0.00, 0.00]; n=36 |
| FD002/xgb/v1/internal_heldout | risk_before | [0.9, 0.95) | 1190 | 100.00 [100.00, 100.00]; n=39 | 5.46 [2.29, 9.29]; n=39 | 100.00 [100.00, 100.00]; n=39 | 29.41 [19.18, 40.38]; n=39 | 0.42 [0.00, 1.36]; n=39 |
| FD002/xgb/v1/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 2270 | 100.00 [100.00, 100.00]; n=39 | 1.54 [0.55, 2.75]; n=39 | 100.00 [100.00, 100.00]; n=39 | 19.38 [11.84, 27.71]; n=39 | 0.00 [0.00, 0.00]; n=39 |
| FD002/xgb/v1/internal_heldout | rul | [0.0, 11.0) | 2095 | 100.00 [100.00, 100.00]; n=39 | 3.10 [1.67, 4.57]; n=39 | 100.00 [100.00, 100.00]; n=39 | 22.91 [15.11, 30.72]; n=39 | 0.00 [0.00, 0.00]; n=39 |
| FD002/xgb/v1/internal_heldout | rul | [11.0, 21.0) | 1470 | 100.00 [100.00, 100.00]; n=39 | 2.72 [1.08, 4.53]; n=39 | 100.00 [100.00, 100.00]; n=39 | 32.99 [22.11, 44.70]; n=39 | 0.34 [0.00, 1.14]; n=39 |
| FD002/xgb/v1/internal_heldout | rul | [21.0, 31.0) | 690 | 100.00 [100.00, 100.00]; n=29 | 4.35 [1.45, 8.18]; n=29 | 100.00 [100.00, 100.00]; n=29 | 34.78 [21.62, 49.57]; n=29 | 1.45 [0.00, 3.88]; n=29 |
| FD002/xgb/v1/internal_heldout | rul | [31.0, 1000000.0) | 300 | 100.00 [100.00, 100.00]; n=15 | 11.67 [5.56, 19.57]; n=15 | 100.00 [100.00, 100.00]; n=15 | 33.33 [14.06, 58.33]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD002/xgb/v1/internal_heldout | life_fraction | [0.7, 0.8) | 30 | 100.00 [100.00, 100.00]; n=6 | 33.33 [0.00, 66.67]; n=6 | 100.00 [100.00, 100.00]; n=6 | 50.00 [16.67, 83.33]; n=6 | 0.00 [0.00, 0.00]; n=6 |
| FD002/xgb/v1/internal_heldout | life_fraction | [0.8, 0.9) | 755 | 100.00 [100.00, 100.00]; n=33 | 6.62 [3.18, 10.60]; n=33 | 100.00 [100.00, 100.00]; n=33 | 46.36 [31.52, 59.86]; n=33 | 1.32 [0.00, 3.64]; n=33 |
| FD002/xgb/v1/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 3770 | 100.00 [100.00, 100.00]; n=39 | 2.92 [1.90, 4.00]; n=39 | 100.00 [100.00, 100.00]; n=39 | 24.93 [16.98, 33.70]; n=39 | 0.13 [0.00, 0.43]; n=39 |
| FD002/xgb/v1/grouped_oof | risk_before | [0.8, 0.85) | 3175 | 100.00 [100.00, 100.00]; n=227 | 6.77 [4.86, 8.93]; n=227 | 100.00 [100.00, 100.00]; n=227 | 49.29 [44.15, 54.15]; n=227 | 0.47 [0.00, 1.04]; n=227 |
| FD002/xgb/v1/grouped_oof | risk_before | [0.85, 0.9) | 4545 | 100.00 [100.00, 100.00]; n=249 | 4.73 [3.31, 6.25]; n=249 | 100.00 [100.00, 100.00]; n=249 | 46.31 [42.40, 50.31]; n=249 | 0.11 [0.00, 0.34]; n=249 |
| FD002/xgb/v1/grouped_oof | risk_before | [0.9, 0.95) | 8090 | 100.00 [100.00, 100.00]; n=258 | 2.72 [1.95, 3.55]; n=258 | 100.00 [100.00, 100.00]; n=258 | 36.28 [32.55, 40.36]; n=258 | 0.00 [0.00, 0.00]; n=258 |
| FD002/xgb/v1/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 12145 | 100.00 [100.00, 100.00]; n=257 | 1.85 [1.21, 2.57]; n=257 | 100.00 [100.00, 100.00]; n=257 | 17.66 [14.75, 20.59]; n=257 | 0.00 [0.00, 0.00]; n=257 |
| FD002/xgb/v1/grouped_oof | rul | [0.0, 11.0) | 13835 | 100.00 [100.00, 100.00]; n=260 | 2.06 [1.48, 2.65]; n=260 | 100.00 [100.00, 100.00]; n=260 | 24.54 [21.73, 27.64]; n=260 | 0.04 [0.00, 0.11]; n=260 |
| FD002/xgb/v1/grouped_oof | rul | [11.0, 21.0) | 9015 | 100.00 [100.00, 100.00]; n=258 | 3.88 [3.05, 4.82]; n=258 | 100.00 [100.00, 100.00]; n=258 | 34.72 [30.63, 38.70]; n=258 | 0.06 [0.00, 0.17]; n=258 |
| FD002/xgb/v1/grouped_oof | rul | [21.0, 31.0) | 3665 | 100.00 [100.00, 100.00]; n=185 | 3.68 [2.51, 4.91]; n=185 | 100.00 [100.00, 100.00]; n=185 | 40.93 [34.91, 47.08]; n=185 | 0.14 [0.00, 0.43]; n=185 |
| FD002/xgb/v1/grouped_oof | rul | [31.0, 1000000.0) | 1440 | 100.00 [100.00, 100.00]; n=86 | 7.29 [4.49, 10.55]; n=86 | 100.00 [100.00, 100.00]; n=86 | 50.35 [40.89, 59.04]; n=86 | 0.35 [0.00, 1.20]; n=86 |
| FD002/xgb/v1/grouped_oof | life_fraction | [0.7, 0.8) | 145 | 100.00 [100.00, 100.00]; n=22 | 10.34 [0.00, 21.88]; n=22 | 100.00 [100.00, 100.00]; n=22 | 72.41 [58.82, 86.21]; n=22 | 0.00 [0.00, 0.00]; n=22 |
| FD002/xgb/v1/grouped_oof | life_fraction | [0.8, 0.9) | 4210 | 100.00 [100.00, 100.00]; n=201 | 5.82 [4.26, 7.48]; n=201 | 100.00 [100.00, 100.00]; n=201 | 50.48 [44.94, 55.63]; n=201 | 0.24 [0.00, 0.62]; n=201 |
| FD002/xgb/v1/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 23600 | 100.00 [100.00, 100.00]; n=260 | 2.61 [2.12, 3.11]; n=260 | 100.00 [100.00, 100.00]; n=260 | 27.63 [24.68, 30.95]; n=260 | 0.04 [0.00, 0.11]; n=260 |
| FD002/xgb/v1/official_test | risk_before | [0.8, 0.85) | 650 | 100.00 [100.00, 100.00]; n=56 | 6.15 [2.50, 10.40]; n=56 | 100.00 [100.00, 100.00]; n=56 | 41.54 [30.95, 51.82]; n=56 | 0.00 [0.00, 0.00]; n=56 |
| FD002/xgb/v1/official_test | risk_before | [0.85, 0.9) | 760 | 100.00 [100.00, 100.00]; n=55 | 7.89 [4.14, 12.03]; n=55 | 100.00 [100.00, 100.00]; n=55 | 46.71 [36.58, 56.25]; n=55 | 1.97 [0.00, 4.43]; n=55 |
| FD002/xgb/v1/official_test | risk_before | [0.9, 0.95) | 1150 | 100.00 [100.00, 100.00]; n=57 | 3.48 [1.06, 6.55]; n=57 | 100.00 [100.00, 100.00]; n=57 | 33.48 [24.42, 42.40]; n=57 | 0.00 [0.00, 0.00]; n=57 |
| FD002/xgb/v1/official_test | risk_before | [0.95, 1.0000000000000002) | 830 | 100.00 [100.00, 100.00]; n=41 | 1.81 [0.00, 4.00]; n=41 | 100.00 [100.00, 100.00]; n=41 | 14.46 [9.09, 20.83]; n=41 | 0.00 [0.00, 0.00]; n=41 |
| FD002/xgb/v1/official_test | rul | [0.0, 11.0) | 320 | 100.00 [100.00, 100.00]; n=22 | 0.00 [0.00, 0.00]; n=22 | 100.00 [100.00, 100.00]; n=22 | 21.88 [11.43, 34.72]; n=22 | 0.00 [0.00, 0.00]; n=22 |
| FD002/xgb/v1/official_test | rul | [11.0, 21.0) | 1530 | 100.00 [100.00, 100.00]; n=50 | 4.90 [2.80, 7.23]; n=50 | 100.00 [100.00, 100.00]; n=50 | 27.78 [19.73, 36.17]; n=50 | 0.00 [0.00, 0.00]; n=50 |
| FD002/xgb/v1/official_test | rul | [21.0, 31.0) | 1005 | 100.00 [100.00, 100.00]; n=47 | 4.48 [2.03, 7.14]; n=47 | 100.00 [100.00, 100.00]; n=47 | 35.82 [25.74, 46.28]; n=47 | 0.50 [0.00, 1.61]; n=47 |
| FD002/xgb/v1/official_test | rul | [31.0, 1000000.0) | 535 | 100.00 [100.00, 100.00]; n=25 | 6.54 [2.54, 11.96]; n=25 | 100.00 [100.00, 100.00]; n=25 | 51.40 [33.33, 70.97]; n=25 | 1.87 [0.00, 5.16]; n=25 |
| FD002/xgb/v1/official_test | life_fraction | [0.0, 0.7) | 5 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 |
| FD002/xgb/v1/official_test | life_fraction | [0.7, 0.8) | 75 | 100.00 [100.00, 100.00]; n=10 | 6.67 [0.00, 23.08]; n=10 | 100.00 [100.00, 100.00]; n=10 | 86.67 [63.64, 100.00]; n=10 | 6.67 [0.00, 23.08]; n=10 |
| FD002/xgb/v1/official_test | life_fraction | [0.8, 0.9) | 1390 | 100.00 [100.00, 100.00]; n=57 | 6.47 [3.86, 9.42]; n=57 | 100.00 [100.00, 100.00]; n=57 | 43.17 [32.67, 53.20]; n=57 | 0.72 [0.00, 1.85]; n=57 |
| FD002/xgb/v1/official_test | life_fraction | [0.9, 1.0000000000000002) | 1920 | 100.00 [100.00, 100.00]; n=53 | 3.12 [1.67, 4.80]; n=53 | 100.00 [100.00, 100.00]; n=53 | 23.96 [17.19, 31.85]; n=53 | 0.00 [0.00, 0.00]; n=53 |
| FD002/xgb/v2/internal_heldout | risk_before | [0.8, 0.85) | 515 | 100.00 [100.00, 100.00]; n=36 | 14.56 [8.74, 20.41]; n=36 | 100.00 [100.00, 100.00]; n=36 | 44.66 [31.37, 56.96]; n=36 | 3.88 [0.86, 7.84]; n=36 |
| FD002/xgb/v2/internal_heldout | risk_before | [0.85, 0.9) | 580 | 100.00 [100.00, 100.00]; n=36 | 16.38 [9.24, 23.64]; n=36 | 100.00 [100.00, 100.00]; n=36 | 49.14 [35.71, 61.29]; n=36 | 0.00 [0.00, 0.00]; n=36 |
| FD002/xgb/v2/internal_heldout | risk_before | [0.9, 0.95) | 1190 | 100.00 [100.00, 100.00]; n=39 | 14.71 [8.95, 20.85]; n=39 | 100.00 [100.00, 100.00]; n=39 | 29.41 [19.18, 40.38]; n=39 | 0.42 [0.00, 1.42]; n=39 |
| FD002/xgb/v2/internal_heldout | risk_before | [0.95, 1.0000000000000002) | 2270 | 100.00 [100.00, 100.00]; n=39 | 6.61 [4.04, 9.38]; n=39 | 100.00 [100.00, 100.00]; n=39 | 19.38 [11.84, 27.71]; n=39 | 0.00 [0.00, 0.00]; n=39 |
| FD002/xgb/v2/internal_heldout | rul | [0.0, 11.0) | 2095 | 100.00 [100.00, 100.00]; n=39 | 9.31 [6.19, 12.50]; n=39 | 100.00 [100.00, 100.00]; n=39 | 22.91 [15.11, 30.72]; n=39 | 0.00 [0.00, 0.00]; n=39 |
| FD002/xgb/v2/internal_heldout | rul | [11.0, 21.0) | 1470 | 100.00 [100.00, 100.00]; n=39 | 12.24 [8.88, 15.58]; n=39 | 100.00 [100.00, 100.00]; n=39 | 32.99 [22.11, 44.70]; n=39 | 1.36 [0.32, 2.89]; n=39 |
| FD002/xgb/v2/internal_heldout | rul | [21.0, 31.0) | 690 | 100.00 [100.00, 100.00]; n=29 | 10.87 [6.87, 15.75]; n=29 | 100.00 [100.00, 100.00]; n=29 | 34.78 [21.62, 49.57]; n=29 | 0.72 [0.00, 2.46]; n=29 |
| FD002/xgb/v2/internal_heldout | rul | [31.0, 1000000.0) | 300 | 100.00 [100.00, 100.00]; n=15 | 15.00 [7.55, 26.19]; n=15 | 100.00 [100.00, 100.00]; n=15 | 33.33 [14.06, 58.33]; n=15 | 0.00 [0.00, 0.00]; n=15 |
| FD002/xgb/v2/internal_heldout | life_fraction | [0.7, 0.8) | 30 | 100.00 [100.00, 100.00]; n=6 | 33.33 [0.00, 66.67]; n=6 | 100.00 [100.00, 100.00]; n=6 | 50.00 [16.67, 83.33]; n=6 | 0.00 [0.00, 0.00]; n=6 |
| FD002/xgb/v2/internal_heldout | life_fraction | [0.8, 0.9) | 755 | 100.00 [100.00, 100.00]; n=33 | 13.25 [8.28, 19.45]; n=33 | 100.00 [100.00, 100.00]; n=33 | 46.36 [31.52, 59.86]; n=33 | 0.66 [0.00, 2.34]; n=33 |
| FD002/xgb/v2/internal_heldout | life_fraction | [0.9, 1.0000000000000002) | 3770 | 100.00 [100.00, 100.00]; n=39 | 10.21 [7.79, 12.62]; n=39 | 100.00 [100.00, 100.00]; n=39 | 24.93 [16.98, 33.70]; n=39 | 0.53 [0.13, 1.11]; n=39 |
| FD002/xgb/v2/grouped_oof | risk_before | [0.8, 0.85) | 3175 | 100.00 [100.00, 100.00]; n=227 | 17.48 [14.56, 20.31]; n=227 | 100.00 [100.00, 100.00]; n=227 | 49.29 [44.15, 54.15]; n=227 | 2.20 [1.14, 3.31]; n=227 |
| FD002/xgb/v2/grouped_oof | risk_before | [0.85, 0.9) | 4545 | 100.00 [100.00, 100.00]; n=249 | 15.62 [13.33, 18.01]; n=249 | 100.00 [100.00, 100.00]; n=249 | 46.31 [42.40, 50.31]; n=249 | 1.76 [0.88, 2.81]; n=249 |
| FD002/xgb/v2/grouped_oof | risk_before | [0.9, 0.95) | 8090 | 100.00 [100.00, 100.00]; n=258 | 10.44 [8.96, 12.06]; n=258 | 100.00 [100.00, 100.00]; n=258 | 36.28 [32.55, 40.36]; n=258 | 0.31 [0.06, 0.62]; n=258 |
| FD002/xgb/v2/grouped_oof | risk_before | [0.95, 1.0000000000000002) | 12145 | 100.00 [100.00, 100.00]; n=257 | 7.86 [6.76, 9.06]; n=257 | 100.00 [100.00, 100.00]; n=257 | 17.66 [14.75, 20.59]; n=257 | 0.08 [0.00, 0.21]; n=257 |
| FD002/xgb/v2/grouped_oof | rul | [0.0, 11.0) | 13835 | 100.00 [100.00, 100.00]; n=260 | 7.55 [6.53, 8.51]; n=260 | 100.00 [100.00, 100.00]; n=260 | 24.54 [21.73, 27.64]; n=260 | 0.07 [0.00, 0.18]; n=260 |
| FD002/xgb/v2/grouped_oof | rul | [11.0, 21.0) | 9015 | 100.00 [100.00, 100.00]; n=258 | 13.48 [11.96, 15.04]; n=258 | 100.00 [100.00, 100.00]; n=258 | 34.72 [30.63, 38.70]; n=258 | 1.05 [0.62, 1.58]; n=258 |
| FD002/xgb/v2/grouped_oof | rul | [21.0, 31.0) | 3665 | 100.00 [100.00, 100.00]; n=185 | 15.42 [13.13, 17.98]; n=185 | 100.00 [100.00, 100.00]; n=185 | 40.93 [34.91, 47.08]; n=185 | 1.77 [0.86, 2.87]; n=185 |
| FD002/xgb/v2/grouped_oof | rul | [31.0, 1000000.0) | 1440 | 100.00 [100.00, 100.00]; n=86 | 16.67 [12.58, 21.40]; n=86 | 100.00 [100.00, 100.00]; n=86 | 50.35 [40.89, 59.04]; n=86 | 1.04 [0.00, 2.24]; n=86 |
| FD002/xgb/v2/grouped_oof | life_fraction | [0.7, 0.8) | 145 | 100.00 [100.00, 100.00]; n=22 | 24.14 [10.00, 39.29]; n=22 | 100.00 [100.00, 100.00]; n=22 | 72.41 [58.82, 86.21]; n=22 | 0.00 [0.00, 0.00]; n=22 |
| FD002/xgb/v2/grouped_oof | life_fraction | [0.8, 0.9) | 4210 | 100.00 [100.00, 100.00]; n=201 | 17.46 [14.69, 20.30]; n=201 | 100.00 [100.00, 100.00]; n=201 | 50.48 [44.94, 55.63]; n=201 | 2.02 [1.07, 3.09]; n=201 |
| FD002/xgb/v2/grouped_oof | life_fraction | [0.9, 1.0000000000000002) | 23600 | 100.00 [100.00, 100.00]; n=260 | 9.72 [8.88, 10.56]; n=260 | 100.00 [100.00, 100.00]; n=260 | 27.63 [24.68, 30.95]; n=260 | 0.42 [0.23, 0.65]; n=260 |
| FD002/xgb/v2/official_test | risk_before | [0.8, 0.85) | 650 | 100.00 [100.00, 100.00]; n=56 | 19.23 [12.59, 26.45]; n=56 | 100.00 [100.00, 100.00]; n=56 | 41.54 [30.95, 51.82]; n=56 | 4.62 [1.55, 8.16]; n=56 |
| FD002/xgb/v2/official_test | risk_before | [0.85, 0.9) | 760 | 100.00 [100.00, 100.00]; n=55 | 16.45 [11.32, 22.22]; n=55 | 100.00 [100.00, 100.00]; n=55 | 46.71 [36.58, 56.25]; n=55 | 1.32 [0.00, 3.23]; n=55 |
| FD002/xgb/v2/official_test | risk_before | [0.9, 0.95) | 1150 | 100.00 [100.00, 100.00]; n=57 | 11.30 [7.28, 15.75]; n=57 | 100.00 [100.00, 100.00]; n=57 | 33.48 [24.42, 42.40]; n=57 | 0.00 [0.00, 0.00]; n=57 |
| FD002/xgb/v2/official_test | risk_before | [0.95, 1.0000000000000002) | 830 | 100.00 [100.00, 100.00]; n=41 | 10.84 [5.68, 17.01]; n=41 | 100.00 [100.00, 100.00]; n=41 | 14.46 [9.09, 20.83]; n=41 | 0.00 [0.00, 0.00]; n=41 |
| FD002/xgb/v2/official_test | rul | [0.0, 11.0) | 320 | 100.00 [100.00, 100.00]; n=22 | 10.94 [4.48, 18.65]; n=22 | 100.00 [100.00, 100.00]; n=22 | 21.88 [11.43, 34.72]; n=22 | 0.00 [0.00, 0.00]; n=22 |
| FD002/xgb/v2/official_test | rul | [11.0, 21.0) | 1530 | 100.00 [100.00, 100.00]; n=50 | 14.71 [10.70, 18.71]; n=50 | 100.00 [100.00, 100.00]; n=50 | 27.78 [19.73, 36.17]; n=50 | 0.98 [0.00, 2.15]; n=50 |
| FD002/xgb/v2/official_test | rul | [21.0, 31.0) | 1005 | 100.00 [100.00, 100.00]; n=47 | 12.44 [8.49, 16.47]; n=47 | 100.00 [100.00, 100.00]; n=47 | 35.82 [25.74, 46.28]; n=47 | 0.00 [0.00, 0.00]; n=47 |
| FD002/xgb/v2/official_test | rul | [31.0, 1000000.0) | 535 | 100.00 [100.00, 100.00]; n=25 | 15.89 [11.00, 22.54]; n=25 | 100.00 [100.00, 100.00]; n=25 | 51.40 [33.33, 70.97]; n=25 | 4.67 [1.39, 8.46]; n=25 |
| FD002/xgb/v2/official_test | life_fraction | [0.0, 0.7) | 5 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 100.00 [100.00, 100.00]; n=1 | 0.00 [0.00, 0.00]; n=1 |
| FD002/xgb/v2/official_test | life_fraction | [0.7, 0.8) | 75 | 100.00 [100.00, 100.00]; n=10 | 13.33 [0.00, 30.77]; n=10 | 100.00 [100.00, 100.00]; n=10 | 86.67 [63.64, 100.00]; n=10 | 6.67 [0.00, 17.65]; n=10 |
| FD002/xgb/v2/official_test | life_fraction | [0.8, 0.9) | 1390 | 100.00 [100.00, 100.00]; n=57 | 15.83 [11.71, 20.36]; n=57 | 100.00 [100.00, 100.00]; n=57 | 43.17 [32.67, 53.20]; n=57 | 1.80 [0.40, 3.34]; n=57 |
| FD002/xgb/v2/official_test | life_fraction | [0.9, 1.0000000000000002) | 1920 | 100.00 [100.00, 100.00]; n=53 | 12.50 [9.22, 16.27]; n=53 | 100.00 [100.00, 100.00]; n=53 | 23.96 [17.19, 31.85]; n=53 | 0.52 [0.00, 1.36]; n=53 |

### Feature-change frequencies and failure reasons

Feature frequencies are descriptive percentages of all query-seed observations. Failure-reason counts include structured rejected results; they are not removed from rates.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: all alerts; FAST; descriptive frequencies. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Profile / population | Engine count | Change frequency (% of observations) | Failure reason counts |
|---|---|---|---|
| FD001/lstm/v1/internal_heldout | 15 | sensor_11: 100.000; sensor_12: 95.143; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 9.714; sensor_17: 24.571; sensor_2: 100.000; sensor_20: 51.143; sensor_21: 38.571; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 80.286; sensor_9: 0.571 | safe_risk_not_reached: 1750 |
| FD001/lstm/v1/grouped_oof | 100 | sensor_11: 95.277; sensor_12: 79.194; sensor_13: 95.277; sensor_14: 95.277; sensor_15: 24.064; sensor_17: 12.744; sensor_2: 95.277; sensor_20: 46.010; sensor_21: 40.065; sensor_3: 95.277; sensor_4: 95.277; sensor_6: 95.277; sensor_7: 95.277; sensor_8: 74.878; sensor_9: 9.446 | infeasible_actuator_interval: 580; mandatory_changes_exceed_sparsity: 65; safe_risk_not_reached: 11635 |
| FD001/lstm/v1/official_test | 16 | sensor_11: 100.000; sensor_12: 100.000; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 10.145; sensor_17: 5.072; sensor_2: 100.000; sensor_20: 76.087; sensor_21: 20.290; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 87.681; sensor_9: 0.725 | safe_risk_not_reached: 690 |
| FD001/lstm/v2/internal_heldout | 15 | sensor_11: 100.000; sensor_12: 95.143; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 9.714; sensor_17: 24.571; sensor_2: 100.000; sensor_20: 51.143; sensor_21: 38.571; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 80.286; sensor_9: 0.571 | safe_risk_not_reached: 1750 |
| FD001/lstm/v2/grouped_oof | 100 | sensor_11: 95.277; sensor_12: 79.194; sensor_13: 95.277; sensor_14: 95.277; sensor_15: 24.064; sensor_17: 12.744; sensor_2: 95.277; sensor_20: 46.010; sensor_21: 40.065; sensor_3: 95.277; sensor_4: 95.277; sensor_6: 95.277; sensor_7: 95.277; sensor_8: 74.878; sensor_9: 9.446 | infeasible_actuator_interval: 580; mandatory_changes_exceed_sparsity: 65; safe_risk_not_reached: 11635 |
| FD001/lstm/v2/official_test | 16 | sensor_11: 100.000; sensor_12: 100.000; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 10.145; sensor_17: 5.072; sensor_2: 100.000; sensor_20: 76.087; sensor_21: 20.290; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 87.681; sensor_9: 0.725 | safe_risk_not_reached: 690 |
| FD001/mlp/v1/internal_heldout | 15 | sensor_11: 100.000; sensor_12: 82.228; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 20.955; sensor_17: 9.549; sensor_2: 100.000; sensor_20: 46.684; sensor_21: 23.873; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 68.170; sensor_9: 33.952 | safe_risk_not_reached: 860; validation_feedback_exhausted: 305 |
| FD001/mlp/v1/grouped_oof | 100 | sensor_11: 95.307; sensor_12: 86.448; sensor_13: 95.307; sensor_14: 95.307; sensor_15: 22.290; sensor_17: 14.684; sensor_2: 95.307; sensor_20: 20.186; sensor_21: 25.971; sensor_3: 95.307; sensor_4: 95.307; sensor_6: 95.307; sensor_7: 95.307; sensor_8: 72.492; sensor_9: 32.807 | infeasible_actuator_interval: 580; mandatory_changes_exceed_sparsity: 65; safe_risk_not_reached: 5530; validation_feedback_exhausted: 1825 |
| FD001/mlp/v1/official_test | 19 | sensor_11: 100.000; sensor_12: 92.941; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 14.706; sensor_17: 4.118; sensor_2: 100.000; sensor_20: 18.824; sensor_21: 21.765; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 79.412; sensor_9: 36.471 | safe_risk_not_reached: 75; validation_feedback_exhausted: 115 |
| FD001/mlp/v2/internal_heldout | 15 | sensor_11: 100.000; sensor_12: 81.963; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 17.772; sensor_17: 7.692; sensor_2: 100.000; sensor_20: 46.684; sensor_21: 21.751; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 66.578; sensor_9: 36.074 | safe_risk_not_reached: 860; validation_feedback_exhausted: 60 |
| FD001/mlp/v2/grouped_oof | 100 | sensor_11: 95.307; sensor_12: 85.882; sensor_13: 95.307; sensor_14: 95.307; sensor_15: 19.417; sensor_17: 13.673; sensor_2: 95.307; sensor_20: 18.244; sensor_21: 22.816; sensor_3: 95.307; sensor_4: 95.307; sensor_6: 95.307; sensor_7: 95.307; sensor_8: 72.006; sensor_9: 35.963 | infeasible_actuator_interval: 580; mandatory_changes_exceed_sparsity: 65; safe_risk_not_reached: 5530; validation_feedback_exhausted: 255 |
| FD001/mlp/v2/official_test | 19 | sensor_11: 100.000; sensor_12: 89.412; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 12.353; sensor_17: 3.529; sensor_2: 100.000; sensor_20: 18.235; sensor_21: 15.294; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 74.706; sensor_9: 42.941 | safe_risk_not_reached: 75; validation_feedback_exhausted: 5 |
| FD001/xgb/v1/internal_heldout | 15 | sensor_11: 100.000; sensor_12: 87.302; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 29.630; sensor_17: 11.376; sensor_2: 100.000; sensor_20: 37.566; sensor_21: 34.921; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 56.085; sensor_9: 34.127 | safe_risk_not_reached: 835; validation_feedback_exhausted: 260 |
| FD001/xgb/v1/grouped_oof | 100 | sensor_11: 95.122; sensor_12: 81.287; sensor_13: 95.122; sensor_14: 95.122; sensor_15: 37.595; sensor_17: 10.513; sensor_2: 95.122; sensor_20: 37.090; sensor_21: 28.007; sensor_3: 95.122; sensor_4: 95.122; sensor_6: 95.122; sensor_7: 95.122; sensor_8: 47.771; sensor_9: 34.062 | infeasible_actuator_interval: 580; mandatory_changes_exceed_sparsity: 65; safe_risk_not_reached: 5000; validation_feedback_exhausted: 1500 |
| FD001/xgb/v1/official_test | 19 | sensor_11: 100.000; sensor_12: 94.969; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 18.239; sensor_17: 6.289; sensor_2: 100.000; sensor_20: 25.786; sensor_21: 26.415; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 55.346; sensor_9: 50.314 | safe_risk_not_reached: 85; validation_feedback_exhausted: 100 |
| FD001/xgb/v2/internal_heldout | 15 | sensor_11: 100.000; sensor_12: 88.624; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 27.513; sensor_17: 9.259; sensor_2: 100.000; sensor_20: 38.360; sensor_21: 32.540; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 55.026; sensor_9: 35.979 | safe_risk_not_reached: 835; validation_feedback_exhausted: 55 |
| FD001/xgb/v2/grouped_oof | 100 | sensor_11: 95.122; sensor_12: 82.002; sensor_13: 95.122; sensor_14: 95.122; sensor_15: 36.039; sensor_17: 9.840; sensor_2: 95.122; sensor_20: 36.249; sensor_21: 24.180; sensor_3: 95.122; sensor_4: 95.122; sensor_6: 95.122; sensor_7: 95.122; sensor_8: 48.402; sensor_9: 35.828 | infeasible_actuator_interval: 580; mandatory_changes_exceed_sparsity: 65; safe_risk_not_reached: 5000; validation_feedback_exhausted: 250 |
| FD001/xgb/v2/official_test | 19 | sensor_11: 100.000; sensor_12: 96.226; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 15.723; sensor_17: 5.031; sensor_2: 100.000; sensor_20: 26.415; sensor_21: 18.868; sensor_3: 100.000; sensor_4: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 58.491; sensor_9: 52.201 | safe_risk_not_reached: 85; validation_feedback_exhausted: 10 |
| FD002/xgb/v1/internal_heldout | 39 | sensor_1: 100.000; sensor_10: 100.000; sensor_11: 100.000; sensor_12: 37.541; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 23.600; sensor_16: 100.000; sensor_17: 26.454; sensor_18: 100.000; sensor_19: 100.000; sensor_2: 100.000; sensor_20: 23.600; sensor_21: 24.149; sensor_3: 100.000; sensor_4: 100.000; sensor_5: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 11.416; sensor_9: 15.697 | validation_feedback_exhausted: 4540 |
| FD002/xgb/v1/grouped_oof | 260 | sensor_1: 100.000; sensor_10: 100.000; sensor_11: 100.000; sensor_12: 41.853; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 20.265; sensor_16: 100.000; sensor_17: 31.765; sensor_18: 99.982; sensor_19: 99.964; sensor_2: 100.000; sensor_20: 19.746; sensor_21: 17.635; sensor_3: 100.000; sensor_4: 100.000; sensor_5: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 15.507; sensor_9: 11.769 | safe_risk_not_reached: 25; validation_feedback_exhausted: 27910 |
| FD002/xgb/v1/official_test | 65 | sensor_1: 100.000; sensor_10: 100.000; sensor_11: 100.000; sensor_12: 38.053; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 16.224; sensor_16: 100.000; sensor_17: 32.448; sensor_18: 100.000; sensor_19: 100.000; sensor_2: 100.000; sensor_20: 22.566; sensor_21: 25.811; sensor_3: 100.000; sensor_4: 100.000; sensor_5: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 7.080; sensor_9: 9.145 | validation_feedback_exhausted: 3375 |
| FD002/xgb/v2/internal_heldout | 39 | sensor_1: 100.000; sensor_10: 100.000; sensor_11: 100.000; sensor_12: 37.212; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 27.442; sensor_16: 100.000; sensor_17: 23.600; sensor_18: 100.000; sensor_19: 100.000; sensor_2: 100.000; sensor_20: 30.406; sensor_21: 24.588; sensor_3: 100.000; sensor_4: 100.000; sensor_5: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 10.757; sensor_9: 15.917 | validation_feedback_exhausted: 4530 |
| FD002/xgb/v2/grouped_oof | 260 | sensor_1: 100.000; sensor_10: 100.000; sensor_11: 100.000; sensor_12: 41.603; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 23.502; sensor_16: 100.000; sensor_17: 27.330; sensor_18: 100.000; sensor_19: 99.714; sensor_2: 100.000; sensor_20: 22.751; sensor_21: 20.837; sensor_3: 100.000; sensor_4: 100.000; sensor_5: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 15.185; sensor_9: 12.699 | safe_risk_not_reached: 20; validation_feedback_exhausted: 27750 |
| FD002/xgb/v2/official_test | 65 | sensor_1: 100.000; sensor_10: 100.000; sensor_11: 100.000; sensor_12: 36.136; sensor_13: 100.000; sensor_14: 100.000; sensor_15: 21.386; sensor_16: 100.000; sensor_17: 28.319; sensor_18: 100.000; sensor_19: 99.853; sensor_2: 100.000; sensor_20: 29.646; sensor_21: 25.811; sensor_3: 100.000; sensor_4: 100.000; sensor_5: 100.000; sensor_6: 100.000; sensor_7: 100.000; sensor_8: 6.932; sensor_9: 12.242 | validation_feedback_exhausted: 3350 |

### Held-out coupling residual diagnostics

These are saved validation-engine residual diagnostics for the base bundles. Coupling regressors were fitted on training engines; residual thresholds were calibrated on disjoint validation engines. Constant channels can have zero threshold or unstable R2; a fitted relationship is not a physics law. Fold-specific coupling diagnostics are saved in `artifacts/phase7-models/index.json`, under `models[profile].coupling_calibration` (post-audit pointer correction; measurements unchanged).

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: saved healthy-to-moderate coupling validation engines. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Bundle | Dependent channel | Validation engines | R2 | Residual std (raw) | Share beyond threshold % | Residual threshold (raw) |
|---|---|---|---|---|---|---|
| FD001/xgb/base | sensor_11 | 16 | 0.695 | 0.114326 | 0.264 | 0.342978 |
| FD001/xgb/base | sensor_13 | 16 | 0.700 | 0.035202 | 0.264 | 0.105607 |
| FD001/xgb/base | sensor_14 | 16 | 0.896 | 4.724522 | 0.378 | 14.173567 |
| FD001/xgb/base | sensor_2 | 16 | 0.433 | 0.311562 | 0.340 | 0.934687 |
| FD001/xgb/base | sensor_3 | 16 | 0.353 | 4.111054 | 0.302 | 12.333161 |
| FD001/xgb/base | sensor_4 | 16 | 0.608 | 4.447479 | 0.302 | 13.342436 |
| FD001/xgb/base | sensor_6 | 16 | 0.032 | 0.001653 | 2.907 | 0.004958 |
| FD001/xgb/base | sensor_7 | 16 | 0.597 | 0.458173 | 0.151 | 1.374520 |
| FD001/mlp/base | sensor_11 | 16 | 0.695 | 0.114326 | 0.264 | 0.342978 |
| FD001/mlp/base | sensor_13 | 16 | 0.700 | 0.035202 | 0.264 | 0.105607 |
| FD001/mlp/base | sensor_14 | 16 | 0.896 | 4.724522 | 0.378 | 14.173567 |
| FD001/mlp/base | sensor_2 | 16 | 0.433 | 0.311562 | 0.340 | 0.934687 |
| FD001/mlp/base | sensor_3 | 16 | 0.353 | 4.111054 | 0.302 | 12.333161 |
| FD001/mlp/base | sensor_4 | 16 | 0.608 | 4.447479 | 0.302 | 13.342436 |
| FD001/mlp/base | sensor_6 | 16 | 0.032 | 0.001653 | 2.907 | 0.004958 |
| FD001/mlp/base | sensor_7 | 16 | 0.597 | 0.458173 | 0.151 | 1.374520 |
| FD001/lstm/base | sensor_11 | 16 | 0.695 | 0.114326 | 0.264 | 0.342978 |
| FD001/lstm/base | sensor_13 | 16 | 0.700 | 0.035202 | 0.264 | 0.105607 |
| FD001/lstm/base | sensor_14 | 16 | 0.896 | 4.724522 | 0.378 | 14.173567 |
| FD001/lstm/base | sensor_2 | 16 | 0.433 | 0.311562 | 0.340 | 0.934687 |
| FD001/lstm/base | sensor_3 | 16 | 0.353 | 4.111054 | 0.302 | 12.333161 |
| FD001/lstm/base | sensor_4 | 16 | 0.608 | 4.447479 | 0.302 | 13.342436 |
| FD001/lstm/base | sensor_6 | 16 | 0.032 | 0.001653 | 2.907 | 0.004958 |
| FD001/lstm/base | sensor_7 | 16 | 0.597 | 0.458173 | 0.151 | 1.374520 |
| FD002/xgb/base | sensor_1 | 40 | 1.000 | 0.045797 | 0.872 | 0.137392 |
| FD002/xgb/base | sensor_10 | 40 | 1.000 | 0.001768 | 2.878 | 0.005303 |
| FD002/xgb/base | sensor_11 | 40 | 0.998 | 0.131597 | 0.218 | 0.394791 |
| FD002/xgb/base | sensor_13 | 40 | 1.000 | 0.118248 | 0.916 | 0.354745 |
| FD002/xgb/base | sensor_14 | 40 | 0.997 | 4.752719 | 0.334 | 14.258158 |
| FD002/xgb/base | sensor_16 | 40 | 0.934 | 0.001192 | 1.628 | 0.003575 |
| FD002/xgb/base | sensor_18 | 40 | 1.000 | 0.111772 | 0.843 | 0.335316 |
| FD002/xgb/base | sensor_19 | 40 | 1.000 | 0.000032 | 1.018 | 0.000095 |
| FD002/xgb/base | sensor_2 | 40 | 1.000 | 0.332113 | 0.204 | 0.996339 |
| FD002/xgb/base | sensor_3 | 40 | 0.998 | 4.254253 | 0.233 | 12.762759 |
| FD002/xgb/base | sensor_4 | 40 | 0.998 | 4.768153 | 0.349 | 14.304458 |
| FD002/xgb/base | sensor_5 | 40 | 1.000 | 0.009727 | 0.349 | 0.029181 |
| FD002/xgb/base | sensor_6 | 40 | 1.000 | 0.015361 | 0.320 | 0.046084 |
| FD002/xgb/base | sensor_7 | 40 | 1.000 | 0.510288 | 0.262 | 1.530865 |

## Paired baselines, constraint ladders, ablations and sensitivities

Every following row uses the same paired internal diagnostic population for its dataset/protocol; these are diagnostic measurements, not held-out all-alert headlines. Each one-factor sensitivity is labeled; H changes use genuinely refitted/recalibrated models on the original partitions. Validity remains fixed at 0.20 even when a sensitivity solver target differs. Each row records its effective config hash and bounds/rates remain frozen. Complete metric/seed tables are in report.md/metrics.csv. Structured funnel, stratum, per-feature, failure, D_M and coupling-margin fields are in summary.json and exposed above for the headline populations.

Changing beta cannot undo a hard immutable freeze; gamma can be inactive inside a hard box. Invariant sensitivity results reflect these search policies. Dense research gradients are dense; their fallback grid retains the frozen sparse support cap, as preregistered. DiCE is the actual installed method and its failures remain in denominators.

### FD001/xgb/v1

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: FD001/xgb/v1/paired_internal_diagnostic; FAST; solver seed 1729. settings vary only as labeled per row; original final validators retained. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Variant | Effective config SHA-256 | tau / k / K / D_max | Validity % | Tier 2 all % | Tier 2 returned % | Joint % | Risk drop |
|---|---|---|---|---|---|---|---|
| L0_all_free | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/18/1/5.0 | 75.00 [56.25, 91.14]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.74 [0.68, 0.79]; n=10 |
| L1_immutable | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/15/1/5.0 | 75.00 [56.25, 91.14]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.74 [0.68, 0.79]; n=10 |
| L2_bounds | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/15/1/5.0 | 66.67 [45.45, 90.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.68 [0.59, 0.75]; n=10 |
| L3_rates | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/15/1/5.0 | 50.00 [23.08, 80.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 8.33 [0.00, 27.27]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.59 [0.45, 0.72]; n=10 |
| L4_propagation | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/7/1/5.0 | 50.00 [23.08, 80.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 25.00 [6.67, 50.00]; n=10 | 0.55 [0.40, 0.71]; n=10 |
| L5_sparsity | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 16.67 [0.00, 36.36]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| L6_mahalanobis | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| L7_coupling | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| ablation-Dmax-method-chi_square | 5112487f2c05a824c37d678d5ab2c10a3b42f86d6233dcb4d44fe265d3e410e9 | 0.2/3/1/5.899602167494438 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| ablation-Dmax-method-empirical | 1531b3defd7f4a26864fdfb9bcae988772576133755d4ebd97cb7eb86accb6a6 | 0.2/3/1/8.245478907143303 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| ablation-reference-all_cycles | 354ee05b0f05b113d68f94fe5b65209cd429179696dbedaa81655fea103c70ec | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| ablation-reference-healthy_to_moderate | f79829b1f5b52d25ed115b72dba04cb04969cb30b3635aad60039b7bd4e6c3ec | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 25.00 [0.00, 54.55]; n=10 | 25.00 [0.00, 54.55]; n=10 | 25.00 [0.00, 54.55]; n=10 | 0.49 [0.36, 0.65]; n=10 |
| bounded_without_plausibility | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 16.67 [0.00, 36.36]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| dice | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/18/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.79, 0.84]; n=10 |
| full | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| no_bounds | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 41.67 [16.67, 72.73]; n=10 | 41.67 [16.67, 72.73]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.56 [0.41, 0.72]; n=10 |
| no_coupling_propagation | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 0.00 [0.00, 0.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.26 [0.14, 0.40]; n=10 |
| no_immutable_freezing | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.49 [0.36, 0.64]; n=10 |
| no_mahalanobis | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 16.67 [0.00, 36.36]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| no_sparsity | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/7/1/5.0 | 41.67 [15.38, 70.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.53 [0.39, 0.68]; n=10 |
| no_validation_in_loop | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 16.67 [0.00, 36.36]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-chi_square-q-0.95 | 2acf2f6654536f27bc9abc1346f90dd0c0e5b624de9cd52603285568f62c72fb | 0.2/3/1/5.373015859867959 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.49 [0.36, 0.65]; n=10 |
| sensitivity-Dmax-chi_square-q-0.99 | 5112487f2c05a824c37d678d5ab2c10a3b42f86d6233dcb4d44fe265d3e410e9 | 0.2/3/1/5.899602167494438 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-chi_square-q-0.999 | b16e529bc03a3b3bdebe0386687eba18b9f9f9164ee845b0e0e984ea232cdcd5 | 0.2/3/1/6.504797947029559 | 33.33 [8.33, 60.00]; n=10 | 75.00 [50.00, 100.00]; n=10 | 75.00 [50.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-empirical-q-0.95 | 99ce1bcc36bbc8737b4a068966d9c4c881cafd8713017176b9a2febfb7fc62e2 | 0.2/3/1/5.4033146750331 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-empirical-q-0.99 | 1531b3defd7f4a26864fdfb9bcae988772576133755d4ebd97cb7eb86accb6a6 | 0.2/3/1/8.245478907143303 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-empirical-q-0.999 | 3372d4fdef5239a757fce20526d6879c86caca5b687b267d55abd0097408ab14 | 0.2/3/1/8.920299723402897 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-horizon-K-1 | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-horizon-K-10 | 0575f035ee4820ca8adf1971ca6bde91e509ab04b18d16f925defd3090055a49 | 0.2/3/10/5.0 | 100.00 [100.00, 100.00]; n=10 | 66.67 [40.00, 91.67]; n=10 | 66.67 [40.00, 91.67]; n=10 | 66.67 [40.00, 91.67]; n=10 | 0.79 [0.77, 0.82]; n=10 |
| sensitivity-horizon-K-2 | df4a7a692b4adde58409160a7f31455a99d6e3e38c18f8acf0d8cafe4b108c21 | 0.2/3/2/5.0 | 91.67 [72.73, 100.00]; n=10 | 58.33 [36.36, 81.82]; n=10 | 58.33 [36.36, 81.82]; n=10 | 58.33 [36.36, 81.82]; n=10 | 0.77 [0.67, 0.84]; n=10 |
| sensitivity-horizon-K-3 | c99cfd118e0c698c20c51868f6a6f934a8e5efd6078702dafe29320863c21c16 | 0.2/3/3/5.0 | 91.67 [72.73, 100.00]; n=10 | 58.33 [30.00, 84.62]; n=10 | 58.33 [30.00, 84.62]; n=10 | 58.33 [30.00, 84.62]; n=10 | 0.79 [0.75, 0.82]; n=10 |
| sensitivity-horizon-K-5 | c8adcbe44e5425eb3ee06400242e398c8e9e7ac79b317e8a34c793a74c0e3c73 | 0.2/3/5/5.0 | 100.00 [100.00, 100.00]; n=10 | 66.67 [40.00, 91.67]; n=10 | 66.67 [40.00, 91.67]; n=10 | 66.67 [40.00, 91.67]; n=10 | 0.81 [0.77, 0.83]; n=10 |
| sensitivity-label-H-15 | 0095cef1d72b52191463c3a1cd36dff5acb47439b59182866b9fdffe5b1c89e5 | 0.2/3/1/5.0 | 50.00 [20.00, 76.92]; n=10 | 66.67 [40.00, 91.67]; n=10 | 50.00 [12.50, 100.00]; n=10 | 33.33 [7.13, 66.67]; n=10 | 0.38 [0.20, 0.57]; n=10 |
| sensitivity-label-H-30 | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-label-H-50 | e31954de1f4309ab7d57e25ffd9dfe0cc901ecec6042dc29896c89eb41db5c67 | 0.2/3/1/5.0 | 8.33 [0.00, 28.61]; n=10 | 8.33 [0.00, 27.27]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.27 [0.11, 0.48]; n=10 |
| sensitivity-sparsity-k_max-1 | 76f6e8d62ddf7a680d4699a9fcd5c24ab0e68aa3ba6228fab7e04570ffa8eab9 | 0.2/1/1/5.0 | 0.00 [0.00, 0.00]; n=10 | 41.67 [15.38, 70.00]; n=10 | 45.45 [16.67, 75.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.14 [0.06, 0.24]; n=10 |
| sensitivity-sparsity-k_max-2 | f02ae38112a5da321e16342d56ff7edb6be5f6d6be22a2ba7ec54856b042d71d | 0.2/2/1/5.0 | 25.00 [6.67, 50.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 33.33 [9.09, 60.00]; n=10 | 16.67 [0.00, 36.36]; n=10 | 0.34 [0.19, 0.53]; n=10 |
| sensitivity-sparsity-k_max-3 | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-sparsity-k_max-5 | f7143433a20f0cb2c7ce3763c84ac1f7cdaa9763e2f5cb966915f17f8eeda047 | 0.2/5/1/5.0 | 75.00 [56.25, 91.14]; n=10 | 83.33 [61.54, 100.00]; n=10 | 83.33 [61.54, 100.00]; n=10 | 75.00 [56.25, 91.14]; n=10 | 0.69 [0.59, 0.77]; n=10 |
| sensitivity-threshold-tau_safe-0.1 | 808320b9096d7920eac291c6c28f8ba1a06a63f7898dde37a7af1dbfea411bb1 | 0.1/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.52 [0.38, 0.68]; n=10 |
| sensitivity-threshold-tau_safe-0.2 | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-threshold-tau_safe-0.3 | f79fdb41e4bd00ff5912a2b1813cc7b8924e1c9bdc72ab8a82680ff9df058ac6 | 0.3/3/1/5.0 | 0.00 [0.00, 0.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.47 [0.34, 0.61]; n=10 |
| sensitivity-weight-alpha-1.0 | cb80f79dc6f77feae3353996e13f89f902ba0a9cb8e6ad36c9f3f9f6e1a45f41 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.49 [0.36, 0.64]; n=10 |
| sensitivity-weight-alpha-10.0 | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-weight-alpha-100.0 | cff6f9bb461fd7aa05f9649520aa0ef5b0474be7a02dd325b9a7e390a5386b1c | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.49 [0.36, 0.64]; n=10 |
| sensitivity-weight-beta-0.0 | 02ad68eb0e05ebe228ed4e541b80b9b96d9a8315267519206c74217c379eefcb | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-weight-beta-1.0 | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-weight-beta-100.0 | ac9ee235c736c70acb0b17d4319ebddf3c884ae47b6d304ad0a3afb9f847408b | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-weight-gamma-0.0 | f1c9ee72258a4de53c5d930de5d5a852ce27686a08331a4337d52537c427cc95 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-weight-gamma-1.0 | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| sensitivity-weight-gamma-100.0 | 7e17a1dcfcda232ab680b486baebfe17ae303ac3ecc5c1ffe11b308ff483b90a | 0.2/3/1/5.0 | 33.33 [8.33, 60.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| unconstrained | 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271 | 0.2/18/1/5.0 | 0.00 [0.00, 0.00]; n=10 | 50.00 [25.00, 75.00]; n=10 | 25.00 [0.00, 75.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.03 [0.00, 0.08]; n=10 |

### FD001/xgb/v2

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: FD001/xgb/v2/paired_internal_diagnostic; FAST; solver seed 1729. settings vary only as labeled per row; original final validators retained. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Variant | Effective config SHA-256 | tau / k / K / D_max | Validity % | Tier 2 all % | Tier 2 returned % | Joint % | Risk drop |
|---|---|---|---|---|---|---|---|
| L0_all_free | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/18/1/8.0 | 75.00 [56.25, 91.14]; n=10 | 33.33 [8.33, 60.04]; n=10 | 33.33 [8.33, 60.04]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.74 [0.68, 0.79]; n=10 |
| L1_immutable | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/15/1/8.0 | 75.00 [56.25, 91.14]; n=10 | 33.33 [8.33, 60.04]; n=10 | 33.33 [8.33, 60.04]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.74 [0.68, 0.79]; n=10 |
| L2_bounds | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/15/1/8.0 | 66.67 [45.45, 90.00]; n=10 | 41.67 [15.38, 70.00]; n=10 | 41.67 [15.38, 70.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.68 [0.59, 0.75]; n=10 |
| L3_rates | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/15/1/8.0 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.59 [0.45, 0.72]; n=10 |
| L4_propagation | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/7/1/8.0 | 50.00 [23.08, 80.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 0.55 [0.40, 0.71]; n=10 |
| L5_sparsity | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| L6_mahalanobis | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| L7_coupling | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| ablation-Dmax-method-chi_square | ecc48e289aa6f04f3cbb70611fee43ad3fe701c441c4730c6f4611630779723b | 0.2/3/1/5.899602167494438 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| ablation-Dmax-method-empirical | 5c2cb3840edeecfbce5c42fce4fae0ec7f29fb5848be459469f9516da9981938 | 0.2/3/1/8.245478907143303 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| ablation-reference-all_cycles | 91a3e1a5a38f3c4f2a798e78a144338e03b55a2c5e9d987ef6470ddc38cfccb4 | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| ablation-reference-healthy_to_moderate | dc4c61a052a229faa8f4bffe3598b3d8dea04246acfad645e4d4b648615e1691 | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 83.33 [61.54, 100.00]; n=10 | 83.33 [61.54, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| bounded_without_plausibility | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| dice | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/18/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.79, 0.84]; n=10 |
| full | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| no_bounds | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.55 [0.41, 0.71]; n=10 |
| no_coupling_propagation | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 0.00 [0.00, 0.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.26 [0.14, 0.40]; n=10 |
| no_immutable_freezing | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.65]; n=10 |
| no_mahalanobis | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| no_sparsity | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/7/1/8.0 | 50.00 [23.08, 80.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 0.55 [0.40, 0.71]; n=10 |
| no_validation_in_loop | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-chi_square-q-0.95 | 5c5ac9b9eadce7e14c6cc030a859bdb84cf2e788a90aae816e8318068de14ca7 | 0.2/3/1/5.373015859867959 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.49 [0.36, 0.65]; n=10 |
| sensitivity-Dmax-chi_square-q-0.99 | ecc48e289aa6f04f3cbb70611fee43ad3fe701c441c4730c6f4611630779723b | 0.2/3/1/5.899602167494438 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-chi_square-q-0.999 | 7c25d523304f6fcfbb517a34c4785de006f4c03f612e6527fc1470340b2a52e4 | 0.2/3/1/6.504797947029559 | 33.33 [8.33, 60.00]; n=10 | 75.00 [50.00, 100.00]; n=10 | 75.00 [50.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-empirical-q-0.95 | 43dbebf1e100d56e05e614132e1cf357e908a4265f07de3bf83a2c6a4f0e6024 | 0.2/3/1/5.4033146750331 | 33.33 [8.33, 60.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 58.33 [30.77, 90.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-empirical-q-0.99 | 5c2cb3840edeecfbce5c42fce4fae0ec7f29fb5848be459469f9516da9981938 | 0.2/3/1/8.245478907143303 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-Dmax-empirical-q-0.999 | 879fe8546f98d4e2728365b7c9ab0509eb15c66917aa8806c2a9690da42375fa | 0.2/3/1/8.920299723402897 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-horizon-K-1 | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-horizon-K-10 | c8d194e2ed2413ebbfa0f6d16758fd00f9b32aba6624996b0a02d30a56139eab | 0.2/3/10/8.0 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 91.67 [76.92, 100.00]; n=10 | 0.79 [0.76, 0.82]; n=10 |
| sensitivity-horizon-K-2 | ecd9ff96838460e72cad28a6708b55b2a4736f4120e755f2733f17ea6a369a19 | 0.2/3/2/8.0 | 91.67 [72.73, 100.00]; n=10 | 91.67 [72.73, 100.00]; n=10 | 91.67 [72.73, 100.00]; n=10 | 83.33 [61.54, 100.00]; n=10 | 0.76 [0.66, 0.83]; n=10 |
| sensitivity-horizon-K-3 | 28c1cf1a21ea0891511bfd90713ab9299b9cfd60dc2d9e3055b3302e9c57d3de | 0.2/3/3/8.0 | 91.67 [72.73, 100.00]; n=10 | 91.67 [72.73, 100.00]; n=10 | 91.67 [72.73, 100.00]; n=10 | 83.33 [61.54, 100.00]; n=10 | 0.78 [0.75, 0.81]; n=10 |
| sensitivity-horizon-K-5 | dc8806e1737f075b155e54e7301a173ae9244710e2d8aa649fdb33a6aa031185 | 0.2/3/5/8.0 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 91.67 [76.92, 100.00]; n=10 | 0.79 [0.77, 0.82]; n=10 |
| sensitivity-label-H-15 | bdbb0626c23ef38aeaf74734fce708b0ff3717f392e20967c9e2cc6d98801396 | 0.2/3/1/8.0 | 50.00 [20.00, 76.92]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 41.67 [9.09, 75.00]; n=10 | 0.38 [0.20, 0.57]; n=10 |
| sensitivity-label-H-30 | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-label-H-50 | 2683c8be70dabd79f510743064f10b6ae20216db50ff2217740340c68d28c093 | 0.2/3/1/8.0 | 8.33 [0.00, 28.61]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 28.61]; n=10 | 0.27 [0.11, 0.48]; n=10 |
| sensitivity-sparsity-k_max-1 | 1f0d1a61c3089bb92756f978e87272b176bf9f30914a712b40293aed6b51f047 | 0.2/1/1/8.0 | 0.00 [0.00, 0.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.14 [0.06, 0.24]; n=10 |
| sensitivity-sparsity-k_max-2 | 187d29f26208a3295e6deba8d57d720bb5ed1ea995eae894cc94e5009ca0846c | 0.2/2/1/8.0 | 25.00 [6.67, 50.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 25.00 [6.67, 50.00]; n=10 | 0.34 [0.19, 0.53]; n=10 |
| sensitivity-sparsity-k_max-3 | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-sparsity-k_max-5 | c7c182030cc25a6a2e240e2be5852dc7560ec3f46d32bb72ec52f907571b2049 | 0.2/5/1/8.0 | 75.00 [56.25, 91.14]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 75.00 [56.25, 91.14]; n=10 | 0.70 [0.60, 0.78]; n=10 |
| sensitivity-threshold-tau_safe-0.1 | 7a8a2965573e304e1d7e5b895eccc770a05efe77a47d29c83a8ef2e976f61416 | 0.1/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.53 [0.38, 0.69]; n=10 |
| sensitivity-threshold-tau_safe-0.2 | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-threshold-tau_safe-0.3 | 1e008ec6f4165c9863d9baa138b40b544afcbf35f4549fc9e5f92bec7673f672 | 0.3/3/1/8.0 | 0.00 [0.00, 0.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.47 [0.35, 0.61]; n=10 |
| sensitivity-weight-alpha-1.0 | 0747e67842f08a515c664e754056370f5c5e15e85117e93548b38534e6ae4c85 | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.49 [0.36, 0.64]; n=10 |
| sensitivity-weight-alpha-10.0 | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-weight-alpha-100.0 | 8603f00343f06a85b9c4315ca0f0e4b7faf907e120eb1cfca92d1552120ee390 | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.49 [0.36, 0.65]; n=10 |
| sensitivity-weight-beta-0.0 | 92b519e526f41cf305173c310bb8ac03795a6fd9abcc16a1b9db1c0ac0227f0d | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-weight-beta-1.0 | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-weight-beta-100.0 | 4b5c41301b70460b072c0ad54831efc9df8ed92957140da520db603d109c9343 | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-weight-gamma-0.0 | 4563dc9bda1a383f5431ad1d2c3cfa064fd9e61c12baf2c862a2ecb3e285f55c | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-weight-gamma-1.0 | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| sensitivity-weight-gamma-100.0 | fbfe496a7d0cb6be4c6c4902450837d70220fa6532c06910b4c0547813e02e32 | 0.2/3/1/8.0 | 33.33 [8.33, 60.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 33.33 [8.33, 60.00]; n=10 | 0.50 [0.36, 0.66]; n=10 |
| unconstrained | 42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a | 0.2/18/1/8.0 | 0.00 [0.00, 0.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.03 [0.00, 0.08]; n=10 |

### FD002/xgb/v1

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: FD002/xgb/v1/paired_internal_diagnostic; FAST; solver seed 1729. settings vary only as labeled per row; original final validators retained. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Variant | Effective config SHA-256 | tau / k / K / D_max | Validity % | Tier 2 all % | Tier 2 returned % | Joint % | Risk drop |
|---|---|---|---|---|---|---|---|
| L0_all_free | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/24/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.78, 0.84]; n=10 |
| L1_immutable | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/21/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.78, 0.87]; n=10 |
| L2_bounds | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/21/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.77, 0.86]; n=10 |
| L3_rates | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/21/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.79 [0.75, 0.82]; n=10 |
| L4_propagation | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/7/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.80 [0.77, 0.82]; n=10 |
| L5_sparsity | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| L6_mahalanobis | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.80, 0.86]; n=10 |
| L7_coupling | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| ablation-Dmax-method-chi_square | 42bd590c11a5b63cda41f1fdcb4bc37be04f5a6b067e5b5bf4f0d4de7e4e7326 | 0.2/3/1/6.555899643782816 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| ablation-Dmax-method-empirical | bf5b24154bcbf161968206005ad4933cce5969968648e4df559ad8806112893c | 0.2/3/1/5.330824290381573/5.691019414122626/6.119537189503274/7.300729302961863/7.361857045253089 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| ablation-reference-all_cycles | 0851c1b04c3bcf30d583982ab85567148e42492699a78e49be9fe5811dff305c | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| ablation-reference-healthy_to_moderate | eb465c0354c7632d600083aa314e836532df30e5d834d96fb533f1d4fce2ba80 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.80, 0.86]; n=10 |
| bounded_without_plausibility | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| dice | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/24/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.84 [0.79, 0.89]; n=10 |
| full | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| no_bounds | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.86 [0.81, 0.90]; n=10 |
| no_coupling_propagation | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.77, 0.85]; n=10 |
| no_immutable_freezing | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.76, 0.84]; n=10 |
| no_mahalanobis | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.78, 0.84]; n=10 |
| no_sparsity | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/7/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| no_validation_in_loop | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-Dmax-chi_square-q-0.95 | 8fc0f0506f455a79b365eb1b8f4682b1f3b28ab6e6bb21b77f0baef5e694733e | 0.2/3/1/6.034486598030301 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-Dmax-chi_square-q-0.99 | 42bd590c11a5b63cda41f1fdcb4bc37be04f5a6b067e5b5bf4f0d4de7e4e7326 | 0.2/3/1/6.555899643782816 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-Dmax-chi_square-q-0.999 | c9a63dc8d0d56ffdf25cd50feb590acdd360cb12e861e3a37a5b5e082d2fac0d | 0.2/3/1/7.153921845909235 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.78, 0.85]; n=10 |
| sensitivity-Dmax-empirical-q-0.95 | 200319bc8c8c9979eaf0015cf03be449027c222e3c776ae2d9f0c4045ec75352 | 0.2/3/1/4.581612281768285/4.66962570469499/4.711480792116022/4.8136143263128695/5.257516002558776 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.79, 0.86]; n=10 |
| sensitivity-Dmax-empirical-q-0.99 | bf5b24154bcbf161968206005ad4933cce5969968648e4df559ad8806112893c | 0.2/3/1/5.330824290381573/5.691019414122626/6.119537189503274/7.300729302961863/7.361857045253089 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-Dmax-empirical-q-0.999 | 7714b8559571c4302badb1335cf001e04badc8724fe9094c59d4a1d77ea7f2b6 | 0.2/3/1/11.05848299986296/7.361880026686216/7.569037015515151/7.987376939697434/8.373096617110614 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-horizon-K-1 | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-horizon-K-10 | f2969e31abfa22cbe21dd23155d7e7d9b3b1dea884a12293657db4585039c671 | 0.2/3/10/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-horizon-K-2 | a27509e73fcf81b8131d697030cf62313002e6447d3ddda0bf3a8a27feff7493 | 0.2/3/2/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-horizon-K-3 | 86c7de3f5aa62d189f91a84aa49972b42fea27dd710f2951a6b66ea2e9554417 | 0.2/3/3/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-horizon-K-5 | ac935687820da6da6e2dad78f7ea00ec095565c35944949163636e7569c673f8 | 0.2/3/5/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-label-H-15 | c182f2816118606efdf34acf1678316e8bedb55df618d64ccdd1f9f9dec1f7e9 | 0.2/3/1/5.0 | 50.00 [20.00, 76.92]; n=10 | 58.33 [29.39, 90.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.28 [0.00, 0.51]; n=10 |
| sensitivity-label-H-30 | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-label-H-50 | 435d7f3552e3baaafde84466a72dd4e5feaa10c06848065012e5a19f047966c2 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.89 [0.86, 0.91]; n=10 |
| sensitivity-sparsity-k_max-1 | be482f81cf13a86200ecc16727cbc38c1425728bd0ab2f20fa05294e11314bc0 | 0.2/1/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.79, 0.87]; n=10 |
| sensitivity-sparsity-k_max-2 | 0a04942711303ca7352de00b1a857433588781325b7a67a7c3a92acaa55cdd26 | 0.2/2/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-sparsity-k_max-3 | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-sparsity-k_max-5 | 359431ea5f336a971da860b8c25a950fe73500eb0f6f8a2e1671bc390d5811b4 | 0.2/5/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-threshold-tau_safe-0.1 | 3122feadc5843c33c5cb518cb8ea8c95a3c881d9be5dd3aa6290e3ed6d8c9977 | 0.1/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.88 [0.84, 0.91]; n=10 |
| sensitivity-threshold-tau_safe-0.2 | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-threshold-tau_safe-0.3 | 003b87cb4c44ad1a61175b0d8f4de1732db6c531069cded7921d821f0f14a547 | 0.3/3/1/5.0 | 66.67 [38.46, 91.67]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.78 [0.72, 0.82]; n=10 |
| sensitivity-weight-alpha-1.0 | c6e5cdb7a39e281efb132a210fad12c17c5d7e7f14860be3f42b8b478eed6397 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.78, 0.85]; n=10 |
| sensitivity-weight-alpha-10.0 | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-weight-alpha-100.0 | d8500c4dbfa6a7b732f6c00cff0861fefc197fef2c8cc24bfe730575c5829129 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.78, 0.84]; n=10 |
| sensitivity-weight-beta-0.0 | 6f6a6ebd0d2737e5b61e55d8cb7ee411678f62f61496892090423d4c7189a2e1 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-weight-beta-1.0 | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-weight-beta-100.0 | b1e4d82d9829cc0d0386669358224e2e37be9118c198fde000bf7657c61537b6 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-weight-gamma-0.0 | c80f64382f4eeec2934ae8163b7e9d05bbe022d6ad9ad31727e05274cda75d62 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-weight-gamma-1.0 | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| sensitivity-weight-gamma-100.0 | 77cab6a99b511409cbdcc737e6ffdca901ebc22248f72f0a383219e7e7bb718e | 0.2/3/1/5.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.80, 0.85]; n=10 |
| unconstrained | b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264 | 0.2/24/1/5.0 | 50.00 [23.08, 80.00]; n=10 | 33.33 [7.68, 63.64]; n=10 | 33.33 [7.68, 63.64]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.62 [0.50, 0.75]; n=10 |

### FD002/xgb/v2

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: FD002/xgb/v2/paired_internal_diagnostic; FAST; solver seed 1729. settings vary only as labeled per row; original final validators retained. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Variant | Effective config SHA-256 | tau / k / K / D_max | Validity % | Tier 2 all % | Tier 2 returned % | Joint % | Risk drop |
|---|---|---|---|---|---|---|---|
| L0_all_free | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/24/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 58.33 [36.36, 81.82]; n=10 | 58.33 [36.36, 81.82]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.78, 0.84]; n=10 |
| L1_immutable | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/21/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 58.33 [36.36, 81.82]; n=10 | 58.33 [36.36, 81.82]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.78, 0.87]; n=10 |
| L2_bounds | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/21/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 50.00 [23.08, 80.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.81 [0.77, 0.86]; n=10 |
| L3_rates | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/21/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 50.00 [20.00, 81.82]; n=10 | 50.00 [20.00, 81.82]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.79 [0.75, 0.82]; n=10 |
| L4_propagation | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/7/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.80 [0.77, 0.82]; n=10 |
| L5_sparsity | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| L6_mahalanobis | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| L7_coupling | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| ablation-Dmax-method-chi_square | dcdda2fc6a893f00de8ef0ff3e69ee589308e86e425609d711def5221fc8db83 | 0.2/3/1/6.555899643782816 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| ablation-Dmax-method-empirical | 551dc3451f3fdd64d62128ebe0b091f6460bb9f260b19f414047f794dbcd170e | 0.2/3/1/5.330824290381573/5.691019414122626/6.119537189503274/7.300729302961863/7.361857045253089 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| ablation-reference-all_cycles | 94a5513787a02ef180c9417ec5f6c9b1a3a42190acfb93ede88865e6c4c00849 | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| ablation-reference-healthy_to_moderate | 4ac8eb2dc9e6c7467e46afdcf312b29a030f53f022226d98e16f5ee0fe43ef17 | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.80, 0.85]; n=10 |
| bounded_without_plausibility | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| dice | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/24/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.84 [0.79, 0.89]; n=10 |
| full | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| no_bounds | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.85 [0.81, 0.88]; n=10 |
| no_coupling_propagation | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 16.67 [0.00, 45.45]; n=10 | 16.67 [0.00, 45.45]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.79 [0.76, 0.83]; n=10 |
| no_immutable_freezing | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.80 [0.76, 0.84]; n=10 |
| no_mahalanobis | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.78, 0.84]; n=10 |
| no_sparsity | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/7/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| no_validation_in_loop | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-Dmax-chi_square-q-0.95 | d1fa6757196069046bccc7222236511bea3df4df3299dfaca9fd72755a924fec | 0.2/3/1/6.034486598030301 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-Dmax-chi_square-q-0.99 | dcdda2fc6a893f00de8ef0ff3e69ee589308e86e425609d711def5221fc8db83 | 0.2/3/1/6.555899643782816 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-Dmax-chi_square-q-0.999 | 9f7a9c141e0bacda60f8d36d92ecf44edb1d660bbae11a01ccf0f98e1e1cc631 | 0.2/3/1/7.153921845909235 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.78, 0.85]; n=10 |
| sensitivity-Dmax-empirical-q-0.95 | 6bf02f1a603afd498e10bea1c66a9d987472ad95630375ea28bee1709e3858fa | 0.2/3/1/4.581612281768285/4.66962570469499/4.711480792116022/4.8136143263128695/5.257516002558776 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.79, 0.86]; n=10 |
| sensitivity-Dmax-empirical-q-0.99 | 551dc3451f3fdd64d62128ebe0b091f6460bb9f260b19f414047f794dbcd170e | 0.2/3/1/5.330824290381573/5.691019414122626/6.119537189503274/7.300729302961863/7.361857045253089 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-Dmax-empirical-q-0.999 | e82cbb76bbdd3b2ab43d8b2ebc8d0f8bab62466bdf6468c25c73a76bb696065e | 0.2/3/1/11.05848299986296/7.361880026686216/7.569037015515151/7.987376939697434/8.373096617110614 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.85]; n=10 |
| sensitivity-horizon-K-1 | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-horizon-K-10 | 9c8698c8b0c8ea5e0a5893702f14307b1755453d49eccd00010df5181e6a7430 | 0.2/3/10/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-horizon-K-2 | c8f7dc38c675881907f3c02882645457f03cf0089c7df1ce4681e4566e996a32 | 0.2/3/2/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-horizon-K-3 | 12f1acb8773fa5552e1e7a251827d8f3dcf69ac087ee4d1fdc54b9487076327b | 0.2/3/3/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-horizon-K-5 | d3bda333eeb0cbbbe4ae7b3a4e5f8d735382c06953789373728b7b9c36d47c27 | 0.2/3/5/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-label-H-15 | ccf3a4f56ec56bb5594992c7c2916a963d32c9ea0785d1d728007cffe6684456 | 0.2/3/1/8.0 | 50.00 [20.00, 76.92]; n=10 | 66.67 [38.46, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 8.33 [0.00, 27.27]; n=10 | 0.28 [0.00, 0.51]; n=10 |
| sensitivity-label-H-30 | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-label-H-50 | 50a6a83ea85d1b5fb68e4b23cc25d8686cc25e9db672ac8971f643c58461070a | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.90 [0.86, 0.92]; n=10 |
| sensitivity-sparsity-k_max-1 | 2131edc4dbfdcad48970ad33b4d14bdbec08c4eadab2f641405c02d9322cb604 | 0.2/1/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.83 [0.79, 0.87]; n=10 |
| sensitivity-sparsity-k_max-2 | a18b72c405f7779977b4db2f8cfc2dfb0175c6ed4a63d7aab0547df28b045970 | 0.2/2/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-sparsity-k_max-3 | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-sparsity-k_max-5 | cc8bad585e1b8bae65f6eb38f4904e4b68d5df9ecb752784c434e3f789376799 | 0.2/5/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-threshold-tau_safe-0.1 | 8af93451ea4af5b76ecc74053d9189cb9af9414b00031577a23d4f345e773757 | 0.1/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.88 [0.84, 0.91]; n=10 |
| sensitivity-threshold-tau_safe-0.2 | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-threshold-tau_safe-0.3 | 497a7e1f6bad07ec424191feba8fe0d8d7dd7c09a758d29ad01be09910282ab3 | 0.3/3/1/8.0 | 66.67 [38.46, 91.67]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.78 [0.72, 0.83]; n=10 |
| sensitivity-weight-alpha-1.0 | 1c88bdefadde5a07c6e980b60f24141111b11184bcb88f4db9f147b246675645 | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.78, 0.84]; n=10 |
| sensitivity-weight-alpha-10.0 | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-weight-alpha-100.0 | 9916034ea64d7622ea79151bb497cd63d2becedfacb00c43e088ee931b7b2a4b | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.80 [0.77, 0.83]; n=10 |
| sensitivity-weight-beta-0.0 | 5ec8552517923edfd57631066a9a7048d5a8b445599feb24e2b25dadeb069e2d | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-weight-beta-1.0 | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-weight-beta-100.0 | fbb707e72e4bbef34d784aa20cccfeeeb75dd9eb9723f1801aa7854227c7ee7d | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-weight-gamma-0.0 | 0aaf30d803ea3be6d489069d2316bffe289ad7669103b4125a331aa67cb81aca | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-weight-gamma-1.0 | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| sensitivity-weight-gamma-100.0 | e25947e4edab3279d99ca26466d256e9981a626811e21bdbd369abe2002083ec | 0.2/3/1/8.0 | 100.00 [100.00, 100.00]; n=10 | 8.33 [0.00, 23.08]; n=10 | 8.33 [0.00, 23.08]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.82 [0.79, 0.84]; n=10 |
| unconstrained | 657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd | 0.2/24/1/8.0 | 50.00 [23.08, 80.00]; n=10 | 83.33 [66.67, 100.00]; n=10 | 83.33 [66.67, 100.00]; n=10 | 0.00 [0.00, 0.00]; n=10 | 0.62 [0.50, 0.75]; n=10 |

## Reference search and leverage

All declared production cases have leverage measurements. Reference classification applies only to failed production cases; successful production cases are not relabeled. Every reference checkpoint must reproduce the production candidate before claiming a finite search superset. Absence on the finite union remains **unresolved**, never a global continuous or real-machine infeasibility certificate. Endpoint leverage and margins are in reference.json.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: failed paired production states only; FAST; diagnostic seed; both D_max versions. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Failed production group | Classification | Share % (engine CI) | Failed observations |
|---|---|---|---|
| FD002/xgb/v2/paired_internal_diagnostic/fast/full | unresolved_finite_search | 100.00 [100.00, 100.00]; n=10 | 12 |
| FD002/xgb/v1/paired_internal_diagnostic/fast/full | unresolved_finite_search | 100.00 [100.00, 100.00]; n=10 | 12 |
| FD001/xgb/v1/paired_internal_diagnostic/fast/full | unresolved_finite_search | 100.00 [100.00, 100.00]; n=7 | 8 |
| FD001/xgb/v2/paired_internal_diagnostic/fast/full | unresolved_finite_search | 100.00 [100.00, 100.00]; n=7 | 8 |

## Warm serial latency

The workload is fixed-order repeated validation alerts for FD001/XGBoost/v1, K=1, k_max=3, D_max=5. It is a development workload, not a latency estimate over all datasets/models or unseen deployment machines. Ten warmups per mode are excluded. Each measured call actually executes recommendation; no cached recommendation substitutes for computation. Budgets use the upper number only; faster passes. Backend total excludes UI/network/startup. THOROUGH need not be slower on every state because its search can terminate differently.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: development_all_alerts_repeated_fixed_order. FD001/xgb/v1; k_max=3; K=1; D_max=5; config SHA-256 47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Mode | Stage | Calls | p50 ms | p95 ms | p99 ms | p95 engine CI (ms) | Upper budget ms | Verdict |
|---|---|---|---|---|---|---|---|---|
| FAST | ingestion_ms | 1000 | 0.123 | 0.178 | 0.226 | 0.18 [0.17, 0.18]; n=16 | 10.000 | pass |
| FAST | inference_ms | 1000 | 2.334 | 3.048 | 3.640 | 3.05 [3.02, 3.12]; n=16 | 15.000 | pass |
| FAST | optimization_ms | 1000 | 1339.744 | 2339.075 | 2768.989 | 2339.07 [2256.87, 2403.27]; n=16 | 1800.000 | miss |
| FAST | validation_ms | 1000 | 4.010 | 5.494 | 6.448 | 5.49 [5.21, 5.68]; n=16 | 100.000 | pass |
| FAST | pipeline_ms | 1000 | 1348.602 | 2348.233 | 2776.910 | 2348.23 [2265.85, 2414.08]; n=16 | 2200.000 | miss |
| FAST | dashboard_ms | 0 | NA | NA | NA | unmeasured | 250.000 | unmeasured |
| THOROUGH | ingestion_ms | 1000 | 0.124 | 0.183 | 0.232 | 0.18 [0.18, 0.20]; n=16 | 10.000 | pass |
| THOROUGH | inference_ms | 1000 | 2.347 | 3.109 | 3.775 | 3.11 [3.00, 3.21]; n=16 | 15.000 | pass |
| THOROUGH | optimization_ms | 1000 | 1127.764 | 2080.227 | 2574.888 | 2080.23 [2029.10, 2171.67]; n=16 | 1800.000 | miss |
| THOROUGH | validation_ms | 1000 | 4.186 | 5.771 | 7.801 | 5.77 [5.57, 6.10]; n=16 | 100.000 | pass |
| THOROUGH | pipeline_ms | 1000 | 1136.644 | 2089.845 | 2584.860 | 2089.85 [2039.34, 2181.37]; n=16 | 2200.000 | pass |
| THOROUGH | dashboard_ms | 0 | NA | NA | NA | unmeasured | 250.000 | unmeasured |

Optimization dominates latency. Its p95 misses the 1.80 s budget in both modes; FAST total also exceeds 2.20 s, while THOROUGH total passes. Ingestion, inference and validation pass their upper budgets. These misses are retained as measured design gaps. Phase 9 profiling may identify result-preserving optimizations; it cannot rewrite this historical measurement.

## Evidence files and reproduction

The full saved report has 272 groups, including all development, first-alert, diagnostic and sensitivity strata. Its risk histogram and K curve are standalone HTML files. All raw telemetry/fitted artifacts and generated experiment outputs remain git-ignored.

To regenerate the full saved report without running an experiment:

```powershell
uv run python scripts/diagnostics/phase7_experiments.py --run-id phase7-20261020T102540Z --stage report
```

This command requires the frozen study, configs, raw archive, prepared artifacts and saved SQLite checkpoints. A new measurement must use a new run ID and committed protocol; do not rerun completed measurements to improve a target.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: complete saved evidence; file hashes are integrity references, not performance metrics. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Saved evidence | SHA-256 |
|---|---|
| artifacts/experiments/phase7-20261020T102540Z/manifest.json | 4b4497f856f8af6bf5966942b488bbac0b0d0474645910777fa0762730d6da1d |
| artifacts/experiments/phase7-20261020T102540Z/stages.json | f75e4edc765bf6d2737ddfd64df051079607ab025b17b83519e733dcf87ec9e0 |
| artifacts/experiments/phase7-20261020T102540Z/summary.json | e0de87c06b418be761142d259ccad8870b81232217b6d75303ee7a91957082fe |
| artifacts/experiments/phase7-20261020T102540Z/metrics.csv | 0c137be416a912493147e8662d707b2f299b5024ba460ca564ad3d299b311b41 |
| artifacts/experiments/phase7-20261020T102540Z/report.md | b8d8414c5b1fa1c22b8474509c3c150f21b4320430909b48a25784975076b39a |
| artifacts/experiments/phase7-20261020T102540Z/reference.json | ea5796526729f1717baf15ac6168e319388568b5298741950343e09f026f7891 |
| artifacts/experiments/phase7-20261020T102540Z/latency.json | e0915d1178942d8804dd0b2b60c7c529e783757325faa504e46bb8cc0a55b78f |

## Closure audit and software gate

Independent audit found no discrepancy or missing required measurement. Audit scope is explicit: all records received structural/logical checks; numerical predictor/validator recomputation was stratified, not a full re-execution of every recommendation.

- All 173,986 records/cases: exact identity/config/policy/seed/population/input/partition/acceptance checks passed; 112 fitted-artifact hashes and 44 diagnostic-validator hashes matched.
- Independent numerical recomputation: 1,631 observed strata, including 220 genuine LSTM history checks. True calibrated risks, coupling margins, raw/scaled L1, raw input and RUL errors were zero. Maximum D_M error was 2.27e-13; maximum round-trip error 2.84e-14.
- Independently recomputed 26,970 whole-engine intervals, 9,248 seed statistics and 1,904 funnel counts; all matched.
- Reference coverage: 48 leverage cases and 40 failed-production oracle records; all finite absences remain unresolved. Recorded production reproduction/superset proofs were checked; the independent audit did not rerun optimization.
- Latency workload identity was independently reconstructed from all 3,145 validation telemetry rows using saved singleton predictor inference. The 376 alerts, 16 engines and every persisted engine/cycle index matched. No model fitting or recourse computation was performed during that audit.
- FD002 high-Tier-1 leakage guard: all input features are sensors/operating settings, not RUL/labels/engine IDs/cycle. Fitting, calibration and test partitions remain disjoint. Base and fold/H training provenance is retained rather than relabeled as measurement-source training.
- Ruff: clean. Strict mypy: clean for 55 source files. Pytest: **276 passed**, 70 warnings, 119.22 s in the final precision-corrected run. Docs presence and locked dependency checks passed.
- Coverage: **83.350719799708%** branch-inclusive and **87.289539056031%** line coverage. Branch-inclusive coverage equals the pre-measurement Phase 7 value and exceeds the Phase 6 baseline. The enforced floor is ratcheted to the exact Phase 7 value. Explicit precision corrects the coverage tool's integer-rounding comparison; the threshold was not reduced.
- The supplemental report was independently compared with saved summaries: no value mismatch. Runtime-hash registry scope, JSON-field locations and float endpoint labels were corrected without changing measurements. The complete gate passes with honestly retained target misses.

Run `phase7-20261020T102540Z`; measured source `63c2ed445fba16c73a2771e184f635abf76b4405`; committed study config `configs\experiments\phase7-study.yaml` (SHA-256 `67094790e414a57b3d6a403f3682bd3ebb1914be74584379c482ddfad1d48c5a`). Population: independent audits and final software gate; no measurements rerun. k_max=3; K=1; D_max v1=5 / v2=8. Profile/variant rows identify the protocol and effective configuration; base/internal FAST hashes are registered below; exact fold/mode runtime hashes are in each saved report group label.

| Final evidence | SHA-256 |
|---|---|
| artifacts/phase7-final-audit/framework-audit.json | d4b9b16bc771e6d65ce8966abb7025eb81d3270ba0ee1e40b7f95196d4a0d078 |
| artifacts/phase7-final-audit/numerical_audit.json | b3e21a5405c7d85f840656b52e3236996dbe5dc4345ad29d9a5598a6cf920d2d |
| artifacts/phase7-final-audit/interval-reference-latency-audit.json | fc3b6bd49012a854cdf3d0c6ae2b0170a37059fdae006fb9239aa9c78b17af88 |
| artifacts/phase7-final-audit/latency-workload-identity-audit.json | 6d0fb8c8907af0425aca3f423cbd5d71ef6e92514fc8fc6e37ed40ee9c3e9c20 |
| artifacts/phase7-final-audit/fd002-leakage-metadata.json | ec47956cb275411343f8f1f113c45391f2cf448ce4d22c76f87e727d9acc2197 |
| artifacts/phase7-final-gate-status.json | b24b06b4b6ddd20b92dd88d90071416184a73d92c3cd5bc4936ca6b539f3b256 |
| artifacts/phase7-final-gate-precise.log | 1139d93e54da084fae73fa4db7de5d71fbe62056e69b7e6c8641405e32e46c53 |
| artifacts/phase7-final-coverage.json | d7ef920f8088c492e4eff384cdce7d2974367ac88f9e67aa02b7b90f1df11e43 |

