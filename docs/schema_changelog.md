# Public schema history

## Phase 17 machine limits status

The version 1 machine spec accepts an optional `limits_status`. A confirmed
spec requires a complete engineer confirmation record. A demonstration
spec rejects such a record and labels its decisions through the existing
warnings field. A spec with no status remains Alerts-only and retains its
historical hash. The version 3 decision and version 2 validation schemas
retain their fields.

## Phase 17 replay follow-up context

The local SQLite log can now associate an optional version 1 replay context
record with an existing feedback row. The context stores the input hash,
recorded unit and time, model configuration, reported choice and optional
reason, and demo seed when applicable. Existing feedback records, their API
response schema, and decision and validation schemas retain their versions.
A database with only the original feedback table remains readable.


## 3.0.0 — Phase 13 named-machine decisions

The machine-prefixed HTTP routes and machine-aware CLI use version 3. The
serialized decision retains the version 2 numerical fields and adds
`machine_id`, `spec_hash`, `protocol_version` and `synthetic`.
The independent ValidationReport remains at version 2.

Use `migrate_recourse_result` for a previously saved v2 row. The migration
defaults its machine to `cmapss_fd001` as the legacy compatibility mapping
and leaves the unrecorded spec hash and protocol null. It preserves the
saved decision and verifies its serialized verdicts. The existing
unprefixed routes still return v2. The SQLite feedback payload starts at
version 1 and records the named machine, exact spec, protocol and result run.

## 2.0.0 — Phase 6

One public RecourseResult is shared by library PrescriptXAI, CLI and HTTP responses. It adds
status/triage, explicit mode, separate true/surrogate probabilities, complete raw/scaled deltas
with action/dependent roles, escalation diagnostics, proxy assumptions, timings and provenance.
ValidationReport retains independent Tier 1/Tier 2/Tiers 3–4/joint and explicit skipped dynamics.
Read-only outcome/tiers aliases retain those views for readers without a separate computation.
This major version changes the service contract; clients using other legacy fields need migration.
The existing PrescriptXAIEngine runtime remains available for earlier internal dashboard and
evaluation callers; new callers use PrescriptXAI.from_config/from_artifacts.

At Phase 6 closure, JSON-schema snapshots are frozen. After closure both schemas require a
version bump, this changelog update and agreement from library, CLI, API and dashboard owners.
No retrospective owner approval is inferred for future changes. Historical Phase 5 saved reports
remain schema1.1.0 and are preserved as evidence, not relabeled as new contract outputs.

## 1.1.0 — Phase 5

Independent tier verdicts, status, margins, evidence and assumptions. Legacy precision-only
covariance artifacts need refitting; result schema migration does not refit a model.


### Service migration from 1.1 to 2.0

| Legacy field | Public 2.0 representation |
|---|---|
| solver_success / optimizer_message | status and triage; structured failure and explain_result |
| stage_timings_ms | timings with named ingestion/inference/optimization/validation/pipeline fields |
| objective_value / objective_terms / counterfactual_signs / solver_calls | Internal search diagnostics remain on PrescriptXAIEngine results; public solver_settings contains effective runtime settings |
| outcome.recourse_feasible | Sparse actuator feasibility (action_feasible), independent of true-model validity |

Historical 1.1 reports remain unchanged. The legacy internal engine supports existing dashboard
and evaluation callers; new HTTP consumers adopt the 2.0 schema and independent verdict fields.
