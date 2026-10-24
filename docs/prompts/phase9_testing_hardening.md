# Phase 9 — systematic testing, debugging and hardening

Source: the user's direct prompt, received 2026-10-24 IST. Execute only after the full
Phase 7 gate and then the full Phase 8 gate pass. These are queued requirements, not
completed work. Keep the historical Phase 7 measurement source and results intact.

PHASE 9: systematic testing, debugging and hardening of the whole system. Try to BREAK it and fix what breaks. Log every defect in docs/defects.md (id, symptom, root cause, fix, regression test). Read AGENTS.md and PROGRESS.md first and inspect the repo.

1. COVERAGE: raise line coverage to at least 90% on src/prescriptxai, excluding dashboard rendering internals covered by AppTest; add tests for every meaningfully reachable uncovered branch.
2. PROPERTY-BASED TESTS (hypothesis): frozen features never change; bounds respected; sparsity <= k_max on success; raw/scaled round trip; D_M non-negative and zero at the mean; validation verdict consistent with tier results; recourse never returns NaN or inf; triage outcome consistent with its definition; PARTIAL never reported when f(x') <= 0.20.
3. FUZZING AND EDGE CASES: NaN/inf/None inputs, wrong column order and dtypes, extreme magnitudes, identical vectors, already-safe states, states impossible to fix, empty and huge batches, unicode in API fields, concurrent requests.
4. FAULT INJECTION: corrupt artifacts, missing calibrator, mismatched feature list, singular covariance, solver non-convergence, missing coupling model, contradictory config values. Each must raise a clear typed error or return a structured failure, never a raw stack trace to the operator.
5. GOLDEN REGRESSION TESTS: fixed-seed runs on a fixture produce stored outputs with documented tolerances; changing a golden file requires an explicit flag.
6. NUMERICAL ROBUSTNESS: float32 versus float64 consistency; determinism across two runs and across process restarts.
7. PERFORMANCE: profile (cProfile or py-spy), optimize hot spots without changing results (verified by golden tests), report before and after latency, check memory growth over 10,000 calls.
8. SECURITY: dependency audit (pip-audit), API input size limits, no pickle loading from untrusted paths (use JSON, NPZ, safetensors or XGBoost native formats; document and restrict any pickle), no secrets in the repo.
9. SCIENCE DEBUGGING PASS: for each of these write a test even if no bug is found: leakage (anything fit on test or evaluation states, including solver settings tuned on test states); wrong scaling direction; inverted threshold comparisons; off-by-one in RUL labels; regime mismatch in Mahalanobis; surrogate versus true model confusion in validity; calibration applied twice or not at all; sign errors in rate limits; denominators dropping failed queries from rates; physical_valid versus plausibility definitions mixed up; latency verdicts using the band's lower figure as a minimum.
10. END-TO-END TEST: raw fixture data -> train -> calibrate -> fit validators -> recommend -> validate -> API call -> dashboard AppTest, all in a temp directory.
11. CI: lint, mypy, tests with coverage thresholds, coverage upload; a nightly job for slow tests (markers: slow, e2e, gpu).

GATE: zero failing tests; zero ruff and mypy errors; coverage threshold met; defect log complete; no known open critical bug. Any defect that cannot be fixed goes into docs/limitations.md with an honest impact statement. PROGRESS.md updated.

Inherited phase closure: run the complete gate, preserve coverage, update traceability and
progress, commit conventionally, tag `phase9-closed` only after the gate passes, and send a
short status with real numbers and open issues. Then begin the queued Phase 10 prompt.
