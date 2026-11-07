# Complete C-MAPSS arithmetic-repair impact

Analysis run `phase12-impact-20261108-v1`; source `0d0e6db33bdc47b87ffcd601985eda910fccaf3d`; config SHA256 `3c6dc6473d967404a42dc98816f0c5b78ca46ab9ae091e343ff8ff699c20b438`.

Real benchmark: NASA C-MAPSS FD001 and FD002. Results stay separate by dataset, model, protocol and population.
Each interval is a 95% whole-engine bootstrap (2,000 replicates, seed 1729); N is engines, d is the disclosed denominator.
Validity is calibrated risk <=0.20 (E1). Tier 2 is statistical plausibility (E2); Tiers 3–4 use legacy proxy assumptions (at most E3).
Joint is an additional stricter metric. Failed queries remain in all-query denominators. No physical benefit, safety certification or RUL-extension claim.
Intervals equal to [1,1] describe the empirical bootstrap sample and do not establish certainty for unseen engines.
Parallel replay timings are retained in the source archives and do not certify serial latency.

Historical run `phase7-20261020T102540Z` / source `63c2ed445fba16c73a2771e184f635abf76b4405` remains immutable.
Corrected runs `phase12-corrected-20261107-a` and `phase12-corrected-20261107-b` / source `3441e259b7b57c5ca4b8981298deb24acb1c0ae0`.
Earlier failed Phase 12 intermediate arithmetic runs are superseded for headline use by the demonstrated graph/layout repair; their records remain preserved.

## FD001/lstm/v1/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "b180c160afbd88af629e4c2215703bb0454fbe6916187d9cdc5e5bc86a822a62"}, "corrected_b": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "b180c160afbd88af629e4c2215703bb0454fbe6916187d9cdc5e5bc86a822a62"}, "historical": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "b180c160afbd88af629e4c2215703bb0454fbe6916187d9cdc5e5bc86a822a62"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "lstm", "population": "grouped_oof_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| plausibility_all | 0.228827362 [0.192894166, 0.264114279]; N=100; d=2456 | 0.228827362 [0.192894166, 0.264114279]; N=100; d=2456 | 0.228827362 [0.192894166, 0.264114279]; N=100; d=2456 |
| plausibility_returned | 0.237215299 [0.202864041, 0.271370341]; N=100; d=2327 | 0.237215299 [0.202864041, 0.271370341]; N=100; d=2327 | 0.237215299 [0.202864041, 0.271370341]; N=100; d=2327 |
| tier3 | 0.95276873 [0.922692929, 0.979037478]; N=100; d=2456 | 0.95276873 [0.922692929, 0.979037478]; N=100; d=2456 | 0.95276873 [0.922692929, 0.979037478]; N=100; d=2456 |
| tier4 | 0.919381107 [0.897406082, 0.938243068]; N=100; d=2456 | 0.919381107 [0.897406082, 0.938243068]; N=100; d=2456 | 0.919381107 [0.897406082, 0.938243068]; N=100; d=2456 |
| joint_tiers | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| joint | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| NO_INTERVENTION | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| RECOVERABLE | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| PARTIAL | 0.0191368078 [0.0115212182, 0.0284670778]; N=100; d=2456 | 0.0191368078 [0.0115212182, 0.0284670778]; N=100; d=2456 | 0.0191368078 [0.0115212182, 0.0284670778]; N=100; d=2456 |
| ESCALATE | 0.980863192 [0.971532922, 0.988478782]; N=100; d=2456 | 0.980863192 [0.971532922, 0.988478782]; N=100; d=2456 | 0.980863192 [0.971532922, 0.988478782]; N=100; d=2456 |
| risk_reduction | 0.048938918 [0.0416092045, 0.0565509076]; N=100; d=2456 | 0.048938918 [0.0416092045, 0.0565509076]; N=100; d=2456 | 0.048938918 [0.0416092045, 0.0565509076]; N=100; d=2456 |
| sparsity_all | 2.86400651 [2.7725775, 2.94309254]; N=100; d=2456 | 2.86400651 [2.7725775, 2.94309254]; N=100; d=2456 | 2.86400651 [2.7725775, 2.94309254]; N=100; d=2456 |
| sparsity_returned | 3 [3, 3]; N=100; d=2327 | 3 [3, 3]; N=100; d=2327 | 3 [3, 3]; N=100; d=2327 |

historical query denominators: `{"all_queries": 2456, "failed_joint": 2456, "failed_model_validity": 2456, "not_returned": 129, "returned": 2327, "triage_counts": {"ESCALATE": 2409, "PARTIAL": 47}}`.

corrected_a query denominators: `{"all_queries": 2456, "failed_joint": 2456, "failed_model_validity": 2456, "not_returned": 129, "returned": 2327, "triage_counts": {"ESCALATE": 2409, "PARTIAL": 47}}`.

corrected_b query denominators: `{"all_queries": 2456, "failed_joint": 2456, "failed_model_validity": 2456, "not_returned": 129, "returned": 2327, "triage_counts": {"ESCALATE": 2409, "PARTIAL": 47}}`.

## FD001/lstm/v1/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "78cd7e7d9c4845cd7803c83a5c73b38f5580c23d99cdddd3e3705ba8f5bb7685"}, "corrected_b": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "78cd7e7d9c4845cd7803c83a5c73b38f5580c23d99cdddd3e3705ba8f5bb7685"}, "historical": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "78cd7e7d9c4845cd7803c83a5c73b38f5580c23d99cdddd3e3705ba8f5bb7685"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "lstm", "population": "internal_heldout_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| plausibility_all | 0.217142857 [0.153417166, 0.281526515]; N=15; d=350 | 0.217142857 [0.153417166, 0.281526515]; N=15; d=350 | 0.217142857 [0.153417166, 0.281526515]; N=15; d=350 |
| plausibility_returned | 0.217142857 [0.153417166, 0.281526515]; N=15; d=350 | 0.217142857 [0.153417166, 0.281526515]; N=15; d=350 | 0.217142857 [0.153417166, 0.281526515]; N=15; d=350 |
| tier3 | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 |
| tier4 | 0.948571429 [0.923724278, 0.969703179]; N=15; d=350 | 0.948571429 [0.923724278, 0.969703179]; N=15; d=350 | 0.948571429 [0.923724278, 0.969703179]; N=15; d=350 |
| joint_tiers | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| joint | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| NO_INTERVENTION | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| RECOVERABLE | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| PARTIAL | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| ESCALATE | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 |
| risk_reduction | 0.042170111 [0.0316280759, 0.0522147096]; N=15; d=350 | 0.042170111 [0.0316280759, 0.0522147096]; N=15; d=350 | 0.042170111 [0.0316280759, 0.0522147096]; N=15; d=350 |
| sparsity_all | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 |
| sparsity_returned | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 |

historical query denominators: `{"all_queries": 350, "failed_joint": 350, "failed_model_validity": 350, "not_returned": 0, "returned": 350, "triage_counts": {"ESCALATE": 350}}`.

corrected_a query denominators: `{"all_queries": 350, "failed_joint": 350, "failed_model_validity": 350, "not_returned": 0, "returned": 350, "triage_counts": {"ESCALATE": 350}}`.

corrected_b query denominators: `{"all_queries": 350, "failed_joint": 350, "failed_model_validity": 350, "not_returned": 0, "returned": 350, "triage_counts": {"ESCALATE": 350}}`.

## FD001/lstm/v1/official_test_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "78cd7e7d9c4845cd7803c83a5c73b38f5580c23d99cdddd3e3705ba8f5bb7685"}, "corrected_b": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "78cd7e7d9c4845cd7803c83a5c73b38f5580c23d99cdddd3e3705ba8f5bb7685"}, "historical": {"configs/experiments/phase7-FD001-lstm-v1.yaml": "78cd7e7d9c4845cd7803c83a5c73b38f5580c23d99cdddd3e3705ba8f5bb7685"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "lstm", "population": "official_test_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| plausibility_all | 0.311594203 [0.195400054, 0.42468466]; N=16; d=138 | 0.311594203 [0.195400054, 0.42468466]; N=16; d=138 | 0.311594203 [0.195400054, 0.42468466]; N=16; d=138 |
| plausibility_returned | 0.311594203 [0.195400054, 0.42468466]; N=16; d=138 | 0.311594203 [0.195400054, 0.42468466]; N=16; d=138 | 0.311594203 [0.195400054, 0.42468466]; N=16; d=138 |
| tier3 | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 |
| tier4 | 0.985507246 [0.965517241, 1]; N=16; d=138 | 0.985507246 [0.965517241, 1]; N=16; d=138 | 0.985507246 [0.965517241, 1]; N=16; d=138 |
| joint_tiers | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| joint | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| NO_INTERVENTION | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| RECOVERABLE | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| PARTIAL | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| ESCALATE | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 |
| risk_reduction | 0.111555518 [0.0910890505, 0.133671791]; N=16; d=138 | 0.111555518 [0.0910890505, 0.133671791]; N=16; d=138 | 0.111555518 [0.0910890505, 0.133671791]; N=16; d=138 |
| sparsity_all | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 |
| sparsity_returned | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 |

historical query denominators: `{"all_queries": 138, "failed_joint": 138, "failed_model_validity": 138, "not_returned": 0, "returned": 138, "triage_counts": {"ESCALATE": 138}}`.

corrected_a query denominators: `{"all_queries": 138, "failed_joint": 138, "failed_model_validity": 138, "not_returned": 0, "returned": 138, "triage_counts": {"ESCALATE": 138}}`.

corrected_b query denominators: `{"all_queries": 138, "failed_joint": 138, "failed_model_validity": 138, "not_returned": 0, "returned": 138, "triage_counts": {"ESCALATE": 138}}`.

