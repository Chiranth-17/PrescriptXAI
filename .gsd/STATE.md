---
phase: 7
status: in_progress
---

# Phase 7 execution state

The direct Phase 7 prompt is active. Read AGENTS.md, PROGRESS.md, docs/evaluation_protocol.md,
docs/experimental_framework.md and docs/traceability.md. Phase 6 is closed at tag phase6-closed;
its frozen public schemas remain 2.0.0. Phase 7 is not closed.

Study preregistration: 0c0b6e1; initial asset preparation: 4ffb038. The 28 real model bundles and
112 fitted files are prepared and independently audited. Complete OOF coverage is 100 FD001
engines per model and 260 FD002 engines. Keep original model weights/calibration unchanged.

Before launching real recourse measurements, commit the completed framework and additive protocol
clarifications. The stable all-checks gate passed: Ruff/mypy/docs clean, 276 tests passed in
368.59 s with 83.350720% coverage. Phase 6's 81.017036% coverage is now an enforced floor.

Required execution: assets, diagnostics, quality, reference, serial latency, report. Use the same
run ID for an exact checkpoint resume. Do not run tests/training/quality concurrently with serial
latency. Full required populations are uncapped. Five seeds vary the solver, not predictor fits.
No Phase 7 target has been measured yet. After the full run, audit results, update target/gap
tables and traceability, run the closure gate, commit and tag phase7-closed only if complete.

Proxy controls, bounds/rates and K remain assumptions. Report Tier 1, Tier 2, Tier 3, Tier 4 and
joint success separately; bootstrap whole engines. E3 is the maximum available evidence.
Simulated trajectory health is not evaluated; no RUL-extension claim is supported.

Actual Phase 8–11 prompts and the Part B changes table remain unavailable. Do not invent them.
