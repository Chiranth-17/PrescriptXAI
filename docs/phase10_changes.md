# Phase 10 — packaging and reproducibility

Status: complete software, clean-install, reproduction, documentation and live-demo gates.
Release 0.2.0, 2026-10-27; the closure commit is identified by `phase10-closed`.
Phases 7, 8 and 9 remain closed. Their measured artifacts and public schema 2.0.0 are unchanged.

## Delivered implementation

Package 0.2.0 declares runtime dependencies and service extras, includes portable YAML resources,
and builds source distributions and wheels with embedded source identity. MIT was selected after
the user delegated the license choice. CITATION.cff supplies an organization author without
inventing a DOI or public repository. CLI `init`, `reproduce` and `dashboard` work outside the
checkout. The reproduction uses existing fitting, calibration, validation and search functions.

The manifest retains actual configuration, source hashes, dependency versions, hardware,
engine partitions, output hashes and stage timings. Selected queries and each completed record
are saved durably. Existing output directories cannot be overwritten. Historical experiments
are not rerun by the quickstart.

## Actual installed reproduction and independent audit

Run `reproduce-20261025T062618591382Z`, source
`10d546474e7b211155d2fe190c671cab6ff8d3df`, committed profile
`configs/experiments/phase10-reproduce-v1.yaml`, runtime profile SHA256
`b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e`.
Protocol v1, THOROUGH, k_max=3, assumed K=1, D_max v1=5; reused internal held-out FD001 engines.
All five stages completed in 616.7122392 s, with 69/16/15 fitting/calibration/test engines.
There were 378 eligible alerts, 0 interval pre-screen exclusions, 20 sampled/completed queries
and 11 sampled engines. No failed query was replaced or omitted.

| Metric | Numerator / denominator | Estimate [95% engine-bootstrap CI] | Engines |
|---|---:|---:|---:|
| True model validity | 12/20 | 0.6000 [0.4500, 0.7778] | 11 |
| Tier 2 / all queries | 12/20 | 0.6000 [0.4286, 0.7647] | 11 |
| Tier 2 / returned candidates | 12/20 | 0.6000 [0.4286, 0.7647] | 11 |
| Tier 3 | 20/20 | 1.0000 [1.0000, 1.0000] | 11 |
| Tier 4 | 20/20 | 1.0000 [1.0000, 1.0000] | 11 |
| Joint Tiers 1–4 | 10/20 | 0.5000 [0.3333, 0.6875] | 11 |

Intervals resample whole engines, 2000 draws, seed 1729. The maximum available evidence is E3
under documented proxy assumptions. Validity alone does not demonstrate real-machine safety.
Canonical JSON also contains mean risk drop and successful-query sparsity with intervals.

An independent read-only audit reproduced seeded selection exactly and checked all 20 records,
18 output hashes, 6 report fingerprints, 68 packaged source hashes and 9 fitting-partition
checks. True calibrated risk error was 0; independently solved Mahalanobis error was at most
8.88e-16; bootstrap discrepancy was at most 1.11e-16. No tier mismatches or frozen/bound/rate
violations were found. Runtime/config bytes differ from Git blobs only by disclosed CRLF
normalization; see [reproduction details](reproducibility.md).

The second empty operator workspace followed all five README commands using Python `venv`
and `pip`, without development tooling or source-relative runtime imports. Run
`reproduce-20261026T042558162985Z`, clean source
`8aa18cb086999b885aa95a5af2dcb26315aa0acb`, completed all five stages in **479.8035529 s**.
It retains the same config hash, protocol, 69/16/15 split, 378 alerts, 20 queries and 11 engines.
Independent audit checked its 18 output hashes and 6 report fingerprints. Its selected CSV,
all scientific record fields (including 1,163 numeric fields), and all eight metrics/CIs match
the original Windows run exactly. All eight model-validity failures remain. Timings differ
and both are retained: these are operational workflow durations, not controlled latency
comparisons; Docker/browser verification overlapped the second workflow.

