# PrescriptXAI contributor instructions

- Read `docs/synopsis.pdf` and `.gsd/SPEC.md` before changing model, recourse, or validation behavior.
- Treat the synopsis case study as illustrative. Generate reported numbers from saved, reproducible runs.
- Keep model safety (`f(x') <= tau_safe`) separate from plausibility checks in Tiers 2–4.
- Never claim RUL extension from static C-MAPSS data. Keep the simulator interface optional and off by default.
- Keep thresholds, bounds, masks, rate limits, `D_max`, and sparsity limits in YAML configuration.
- Split by engine ID. Fit scalers, calibrators, and covariance validators on training engines only.
- Keep raw-unit and scaled-space deltas explicit and test their mappings.
- Add unit, integration, and negative/edge tests for each behavior phase. Do not make tests pass by skipping, stubbing, or fabricating results.
- Run `ruff`, `mypy`, and `pytest --cov=prescriptxai`; update `PROGRESS.md` after every phase.
- Keep generated data and fitted artifacts out of version control.

12. BLOCKER PROTOCOL: there is no validated simulator, real actuator telemetry or measured sensor response beyond public datasets, and that is NOT a blocker. C-MAPSS channels are controllable PROXIES; the proxy mapping, bounds and rate limits are documented assumptions (docs/assumptions.md) and are labeled as assumptions in every report and in the dashboard. When a decision needs evidence that does not exist, pick the most conservative documented default, record it and continue. Ask the user only for manual download steps.
13. TARGETS: synopsis numbers are design targets. A measured result with a gap analysis is an acceptable deliverable; a hidden or redefined metric is not. Never change tau_safe, tau_danger, D_max, physical bounds or rate limits after seeing evaluation results to pass a target.
14. LATENCY: synopsis Section 7 values are budgets (ingestion < 10 ms, inference < 15 ms, optimization 1.20-1.80 s, validation < 100 ms, UI < 250 ms, total about 1.5-2.2 s). A stage passes if its p95 is at or below the upper figure. Faster is a pass.
15. TRACEABILITY: every reported number references a committed config under configs/experiments/ and a git hash. No experiment configs under data/. No hardcoded results anywhere; the synopsis case study (88% to 17%, fuel -3.2%, bypass +1.1%) is illustrative only.
16. MODEL SELECTION: choose predictors by predictive and calibration metrics only. Never tune the predictor on recourse outcomes. Recourse feasibility of alternative models may be reported only as a separate, labeled experiment.
17. PRE-REGISTRATION: evaluation populations, metric definitions, the intervention horizon K, D_max method and quantile, and the tuning/test split are written into docs/evaluation_protocol.md and COMMITTED before the experiment that uses them. Solver settings are tuned on development states from validation engines, frozen, and evaluated once on held-out test engines.
18. EVIDENCE LEVELS: E1 model-based validity (Tier 1); E2 statistical plausibility (Tier 2); E3 proxy engineering constraints on C-MAPSS channels (Tiers 3-4); E4 learned emulator validated on held-out units and operating regions; E5 validated physics simulator. Every result and every recommendation states the highest level it reached. No RUL-extension claims. No emulator or learned model is ever described as a physics simulator.
19. INTERFACE FREEZE: the RecourseResult and ValidationReport schemas are versioned. After Phase 6 they change only with a version bump, a changelog entry and agreement from every owner.
20. METRIC DEFINITIONS: Validity = true calibrated f(x') <= 0.20. Plausibility = D_M(x') <= D_max (Tier 2 only), reported both over returned counterfactuals and over all queries. Tier 3 and Tier 4 pass rates are reported separately. Joint success (Tiers 1-4 all pass) is an extra, stricter metric and is never compared with the 90% plausibility target. Failed queries are never dropped from a denominator without being reported.
21. After every phase: run ruff, mypy and pytest with coverage (coverage must not fall); fix every failure; update PROGRESS.md (done, decisions, assumptions, open issues, how to run); commit with a conventional commit message; send the user a short status with real numbers.

22. CIs: every interval is a bootstrap over ENGINES; show the number of engines beside it. Plain binomial intervals over states are not acceptable.
23. EVALUATION SETS: development = validation engines; reported results = held-out test engines, grouped cross-validation across all training engines, and the official test engines when cycle-level RUL can be derived. Report all, side by side.
24. PROTOCOL VERSIONS: v1 (D_max = 5.0) and v2 (D_max = 8.0) are both reported. A new version is committed before the run that uses it, evaluated on fresh engines, and never replaces an earlier one.
25. ASSUMPTION-GOVERNED METRICS: the one-step rate limit and the intervention horizon K are documented assumptions. Validity is shown as a function of K (a curve) next to the K = 1 headline, and is never described as physical fact.
26. ORACLE RULE: a reference search may label a state "truly infeasible" only if it is verified to be a superset of the production search (it must reproduce the production candidate). Classification is per FAILED state of the production solver.
27. RUN LABELS: every table states its run id, config hash, protocol version, k_max, K, D_max version and population. Sensitivity runs change one factor at a time and are labeled as sensitivity. Log EFFECTIVE solver settings at runtime, not the config echo.
28. EVIDENCE FOR CLAIMS: a claim about consistency, fidelity or plausibility cites error or margin metrics (R2, residual std, share beyond threshold, D_M distributions), not the size of a change.
29. TIER 1 IS WEAK ALONE: because the predictor can be driven near zero risk by moving proxy sensors, any report of validity is accompanied by plausibility, coupling checks and the evidence level reached.

30. ADVISORY ONLY. The system recommends; a human decides. It never writes to a machine, PLC, historian or control system. All connectors are read-only.
31. MACHINE-AGNOSTIC CORE. src/prescriptxai/core has no dataset, machine or sensor names. Machine details live in spec files, adapters and the asset library. A test enforces it.
32. TESTED-ONLY CLAIMS. Name the machines tested and mark each real-benchmark or synthetic. Never write "works on any machine", "proven", "certified" or "extends engine life".
33. ENGINEER SIGN-OFF. Bounds, step limits, failure definition and the controllable/frozen split need a named engineer's confirmation (name, role, date). Without it a machine runs in Alerts-only mode.
34. FAIL SAFE. If data quality, input integrity, plausibility or any check fails, withhold the recommendation and say why.
35. EVIDENCE-GATED MODES. Alerts only, Advisory (shadow), Advisory (live). A readiness scorecard decides which are allowed. Promotion is manual, demotion can be automatic.
36. NO POOLED NUMBERS. Results are per machine. Every table carries machine id, spec hash, protocol version, run id, K and population.
37. LABEL SYNTHETIC AND SIMULATED DATA everywhere: tables, charts, exports, UI.
38. SECURITY BY DEFAULT. Authentication on, least-privilege roles, no secrets in the repo, tamper-evident audit log.
39. STANDARDS ARE GUIDANCE ONLY (ISO 13374, ISO 14224, ISO 17359, OPC UA, IEC 62443). Never claim compliance.
40. REPRODUCIBLE. Results are deterministic: fixed seeds, iteration budgets for search (wall-clock only for reporting). Every release passes `make verify` from a clean clone.
Send a short status with real numbers after every phase.
