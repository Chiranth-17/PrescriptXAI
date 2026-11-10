# Advisory safety case

This is a research safety case for advisory software. Qualified people retain
decision authority. The application does not send machine-control commands.
The evaluated C-MAPSS records and their controls are simulated measurements
and proxies. The evidence supports model-risk, statistical and configured
proxy checks within the recorded setting.

| Hazard | Argument and control | Verified evidence | Residual risk |
| --- | --- | --- | --- |
| Operator acts on a wrong recommendation | Use separate model-risk, distribution, control and coupling checks. Withhold a candidate when a required check fails. Show the current limits mode in the interface and export. | Phase 17 exercised Advisory, demonstration and Alerts-only. Its registered subset matched exactly and the live dashboard removed actions on an edit. | High if an operator interprets the demonstration as real machine advice. A real deployment needs engineering confirmation, independent review and a supervised pilot. |
| Operator ignores an alert | Surface a calibrated alert and show when no prescription is available. The operator must have an independent maintenance response. | Phase 17 recorded alert and withholding states. | Human response was not measured. The software cannot establish action or intervention efficacy. |
| Spoofed input causes a candidate to pass | Input quality, user authentication and four independent checks reduce invalid requests. Recheck any applied settings against independently established observations. | The bounded FD001 test withheld eight of 16 spoofed requests. Two published prescriptions failed the model-risk check when rechecked on the original recorded observation. | High for plausible spoofed telemetry. Require authenticated sensor provenance and independent operations review before any plant use. |
| Stale or altered model changes decisions | Bind results to the observed input and model/configuration context. Hosted loaders require an independent checksum manifest and reject modified or unlisted serialized files. | Phase 17 stale-input tests and Phase 16 artifact replacement tests. Authenticated Chromium exercised the retained three pinned fitted files. | Administrator trust, model approval and manifest rotation remain outside the application. |
| Feedback appears to show real actuation | Record configured proxy adherence and preserve the source label. Model recalculation uses the supplied settings and current context. | Phase 17 rendered labeled simulated feedback and scoped results. | A local log does not prove what happened to a machine. Protect the database with host permissions. |

## Bounded FD001 spoofing evidence

The committed design `configs/experiments/phase16-spoofing-v1.yaml` was run
at source `cd61f2d`. It selected four official-test alert presets from
three FD001 units, XGBoost v1, FAST, \(K=1\), and at most three changes.
Each attempt moved one of two dependent sensors ten percent of the distance
to a fitted bound. The original history and all control inputs were held fixed.
A success meant publication on the spoofed input followed by at least one
failed check when the same controls were reapplied to the original observation.

| Outcome | Attempts |
| --- | ---: |
| Withheld on the spoofed request | 8 |
| Published and passed all four checks on the original observation | 6 |
| Published and failed a check on the original observation | 2 |
| Total | 16 |

Tier 1 withheld five and Tier 2 withheld four, with one request in both counts.
The two bypasses occurred at unit 82, cycle 156. Spoofed predictions after the
prescription were 17.52% and 19.40%. On the original recorded observation the
same controls produced 23.65% and 21.39%, both above the registered 20% threshold.
Both bypasses failed Tier 1. The observed success fraction was 2 of 16
(12.5%) in this selected sample. The raw cases and receipt are under
`artifacts/phase16/spoofing-20261110-v1`.

The selected sample supports neither a population attack rate nor a physical
safety claim. Transport authentication establishes the account behind a
request. It does not establish the authenticity of the upstream sensor value.