The two additional canonical metrics are mean risk drop **0.5779404120
[0.4929797414, 0.6735802017]** over 20 queries and successful-query mean sparsity **2.9
[2.6666666667, 3.0]** over 10 successes. Both bootstrap all **11 sampled engines**; no
replicate has a zero denominator, and all 2,000 replicates are retained.

## Container and release gate

The multistage image built successfully after fixing a base-image group-name collision.
Both API and dashboard containers reached healthy status with fitted artifacts mounted read-only.
Verified image `ff8d45fa9abc58c6a27bf3da6d5d985ec8d6d6dadd7c331058abc3f1edd50323`
contains the wheel built from clean source `8aa18cb`. Both services run as UID/GID **10001**;
all three workspace mounts are read-only, and host ports bind loopback. API health, version,
configuration and Streamlit health each returned HTTP 200. Real state assessment and exported
candidate validation returned 200; a malformed boolean measurement returned 422. The actual
candidate's revalidated risk matched the export. Only this project's two containers were
stopped after verification; other projects and host artifacts were left intact.

The checked source distribution builds a wheel with **75 entries / 68 source hashes**, portable
YAML, CLI/dashboard entrypoints, typing marker and MIT license; no fitted data is bundled.
Wheel SHA256 at the tested runtime checkpoint:
`51d6b932ba8fa4d1852c81a429c2464320557e43e93644b24e07fe9360e0b0be`;
sdist SHA256 `af06db054be445f84e2c5b92614604940035e635352061eec2e3220e76d3d97e`.
These identify the tested checkpoint, not byte-identical archives from later documentation
commits. A separate negative audit rebuilt an extracted archive after a harmless source edit:
all six checks passed, the changed source became dirty, parent identity was retained, and only
the edited file's hash changed. The original archive and runtime artifacts were not modified.

### Actual browser walkthrough

Both the Linux container and fresh Windows README installation were operated through the real
browser, including engine/cycle/mode selection, solving, independent tier display and JSON
download. Windows used the newly fitted source `8aa18cb`; Docker used the preserved source
`10d5464` fitted artifacts with runtime `8aa18cb`. Config file SHA above stays unchanged;
service identity hashes differ by platform/path representation: Windows
`f5f591525e1de8b8df2b429518d3d09856d7f6381bbc498947fdb5982a57377c`, Linux
`54ce4cb8f7c7db6ce30e9be1b8179c87fc79ee917ffdb380fbb247edb9eccc3d`.

| Platform / individual state | Mode | Risk before → after | Triage / cumulative evidence |
|---|---|---|---|
| Windows, engine 5 / cycle 241 | THOROUGH | 0.8833731521 → 0.1284214696 | RECOVERABLE / E3 |
| Linux Docker, engine 5 / cycle 241 | THOROUGH | 0.8833731521 → 0.1083572930 | RECOVERABLE / E3 |
| Windows, engine 2 / cycle 278 | THOROUGH | 0.9970382956 → 0.3612983062 | ESCALATE / none |
| Linux Docker, engine 2 / cycle 278 | THOROUGH | 0.9970382956 → 0.3612983062 | ESCALATE / none |

Every row uses protocol v1, k_max=3, assumed K=1, D_max v1=5 and an internal held-out FD001
train-file state. These individual examples have no population CI. The two successful search
candidates differ across platforms; no action identity or physical safety is claimed.
Independent Linux export audit reproduced true risks exactly and D_M **4.3108395311** within
1.78e-15, with all four tiers passing, three controls, zero immutable violations and all
22 raw/scaled delta fields exact. Surrogate disagreement **0.2381609002** is visibly warned;
the true model controls validity. Windows also discloses its surrogate disagreement.
The rejected case retains failed model-safety and Tier 2 checks and is diagnostic only.
The fresh Windows RECOVERABLE and ESCALATE exports and Linux ESCALATE export were also
independently re-scored: true-risk errors **0**, maximum D_M error **8.88e-16**, and all
**132 raw/scaled/percentage delta values** match exactly, with zero immutable changes.
Their observed states match raw NASA telemetry; model/schema identities, action/dependent
roles, triage and evidence levels agree. The escalation candidate's D_M is **5.2541200871**,
above the frozen limit 5; both failed model safety and failed plausibility remain visible.

