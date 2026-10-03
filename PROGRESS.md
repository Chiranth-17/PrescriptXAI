# PrescriptXAI Progress

## Phase status table

| Phase | Status | Notes |
|---|---|---|
| 0 — Project scaffold | Complete | Packaging, configuration, schemas, logging, CI, and checks |
| 1 — Package foundation | Complete | Typed configuration and feature taxonomy |
| 2 — Data and predictive models | Complete | Engine-level splits and training-only fitting |
| 3 — Constrained recourse and validation | Complete | Optimizer and validation tiers |
| 4 — Product surfaces and evaluation | Complete | CLI, optional API, dashboard, reports |
| 5 — End-to-end verification and documentation | Complete | Current measured limits in docs and artifacts |

## Decisions

- Preserve the user-provided synopsis as the source of truth; its numeric case study is illustrative.
- Keep model validity and physical plausibility as separate outcomes.
- Keep every threshold, budget, path, and algorithm parameter in validated YAML.
- Use the PRESCRIPTXAI_ environment variable prefix for runtime overrides; double underscores
  separate nested keys.
- Use PEP 735 dependency groups (core, dev, dashboard, api) with exact pins in pyproject.toml and
  complete transitive pins in uv.lock.

## Assumptions

- Python 3.11 and 3.12 are the supported CI interpreter versions.
- C-MAPSS is static run-to-failure data and does not support RUL-extension claims.
- No C-MAPSS telemetry feature is treated as a controllable actuator without a verified mapping.
- Configured beta and gamma weights are scaffold settings; current hard masks and actuator bounds
  enforce the corresponding immutability and bound requirements directly.

## Open issues

- The default C-MAPSS taxonomy intentionally contains no verified actuator mapping or coupling rules.
  A domain-reviewed taxonomy and operating envelope are required to demonstrate physical recourse.
- The optional simulator remains an interface only and is disabled by default.

Phase 0 scaffold verification is complete. GNU Make's Windows executable is named mingw32-make in
this environment; its all-checks target passed using Python 3.11.17. The same target also passed in
the primary Python 3.13.9 environment. The fresh Python 3.11 environment installed all groups from
the lock, and the package wheel includes its py.typed marker.

## How to run

Install all pinned dependency groups and run checks:

~~~powershell
uv sync --all-groups --locked
make all-checks
~~~

Run individual workflows:

~~~powershell
make data
make train
make evaluate
make dashboard
make api
~~~

Use make clean to remove generated build, test, coverage, and type-check caches. It does not remove
downloaded datasets or trained artifacts.

## Phase 0 verification

- Ruff: passed.
- Mypy: passed for 47 package source files.
- Pytest: 79 passed with coverage enabled (79% overall coverage).
- CI workflow parsed as YAML and includes Python 3.11 and 3.12.
- Fresh Python 3.11.17 sync from pyproject.toml and uv.lock: passed.
- Wheel build and py.typed marker inclusion: passed.