## FD001/lstm/v2/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "53be5cd8279dc27aaa0a13c7edc46b83b98f6d7422f0b923816f1bd96dfcd7e0"}, "corrected_b": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "53be5cd8279dc27aaa0a13c7edc46b83b98f6d7422f0b923816f1bd96dfcd7e0"}, "historical": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "53be5cd8279dc27aaa0a13c7edc46b83b98f6d7422f0b923816f1bd96dfcd7e0"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "lstm", "population": "grouped_oof_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| plausibility_all | 0.976791531 [0.965457542, 0.986684359]; N=100; d=2456 | 0.976791531 [0.965457542, 0.986684359]; N=100; d=2456 | 0.976791531 [0.965457542, 0.986684359]; N=100; d=2456 |
| plausibility_returned | 0.985388913 [0.979017336, 0.991353677]; N=100; d=2327 | 0.985388913 [0.979017336, 0.991353677]; N=100; d=2327 | 0.985388913 [0.979017336, 0.991353677]; N=100; d=2327 |
| tier3 | 0.95276873 [0.922692929, 0.979037478]; N=100; d=2456 | 0.95276873 [0.922692929, 0.979037478]; N=100; d=2456 | 0.95276873 [0.922692929, 0.979037478]; N=100; d=2456 |
| tier4 | 0.919381107 [0.897406082, 0.938243068]; N=100; d=2456 | 0.919381107 [0.897406082, 0.938243068]; N=100; d=2456 | 0.919381107 [0.897406082, 0.938243068]; N=100; d=2456 |
| joint_tiers | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| joint | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| NO_INTERVENTION | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| RECOVERABLE | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 | 0 [0, 0]; N=100; d=2456 |
| PARTIAL | 0.0423452769 [0.0292948406, 0.0575420218]; N=100; d=2456 | 0.0423452769 [0.0292948406, 0.0575420218]; N=100; d=2456 | 0.0423452769 [0.0292948406, 0.0575420218]; N=100; d=2456 |
| ESCALATE | 0.957654723 [0.942457978, 0.970705159]; N=100; d=2456 | 0.957654723 [0.942457978, 0.970705159]; N=100; d=2456 | 0.957654723 [0.942457978, 0.970705159]; N=100; d=2456 |
| risk_reduction | 0.048938918 [0.0416092045, 0.0565509076]; N=100; d=2456 | 0.048938918 [0.0416092045, 0.0565509076]; N=100; d=2456 | 0.048938918 [0.0416092045, 0.0565509076]; N=100; d=2456 |
| sparsity_all | 2.86400651 [2.7725775, 2.94309254]; N=100; d=2456 | 2.86400651 [2.7725775, 2.94309254]; N=100; d=2456 | 2.86400651 [2.7725775, 2.94309254]; N=100; d=2456 |
| sparsity_returned | 3 [3, 3]; N=100; d=2327 | 3 [3, 3]; N=100; d=2327 | 3 [3, 3]; N=100; d=2327 |

historical query denominators: `{"all_queries": 2456, "failed_joint": 2456, "failed_model_validity": 2456, "not_returned": 129, "returned": 2327, "triage_counts": {"ESCALATE": 2352, "PARTIAL": 104}}`.

corrected_a query denominators: `{"all_queries": 2456, "failed_joint": 2456, "failed_model_validity": 2456, "not_returned": 129, "returned": 2327, "triage_counts": {"ESCALATE": 2352, "PARTIAL": 104}}`.

corrected_b query denominators: `{"all_queries": 2456, "failed_joint": 2456, "failed_model_validity": 2456, "not_returned": 129, "returned": 2327, "triage_counts": {"ESCALATE": 2352, "PARTIAL": 104}}`.

## FD001/lstm/v2/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "70f7b33fb185b281c4430ad928be7ce5485544ea50f9db122a062d2c0bd044ba"}, "corrected_b": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "70f7b33fb185b281c4430ad928be7ce5485544ea50f9db122a062d2c0bd044ba"}, "historical": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "70f7b33fb185b281c4430ad928be7ce5485544ea50f9db122a062d2c0bd044ba"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "lstm", "population": "internal_heldout_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| plausibility_all | 0.994285714 [0.985875706, 1]; N=15; d=350 | 0.994285714 [0.985875706, 1]; N=15; d=350 | 0.994285714 [0.985875706, 1]; N=15; d=350 |
| plausibility_returned | 0.994285714 [0.985875706, 1]; N=15; d=350 | 0.994285714 [0.985875706, 1]; N=15; d=350 | 0.994285714 [0.985875706, 1]; N=15; d=350 |
| tier3 | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 |
| tier4 | 0.948571429 [0.923724278, 0.969703179]; N=15; d=350 | 0.948571429 [0.923724278, 0.969703179]; N=15; d=350 | 0.948571429 [0.923724278, 0.969703179]; N=15; d=350 |
| joint_tiers | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| joint | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| NO_INTERVENTION | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| RECOVERABLE | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| PARTIAL | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 | 0 [0, 0]; N=15; d=350 |
| ESCALATE | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 | 1 [1, 1]; N=15; d=350 |
| risk_reduction | 0.042170111 [0.0316280759, 0.0522147096]; N=15; d=350 | 0.042170111 [0.0316280759, 0.0522147096]; N=15; d=350 | 0.042170111 [0.0316280759, 0.0522147096]; N=15; d=350 |
| sparsity_all | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 |
| sparsity_returned | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 | 3 [3, 3]; N=15; d=350 |

historical query denominators: `{"all_queries": 350, "failed_joint": 350, "failed_model_validity": 350, "not_returned": 0, "returned": 350, "triage_counts": {"ESCALATE": 350}}`.

corrected_a query denominators: `{"all_queries": 350, "failed_joint": 350, "failed_model_validity": 350, "not_returned": 0, "returned": 350, "triage_counts": {"ESCALATE": 350}}`.

corrected_b query denominators: `{"all_queries": 350, "failed_joint": 350, "failed_model_validity": 350, "not_returned": 0, "returned": 350, "triage_counts": {"ESCALATE": 350}}`.

## FD001/lstm/v2/official_test_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "70f7b33fb185b281c4430ad928be7ce5485544ea50f9db122a062d2c0bd044ba"}, "corrected_b": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "70f7b33fb185b281c4430ad928be7ce5485544ea50f9db122a062d2c0bd044ba"}, "historical": {"configs/experiments/phase7-FD001-lstm-v2.yaml": "70f7b33fb185b281c4430ad928be7ce5485544ea50f9db122a062d2c0bd044ba"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "lstm", "population": "official_test_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| plausibility_all | 0.97826087 [0.938593117, 1]; N=16; d=138 | 0.97826087 [0.938593117, 1]; N=16; d=138 | 0.97826087 [0.938593117, 1]; N=16; d=138 |
| plausibility_returned | 0.97826087 [0.938593117, 1]; N=16; d=138 | 0.97826087 [0.938593117, 1]; N=16; d=138 | 0.97826087 [0.938593117, 1]; N=16; d=138 |
| tier3 | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 |
| tier4 | 0.985507246 [0.965517241, 1]; N=16; d=138 | 0.985507246 [0.965517241, 1]; N=16; d=138 | 0.985507246 [0.965517241, 1]; N=16; d=138 |
| joint_tiers | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| joint | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| NO_INTERVENTION | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| RECOVERABLE | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| PARTIAL | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 | 0 [0, 0]; N=16; d=138 |
| ESCALATE | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 | 1 [1, 1]; N=16; d=138 |
| risk_reduction | 0.111555518 [0.0910890505, 0.133671791]; N=16; d=138 | 0.111555518 [0.0910890505, 0.133671791]; N=16; d=138 | 0.111555518 [0.0910890505, 0.133671791]; N=16; d=138 |
| sparsity_all | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 |
| sparsity_returned | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 | 3 [3, 3]; N=16; d=138 |

historical query denominators: `{"all_queries": 138, "failed_joint": 138, "failed_model_validity": 138, "not_returned": 0, "returned": 138, "triage_counts": {"ESCALATE": 138}}`.

corrected_a query denominators: `{"all_queries": 138, "failed_joint": 138, "failed_model_validity": 138, "not_returned": 0, "returned": 138, "triage_counts": {"ESCALATE": 138}}`.

corrected_b query denominators: `{"all_queries": 138, "failed_joint": 138, "failed_model_validity": 138, "not_returned": 0, "returned": 138, "triage_counts": {"ESCALATE": 138}}`.

## FD001/mlp/v1/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "554b89577ba6a433741ede9cbe8cd33d2d6921d448d18d2d15f49822b1596b1f"}, "corrected_b": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "554b89577ba6a433741ede9cbe8cd33d2d6921d448d18d2d15f49822b1596b1f"}, "historical": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "554b89577ba6a433741ede9cbe8cd33d2d6921d448d18d2d15f49822b1596b1f"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "mlp", "population": "grouped_oof_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.500404531 [0.470830696, 0.530829136]; N=100; d=2472 | 0.500404531 [0.470830696, 0.530829136]; N=100; d=2472 | 0.500404531 [0.470830696, 0.530829136]; N=100; d=2472 |
| plausibility_all | 0.447411003 [0.404464839, 0.492739412]; N=100; d=2472 | 0.447411003 [0.404464839, 0.492739412]; N=100; d=2472 | 0.447411003 [0.404464839, 0.492739412]; N=100; d=2472 |
| plausibility_returned | 0.467776355 [0.427994616, 0.511308654]; N=100; d=2343 | 0.467776355 [0.427994616, 0.511308654]; N=100; d=2343 | 0.467776355 [0.427994616, 0.511308654]; N=100; d=2343 |
| tier3 | 0.953074434 [0.922541284, 0.979228792]; N=100; d=2472 | 0.953074434 [0.922541284, 0.979228792]; N=100; d=2472 | 0.953074434 [0.922541284, 0.979228792]; N=100; d=2472 |
| tier4 | 0.920307443 [0.899104126, 0.938656199]; N=100; d=2472 | 0.920307443 [0.899104126, 0.938656199]; N=100; d=2472 | 0.920307443 [0.899104126, 0.938656199]; N=100; d=2472 |
| joint_tiers | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 |
| joint | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 |
| NO_INTERVENTION | 0 [0, 0]; N=100; d=2472 | 0 [0, 0]; N=100; d=2472 | 0 [0, 0]; N=100; d=2472 |
| RECOVERABLE | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 | 0.352750809 [0.32020467, 0.386179631]; N=100; d=2472 |
| PARTIAL | 0.0440938511 [0.0345405452, 0.0551023645]; N=100; d=2472 | 0.0440938511 [0.0345405452, 0.0551023645]; N=100; d=2472 | 0.0440938511 [0.0345405452, 0.0551023645]; N=100; d=2472 |
| ESCALATE | 0.60315534 [0.563835061, 0.641960187]; N=100; d=2472 | 0.60315534 [0.563835061, 0.641960187]; N=100; d=2472 | 0.60315534 [0.563835061, 0.641960187]; N=100; d=2472 |
| risk_reduction | 0.535384907 [0.509899507, 0.559896831]; N=100; d=2472 | 0.535384907 [0.509899507, 0.559896831]; N=100; d=2472 | 0.535384907 [0.509899507, 0.559896831]; N=100; d=2472 |
| sparsity_all | 2.74878641 [2.66259704, 2.8266173]; N=100; d=2472 | 2.74878641 [2.66259704, 2.8266173]; N=100; d=2472 | 2.74878641 [2.66259704, 2.8266173]; N=100; d=2472 |
| sparsity_returned | 2.87750747 [2.85640335, 2.89857024]; N=100; d=2343 | 2.87750747 [2.85640335, 2.89857024]; N=100; d=2343 | 2.87750747 [2.85640335, 2.89857024]; N=100; d=2343 |

historical query denominators: `{"all_queries": 2472, "failed_joint": 1600, "failed_model_validity": 1235, "not_returned": 129, "returned": 2343, "triage_counts": {"ESCALATE": 1491, "PARTIAL": 109, "RECOVERABLE": 872}}`.

