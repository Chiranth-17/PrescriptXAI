---
milestone: prescriptxai-v1
version: 0.1.0
updated: 2026-10-03
---

# Roadmap

> **Current Phase:** 3 — Constrained recourse and validation
> **Status:** executing

## Must-Haves

- [ ] Configurable and reproducible data/model/recourse/validation pipeline.
- [ ] Actionable recourse obeys actuator-only, bounds, rate, plausibility, and coupling checks.
- [ ] CLI, optional service, dashboard, evaluation, and technical documentation.
- [ ] Honest measured results and clear static C-MAPSS limitations.

## Phases

### Phase 1: Repository foundation
**Status:** ✅ Complete
**Objective:** Preserve the synopsis, establish package metadata/configuration and project-level usage constraints.
**Plans:**
- [x] Plan 1.1: Package scaffold, configuration, and typed feature taxonomy/schemas

### Phase 2: Data and predictive models
**Status:** 🔄 In Progress
**Depends on:** Phase 1
**Objective:** Implement C-MAPSS ingestion, preprocessing, engine splits, model training, calibration, and registry.
**Plans:**
- [x] Plan 2.1: C-MAPSS ingestion and leakage-safe preprocessing
- [x] Plan 2.2: Predictive model and calibration

### Phase 3: Constrained recourse and validation
**Status:** 🔄 In Progress
**Depends on:** Phase 2
**Objective:** Implement optimizer, sparsification, baselines, and four independent validation tiers.

### Phase 4: Product surfaces and evaluation
**Status:** ⬜ Not Started
**Depends on:** Phase 3
**Objective:** Implement CLI, optional FastAPI, Streamlit dashboard, metrics, ablations, latency, and reports.

### Phase 5: End-to-end verification and documentation
**Status:** ⬜ Not Started
**Depends on:** Phase 4
**Objective:** Complete integration/e2e/regression coverage, run honest experiments, and document outcomes and limitations.

## Progress Summary

| Phase | Status | Plans | Complete |
|---|---|---:|---:|
| 1 | ✅ | 1/1 | Complete |
| 2 | ✅ | 2/2 | Complete |
| 3 | 🔄 | 0/2 | — |
| 4 | ⬜ | 0/2 | — |
| 5 | ⬜ | 0/1 | — |
