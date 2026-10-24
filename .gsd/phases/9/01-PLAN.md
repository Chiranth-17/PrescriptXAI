---
phase: 9
plan: 1
wave: 1
autonomous: true
---

# Adversarial boundaries and numerical correctness

1. Reproduce corrupt/missing/malformed model, calibrator, covariance, coupling and configuration
   faults; log each defect before/with its root-cause fix. Centralize trusted local artifact
   deserialization and typed failures; preserve historical artifacts and frozen result schemas.
2. Add Hypothesis properties and all requested science regressions. Cover finite extreme inputs,
   named order/dtypes, batch limits, Unicode and concurrency; reject invalid probability/label
   coercions and align NumPy/tensor calibration without tuning any scientific threshold.
3. Verify focused tests plus Ruff/mypy. A test must expose real library behavior; no skipped,
   fabricated or monkeypatched successful recommendations. Commit fixes conventionally.

Done: trust/input/science boundaries have executable negative/property regressions and defects
are fixed or honestly documented with impact. Full phase gate remains separate.