corrected_a query denominators: `{"all_queries": 2472, "failed_joint": 1600, "failed_model_validity": 1235, "not_returned": 129, "returned": 2343, "triage_counts": {"ESCALATE": 1491, "PARTIAL": 109, "RECOVERABLE": 872}}`.

corrected_b query denominators: `{"all_queries": 2472, "failed_joint": 1600, "failed_model_validity": 1235, "not_returned": 129, "returned": 2343, "triage_counts": {"ESCALATE": 1491, "PARTIAL": 109, "RECOVERABLE": 872}}`.

## FD001/mlp/v1/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "055449ac85ff54bc6b7793b41849f5e22f5fc642c2613e5ba953e15cfb686248"}, "corrected_b": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "055449ac85ff54bc6b7793b41849f5e22f5fc642c2613e5ba953e15cfb686248"}, "historical": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "055449ac85ff54bc6b7793b41849f5e22f5fc642c2613e5ba953e15cfb686248"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "mlp", "population": "internal_heldout_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.543766578 [0.472771152, 0.607942941]; N=15; d=377 | 0.543766578 [0.472771152, 0.607942941]; N=15; d=377 | 0.543766578 [0.472771152, 0.607942941]; N=15; d=377 |
| plausibility_all | 0.469496021 [0.371119975, 0.555809903]; N=15; d=377 | 0.469496021 [0.371119975, 0.555809903]; N=15; d=377 | 0.469496021 [0.371119975, 0.555809903]; N=15; d=377 |
| plausibility_returned | 0.469496021 [0.371119975, 0.555809903]; N=15; d=377 | 0.469496021 [0.371119975, 0.555809903]; N=15; d=377 | 0.469496021 [0.371119975, 0.555809903]; N=15; d=377 |
| tier3 | 1 [1, 1]; N=15; d=377 | 1 [1, 1]; N=15; d=377 | 1 [1, 1]; N=15; d=377 |
| tier4 | 0.944297082 [0.919997416, 0.967059568]; N=15; d=377 | 0.944297082 [0.919997416, 0.967059568]; N=15; d=377 | 0.944297082 [0.919997416, 0.967059568]; N=15; d=377 |
| joint_tiers | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 |
| joint | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 |
| NO_INTERVENTION | 0 [0, 0]; N=15; d=377 | 0 [0, 0]; N=15; d=377 | 0 [0, 0]; N=15; d=377 |
| RECOVERABLE | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 | 0.381962865 [0.299459906, 0.451706348]; N=15; d=377 |
| PARTIAL | 0.0397877984 [0.0248123603, 0.0557310134]; N=15; d=377 | 0.0397877984 [0.0248123603, 0.0557310134]; N=15; d=377 | 0.0397877984 [0.0248123603, 0.0557310134]; N=15; d=377 |
| ESCALATE | 0.578249337 [0.5, 0.664776446]; N=15; d=377 | 0.578249337 [0.5, 0.664776446]; N=15; d=377 | 0.578249337 [0.5, 0.664776446]; N=15; d=377 |
| risk_reduction | 0.583659723 [0.526925377, 0.633574812]; N=15; d=377 | 0.583659723 [0.526925377, 0.633574812]; N=15; d=377 | 0.583659723 [0.526925377, 0.633574812]; N=15; d=377 |
| sparsity_all | 2.85411141 [2.80716151, 2.90333567]; N=15; d=377 | 2.85411141 [2.80716151, 2.90333567]; N=15; d=377 | 2.85411141 [2.80716151, 2.90333567]; N=15; d=377 |
| sparsity_returned | 2.85411141 [2.80716151, 2.90333567]; N=15; d=377 | 2.85411141 [2.80716151, 2.90333567]; N=15; d=377 | 2.85411141 [2.80716151, 2.90333567]; N=15; d=377 |

historical query denominators: `{"all_queries": 377, "failed_joint": 233, "failed_model_validity": 172, "not_returned": 0, "returned": 377, "triage_counts": {"ESCALATE": 218, "PARTIAL": 15, "RECOVERABLE": 144}}`.

corrected_a query denominators: `{"all_queries": 377, "failed_joint": 233, "failed_model_validity": 172, "not_returned": 0, "returned": 377, "triage_counts": {"ESCALATE": 218, "PARTIAL": 15, "RECOVERABLE": 144}}`.

corrected_b query denominators: `{"all_queries": 377, "failed_joint": 233, "failed_model_validity": 172, "not_returned": 0, "returned": 377, "triage_counts": {"ESCALATE": 218, "PARTIAL": 15, "RECOVERABLE": 144}}`.

## FD001/mlp/v1/official_test_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "055449ac85ff54bc6b7793b41849f5e22f5fc642c2613e5ba953e15cfb686248"}, "corrected_b": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "055449ac85ff54bc6b7793b41849f5e22f5fc642c2613e5ba953e15cfb686248"}, "historical": {"configs/experiments/phase7-FD001-mlp-v1.yaml": "055449ac85ff54bc6b7793b41849f5e22f5fc642c2613e5ba953e15cfb686248"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "mlp", "population": "official_test_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.911764706 [0.858024691, 0.962031287]; N=19; d=170 | 0.911764706 [0.858024691, 0.962031287]; N=19; d=170 | 0.911764706 [0.858024691, 0.962031287]; N=19; d=170 |
| plausibility_all | 0.788235294 [0.705544872, 0.852046614]; N=19; d=170 | 0.788235294 [0.705544872, 0.852046614]; N=19; d=170 | 0.788235294 [0.705544872, 0.852046614]; N=19; d=170 |
| plausibility_returned | 0.788235294 [0.705544872, 0.852046614]; N=19; d=170 | 0.788235294 [0.705544872, 0.852046614]; N=19; d=170 | 0.788235294 [0.705544872, 0.852046614]; N=19; d=170 |
| tier3 | 1 [1, 1]; N=19; d=170 | 1 [1, 1]; N=19; d=170 | 1 [1, 1]; N=19; d=170 |
| tier4 | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 |
| joint_tiers | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 |
| joint | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 |
| NO_INTERVENTION | 0 [0, 0]; N=19; d=170 | 0 [0, 0]; N=19; d=170 | 0 [0, 0]; N=19; d=170 |
| RECOVERABLE | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 | 0.776470588 [0.691335979, 0.844661702]; N=19; d=170 |
| PARTIAL | 0.0117647059 [0, 0.0284090909]; N=19; d=170 | 0.0117647059 [0, 0.0284090909]; N=19; d=170 | 0.0117647059 [0, 0.0284090909]; N=19; d=170 |
| ESCALATE | 0.211764706 [0.147953386, 0.294455128]; N=19; d=170 | 0.211764706 [0.147953386, 0.294455128]; N=19; d=170 | 0.211764706 [0.147953386, 0.294455128]; N=19; d=170 |
| risk_reduction | 0.729391751 [0.715868729, 0.741869946]; N=19; d=170 | 0.729391751 [0.715868729, 0.741869946]; N=19; d=170 | 0.729391751 [0.715868729, 0.741869946]; N=19; d=170 |
| sparsity_all | 2.68235294 [2.61352583, 2.75817542]; N=19; d=170 | 2.68235294 [2.61352583, 2.75817542]; N=19; d=170 | 2.68235294 [2.61352583, 2.75817542]; N=19; d=170 |
| sparsity_returned | 2.68235294 [2.61352583, 2.75817542]; N=19; d=170 | 2.68235294 [2.61352583, 2.75817542]; N=19; d=170 | 2.68235294 [2.61352583, 2.75817542]; N=19; d=170 |

historical query denominators: `{"all_queries": 170, "failed_joint": 38, "failed_model_validity": 15, "not_returned": 0, "returned": 170, "triage_counts": {"ESCALATE": 36, "PARTIAL": 2, "RECOVERABLE": 132}}`.

corrected_a query denominators: `{"all_queries": 170, "failed_joint": 38, "failed_model_validity": 15, "not_returned": 0, "returned": 170, "triage_counts": {"ESCALATE": 36, "PARTIAL": 2, "RECOVERABLE": 132}}`.

corrected_b query denominators: `{"all_queries": 170, "failed_joint": 38, "failed_model_validity": 15, "not_returned": 0, "returned": 170, "triage_counts": {"ESCALATE": 36, "PARTIAL": 2, "RECOVERABLE": 132}}`.

## FD001/mlp/v2/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "92fca7bf3fe895f4fc123b59ea33c8a6de2b422270d1c4add91a1a12bd1f4162"}, "corrected_b": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "92fca7bf3fe895f4fc123b59ea33c8a6de2b422270d1c4add91a1a12bd1f4162"}, "historical": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "92fca7bf3fe895f4fc123b59ea33c8a6de2b422270d1c4add91a1a12bd1f4162"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "mlp", "population": "grouped_oof_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.500404531 [0.470830696, 0.530829136]; N=100; d=2472 | 0.500404531 [0.470830696, 0.530829136]; N=100; d=2472 | 0.500404531 [0.470830696, 0.530829136]; N=100; d=2472 |
| plausibility_all | 0.979368932 [0.968232658, 0.988743015]; N=100; d=2472 | 0.979368932 [0.968232658, 0.988743015]; N=100; d=2472 | 0.979368932 [0.968232658, 0.988743015]; N=100; d=2472 |
| plausibility_returned | 0.988049509 [0.982447901, 0.993154693]; N=100; d=2343 | 0.988049509 [0.982447901, 0.993154693]; N=100; d=2343 | 0.988049509 [0.982447901, 0.993154693]; N=100; d=2343 |
| tier3 | 0.953074434 [0.922541284, 0.979228792]; N=100; d=2472 | 0.953074434 [0.922541284, 0.979228792]; N=100; d=2472 | 0.953074434 [0.922541284, 0.979228792]; N=100; d=2472 |
| tier4 | 0.920307443 [0.899104126, 0.938656199]; N=100; d=2472 | 0.920307443 [0.899104126, 0.938656199]; N=100; d=2472 | 0.920307443 [0.899104126, 0.938656199]; N=100; d=2472 |
| joint_tiers | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 |
| joint | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 |
| NO_INTERVENTION | 0 [0, 0]; N=100; d=2472 | 0 [0, 0]; N=100; d=2472 | 0 [0, 0]; N=100; d=2472 |
| RECOVERABLE | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 | 0.479773463 [0.450502664, 0.510323699]; N=100; d=2472 |
| PARTIAL | 0.221682848 [0.203871184, 0.239556333]; N=100; d=2472 | 0.221682848 [0.203871184, 0.239556333]; N=100; d=2472 | 0.221682848 [0.203871184, 0.239556333]; N=100; d=2472 |
| ESCALATE | 0.298543689 [0.264084671, 0.335509533]; N=100; d=2472 | 0.298543689 [0.264084671, 0.335509533]; N=100; d=2472 | 0.298543689 [0.264084671, 0.335509533]; N=100; d=2472 |
| risk_reduction | 0.535074488 [0.509465344, 0.559788178]; N=100; d=2472 | 0.535074488 [0.509465344, 0.559788178]; N=100; d=2472 | 0.535074488 [0.509465344, 0.559788178]; N=100; d=2472 |
| sparsity_all | 2.68001618 [2.59671163, 2.75799948]; N=100; d=2472 | 2.68001618 [2.59671163, 2.75799948]; N=100; d=2472 | 2.68001618 [2.59671163, 2.75799948]; N=100; d=2472 |
| sparsity_returned | 2.80495092 [2.77456742, 2.83340667]; N=100; d=2343 | 2.80495092 [2.77456742, 2.83340667]; N=100; d=2343 | 2.80495092 [2.77456742, 2.83340667]; N=100; d=2343 |

