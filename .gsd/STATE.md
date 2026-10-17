---
phase: 1
created: 2026-10-03 06:40 UTC
status: complete
---

# Phase 1 State Snapshot — Data Ingestion and Preprocessing

## Objective

Implement canonical C-MAPSS loading and a reproducible preparation workflow with no synthetic
benchmark data, engine-disjoint partitions, train-only preprocessing, and an auditable report.

## Changes Realized

- Canonical `unit_id`, `cycle`, operational settings, and sensor schema with strict file checks.
- RUL labels, optional cap defaulting off, inclusive `RUL <= H` target, and official truncated-test
  RUL expansion.
- Lifetime-stratified engine partitions, per-subset sensor filtering, multi-condition regimes,
  reversible raw/scaled mappings, persisted artifacts, and deterministic data reports.
- `prescriptxai data download|prepare --subset ...` commands and C-MAPSS documentation.

## Verification Results

| Check | Command | Result |
|---|---|---|
| Lint | `mingw32-make all-checks` | Ruff passed |
| Types | `mingw32-make all-checks` | Mypy passed for 48 source files |
| Tests | `mingw32-make all-checks` | 95 passed, 80% coverage |
| Docs | `mingw32-make all-checks` | Passed |
| Real data | `prescriptxai data prepare --subset FD001` plus FD002–FD004 | All published row counts matched |

## Risks and Technical Debt

- No expected archive digest is configured; the local SHA-256 is recorded. Download transfer was
  not attempted because a valid archive was already cached.
- Static C-MAPSS does not support claims of RUL extension or intervention effect.
- Default actuator taxonomy remains unverified and does not establish physical recourse.

## Context for Next Session

See `PROGRESS.md` for exact per-subset retained features and row counts. Real preparation reports
and outputs are present locally in ignored `data/processed/` and `artifacts/` directories.

---
phase: 4
created: 2026-10-17
status: complete
---

# Phase 4 State Snapshot — Constrained Recourse

## Initial diagnostic (superseded)

The first benchmark found 54 actuator-bound and 54 rate-limit violations, plus 42 sampled states
with no nonempty one-step interval. The candidate fallback and actionable-state selection were
subsequently corrected. A later diagnosis also found that Tier 3 was applying empirical sensor
percentiles as actuator constraints, which invalidated every result. Those first-pass results are
historical and are superseded by the corrected run below.

## Corrective work and latest real-data results

- Failed optimization searches now retain the nearest point in the feasible actuator/rate
  intersection when one exists; an empty intersection sets
  `actuator_constraints_feasible=false` and returns a structured failure.
- Tier 3 now checks actuator bounds only; immutable equality and per-step rates remain explicit,
  while empirical sensor distribution is checked by Tier 2 and statistical coupling by Tier 4.
- Replaced the default 3%-of-range proxy rate with the configured training-engine-only p99
  adjacent-cycle telemetry change. It is fitted without crossing engine boundaries and persisted
  with the model artifact. These are sensor movement envelopes, not actual actuator slew rates.
- Added `recourse_feasible` to prevent a risk-safe but over-`k_max` diagnostic from being reported
  as a successful sparse action. Model validity remains the measured calibrated risk check;
  physical plausibility remains Tiers 2–4; joint success also requires sparse optimizer feasibility.
- The corrected real FD001 benchmark sampled 200 of 378 actionable high-risk held-out states. It
  measured model validity 25/200 (12.5%), sparse feasibility 23/200 (11.5%), joint success 22/200
  (11.0%), physical plausibility 136/200 (68%), Tier 2 68%, Tier 3 100%, and Tier 4 100%.
  Mean risk reduction was 0.52495, mean successful-action sparsity 2.27273, and there were zero
  frozen-feature, actuator-bound, or rate-limit violations.
- Mean/P95 optimization latency was 701.71/1,148.80 ms and mean/P95 pipeline latency was
  709.54/1,158.01 ms. The mean latency target minima (1,200 ms and 1,500 ms respectively) were
  not met. Validity, plausibility, risk-reduction, and latency targets remain unmet.
- The benchmark used a temporary ignored config with 25 max iterations, one restart, three alpha
  steps, one L1 escalation step, and a two-support search cap; this is recorded in the saved report.
  A separate 40-state probe with 100 iterations, eight alpha steps, and eight supports increased
  true model validity to 20/40 and joint success to 16/40, but mean optimization latency rose to
  4,655.82 ms; it is not the default strategy. Two risk-safe outputs in that probe exceeded the
  three-feature cap and are now excluded from sparse feasibility and success.
- `mingw32-make all-checks` on Python 3.13.9: Ruff passed, mypy passed for 49 source files, 143
  tests passed with 77% total coverage, and the documentation target passed. The 24 warnings were
  convergence notices from deliberately short nonlinear coupling test fixtures.
