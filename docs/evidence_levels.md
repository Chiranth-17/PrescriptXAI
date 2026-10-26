# Evidence levels

These labels describe the checks reached by a particular result, not operational certification.
Tier verdicts remain visible independently; an overall label cannot replace them.

| Level | Required evidence | Current support |
|---|---|---|
| E1 | Final true calibrated model risk at or below tau_safe | Implemented; model-based only |
| E2 | E1 and Tier2 training-distribution plausibility | Implemented; coarse statistical test |
| E3 | E1/E2 and proxy bounds/rates/frozen features plus learned/configured coupling checks | Implemented under documented C-MAPSS proxy assumptions |
| E4 | Learned dynamic emulator validated on held-out units and operating regions | Unavailable |
| E5 | Independently validated physics simulator | Unavailable; optional interface off by default |

The report's evidence label is conservative and cumulative. PARTIAL fails the model-safe gate,
so it does not inherit E1 just because its proxy constraints pass. ESCALATE may expose a diagnostic
candidate with E1 and failed plausibility; this is not an accepted intervention. NO_INTERVENTION
means below the alert gate, which is distinct from being at or below the safe threshold.

Plausibility means **Tier2 only**, with both all-query and returned-candidate denominators.
Tier3, Tier4 and joint success are additional separate results. Coupling R2/residuals, Mahalanobis
margins, surrogate error and tier failures accompany risk reductions. A learned correlation model,
low predicted risk or a large sensor change never proves real actuator efficacy. No RUL extension
is claimed on static C-MAPSS data. See [assumptions](assumptions.md), [limitations](limitations.md)
and the [measured results](results.md).