historical query denominators: `{"all_queries": 2472, "failed_joint": 1286, "failed_model_validity": 1235, "not_returned": 129, "returned": 2343, "triage_counts": {"ESCALATE": 738, "PARTIAL": 548, "RECOVERABLE": 1186}}`.

corrected_a query denominators: `{"all_queries": 2472, "failed_joint": 1286, "failed_model_validity": 1235, "not_returned": 129, "returned": 2343, "triage_counts": {"ESCALATE": 738, "PARTIAL": 548, "RECOVERABLE": 1186}}`.

corrected_b query denominators: `{"all_queries": 2472, "failed_joint": 1286, "failed_model_validity": 1235, "not_returned": 129, "returned": 2343, "triage_counts": {"ESCALATE": 738, "PARTIAL": 548, "RECOVERABLE": 1186}}`.

## FD001/mlp/v2/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "a10a683c769e1673d383da56ce2cffb53df5a48134895de641ebf9d624888c1d"}, "corrected_b": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "a10a683c769e1673d383da56ce2cffb53df5a48134895de641ebf9d624888c1d"}, "historical": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "a10a683c769e1673d383da56ce2cffb53df5a48134895de641ebf9d624888c1d"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "mlp", "population": "internal_heldout_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.543766578 [0.472771152, 0.607942941]; N=15; d=377 | 0.543766578 [0.472771152, 0.607942941]; N=15; d=377 | 0.543766578 [0.472771152, 0.607942941]; N=15; d=377 |
| plausibility_all | 0.99469496 [0.986944315, 1]; N=15; d=377 | 0.99469496 [0.986944315, 1]; N=15; d=377 | 0.99469496 [0.986944315, 1]; N=15; d=377 |
| plausibility_returned | 0.99469496 [0.986944315, 1]; N=15; d=377 | 0.99469496 [0.986944315, 1]; N=15; d=377 | 0.99469496 [0.986944315, 1]; N=15; d=377 |
| tier3 | 1 [1, 1]; N=15; d=377 | 1 [1, 1]; N=15; d=377 | 1 [1, 1]; N=15; d=377 |
| tier4 | 0.944297082 [0.919997416, 0.967059568]; N=15; d=377 | 0.944297082 [0.919997416, 0.967059568]; N=15; d=377 | 0.944297082 [0.919997416, 0.967059568]; N=15; d=377 |
| joint_tiers | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 |
| joint | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 |
| NO_INTERVENTION | 0 [0, 0]; N=15; d=377 | 0 [0, 0]; N=15; d=377 | 0 [0, 0]; N=15; d=377 |
| RECOVERABLE | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 | 0.51193634 [0.436099422, 0.58297853]; N=15; d=377 |
| PARTIAL | 0.228116711 [0.190345247, 0.266082486]; N=15; d=377 | 0.228116711 [0.190345247, 0.266082486]; N=15; d=377 | 0.228116711 [0.190345247, 0.266082486]; N=15; d=377 |
| ESCALATE | 0.25994695 [0.183875292, 0.35079008]; N=15; d=377 | 0.25994695 [0.183875292, 0.35079008]; N=15; d=377 | 0.25994695 [0.183875292, 0.35079008]; N=15; d=377 |
| risk_reduction | 0.582284674 [0.524868587, 0.632315336]; N=15; d=377 | 0.582284674 [0.524868587, 0.632315336]; N=15; d=377 | 0.582284674 [0.524868587, 0.632315336]; N=15; d=377 |
| sparsity_all | 2.78514589 [2.72832501, 2.84237844]; N=15; d=377 | 2.78514589 [2.72832501, 2.84237844]; N=15; d=377 | 2.78514589 [2.72832501, 2.84237844]; N=15; d=377 |
| sparsity_returned | 2.78514589 [2.72832501, 2.84237844]; N=15; d=377 | 2.78514589 [2.72832501, 2.84237844]; N=15; d=377 | 2.78514589 [2.72832501, 2.84237844]; N=15; d=377 |

historical query denominators: `{"all_queries": 377, "failed_joint": 184, "failed_model_validity": 172, "not_returned": 0, "returned": 377, "triage_counts": {"ESCALATE": 98, "PARTIAL": 86, "RECOVERABLE": 193}}`.

corrected_a query denominators: `{"all_queries": 377, "failed_joint": 184, "failed_model_validity": 172, "not_returned": 0, "returned": 377, "triage_counts": {"ESCALATE": 98, "PARTIAL": 86, "RECOVERABLE": 193}}`.

corrected_b query denominators: `{"all_queries": 377, "failed_joint": 184, "failed_model_validity": 172, "not_returned": 0, "returned": 377, "triage_counts": {"ESCALATE": 98, "PARTIAL": 86, "RECOVERABLE": 193}}`.

## FD001/mlp/v2/official_test_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "a10a683c769e1673d383da56ce2cffb53df5a48134895de641ebf9d624888c1d"}, "corrected_b": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "a10a683c769e1673d383da56ce2cffb53df5a48134895de641ebf9d624888c1d"}, "historical": {"configs/experiments/phase7-FD001-mlp-v2.yaml": "a10a683c769e1673d383da56ce2cffb53df5a48134895de641ebf9d624888c1d"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "mlp", "population": "official_test_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.911764706 [0.858024691, 0.962031287]; N=19; d=170 | 0.911764706 [0.858024691, 0.962031287]; N=19; d=170 | 0.911764706 [0.858024691, 0.962031287]; N=19; d=170 |
| plausibility_all | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 |
| plausibility_returned | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 |
| tier3 | 1 [1, 1]; N=19; d=170 | 1 [1, 1]; N=19; d=170 | 1 [1, 1]; N=19; d=170 |
| tier4 | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 | 0.994117647 [0.979591837, 1]; N=19; d=170 |
| joint_tiers | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 |
| joint | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 |
| NO_INTERVENTION | 0 [0, 0]; N=19; d=170 | 0 [0, 0]; N=19; d=170 | 0 [0, 0]; N=19; d=170 |
| RECOVERABLE | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 | 0.905882353 [0.85255102, 0.955555556]; N=19; d=170 |
| PARTIAL | 0.0882352941 [0.0379687127, 0.141975309]; N=19; d=170 | 0.0882352941 [0.0379687127, 0.141975309]; N=19; d=170 | 0.0882352941 [0.0379687127, 0.141975309]; N=19; d=170 |
| ESCALATE | 0.00588235294 [0, 0.0204081633]; N=19; d=170 | 0.00588235294 [0, 0.0204081633]; N=19; d=170 | 0.00588235294 [0, 0.0204081633]; N=19; d=170 |
| risk_reduction | 0.725954348 [0.713011801, 0.737363036]; N=19; d=170 | 0.725954348 [0.713011801, 0.737363036]; N=19; d=170 | 0.725954348 [0.713011801, 0.737363036]; N=19; d=170 |
| sparsity_all | 2.56470588 [2.47976644, 2.64497041]; N=19; d=170 | 2.56470588 [2.47976644, 2.64497041]; N=19; d=170 | 2.56470588 [2.47976644, 2.64497041]; N=19; d=170 |
| sparsity_returned | 2.56470588 [2.47976644, 2.64497041]; N=19; d=170 | 2.56470588 [2.47976644, 2.64497041]; N=19; d=170 | 2.56470588 [2.47976644, 2.64497041]; N=19; d=170 |

historical query denominators: `{"all_queries": 170, "failed_joint": 16, "failed_model_validity": 15, "not_returned": 0, "returned": 170, "triage_counts": {"ESCALATE": 1, "PARTIAL": 15, "RECOVERABLE": 154}}`.

corrected_a query denominators: `{"all_queries": 170, "failed_joint": 16, "failed_model_validity": 15, "not_returned": 0, "returned": 170, "triage_counts": {"ESCALATE": 1, "PARTIAL": 15, "RECOVERABLE": 154}}`.

corrected_b query denominators: `{"all_queries": 170, "failed_joint": 16, "failed_model_validity": 15, "not_returned": 0, "returned": 170, "triage_counts": {"ESCALATE": 1, "PARTIAL": 15, "RECOVERABLE": 154}}`.

## FD001/xgb/v1/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "70249f824c981405607040d644333058af63202efc6d312ac7b82450b30bc547"}, "corrected_b": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "70249f824c981405607040d644333058af63202efc6d312ac7b82450b30bc547"}, "historical": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "70249f824c981405607040d644333058af63202efc6d312ac7b82450b30bc547"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "xgb", "population": "grouped_oof_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.525231287 [0.493042329, 0.556434093]; N=100; d=2378 | 0.525231287 [0.493042329, 0.556434093]; N=100; d=2378 | 0.525231287 [0.493042329, 0.556434093]; N=100; d=2378 |
| plausibility_all | 0.486963835 [0.445946048, 0.526111941]; N=100; d=2378 | 0.486963835 [0.445946048, 0.526111941]; N=100; d=2378 | 0.486963835 [0.445946048, 0.526111941]; N=100; d=2378 |
| plausibility_returned | 0.510449088 [0.474595694, 0.544636191]; N=100; d=2249 | 0.510449088 [0.474595694, 0.544636191]; N=100; d=2249 | 0.510449088 [0.474595694, 0.544636191]; N=100; d=2249 |
| tier3 | 0.951219512 [0.920096479, 0.97826521]; N=100; d=2378 | 0.951219512 [0.920096479, 0.97826521]; N=100; d=2378 | 0.951219512 [0.920096479, 0.97826521]; N=100; d=2378 |
| tier4 | 0.916736754 [0.894516787, 0.936155068]; N=100; d=2378 | 0.916736754 [0.894516787, 0.936155068]; N=100; d=2378 | 0.916736754 [0.894516787, 0.936155068]; N=100; d=2378 |
| joint_tiers | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 |
| joint | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 |
| NO_INTERVENTION | 0 [0, 0]; N=100; d=2378 | 0 [0, 0]; N=100; d=2378 | 0 [0, 0]; N=100; d=2378 |
| RECOVERABLE | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 | 0.399074853 [0.367285456, 0.429127112]; N=100; d=2378 |
| PARTIAL | 0.0513036165 [0.0398211182, 0.0637739502]; N=100; d=2378 | 0.0513036165 [0.0398211182, 0.0637739502]; N=100; d=2378 | 0.0513036165 [0.0398211182, 0.0637739502]; N=100; d=2378 |
| ESCALATE | 0.549621531 [0.513848463, 0.58731204]; N=100; d=2378 | 0.549621531 [0.513848463, 0.58731204]; N=100; d=2378 | 0.549621531 [0.513848463, 0.58731204]; N=100; d=2378 |
| risk_reduction | 0.5632003 [0.535622883, 0.5896191]; N=100; d=2378 | 0.5632003 [0.535622883, 0.5896191]; N=100; d=2378 | 0.5632003 [0.535622883, 0.5896191]; N=100; d=2378 |
| sparsity_all | 2.76324643 [2.66878421, 2.84664139]; N=100; d=2378 | 2.76324643 [2.66878421, 2.84664139]; N=100; d=2378 | 2.76324643 [2.66878421, 2.84664139]; N=100; d=2378 |
| sparsity_returned | 2.89817697 [2.8830253, 2.91246621]; N=100; d=2249 | 2.89817697 [2.8830253, 2.91246621]; N=100; d=2249 | 2.89817697 [2.8830253, 2.91246621]; N=100; d=2249 |

