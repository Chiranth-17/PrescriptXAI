# Phase 10 — packaging and reproducibility

Status: implementation and real-run verification in progress; full closure gate pending.
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

## Container and release gate

The multistage image built successfully after fixing a base-image group-name collision.
Both API and dashboard containers reached healthy status with fitted artifacts mounted read-only.
Final image/source, non-root/HTTP/demo verification and complete test/coverage/docs results will
be recorded here before closure. No Phase 10 closure tag exists at this checkpoint.

## How to run and remaining work

Use the README five commands from an empty operator workspace; see
[reproduction and Docker](reproducibility.md). Remaining gate work: final clean distribution
smoke, live demo/screenshots, strict docs build, all tests/coverage, Ruff/mypy, independent
review, progress/traceability update and conventional closure commit/tag. No Phase 11 prompt
or Part B table has been supplied.
