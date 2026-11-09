# Phase 12 mismatch classification

The 712 diagnostic cases compare the immutable Phase 7 reference with the intermediate failed repair. The corrected full replay matched the reference across all 32,116 cases. The classification below records the historical discrepancy.

The independent extraction is saved at `artifacts/phase12/solo-closeout-classification-audit.json`, SHA-256 `6c0ea875514437cc39828d2e4b7ad1575b3e0cc02cdb61d6c3e5da3c514507d4`. The registered diagnostic is `configs/experiments/phase12-closure-712-v1.yaml`, SHA-256 `0734fe7c3ff3a625413bc954f617af0de52e0e6fc0edcb831511782fb1efb5c1`. The reference source is `63c2ed445fba16c73a2771e184f635abf76b4405`, and the classification source is `2f31e51d56bd85100859bd2a64fa9480ae24e592`.

## Tier 2 and triage flips

All three triage flips overlap the 15 Tier 2 flips. Eight Tier 2 decisions changed from pass to fail and seven changed from fail to pass. The smallest absolute Tier 2 margin was 0.00019841391200259295 historically and 0.0007468255054048356 in the intermediate repair. Every flip lies outside the registered 1e-6 borderline band.

The controlled graph/layout factorial attributes all 15 flips to changed candidates from feature-lift graph arithmetic. Its graph-only arm recovers the original candidates and verdicts. Repetition across eight process and thread conditions reproduced the intermediate results exactly. The independent saved-candidate checks agreed exactly on all 1,424 primary score comparisons. The scaler-layout arm explains the remaining surrogate score differences. The combined arm recovers all 712 results exactly. The factorial contains two documented segments.

Run `closure-712-20261106-v1`, FD002 XGBoost FAST, K=1, k_max=3. Protocol v1 uses D_max=5 and v2 uses D_max=8. Positive margin means the Mahalanobis check passed.

| Case ID | Protocol | Population | Engine/cycle | Reference margin | Intermediate margin | Triage |
| --- | --- | --- | --- | ---: | ---: | --- |
| `15d76dc4cc4cf4cc6f5fcb7c302e44fcf48c501ea6f93ee786086d29381bcf88` | v2 | grouped_oof_all_alerts | 107/131 | 0.000972725506735 | -40.6284915313 | RECOVERABLE → ESCALATE |
| `30cbf8dd57edf09a184288f28e39fcb214d47fecb6ce529f4194ea9d87f21394` | v2 | official_test_all_alerts | 10116/149 | -0.0121526008003 | 0.104544006565 | ESCALATE → RECOVERABLE |
| `37f42e9130db62fed08513c6a1339d259808d754db81202b4ca970067ae48965` | v1 | grouped_oof_all_alerts | 245/222 | -7.10636155069 | 0.0287202008143 | ESCALATE |
| `521d7c2681865820129bc4f0fcc962909d139a5ca08d01d8e971eb32302a5e42` | v2 | grouped_oof_all_alerts | 105/262 | 0.0893061197006 | -0.0100919025325 | ESCALATE |
| `5a2e399370f929faed7930c5170e1022e5cd131e7ab71ba1279c48a9cb20ae47` | v2 | official_test_all_alerts | 10064/217 | -0.000198413912003 | 0.263467992382 | ESCALATE → RECOVERABLE |
| `708c12859bd3581a34d2ec8c0f1819ad81c9fbca6989efac6edb0f471e2b6c65` | v1 | grouped_oof_all_alerts | 113/216 | -7.64456788968 | 0.310941322783 | ESCALATE |
| `7ae8171b45b02208ce61b7917fd0ae397ad60278902cdec120718abaac7b59c8` | v2 | grouped_oof_all_alerts | 83/158 | 2.67663209831 | -5.35339411401 | ESCALATE |
| `8b9d006a4261c7337d6ebe70d49d1b117edcc5c9674a2ef39b23f7ad887d356e` | v2 | official_test_all_alerts | 10090/157 | 2.36597957151 | -4.1278362668 | ESCALATE |
| `a25b2f6d35c79883ca95c8178df126fb1ee0acc388bea28dcc23028ddd99bed3` | v1 | grouped_oof_all_alerts | 94/287 | 0.000319011028279 | -0.00168798413389 | ESCALATE |
| `b114e1db7252290481c37f3831f88c8d545a8bee6811c23b52cc2dca76be87a3` | v1 | internal_heldout_all_alerts | 2/245 | 0.819775286073 | -7.13656451807 | ESCALATE |
| `b2bb8ec0a9bde4e47864f034ceee7488700b56c7ad8fbba8b775008f5a10dcec` | v2 | grouped_oof_all_alerts | 247/196 | -5.55697383416 | 0.0460082275775 | ESCALATE |
| `bc33e72061d6d9ed0b1000268ba1b36fc9f6849970721bad541f6841a417a104` | v2 | grouped_oof_all_alerts | 145/250 | 0.131125726785 | -11.3917453053 | ESCALATE |
| `ecf384cd945a3e07a0c634eef2cdd16ece4703019e4889b41c82965c815bd19a` | v1 | internal_heldout_all_alerts | 113/204 | -0.000547508052231 | 0.544139577416 | ESCALATE |
| `eeb2001699ddae4a030b92d532cad02cff7a9b574c5cd06097bce0619769a19b` | v1 | grouped_oof_all_alerts | 221/169 | 0.0321872758878 | -0.000746825505405 | ESCALATE |
| `f7625ab48faa69c2a30dcb3f55832a8f51d5b69cec6f3423642849dbbf3a3d83` | v2 | internal_heldout_all_alerts | 112/359 | -0.0174441532403 | 0.0539340077598 | ESCALATE |