The invalid CLI example engine 5 / cycle 999999 returns a readable observation error and
**exit 2**, without a recommendation or traceback, in both installed environments.
Docker's Evaluation Results and Model and Validation Diagnostics pages show the actual
complete manifest, eight metrics, engine CIs, predictor/coupling diagnostics, and explicit
absence of a new ladder/K/serial-latency study. Real captures are linked from the
[five-minute demo](demo_script.md); no backup video is claimed.

### Full software and documentation verification

Runtime source `8aa18cb` passes **524 tests**, with 66 warnings from deliberately short
test-only nonlinear fits, in **353.04 s**. Ruff is clean; strict mypy checks **65 source files**.
Focused package/reproduction/AppTest verification separately passes 11 tests in 22.69 s.

| Coverage | Phase 9 floor | Phase 10 measured | Gate |
|---|---:|---:|---|
| Scoped line | 90% | 7622/8390 = 90.84624553039332% | PASS |
| Full package line | 89.56184002912975% | 7622/8483 = 89.85028881291996% | PASS |
| Full line + branch | 86.07837763770897% | 9704/11233 = 86.38832012819371% | PASS |

Only the AppTest-covered dashboard entrypoint is excluded from the scoped line gate;
the full-package figures include it. No floor was lowered. All changes after this test run
are documentation, screenshots and closure records; the measured source and tests are unchanged.
Strict MkDocs builds the Material site, LaTeX mathematics and docstring API reference.
The dependency audit finds **0 known vulnerabilities in 132 third-party distributions**;
the local project is explicitly outside the PyPI audit. The final checkpoint credential scan
finds **0 matches in 366 files** for its documented high-confidence patterns; this is not a
proof that every possible secret pattern is absent. Phase 9's separate history scan is preserved.

Independent documentation audit matches **24 population rows / 144 metric and CI cells**,
their engine counts and config/source labels, plus the six compact README/paper rows. The
figures are generated from saved Phase 7 evidence. All seven prompt tasks are mapped in
[traceability](traceability.md); 21 defense answers include the two synopsis questions and
19 additions. The paper skeleton marks literature citations TODO-VERIFY. SDG 9.1/9.4 remain
conditional motivations, without invented field outcomes.

## How to run, evidence locations and remaining limitations

Use the README five commands from an empty operator workspace; see
[reproduction and Docker](reproducibility.md). The verified fresh workspace is
`C:/Users/chira/prescriptxai-phase10-readme`; its dashboard was left available at
`http://127.0.0.1:8501` after the walkthrough. Generated data and fitted files remain outside Git.
The original independent workspace is `C:/Users/chira/prescriptxai-phase10-clean/demo`.

Ignored proof files under `artifacts/phase10/` include `full-gate-first.log`,
`coverage-8aa18cb.json`, `coverage-gate-first.json`, `readme-install.log`,
`readme-reproduce.log`, `readme-dashboard.log`, `readme-invalid.log/.exit`,
`readme-recoverable.json`, `readme-escalate.json`, `docker-http-functional.json`,
`docker-recoverable.json`, `docker-escalate.json`, `docker-build-8aa18cb.log`,
`dependency-audit.json`, `secret-scan-final.log` and distribution/audit directories.
Both external workspaces retain their full reproduction manifests, records and timing segments.

Historical validity, plausibility and optimization latency target misses remain diagnosed in
the Phase 7 report; packaging does not erase them. Learned coupling/surrogate limitations,
reused engines, proxy bounds/rates/K and the E3 ceiling remain explicit. There is no validated
physics simulator, physical-safety or RUL-extension claim, package upload, hosted-CI success,
DOI or deployment certification. No Phase 11 prompt or Part B table was supplied or invented.
