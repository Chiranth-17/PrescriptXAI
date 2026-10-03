---
status: FINALIZED
created: 2026-10-03
finalized: 2026-10-03
source: docs/synopsis.pdf and user project request
---

# SPEC.md — PrescriptXAI Project Specification

## Vision

Build `prescriptxai`, a reproducible Python package for generating sparse, actuator-only recourse for high-risk predictive-maintenance states and independently validating model safety and physical plausibility. The system must present recommendations as decision support, never as proof of real-world safety or RUL extension.

## Goals

1. Provide an end-to-end C-MAPSS workflow with engine-level data splits and train-only fitting of scalers, calibrators, and operating-distribution validators.
2. Generate sparse bounded recourse that targets configurable failure risk and observes actuator bounds, rate limits, immutable masks, and sensor-coupling rules.
3. Validate model risk separately from Mahalanobis plausibility, engineering constraints, and coupling; report measured evaluation outcomes without hardcoded results.
4. Deliver a typed library, YAML configuration, CLI, optional FastAPI service, Streamlit dashboard, evaluation suite, and technical documentation.

## Non-Goals

- Claiming causal intervention effects, closed-loop control, or real-machine safety from static benchmark data.
- Claiming RUL extension on C-MAPSS.
- Enabling simulator validation by default or presenting an unavailable simulator as implemented.
- Embedding synopsis case-study numbers as benchmark results.

## Constraints

- Python 3.11+, `src/` layout, pinned dependencies, and the user-specified stack and repository layout.
- Data and trained artifacts are git-ignored; data directories retain `.gitkeep`.
- All thresholds, masks, bounds, rate limits, `D_max`, and sparsity `k` are YAML-configurable.
- Failure label is `1[RUL <= H]`, with configurable default `H=30`, `tau_danger=0.80`, `tau_safe=0.20`.
- Split by engine ID. Fit preprocessing, covariances, and calibration only from training engines.
- Report both raw physical deltas and scaled optimization deltas, with tested mappings.
- C-MAPSS is static run-to-failure data. Simulator interface is optional and disabled by default.
- No fake results or skipped/stubbed tests. Record blockers in `PROGRESS.md` with reason and options.
- Each implementation phase should include unit, integration, and negative/edge coverage; run ruff, mypy, and pytest with coverage, update `PROGRESS.md`, and commit conventionally. If the workspace is not a Git repository, document that blocker rather than claiming a commit.

## Success Criteria

- [ ] Requested package, CLI, optional API, dashboard, evaluation, and docs exist and are runnable.
- [ ] Engine-level splitting and train-only fitting are enforced and covered by tests.
- [ ] Recourse either satisfies all configured constraints or returns a truthful failure with diagnostics.
- [ ] Model validity and physical plausibility are always distinct in API and reporting.
- [ ] Metrics, latency, and dashboard values are generated from real runs and compared honestly with synopsis targets.
- [ ] Ruff, mypy, pytest with coverage, and pre-commit checks pass for delivered phases.
- [ ] C-MAPSS limitations and absence of dynamic RUL claims are visible in docs and dashboard.

## Decisions and Open Questions

- Treat the user's detailed engineering rules as acceptance criteria; the synopsis is authoritative for the research framing and targets.
- Use a transparent, deterministic baseline before exploring more complex optimizers or deep models. Do not imply gradients for models that do not provide them.
- Dataset retrieval may require network access or user-provided files; acquisition failures must be explicit and must not generate synthetic benchmark results.
- Dynamic simulator integrations remain optional adapters and are not required for baseline acceptance.
