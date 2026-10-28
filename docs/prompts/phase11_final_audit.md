# Phase 11 — final independent audit

Source: the user's direct prompt received 2026-10-27 IST, after verified Phase 10 closure.
No new features: verify and fix gaps. Independent reviewers must not have written the code
being audited. Read AGENTS.md, PROGRESS.md and docs/synopsis.pdf.

1. Map EVERY synopsis requirement to implementing files, tests, result/screenshot evidence,
   and Done / Partial / Not met with honest notes: research question, optimization terms,
   Tiers1–4/optional, pipeline stages, latency rows, five metrics, taxonomy rows, roadmap,
   SDG9 targets and both defense answers. Not met with evidence is acceptable; Blocked is not.
2. Run the full project check command, reproduce, API smoke, dashboard smoke and Docker build
   when available. Paste actual output into docs/final_verification.md.
3. Search source/docs/README/dashboard/reports for illustrative numbers88%,17%,3.2%,1.1%,
   targets95%,90%,0.60 and latency figures; audit RUL-extension and unsupported claims.
   Fix or label each. Show each design target with measured value, CI and gap.
4. Check Git preregistration before final evaluation; no post-diagnosis changes to tau_safe,
   tau_danger,D_max,bounds/rates; development-only tuning and once-on-test evaluation;
   committed config path and git hash for every reported number.
5. Separate validity,Tier2 both denominators,Tier3,Tier4,joint. Retain failed queries and
   apply upper-budget latency verdicts.
6. Confirm no unfinished placeholder,TODO,stub,pass-only function or NotImplementedError in
   src except documented simulator interface; TODO-VERIFY citations allowed in paper skeleton.
7. Re-run final evaluation on a second seed and compare against documented tolerance;
   confirm leakage safeguards, determinism and artifact versioning.
8. Final PROGRESS: completed work, each target/value/gap, limitations,evidence level and
   prioritized future simulator integration,N-CMAPSS,first-principles coupling,richer actuators.

Deliver a short final report listing every Partial or Not met item and reason. No Done without
evidence. The complete original user message is retained in the conversation.