historical query denominators: `{"all_queries": 2378, "failed_joint": 1429, "failed_model_validity": 1129, "not_returned": 129, "returned": 2249, "triage_counts": {"ESCALATE": 1307, "PARTIAL": 122, "RECOVERABLE": 949}}`.

corrected_a query denominators: `{"all_queries": 2378, "failed_joint": 1429, "failed_model_validity": 1129, "not_returned": 129, "returned": 2249, "triage_counts": {"ESCALATE": 1307, "PARTIAL": 122, "RECOVERABLE": 949}}`.

corrected_b query denominators: `{"all_queries": 2378, "failed_joint": 1429, "failed_model_validity": 1129, "not_returned": 129, "returned": 2249, "triage_counts": {"ESCALATE": 1307, "PARTIAL": 122, "RECOVERABLE": 949}}`.

## FD001/xgb/v1/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271"}, "corrected_b": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271"}, "historical": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "xgb", "population": "internal_heldout_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.558201058 [0.48998262, 0.625008075]; N=15; d=378 | 0.558201058 [0.48998262, 0.625008075]; N=15; d=378 | 0.558201058 [0.48998262, 0.625008075]; N=15; d=378 |
| plausibility_all | 0.513227513 [0.443888908, 0.575345093]; N=15; d=378 | 0.513227513 [0.443888908, 0.575345093]; N=15; d=378 | 0.513227513 [0.443888908, 0.575345093]; N=15; d=378 |
| plausibility_returned | 0.513227513 [0.443888908, 0.575345093]; N=15; d=378 | 0.513227513 [0.443888908, 0.575345093]; N=15; d=378 | 0.513227513 [0.443888908, 0.575345093]; N=15; d=378 |
| tier3 | 1 [1, 1]; N=15; d=378 | 1 [1, 1]; N=15; d=378 | 1 [1, 1]; N=15; d=378 |
| tier4 | 0.944444444 [0.920244251, 0.967443314]; N=15; d=378 | 0.944444444 [0.920244251, 0.967443314]; N=15; d=378 | 0.944444444 [0.920244251, 0.967443314]; N=15; d=378 |
| joint_tiers | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 |
| joint | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 |
| NO_INTERVENTION | 0 [0, 0]; N=15; d=378 | 0 [0, 0]; N=15; d=378 | 0 [0, 0]; N=15; d=378 |
| RECOVERABLE | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 | 0.420634921 [0.379208365, 0.461538462]; N=15; d=378 |
| PARTIAL | 0.0582010582 [0.0314132964, 0.0900266296]; N=15; d=378 | 0.0582010582 [0.0314132964, 0.0900266296]; N=15; d=378 | 0.0582010582 [0.0314132964, 0.0900266296]; N=15; d=378 |
| ESCALATE | 0.521164021 [0.469013214, 0.578005115]; N=15; d=378 | 0.521164021 [0.469013214, 0.578005115]; N=15; d=378 | 0.521164021 [0.469013214, 0.578005115]; N=15; d=378 |
| risk_reduction | 0.598155798 [0.543098496, 0.650297146]; N=15; d=378 | 0.598155798 [0.543098496, 0.650297146]; N=15; d=378 | 0.598155798 [0.543098496, 0.650297146]; N=15; d=378 |
| sparsity_all | 2.91005291 [2.8851167, 2.93203949]; N=15; d=378 | 2.91005291 [2.8851167, 2.93203949]; N=15; d=378 | 2.91005291 [2.8851167, 2.93203949]; N=15; d=378 |
| sparsity_returned | 2.91005291 [2.8851167, 2.93203949]; N=15; d=378 | 2.91005291 [2.8851167, 2.93203949]; N=15; d=378 | 2.91005291 [2.8851167, 2.93203949]; N=15; d=378 |

historical query denominators: `{"all_queries": 378, "failed_joint": 219, "failed_model_validity": 167, "not_returned": 0, "returned": 378, "triage_counts": {"ESCALATE": 197, "PARTIAL": 22, "RECOVERABLE": 159}}`.

corrected_a query denominators: `{"all_queries": 378, "failed_joint": 219, "failed_model_validity": 167, "not_returned": 0, "returned": 378, "triage_counts": {"ESCALATE": 197, "PARTIAL": 22, "RECOVERABLE": 159}}`.

corrected_b query denominators: `{"all_queries": 378, "failed_joint": 219, "failed_model_validity": 167, "not_returned": 0, "returned": 378, "triage_counts": {"ESCALATE": 197, "PARTIAL": 22, "RECOVERABLE": 159}}`.

## FD001/xgb/v1/official_test_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271"}, "corrected_b": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271"}, "historical": {"configs/experiments/phase7-FD001-xgb-v1.yaml": "47254ac5ea494ee5e333a754252edca0b9024d9ed5b792f3d0f561b5b0cb2271"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "xgb", "population": "official_test_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.893081761 [0.835714286, 0.943551227]; N=19; d=159 | 0.893081761 [0.835714286, 0.943551227]; N=19; d=159 | 0.893081761 [0.835714286, 0.943551227]; N=19; d=159 |
| plausibility_all | 0.779874214 [0.704223269, 0.843753811]; N=19; d=159 | 0.779874214 [0.704223269, 0.843753811]; N=19; d=159 | 0.779874214 [0.704223269, 0.843753811]; N=19; d=159 |
| plausibility_returned | 0.779874214 [0.704223269, 0.843753811]; N=19; d=159 | 0.779874214 [0.704223269, 0.843753811]; N=19; d=159 | 0.779874214 [0.704223269, 0.843753811]; N=19; d=159 |
| tier3 | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 |
| tier4 | 0.987421384 [0.96570936, 1]; N=19; d=159 | 0.987421384 [0.96570936, 1]; N=19; d=159 | 0.987421384 [0.96570936, 1]; N=19; d=159 |
| joint_tiers | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 |
| joint | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 |
| NO_INTERVENTION | 0 [0, 0]; N=19; d=159 | 0 [0, 0]; N=19; d=159 | 0 [0, 0]; N=19; d=159 |
| RECOVERABLE | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 | 0.767295597 [0.687488073, 0.836604642]; N=19; d=159 |
| PARTIAL | 0.0125786164 [0, 0.0306748466]; N=19; d=159 | 0.0125786164 [0, 0.0306748466]; N=19; d=159 | 0.0125786164 [0, 0.0306748466]; N=19; d=159 |
| ESCALATE | 0.220125786 [0.156246189, 0.295776731]; N=19; d=159 | 0.220125786 [0.156246189, 0.295776731]; N=19; d=159 | 0.220125786 [0.156246189, 0.295776731]; N=19; d=159 |
| risk_reduction | 0.74241505 [0.727847825, 0.758046816]; N=19; d=159 | 0.74241505 [0.727847825, 0.758046816]; N=19; d=159 | 0.74241505 [0.727847825, 0.758046816]; N=19; d=159 |
| sparsity_all | 2.77358491 [2.64326441, 2.87075379]; N=19; d=159 | 2.77358491 [2.64326441, 2.87075379]; N=19; d=159 | 2.77358491 [2.64326441, 2.87075379]; N=19; d=159 |
| sparsity_returned | 2.77358491 [2.64326441, 2.87075379]; N=19; d=159 | 2.77358491 [2.64326441, 2.87075379]; N=19; d=159 | 2.77358491 [2.64326441, 2.87075379]; N=19; d=159 |

historical query denominators: `{"all_queries": 159, "failed_joint": 37, "failed_model_validity": 17, "not_returned": 0, "returned": 159, "triage_counts": {"ESCALATE": 35, "PARTIAL": 2, "RECOVERABLE": 122}}`.

corrected_a query denominators: `{"all_queries": 159, "failed_joint": 37, "failed_model_validity": 17, "not_returned": 0, "returned": 159, "triage_counts": {"ESCALATE": 35, "PARTIAL": 2, "RECOVERABLE": 122}}`.

corrected_b query denominators: `{"all_queries": 159, "failed_joint": 37, "failed_model_validity": 17, "not_returned": 0, "returned": 159, "triage_counts": {"ESCALATE": 35, "PARTIAL": 2, "RECOVERABLE": 122}}`.

