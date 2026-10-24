---
phase: 8
plan: 4
completed_at: 2026-10-24
---

# Real walkthrough and gate

Project dashboard command and a final cold process were verified in the actual browser.
Real RECOVERABLE, PARTIAL and safe-model/manual rejection exports match independent library
reconstruction with zero discrepancies; nine actual captures are saved under docs/screenshots/.
Full commands, limits and identities are in docs/phase8_walkthrough.md.

UI timing preregistration215cb1f preceded32serialcallbacks/8engines on source52affd0. Zero
discarded samples/operator failures; p95=115.3545ms,whole-engine95%CI[108.80,120.46]ms,
8engines/2000replicates,upper250msbudget passes in the explicit server UI build scope.
One browser wait timeout recovered the same completed callback without rerunning it.

Fullgate321pass/70warnings/184.09s,Ruffclean,mypy61clean,docs/lockpass,coverage
83.66412213740458%branchinclusive/87.32997481108312%line; both exceed Phase7 floors.
An intermediate line decrease was fixed with real cache/artifact regression coverage, not a
lower threshold. Historical Phase7 records and public2.0.0schemas remain untouched.
Conventional closure commit/tag follows audit and documentation completion; immediately Phase9.
