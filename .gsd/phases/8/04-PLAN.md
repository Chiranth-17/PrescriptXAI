---
phase: 8
plan: 4
wave: 4
depends_on: [8.3]
files_modified: [docs/phase8_walkthrough.md, docs/screenshots/, PROGRESS.md, docs/traceability.md, .gsd/STATE.md, .gsd/JOURNAL.md]
autonomous: true
must_haves:
  truths: [Actual dashboard starts from project command, Real high-risk and failure walkthrough works, Full phase gate passes without coverage decrease]
  artifacts: [Real walkthrough/screenshots, Independent audits, Conventional closure commit and phase8-closed tag]
---

# Plan 8.4: Real walkthrough and full gate

## Task 1 — Actual UI walkthrough

Files: docs/phase8_walkthrough.md, docs/screenshots/.
Action: launch project dashboard hidden helper, inspect browser using supported computer-use
APIs, exercise actual measured high-risk RECOVERABLE/PARTIAL/ESCALATE/failure engine/cycles,
manual slider validation, waterfall/tiers/exports, every page. Save real screenshots and exact
commands/data/config/engine/cycle timings. Optional Playwright if already available/installable;
never substitute mocks, generated images or AppTest-only claims for live walkthrough.
Verify: screenshots inspected, no raw stacktrace, all required widgets and honest labels visible.
Done: real walkthrough covers both validated action and rejected diagnostic/failure paths.

## Task 2 — Independent audits and closure

Files: PROGRESS.md, docs/traceability.md, .gsd/STATE.md, .gsd/JOURNAL.md, walkthrough doc.
Action: independent read-only audits (no implementation delegation); fix actual root causes
under user's two-fix/blocker rules. Run Ruff, strict mypy and all pytest with coverage >=
Phase7 83.3507197997079% branch-inclusive, docs/lock checks. Record UI render scope/budget
honestly and any measured miss. Update done/decisions/assumptions/issues/run instructions,
commit conventionally and tag phase8-closed only full gate. Then immediately execute Phase9.
Verify: complete11-task traceability, zero failures and no schema changes; source/tag evidence.
Done: Phase8 is closed, and authorized Phase9 work starts without another confirmation.