## FD001/xgb/v2/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "2b894b9d3532e5c39f5c8653e6c5fa2acb7d24ca5f3f8431fb4253078eee0774"}, "corrected_b": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "2b894b9d3532e5c39f5c8653e6c5fa2acb7d24ca5f3f8431fb4253078eee0774"}, "historical": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "2b894b9d3532e5c39f5c8653e6c5fa2acb7d24ca5f3f8431fb4253078eee0774"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "xgb", "population": "grouped_oof_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.525231287 [0.493042329, 0.556434093]; N=100; d=2378 | 0.525231287 [0.493042329, 0.556434093]; N=100; d=2378 | 0.525231287 [0.493042329, 0.556434093]; N=100; d=2378 |
| plausibility_all | 0.980656013 [0.970024248, 0.989206108]; N=100; d=2378 | 0.980656013 [0.970024248, 0.989206108]; N=100; d=2378 | 0.980656013 [0.970024248, 0.989206108]; N=100; d=2378 |
| plausibility_returned | 0.989773233 [0.984546844, 0.994230235]; N=100; d=2249 | 0.989773233 [0.984546844, 0.994230235]; N=100; d=2249 | 0.989773233 [0.984546844, 0.994230235]; N=100; d=2249 |
| tier3 | 0.951219512 [0.920096479, 0.97826521]; N=100; d=2378 | 0.951219512 [0.920096479, 0.97826521]; N=100; d=2378 | 0.951219512 [0.920096479, 0.97826521]; N=100; d=2378 |
| tier4 | 0.916736754 [0.894516787, 0.936155068]; N=100; d=2378 | 0.916736754 [0.894516787, 0.936155068]; N=100; d=2378 | 0.916736754 [0.894516787, 0.936155068]; N=100; d=2378 |
| joint_tiers | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 |
| joint | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 |
| NO_INTERVENTION | 0 [0, 0]; N=100; d=2378 | 0 [0, 0]; N=100; d=2378 | 0 [0, 0]; N=100; d=2378 |
| RECOVERABLE | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 | 0.504205214 [0.472895721, 0.534791723]; N=100; d=2378 |
| PARTIAL | 0.234230446 [0.215167428, 0.253282927]; N=100; d=2378 | 0.234230446 [0.215167428, 0.253282927]; N=100; d=2378 | 0.234230446 [0.215167428, 0.253282927]; N=100; d=2378 |
| ESCALATE | 0.26156434 [0.223150596, 0.300578465]; N=100; d=2378 | 0.26156434 [0.223150596, 0.300578465]; N=100; d=2378 | 0.26156434 [0.223150596, 0.300578465]; N=100; d=2378 |
| risk_reduction | 0.5635626 [0.536284555, 0.589941016]; N=100; d=2378 | 0.5635626 [0.536284555, 0.589941016]; N=100; d=2378 | 0.5635626 [0.536284555, 0.589941016]; N=100; d=2378 |
| sparsity_all | 2.7253995 [2.6361068, 2.80742348]; N=100; d=2378 | 2.7253995 [2.6361068, 2.80742348]; N=100; d=2378 | 2.7253995 [2.6361068, 2.80742348]; N=100; d=2378 |
| sparsity_returned | 2.85815918 [2.84110735, 2.87259334]; N=100; d=2249 | 2.85815918 [2.84110735, 2.87259334]; N=100; d=2249 | 2.85815918 [2.84110735, 2.87259334]; N=100; d=2249 |

historical query denominators: `{"all_queries": 2378, "failed_joint": 1179, "failed_model_validity": 1129, "not_returned": 129, "returned": 2249, "triage_counts": {"ESCALATE": 622, "PARTIAL": 557, "RECOVERABLE": 1199}}`.

corrected_a query denominators: `{"all_queries": 2378, "failed_joint": 1179, "failed_model_validity": 1129, "not_returned": 129, "returned": 2249, "triage_counts": {"ESCALATE": 622, "PARTIAL": 557, "RECOVERABLE": 1199}}`.

corrected_b query denominators: `{"all_queries": 2378, "failed_joint": 1179, "failed_model_validity": 1129, "not_returned": 129, "returned": 2249, "triage_counts": {"ESCALATE": 622, "PARTIAL": 557, "RECOVERABLE": 1199}}`.

## FD001/xgb/v2/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a"}, "corrected_b": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a"}, "historical": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "xgb", "population": "internal_heldout_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.558201058 [0.48998262, 0.625008075]; N=15; d=378 | 0.558201058 [0.48998262, 0.625008075]; N=15; d=378 | 0.558201058 [0.48998262, 0.625008075]; N=15; d=378 |
| plausibility_all | 0.989417989 [0.980906106, 0.997361651]; N=15; d=378 | 0.989417989 [0.980906106, 0.997361651]; N=15; d=378 | 0.989417989 [0.980906106, 0.997361651]; N=15; d=378 |
| plausibility_returned | 0.989417989 [0.980906106, 0.997361651]; N=15; d=378 | 0.989417989 [0.980906106, 0.997361651]; N=15; d=378 | 0.989417989 [0.980906106, 0.997361651]; N=15; d=378 |
| tier3 | 1 [1, 1]; N=15; d=378 | 1 [1, 1]; N=15; d=378 | 1 [1, 1]; N=15; d=378 |
| tier4 | 0.944444444 [0.920244251, 0.967443314]; N=15; d=378 | 0.944444444 [0.920244251, 0.967443314]; N=15; d=378 | 0.944444444 [0.920244251, 0.967443314]; N=15; d=378 |
| joint_tiers | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 |
| joint | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 |
| NO_INTERVENTION | 0 [0, 0]; N=15; d=378 | 0 [0, 0]; N=15; d=378 | 0 [0, 0]; N=15; d=378 |
| RECOVERABLE | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 | 0.529100529 [0.461345919, 0.596057434]; N=15; d=378 |
| PARTIAL | 0.246031746 [0.192209258, 0.297370919]; N=15; d=378 | 0.246031746 [0.192209258, 0.297370919]; N=15; d=378 | 0.246031746 [0.192209258, 0.297370919]; N=15; d=378 |
| ESCALATE | 0.224867725 [0.139235429, 0.319450137]; N=15; d=378 | 0.224867725 [0.139235429, 0.319450137]; N=15; d=378 | 0.224867725 [0.139235429, 0.319450137]; N=15; d=378 |
| risk_reduction | 0.599881699 [0.544213951, 0.6519866]; N=15; d=378 | 0.599881699 [0.544213951, 0.6519866]; N=15; d=378 | 0.599881699 [0.544213951, 0.6519866]; N=15; d=378 |
| sparsity_all | 2.87301587 [2.84900891, 2.89966675]; N=15; d=378 | 2.87301587 [2.84900891, 2.89966675]; N=15; d=378 | 2.87301587 [2.84900891, 2.89966675]; N=15; d=378 |
| sparsity_returned | 2.87301587 [2.84900891, 2.89966675]; N=15; d=378 | 2.87301587 [2.84900891, 2.89966675]; N=15; d=378 | 2.87301587 [2.84900891, 2.89966675]; N=15; d=378 |

historical query denominators: `{"all_queries": 378, "failed_joint": 178, "failed_model_validity": 167, "not_returned": 0, "returned": 378, "triage_counts": {"ESCALATE": 85, "PARTIAL": 93, "RECOVERABLE": 200}}`.

corrected_a query denominators: `{"all_queries": 378, "failed_joint": 178, "failed_model_validity": 167, "not_returned": 0, "returned": 378, "triage_counts": {"ESCALATE": 85, "PARTIAL": 93, "RECOVERABLE": 200}}`.

corrected_b query denominators: `{"all_queries": 378, "failed_joint": 178, "failed_model_validity": 167, "not_returned": 0, "returned": 378, "triage_counts": {"ESCALATE": 85, "PARTIAL": 93, "RECOVERABLE": 200}}`.

## FD001/xgb/v2/official_test_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD001", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a"}, "corrected_b": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a"}, "historical": {"configs/experiments/phase7-FD001-xgb-v2.yaml": "42d1cdd4424b16c719947f97e467daf178f22ba1ad985b3b47ddd3012ac0a69a"}}, "k_max": 3, "machine_id": "cmapss_fd001", "mode": "FAST", "model": "xgb", "population": "official_test_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 0.893081761 [0.835714286, 0.943551227]; N=19; d=159 | 0.893081761 [0.835714286, 0.943551227]; N=19; d=159 | 0.893081761 [0.835714286, 0.943551227]; N=19; d=159 |
| plausibility_all | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 |
| plausibility_returned | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 |
| tier3 | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 | 1 [1, 1]; N=19; d=159 |
| tier4 | 0.987421384 [0.96570936, 1]; N=19; d=159 | 0.987421384 [0.96570936, 1]; N=19; d=159 | 0.987421384 [0.96570936, 1]; N=19; d=159 |
| joint_tiers | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 |
| joint | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 |
| NO_INTERVENTION | 0 [0, 0]; N=19; d=159 | 0 [0, 0]; N=19; d=159 | 0 [0, 0]; N=19; d=159 |
| RECOVERABLE | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 | 0.880503145 [0.820339021, 0.931975939]; N=19; d=159 |
| PARTIAL | 0.106918239 [0.0564487733, 0.164285714]; N=19; d=159 | 0.106918239 [0.0564487733, 0.164285714]; N=19; d=159 | 0.106918239 [0.0564487733, 0.164285714]; N=19; d=159 |
| ESCALATE | 0.0125786164 [0, 0.0342906404]; N=19; d=159 | 0.0125786164 [0, 0.0342906404]; N=19; d=159 | 0.0125786164 [0, 0.0342906404]; N=19; d=159 |
| risk_reduction | 0.741152642 [0.727216568, 0.755718068]; N=19; d=159 | 0.741152642 [0.727216568, 0.755718068]; N=19; d=159 | 0.741152642 [0.727216568, 0.755718068]; N=19; d=159 |
| sparsity_all | 2.72955975 [2.61400679, 2.83648802]; N=19; d=159 | 2.72955975 [2.61400679, 2.83648802]; N=19; d=159 | 2.72955975 [2.61400679, 2.83648802]; N=19; d=159 |
| sparsity_returned | 2.72955975 [2.61400679, 2.83648802]; N=19; d=159 | 2.72955975 [2.61400679, 2.83648802]; N=19; d=159 | 2.72955975 [2.61400679, 2.83648802]; N=19; d=159 |

historical query denominators: `{"all_queries": 159, "failed_joint": 19, "failed_model_validity": 17, "not_returned": 0, "returned": 159, "triage_counts": {"ESCALATE": 2, "PARTIAL": 17, "RECOVERABLE": 140}}`.

corrected_a query denominators: `{"all_queries": 159, "failed_joint": 19, "failed_model_validity": 17, "not_returned": 0, "returned": 159, "triage_counts": {"ESCALATE": 2, "PARTIAL": 17, "RECOVERABLE": 140}}`.

corrected_b query denominators: `{"all_queries": 159, "failed_joint": 19, "failed_model_validity": 17, "not_returned": 0, "returned": 159, "triage_counts": {"ESCALATE": 2, "PARTIAL": 17, "RECOVERABLE": 140}}`.

## FD002/xgb/v1/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD002", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "7960959a4f452ce4eacf2d22f46de95adcc38cb0cedb8a4d9a8c89ef3a9aa52c"}, "corrected_b": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "7960959a4f452ce4eacf2d22f46de95adcc38cb0cedb8a4d9a8c89ef3a9aa52c"}, "historical": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "7960959a4f452ce4eacf2d22f46de95adcc38cb0cedb8a4d9a8c89ef3a9aa52c"}}, "k_max": 3, "machine_id": "cmapss_fd002", "mode": "FAST", "model": "xgb", "population": "grouped_oof_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 |
| plausibility_all | 0.0313003041 [0.0265388538, 0.0363736317]; N=260; d=5591 | 0.0313003041 [0.0265388538, 0.0363736317]; N=260; d=5591 | 0.0313003041 [0.0265388538, 0.0363736317]; N=260; d=5591 |
| plausibility_returned | 0.0313003041 [0.0265388538, 0.0363736317]; N=260; d=5591 | 0.0313003041 [0.0265388538, 0.0363736317]; N=260; d=5591 | 0.0313003041 [0.0265388538, 0.0363736317]; N=260; d=5591 |
| tier3 | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 |
| tier4 | 0.313003041 [0.282128977, 0.346051437]; N=260; d=5591 | 0.313003041 [0.282128977, 0.346051437]; N=260; d=5591 | 0.313003041 [0.282128977, 0.346051437]; N=260; d=5591 |
| joint_tiers | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 |
| joint | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 |
| NO_INTERVENTION | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 |
| RECOVERABLE | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 | 0.000715435521 [0.000174092436, 0.00145166194]; N=260; d=5591 |
| PARTIAL | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 |
| ESCALATE | 0.999284564 [0.998548338, 0.999825908]; N=260; d=5591 | 0.999284564 [0.998548338, 0.999825908]; N=260; d=5591 | 0.999284564 [0.998548338, 0.999825908]; N=260; d=5591 |
| risk_reduction | 0.835903371 [0.83314264, 0.838834363]; N=260; d=5591 | 0.835903371 [0.83314264, 0.838834363]; N=260; d=5591 | 0.835903371 [0.83314264, 0.838834363]; N=260; d=5591 |
| sparsity_all | 1.58540512 [1.56143312, 1.60897118]; N=260; d=5591 | 1.58540512 [1.56143312, 1.60897118]; N=260; d=5591 | 1.58540512 [1.56143312, 1.60897118]; N=260; d=5591 |
| sparsity_returned | 1.58540512 [1.56143312, 1.60897118]; N=260; d=5591 | 1.58540512 [1.56143312, 1.60897118]; N=260; d=5591 | 1.58540512 [1.56143312, 1.60897118]; N=260; d=5591 |