## Other 697 cases

The remaining cases include 29 support changes, 660 cases with the same support and changed control values, and eight identical candidates. Several differences exceed 1e-6, including a primary risk difference of 0.1691702562816351. The graph/layout factorial accounts for these differences too.

These are fieldwise maxima for the registered diagnostic selection. The associated run group identifies the dataset, model, protocol and population at each maximum. Absolute maxima use the recorded field units. Relative fractions divide by the magnitude of the historical value, with zero denominators excluded.

| Field | Maximum absolute difference | Run group at absolute maximum | Maximum relative fraction | Run group at relative maximum |
| --- | ---: | --- | ---: | --- |
| `/candidate/sensor_1` | 1.17252793579 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.00239266244101 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_10` | 0.0592943642932 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.0524387955512 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_11` | 2.04436568675 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.0480626287584 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_12` | 90.012 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.401591876433 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_13` | 0.513191605411 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 0.000214911123145 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_14` | 49.1980462902 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 0.00610870717009 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_15` | 0.0824239177689 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 0.00891377092577 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_16` | 0.000496292226519 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.0169179640656 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_17` | 5.39999615748 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 0.0164835047542 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_18` | 0.726986555618 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.000312707196348 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_19` | 0.000163067126152 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 1.63066748013e-06 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_2` | 6.66112550978 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.0110878992643 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_20` | 0.604987197584 | FD002/xgb/v2/internal_heldout_all_alerts/fast/full | 0.0244686429761 | FD002/xgb/v2/internal_heldout_all_alerts/fast/full |
| `/candidate/sensor_21` | 0.283728586245 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 0.023734217824 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_3` | 41.5813209247 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.0286623540902 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_4` | 58.1744200008 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.0487976159496 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_5` | 2.34706745558 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.335604202464 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_6` | 3.58005494918 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.355689714543 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_7` | 88.3749922508 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.360233249481 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_8` | 0.00473148911829 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 2.46925425857e-06 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/candidate/sensor_9` | 61.7834471356 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 0.00709607201105 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/changed_features` | — | — | — | — |
| `/mahalanobis_after` | 296.268133173 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 0.98336279514 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/proxy_sparsity` | 2 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 2 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/raw_l1` | 310.141451666 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 1.75358076443 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/risk_after` | 0.169170256282 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full | 6.57555050858 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/scaled_l1` | 5.07738504352 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 1.75849523634 | FD002/xgb/v2/grouped_oof_all_alerts/fast/full |
| `/sparsity` | 2 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 2 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |
| `/surrogate_after` | 0.206051951063 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full | 19056.182632 | FD002/xgb/v1/grouped_oof_all_alerts/fast/full |

The full corrected replay preserves the original counts, whole-engine confidence intervals and denominators for all 24 headline groups. See [the headline impact report](phase12_headline_impact.md). The known-differences list is empty.
