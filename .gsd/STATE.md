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

## Failed validation evidence

The first deterministic 200-row FD001 high-risk held-out sample selected randomly from 378
high-risk rows. It reported model-validity rate 0.0, mean risk reduction 0.08650, mean optimization
time 2573.73 ms, and zero frozen-feature changes. It also found 54 actuator-bound and 54 rate-limit
violations. Inspection showed 42 sampled states had no nonempty one-step intersection of empirical
actuator bounds, rate limits, and the configured scaled movement limit; two other failed outputs
echoed an out-of-range input rather than projecting to a reachable bound.

## Corrective work and final verification

- Failed optimization searches now retain the nearest point in the feasible actuator/rate
  intersection when one exists; an empty intersection sets
  `actuator_constraints_feasible=false` and returns a structured failure.
- Evaluation counts every high-risk held-out row, reports infeasible-interval cases separately,
  and samples the requested recourse benchmark from the remaining actionable states.
- The final real-data FD001 run sampled 200 of 308 actionable states out of 378 total high-risk
  held-out rows. It recorded 0 frozen-feature, 0 actuator-bound, and 0 rate-limit violations.
- No recourse candidate met the true calibrated risk target: model validity 0/200, Tier 2 95.5%,
  Tier 3 0%, Tier 4 100%, and overall physical plausibility 0%. Mean risk drop was 0.12047. Mean
  returned diagnostic action size was 2.595; valid-result sparsity remains unmeasured.
- The measured mean/P95 optimization latency was 472.10/1,104.92 ms, below the synopsis target
  interval 1,200–1,800 ms; mean pipeline latency was 483.32 ms, below its 1,500–2,200 ms interval.
- The benchmark used a temporary ignored config with 25 max iterations, one restart, three alpha
  steps, one L1 escalation step, and a two-support search cap; this is recorded in the saved report.
  This reduced search budget is a limitation of the benchmark and does not change its validity
  criterion. The full default search was stopped after it spent over 20 minutes in one case.
- `mingw32-make all-checks`: Ruff passed; mypy passed for 49 source files; 139 tests passed with
  77% total coverage; docs target passed. The only warnings came from deliberately short nonlinear
  coupling test fixtures.
