# Public schema history

## 2.0.0 — Phase 6

One public RecourseResult is shared by library PrescriptXAI, CLI and HTTP responses. It adds
status/triage, explicit mode, separate true/surrogate probabilities, complete raw/scaled deltas
with action/dependent roles, escalation diagnostics, proxy assumptions, timings and provenance.
ValidationReport retains independent Tier 1/Tier 2/Tiers 3–4/joint and explicit skipped dynamics.
Read-only outcome/tiers aliases preserve existing API clients without a separate computation.
The existing PrescriptXAIEngine runtime remains available for earlier internal dashboard and
evaluation callers; new callers use PrescriptXAI.from_config/from_artifacts.

At Phase 6 closure, JSON-schema snapshots are frozen. After closure both schemas require a
version bump, this changelog update and agreement from library, CLI, API and dashboard owners.
No retrospective owner approval is inferred for future changes. Historical Phase 5 saved reports
remain schema1.1.0 and are preserved as evidence, not relabeled as new contract outputs.

## 1.1.0 — Phase 5

Independent tier verdicts, status, margins, evidence and assumptions. Legacy precision-only
covariance artifacts need refitting; result schema migration does not refit a model.
