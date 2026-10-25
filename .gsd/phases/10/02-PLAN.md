---
phase: 10
plan: 2
depends_on: [10.1]
autonomous: true
---

# One-command reproducibility

1. Implement reproduce orchestration using existing prepare/train/calibrate/coupling/validator/
   evaluation/report functions, fixed committed config and engine provenance; write complete
   source/config/input/artifact/runtime/stage manifest and refuse output replacement.
2. Exercise actual temporary raw fixture end-to-end, then real configured C-MAPSS reproduction.
   Preserve all historical measurements/settings/populations; label reused-engine reproduction.
3. Verify README-only five-command workflow in clean environment, exact reproducible demo
   cases (RECOVERABLE, PARTIAL/ESCALATE, failure), real timings/hardware and exported evidence.

Done: installed reproduce command creates usable API/dashboard/report artifacts with real proof.
