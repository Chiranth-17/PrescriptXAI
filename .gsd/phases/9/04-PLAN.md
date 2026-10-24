---
phase: 9
plan: 4
wave: 4
depends_on: [9.1, 9.2, 9.3]
autonomous: true
---

# Security, CI and full closure

1. Run pip-audit on the installed/locked distribution, inspect secret exposure and artifact/input
   boundaries. Fix verified defects; any remaining issue has an honest impact statement. Never
   deserialize operator-uploaded pickle; document and restrict retained legacy trusted artifacts.
2. CI runs lint, strict mypy, tests and explicit coverage thresholds, uploads coverage, and has a
   nightly slow/e2e/gpu marker job. CPU hosts run all applicable cases; GPU-specific absence is
   disclosed rather than counted as a fabricated pass.
3. Independent audits only after primary implementation; fix findings, full zero-failure gate,
   complete defects/limitations/traceability/PROGRESS, conventional commit and phase9-closed.
   Immediately start the complete authorized Phase10 prompt without confirmation.

Done: all11 requested task areas have evidence, >=90% line gate passes, no known critical defect,
all Ruff/mypy/tests/coverage checks pass, and only then is the phase tagged closed.