historical query denominators: `{"all_queries": 5591, "failed_joint": 5587, "failed_model_validity": 0, "not_returned": 0, "returned": 5591, "triage_counts": {"ESCALATE": 5587, "RECOVERABLE": 4}}`.

corrected_a query denominators: `{"all_queries": 5591, "failed_joint": 5587, "failed_model_validity": 0, "not_returned": 0, "returned": 5591, "triage_counts": {"ESCALATE": 5587, "RECOVERABLE": 4}}`.

corrected_b query denominators: `{"all_queries": 5591, "failed_joint": 5587, "failed_model_validity": 0, "not_returned": 0, "returned": 5591, "triage_counts": {"ESCALATE": 5587, "RECOVERABLE": 4}}`.

## FD002/xgb/v1/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD002", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264"}, "corrected_b": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264"}, "historical": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264"}}, "k_max": 3, "machine_id": "cmapss_fd002", "mode": "FAST", "model": "xgb", "population": "internal_heldout_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 |
| plausibility_all | 0.0373216246 [0.0271725313, 0.0482994868]; N=39; d=911 | 0.0373216246 [0.0271725313, 0.0482994868]; N=39; d=911 | 0.0373216246 [0.0271725313, 0.0482994868]; N=39; d=911 |
| plausibility_returned | 0.0373216246 [0.0271725313, 0.0482994868]; N=39; d=911 | 0.0373216246 [0.0271725313, 0.0482994868]; N=39; d=911 | 0.0373216246 [0.0271725313, 0.0482994868]; N=39; d=911 |
| tier3 | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 |
| tier4 | 0.286498353 [0.200858406, 0.378412691]; N=39; d=911 | 0.286498353 [0.200858406, 0.378412691]; N=39; d=911 | 0.286498353 [0.200858406, 0.378412691]; N=39; d=911 |
| joint_tiers | 0.00329308452 [0, 0.00734455324]; N=39; d=911 | 0.00329308452 [0, 0.00734455324]; N=39; d=911 | 0.00329308452 [0, 0.00734455324]; N=39; d=911 |
| joint | 0.00329308452 [0, 0.00734455324]; N=39; d=911 | 0.00329308452 [0, 0.00734455324]; N=39; d=911 | 0.00329308452 [0, 0.00734455324]; N=39; d=911 |
| NO_INTERVENTION | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 |
| RECOVERABLE | 0.00329308452 [0, 0.00734455324]; N=39; d=911 | 0.00329308452 [0, 0.00734455324]; N=39; d=911 | 0.00329308452 [0, 0.00734455324]; N=39; d=911 |
| PARTIAL | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 |
| ESCALATE | 0.996706915 [0.992655447, 1]; N=39; d=911 | 0.996706915 [0.992655447, 1]; N=39; d=911 | 0.996706915 [0.992655447, 1]; N=39; d=911 |
| risk_reduction | 0.83812126 [0.832635543, 0.843150224]; N=39; d=911 | 0.83812126 [0.832635543, 0.843150224]; N=39; d=911 | 0.83812126 [0.832635543, 0.843150224]; N=39; d=911 |
| sparsity_all | 1.62458836 [1.57261675, 1.67350945]; N=39; d=911 | 1.62458836 [1.57261675, 1.67350945]; N=39; d=911 | 1.62458836 [1.57261675, 1.67350945]; N=39; d=911 |
| sparsity_returned | 1.62458836 [1.57261675, 1.67350945]; N=39; d=911 | 1.62458836 [1.57261675, 1.67350945]; N=39; d=911 | 1.62458836 [1.57261675, 1.67350945]; N=39; d=911 |

historical query denominators: `{"all_queries": 911, "failed_joint": 908, "failed_model_validity": 0, "not_returned": 0, "returned": 911, "triage_counts": {"ESCALATE": 908, "RECOVERABLE": 3}}`.

corrected_a query denominators: `{"all_queries": 911, "failed_joint": 908, "failed_model_validity": 0, "not_returned": 0, "returned": 911, "triage_counts": {"ESCALATE": 908, "RECOVERABLE": 3}}`.

corrected_b query denominators: `{"all_queries": 911, "failed_joint": 908, "failed_model_validity": 0, "not_returned": 0, "returned": 911, "triage_counts": {"ESCALATE": 908, "RECOVERABLE": 3}}`.

## FD002/xgb/v1/official_test_all_alerts/fast/full

