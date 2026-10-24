# Phase 10 — packaging, documentation, reproducibility and demo readiness

Source: the user's direct prompt, received 2026-10-24 IST. Execute after verified closure
of Phase 7, then Phase 8, then Phase 9. These are queued requirements, not completed work.
Keep historical measurements and their source/config provenance intact.

PHASE 10: packaging, documentation, reproducibility and demo readiness. Read AGENTS.md and PROGRESS.md; inspect the repo.

1. PACKAGING: build sdist and wheel, install into a clean venv, run the CLI and a library import smoke test; semantic versioning; CHANGELOG.md; LICENSE (ask which license; default MIT if no answer); CITATION.cff.
2. DOCKER: multi-stage Dockerfile with a non-root user and docker-compose.yml for the API and dashboard; healthchecks; artifact and data volumes; verify build and run if Docker is available, otherwise document as unverified.
3. REPRODUCIBILITY: one command ("reproduce") that runs data prepare -> train -> calibrate -> fit validators -> evaluate -> report with fixed seeds, writing a manifest; document expected runtime and hardware.
4. DOCS:
   - README: what it is and why (predictive versus diagnostic versus unconstrained recourse versus prescriptive, per synopsis Section 2), quickstart in 5 commands, Mermaid architecture diagram, screenshots, results table pulled from real runs, limitations, citation.
   - architecture.md: modules, data flow, extension points (new predictor, constraints, simulator or emulator).
   - math.md: full optimization formulation, L1 handling (variable splitting or smooth approximation), Mahalanobis, D_max methods, coupling model, calibration, metric definitions, in LaTeX.
   - limitations.md: C-MAPSS is static; sensor channels are proxies for actuators; no RUL extension; surrogate fidelity limits; coupling is learned, not first-principles; plausibility is not physical proof; validity is model-based.
   - assumptions.md and evidence_levels.md kept current.
   - defense_qa.md: the synopsis Q&A plus at least 15 more likely examiner questions with answers grounded in this repo's real results, including: why L1 and not L0; why Mahalanobis; why calibration; how immutable features were chosen; what if the surrogate is wrong; why not RL; deployment path; novelty versus DiCE and other recourse libraries; SDG 9 linkage; "why not 95% validity?" answered with the funnel, constraint ladder, oracle split and triage; "is plausibility 90% just a constraint you imposed?" answered with both denominators and the trade-off table; "what evidence level did you reach?".
   - API reference generated from docstrings (mkdocs-material or sphinx), buildable with the docs command.
5. SDG 9 section tying to Targets 9.1 and 9.4 without exaggeration; every quantitative claim traceable to a measured result or labeled as an assumption.
6. DEMO ASSETS: docs/demo_script.md for a 5-minute live demo with the exact engine ids and cycles that give an interesting high-risk RECOVERABLE case, a PARTIAL or ESCALATE case and a failure case; backup recording instructions; a slide outline mapping to the synopsis sections (problem, gap, math, architecture, case study with REAL numbers, evaluation with the design target / measured / gap table, limitations, SDG 9); figures into docs/figures/.
7. PAPER SKELETON in paper/: IEEE-style abstract, introduction, related work (every citation marked TODO-VERIFY; never invent references), method, experiments (tables auto-filled from results), limitations, conclusion.

GATE: a clean-environment install and the demo work from the README alone; docs build; all checks green; PROGRESS.md updated with final run instructions.

Inherited phase closure: run the complete gate, preserve coverage, update traceability and
progress, commit conventionally, tag `phase10-closed` only after the gate passes, and send a
short status with real numbers and open issues. The authorized follow-up stops after Phase 10
closes, or on the user's explicit stop request. No Phase 11 prompt has been supplied.
