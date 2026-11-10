# Phase 17 slider response

The synopsis UI budget remains 250 ms. One of eight measured groups met it
after the dashboard changes. The original solo workflow's 50 ms browser target
also remains unmet. Each group contains 20 measured edits and four warmups.

| Viewport | Recorded unit / cycle | Before scoring p95 (ms) | After scoring p95 (ms) | Before browser p95 (ms) | After browser p95 (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| desktop | 82 / 156 | 23.3 | 32.0 | 372.8 | 437.6 |
| desktop | 31 / 190 | 24.3 | 31.0 | 389.0 | 443.2 |
| desktop | 76 / 205 | 23.7 | 26.8 | 396.8 | 241.8 |
| desktop | 76 / 201 | 24.3 | 26.3 | 380.7 | 258.3 |
| phone | 82 / 156 | 24.7 | 29.8 | 364.4 | 440.1 |
| phone | 31 / 190 | 24.3 | 31.0 | 390.8 | 423.2 |
| phone | 76 / 205 | 24.6 | 31.9 | 385.1 | 281.2 |
| phone | 76 / 201 | 23.5 | 28.4 | 376.8 | 250.7 |

The browser interval runs from a trusted keyboard edit to the first frame with
the updated settings and risk on an idle page. Server scoring measures only the
`simulate_risk` call, which includes input validation and result binding. The
benchmark repeats the same registered FD001 XGBoost v1 presets and slider
endpoints at both widths. The earlier run used Alerts-only. The new run used
demonstration limits, where returning to recorded settings can also render a
completed prescription and follow-up. The difference in publication mode means
the before/after comparison does not isolate the effect of caching or fragments.

The model resource, parsed spec and observed data are cached with content-based
identity. Streamlit reruns the adjustable controls, risk and dependent output
cards as a fragment, leaving the surrounding page in place. Manual edits do not
start prescription solves. The remaining browser interval includes Streamlit's
widget event, fragment execution and result delivery, plus browser rendering.
This benchmark measures that combined path. It does not assign times to its
individual parts. The 400 ms debounce applies only to recorded prescriptions.
A separate process runs native FAST search with the existing single-thread
worker policy. A superseded result cannot publish.

The earlier source was `6a9ba75e352381f55afc9fd790a5afd7ebb1e7ed`.
The after source was `2376bdbb0ea9a2df207765e464bf157ac60228d8`.
The registered after plan was `configs/experiments/phase17-preview-latency-v3.json`
(SHA-256 `2002dd767729a2c816a933b4611b35e7878e22bfa673c2d4bf0079e56d92c9f1`).
Both completed runs retained 192 observations each under
`artifacts/phase17/preview-latency-20261110-v2` and
`artifacts/phase17/preview-latency-20261110-v7`. The intermediate attempts
remain preserved. They captured an ordering race between the settings URL and
risk display, and prescription settling timeouts before process isolation.
These measurements cover the local browser workflow. Historical serial and
prescription latency use separate evidence.