Labels: `{"D_max": 5.0, "K": 1, "dataset": "FD002", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264"}, "corrected_b": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264"}, "historical": {"configs/experiments/phase7-FD002-xgb-v1.yaml": "b94e70437c22a5becc67c458f30b83a91577c8ab6db7ac857ef67a5cb3257264"}}, "k_max": 3, "machine_id": "cmapss_fd002", "mode": "FAST", "model": "xgb", "population": "official_test_all_alerts", "protocol": "v1", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 |
| plausibility_all | 0.0457227139 [0.0306122449, 0.062992444]; N=65; d=678 | 0.0457227139 [0.0306122449, 0.062992444]; N=65; d=678 | 0.0457227139 [0.0306122449, 0.062992444]; N=65; d=678 |
| plausibility_returned | 0.0457227139 [0.0306122449, 0.062992444]; N=65; d=678 | 0.0457227139 [0.0306122449, 0.062992444]; N=65; d=678 | 0.0457227139 [0.0306122449, 0.062992444]; N=65; d=678 |
| tier3 | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 |
| tier4 | 0.333333333 [0.258401154, 0.410441481]; N=65; d=678 | 0.333333333 [0.258401154, 0.410441481]; N=65; d=678 | 0.333333333 [0.258401154, 0.410441481]; N=65; d=678 |
| joint_tiers | 0.00442477876 [0, 0.0102219011]; N=65; d=678 | 0.00442477876 [0, 0.0102219011]; N=65; d=678 | 0.00442477876 [0, 0.0102219011]; N=65; d=678 |
| joint | 0.00442477876 [0, 0.0102219011]; N=65; d=678 | 0.00442477876 [0, 0.0102219011]; N=65; d=678 | 0.00442477876 [0, 0.0102219011]; N=65; d=678 |
| NO_INTERVENTION | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 |
| RECOVERABLE | 0.00442477876 [0, 0.0102219011]; N=65; d=678 | 0.00442477876 [0, 0.0102219011]; N=65; d=678 | 0.00442477876 [0, 0.0102219011]; N=65; d=678 |
| PARTIAL | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 |
| ESCALATE | 0.995575221 [0.989778099, 1]; N=65; d=678 | 0.995575221 [0.989778099, 1]; N=65; d=678 | 0.995575221 [0.989778099, 1]; N=65; d=678 |
| risk_reduction | 0.821257603 [0.814287157, 0.827572854]; N=65; d=678 | 0.821257603 [0.814287157, 0.827572854]; N=65; d=678 | 0.821257603 [0.814287157, 0.827572854]; N=65; d=678 |
| sparsity_all | 1.51327434 [1.46163277, 1.56465358]; N=65; d=678 | 1.51327434 [1.46163277, 1.56465358]; N=65; d=678 | 1.51327434 [1.46163277, 1.56465358]; N=65; d=678 |
| sparsity_returned | 1.51327434 [1.46163277, 1.56465358]; N=65; d=678 | 1.51327434 [1.46163277, 1.56465358]; N=65; d=678 | 1.51327434 [1.46163277, 1.56465358]; N=65; d=678 |

historical query denominators: `{"all_queries": 678, "failed_joint": 675, "failed_model_validity": 0, "not_returned": 0, "returned": 678, "triage_counts": {"ESCALATE": 675, "RECOVERABLE": 3}}`.

corrected_a query denominators: `{"all_queries": 678, "failed_joint": 675, "failed_model_validity": 0, "not_returned": 0, "returned": 678, "triage_counts": {"ESCALATE": 675, "RECOVERABLE": 3}}`.

corrected_b query denominators: `{"all_queries": 678, "failed_joint": 675, "failed_model_validity": 0, "not_returned": 0, "returned": 678, "triage_counts": {"ESCALATE": 675, "RECOVERABLE": 3}}`.

## FD002/xgb/v2/grouped_oof_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD002", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "f1d8b4a8b45342a65cc2c9f52b3fccbc90f5ca56b63d940326c4b74ec482db65"}, "corrected_b": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "f1d8b4a8b45342a65cc2c9f52b3fccbc90f5ca56b63d940326c4b74ec482db65"}, "historical": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "f1d8b4a8b45342a65cc2c9f52b3fccbc90f5ca56b63d940326c4b74ec482db65"}}, "k_max": 3, "machine_id": "cmapss_fd002", "mode": "FAST", "model": "xgb", "population": "grouped_oof_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 |
| plausibility_all | 0.109640494 [0.100900621, 0.117758016]; N=260; d=5591 | 0.109640494 [0.100900621, 0.117758016]; N=260; d=5591 | 0.109640494 [0.100900621, 0.117758016]; N=260; d=5591 |
| plausibility_returned | 0.109640494 [0.100900621, 0.117758016]; N=260; d=5591 | 0.109640494 [0.100900621, 0.117758016]; N=260; d=5591 | 0.109640494 [0.100900621, 0.117758016]; N=260; d=5591 |
| tier3 | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 | 1 [1, 1]; N=260; d=5591 |
| tier4 | 0.313003041 [0.282128977, 0.346051437]; N=260; d=5591 | 0.313003041 [0.282128977, 0.346051437]; N=260; d=5591 | 0.313003041 [0.282128977, 0.346051437]; N=260; d=5591 |
| joint_tiers | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 |
| joint | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 |
| NO_INTERVENTION | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 |
| RECOVERABLE | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 | 0.00661777857 [0.00447998645, 0.00897730718]; N=260; d=5591 |
| PARTIAL | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 | 0 [0, 0]; N=260; d=5591 |
| ESCALATE | 0.993382221 [0.991022693, 0.995520014]; N=260; d=5591 | 0.993382221 [0.991022693, 0.995520014]; N=260; d=5591 | 0.993382221 [0.991022693, 0.995520014]; N=260; d=5591 |
| risk_reduction | 0.836746459 [0.833819768, 0.839684357]; N=260; d=5591 | 0.836746459 [0.833819768, 0.839684357]; N=260; d=5591 | 0.836746459 [0.833819768, 0.839684357]; N=260; d=5591 |
| sparsity_all | 1.63906278 [1.61889243, 1.65893234]; N=260; d=5591 | 1.63906278 [1.61889243, 1.65893234]; N=260; d=5591 | 1.63906278 [1.61889243, 1.65893234]; N=260; d=5591 |
| sparsity_returned | 1.63906278 [1.61889243, 1.65893234]; N=260; d=5591 | 1.63906278 [1.61889243, 1.65893234]; N=260; d=5591 | 1.63906278 [1.61889243, 1.65893234]; N=260; d=5591 |

historical query denominators: `{"all_queries": 5591, "failed_joint": 5554, "failed_model_validity": 0, "not_returned": 0, "returned": 5591, "triage_counts": {"ESCALATE": 5554, "RECOVERABLE": 37}}`.

corrected_a query denominators: `{"all_queries": 5591, "failed_joint": 5554, "failed_model_validity": 0, "not_returned": 0, "returned": 5591, "triage_counts": {"ESCALATE": 5554, "RECOVERABLE": 37}}`.

corrected_b query denominators: `{"all_queries": 5591, "failed_joint": 5554, "failed_model_validity": 0, "not_returned": 0, "returned": 5591, "triage_counts": {"ESCALATE": 5554, "RECOVERABLE": 37}}`.

## FD002/xgb/v2/internal_heldout_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD002", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd"}, "corrected_b": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd"}, "historical": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd"}}, "k_max": 3, "machine_id": "cmapss_fd002", "mode": "FAST", "model": "xgb", "population": "internal_heldout_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 |
| plausibility_all | 0.108671789 [0.0857128114, 0.132075472]; N=39; d=911 | 0.108671789 [0.0857128114, 0.132075472]; N=39; d=911 | 0.108671789 [0.0857128114, 0.132075472]; N=39; d=911 |
| plausibility_returned | 0.108671789 [0.0857128114, 0.132075472]; N=39; d=911 | 0.108671789 [0.0857128114, 0.132075472]; N=39; d=911 | 0.108671789 [0.0857128114, 0.132075472]; N=39; d=911 |
| tier3 | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 | 1 [1, 1]; N=39; d=911 |
| tier4 | 0.286498353 [0.200858406, 0.378412691]; N=39; d=911 | 0.286498353 [0.200858406, 0.378412691]; N=39; d=911 | 0.286498353 [0.200858406, 0.378412691]; N=39; d=911 |
| joint_tiers | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 |
| joint | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 |
| NO_INTERVENTION | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 |
| RECOVERABLE | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 | 0.0054884742 [0.00112723773, 0.0107071486]; N=39; d=911 |
| PARTIAL | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 | 0 [0, 0]; N=39; d=911 |
| ESCALATE | 0.994511526 [0.989292851, 0.998872762]; N=39; d=911 | 0.994511526 [0.989292851, 0.998872762]; N=39; d=911 | 0.994511526 [0.989292851, 0.998872762]; N=39; d=911 |
| risk_reduction | 0.839364597 [0.834411908, 0.843931433]; N=39; d=911 | 0.839364597 [0.834411908, 0.843931433]; N=39; d=911 | 0.839364597 [0.834411908, 0.843931433]; N=39; d=911 |
| sparsity_all | 1.69923161 [1.64587694, 1.75203878]; N=39; d=911 | 1.69923161 [1.64587694, 1.75203878]; N=39; d=911 | 1.69923161 [1.64587694, 1.75203878]; N=39; d=911 |
| sparsity_returned | 1.69923161 [1.64587694, 1.75203878]; N=39; d=911 | 1.69923161 [1.64587694, 1.75203878]; N=39; d=911 | 1.69923161 [1.64587694, 1.75203878]; N=39; d=911 |

historical query denominators: `{"all_queries": 911, "failed_joint": 906, "failed_model_validity": 0, "not_returned": 0, "returned": 911, "triage_counts": {"ESCALATE": 906, "RECOVERABLE": 5}}`.

corrected_a query denominators: `{"all_queries": 911, "failed_joint": 906, "failed_model_validity": 0, "not_returned": 0, "returned": 911, "triage_counts": {"ESCALATE": 906, "RECOVERABLE": 5}}`.

corrected_b query denominators: `{"all_queries": 911, "failed_joint": 906, "failed_model_validity": 0, "not_returned": 0, "returned": 911, "triage_counts": {"ESCALATE": 906, "RECOVERABLE": 5}}`.

## FD002/xgb/v2/official_test_all_alerts/fast/full

Labels: `{"D_max": 8.0, "K": 1, "dataset": "FD002", "effective_config_hashes": {"corrected_a": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd"}, "corrected_b": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd"}, "historical": {"configs/experiments/phase7-FD002-xgb-v2.yaml": "657b645f03339a7f18f21a97ea28ba8f40191199c7655708dcc5a6d27c6057bd"}}, "k_max": 3, "machine_id": "cmapss_fd002", "mode": "FAST", "model": "xgb", "population": "official_test_all_alerts", "protocol": "v2", "seed": 1729, "spec_hash": "not yet applicable: legacy feature taxonomy before Phase13"}`.

| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |
|---|---|---|---|
| validity | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 |
| plausibility_all | 0.138643068 [0.112533972, 0.164534965]; N=65; d=678 | 0.138643068 [0.112533972, 0.164534965]; N=65; d=678 | 0.138643068 [0.112533972, 0.164534965]; N=65; d=678 |
| plausibility_returned | 0.138643068 [0.112533972, 0.164534965]; N=65; d=678 | 0.138643068 [0.112533972, 0.164534965]; N=65; d=678 | 0.138643068 [0.112533972, 0.164534965]; N=65; d=678 |
| tier3 | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 | 1 [1, 1]; N=65; d=678 |
| tier4 | 0.333333333 [0.258401154, 0.410441481]; N=65; d=678 | 0.333333333 [0.258401154, 0.410441481]; N=65; d=678 | 0.333333333 [0.258401154, 0.410441481]; N=65; d=678 |
| joint_tiers | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 |
| joint | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 |
| NO_INTERVENTION | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 |
| RECOVERABLE | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 | 0.01179941 [0.00480598341, 0.0195517234]; N=65; d=678 |
| PARTIAL | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 | 0 [0, 0]; N=65; d=678 |
| ESCALATE | 0.98820059 [0.980448277, 0.995194017]; N=65; d=678 | 0.98820059 [0.980448277, 0.995194017]; N=65; d=678 | 0.98820059 [0.980448277, 0.995194017]; N=65; d=678 |
| risk_reduction | 0.820837974 [0.813635573, 0.827505721]; N=65; d=678 | 0.820837974 [0.813635573, 0.827505721]; N=65; d=678 | 0.820837974 [0.813635573, 0.827505721]; N=65; d=678 |
| sparsity_all | 1.60471976 [1.54667945, 1.66082877]; N=65; d=678 | 1.60471976 [1.54667945, 1.66082877]; N=65; d=678 | 1.60471976 [1.54667945, 1.66082877]; N=65; d=678 |
| sparsity_returned | 1.60471976 [1.54667945, 1.66082877]; N=65; d=678 | 1.60471976 [1.54667945, 1.66082877]; N=65; d=678 | 1.60471976 [1.54667945, 1.66082877]; N=65; d=678 |

historical query denominators: `{"all_queries": 678, "failed_joint": 670, "failed_model_validity": 0, "not_returned": 0, "returned": 678, "triage_counts": {"ESCALATE": 670, "RECOVERABLE": 8}}`.

corrected_a query denominators: `{"all_queries": 678, "failed_joint": 670, "failed_model_validity": 0, "not_returned": 0, "returned": 678, "triage_counts": {"ESCALATE": 670, "RECOVERABLE": 8}}`.

corrected_b query denominators: `{"all_queries": 678, "failed_joint": 670, "failed_model_validity": 0, "not_returned": 0, "returned": 678, "triage_counts": {"ESCALATE": 670, "RECOVERABLE": 8}}`.

## Borderline predicates

Every tier, individual check, alert/safety gate and triage-improvement margin within the registered1e-6 native-unit envelope is retained in the adjacent `borderline.csv`.
No margin is rounded for classification and no verdict changes. Counts include structural zero margins; these do not imply a failed check.

Borderline export SHA256 `59a149c7dea261a95ffef31a9a938aeca68e2e4522fdebb218f1f4997a783eda`; counts by run/predicate:

```json
{
  "corrected_a/tier4_sensor_coupling": 13538,
  "corrected_a/tier4_sensor_coupling/checks/0/learned_sensor_1": 14612,
  "corrected_a/tier4_sensor_coupling/checks/1/learned_sensor_10": 14612,
  "corrected_a/tier4_sensor_coupling/checks/11/learned_sensor_5": 14612,
  "corrected_a/tier4_sensor_coupling/checks/5/learned_sensor_16": 14612,
  "corrected_a/tier4_sensor_coupling/checks/6/learned_sensor_18": 14612,
  "corrected_a/tier4_sensor_coupling/checks/7/learned_sensor_19": 14784,
  "corrected_b/tier4_sensor_coupling": 13538,
  "corrected_b/tier4_sensor_coupling/checks/0/learned_sensor_1": 14612,
  "corrected_b/tier4_sensor_coupling/checks/1/learned_sensor_10": 14612,
  "corrected_b/tier4_sensor_coupling/checks/11/learned_sensor_5": 14612,
  "corrected_b/tier4_sensor_coupling/checks/5/learned_sensor_16": 14612,
  "corrected_b/tier4_sensor_coupling/checks/6/learned_sensor_18": 14612,
  "corrected_b/tier4_sensor_coupling/checks/7/learned_sensor_19": 14784,
  "historical/tier4_sensor_coupling": 13538,
  "historical/tier4_sensor_coupling/checks/0/learned_sensor_1": 14612,
  "historical/tier4_sensor_coupling/checks/1/learned_sensor_10": 14612,
  "historical/tier4_sensor_coupling/checks/11/learned_sensor_5": 14612,
  "historical/tier4_sensor_coupling/checks/5/learned_sensor_16": 14612,
  "historical/tier4_sensor_coupling/checks/6/learned_sensor_18": 14612,
  "historical/tier4_sensor_coupling/checks/7/learned_sensor_19": 14784
}
```
