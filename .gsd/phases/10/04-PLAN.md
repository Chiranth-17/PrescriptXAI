---
phase: 10
plan: 4
depends_on: [10.1, 10.2, 10.3]
autonomous: true
---

# Independent audits and final release gate

1. Read-only audits of clean install/reproduction/docs/scientific tables and actual demo outputs;
   root fixes findings. Verify Docker health/non-root, source-free clean environment and docs.
2. Full Ruff/mypy/pytest coverage with Phase9 ratchets, dependency/secret security checks,
   progress/traceability/final instructions. Conventional commit/tagphase10-closed only fullpass.
3. Delete the existing heartbeat only after verified Phase10 closure; no Phase11 invention.

Done: user can install/reproduce/demo from README; all checks green and final artifacts reviewable.
