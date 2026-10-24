---
phase: 9
plan: 2
wave: 2
depends_on: [9.1]
autonomous: true
---

# Golden, restart, end-to-end and coverage evidence

1. Create fixed-seed genuinely fitted fixture goldens with documented tolerances, excluding only
   run identity/timing/path-specific provenance. An explicit --update-golden flag is required to
   write expected files. Verify repeated runs, process restarts and float32/float64 inputs.
2. Add raw fixture -> train -> calibrate -> fit validators -> recommend -> validate -> HTTP ->
   actual dashboard AppTest in one temporary directory. Exercise meaningful uncovered branches
   across CLI, persistence, configuration, calibration, preprocessing and validators.
3. Enforce >=90% source line coverage excluding only explicitly listed rendering internals that
   AppTest executes; retain full-package line and branch ratchets alongside that scoped measure.
   Record excluded files and full/scoped denominators; do not hide failed queries or branches.

Done: goldens/process equality/full temp E2E pass and coverage gate is measured, not inferred.
