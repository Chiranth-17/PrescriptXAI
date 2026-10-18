# Phase 4 diagnosis — superseded historical record

This historical report is superseded by [the final Phase 4 evaluation](phase4_final.md). The
historical table below is preserved only to explain a count discrepancy; it is not a current result
or an approved headline protocol. Its original content was hashed as
`75abd02b4ca3183fa1f9ce97e1d11964ccbd3c8afcc83bcc9cafd17176953f56` in the closure evidence.

## Historical count audit

| Source | Runtime settings | Tier 1 | Tier 2 | Joint |
|---|---|---:|---:|---:|
| Old diagnosis table | Claimed expanded: k=5, scaled movement radius=6, 3 restarts, 100 iterations, 10-point grid | 112/200 | 106/200 | 87/200 |
| Saved k3 run | k=3, radius=4, 1 restart, 25 iterations, 5-point grid | 135/200 | 158/200 | 127/200 |
| Saved k5 run | k=5, radius=6, 3 restarts, 100 iterations, 10-point grid | 174/200 | 161/200 | 156/200 |

The saved k3 and k5 artifacts do not show identical outcomes. The old diagnosis table has no
matching per-query run artifact, so its cause cannot be established. The current one-factor
sensitivity experiment confirms that k=5 changes measured outcomes relative to k=3; the radius 2
and radius 6 experiments leave the measured Tier 1, Tier 2, and joint rates unchanged on that
sample, while latency differs. `max_scaled_distance=6` is a scaled per-feature movement radius,
not Mahalanobis `D_max`; the old expanded run retained `D_max=5`.

See `docs/phase4_final.md` and `docs/phase4_full_diagnosis_results.json` for the current frozen
k≤3 headline, protocol v1/v2, all-alert, first-alert, grouped OOF, official-test, triage, sensitivity,
and diagnostic evidence. C-MAPSS has no real actuator commands or intervention responses; the
results are E1 software/dataset evidence and do not show RUL extension or operational safety.
