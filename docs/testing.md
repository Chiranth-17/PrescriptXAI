# Verification targets

Run these targets from the repository root with the locked environment and the registered inputs. On Windows, use `mingw32-make` in place of `make`.

| Target | Verification |
| --- | --- |
| `make check` | Ruff, mypy, the default pytest suite, the fixed regression subset and both coverage reports. The target is under ten minutes with compatible cached evidence. |
| `make regression-full` | Every one of the 32,116 registered cases, including each of the 24 original groups. |
| `make release-gate` | Sequential check, full regression and strict documentation build. A receipt binds the test and coverage evidence to one committed source. |
| `make all-checks` | Alias for `make check`. |

The default pytest collection deselects the explicit `regression_full` marker. The fixed subset is mandatory. Its manifest pins the selection policy and the ID file. Selection includes every historical diagnostic case, every native borderline case, and up to four cases from each registered stratum ranked by seed 1729.

Both regression tiers use exact keys covering the result-affecting source, genuine inputs, recorded case configuration, numerical runtime and case ID. A warm hit revalidates a saved observation against the fixture and reports it as reused. An unmatched key requires a real solve. Cold runs can take hours, especially when source changes invalidate the full key set. Use `REUSE_ONLY=1` to fail on a miss before starting a solve. Missing or changed required assets fail the gate.

The initial Phase 12 cache seed requires the independently audited clean-clone run and the receipts pinned by `configs/experiments/phase12-test-cache-origin-v1.json`. Import it explicitly with `uv run python -m scripts.diagnostics.regression_tiers --import-run <audited-run-directory>`. Admission compares the origin's recorded runtime and verified source and asset bytes with the current execution context. Additional binary fingerprints are reconstructed from the preserved origin environment. The local cache and its authentication key live under the ignored `artifacts/regression-cache` directory.

For a handled interruption, `make regression-full RESUME=<prior-tier-output>` admits authenticated rows from the preserved execution segment after checking its manifest, miss set and checkpoint. It records any fresh solves separately. An abrupt process loss can leave an unsealed partial. Preserve that evidence for review and use an authenticated segment to resume.

The approved known-differences list is empty. The original numeric envelope remains recorded for historical classification. The tier checks require exact equality or an explicit case and field exception. The run receipts preserve the reused and recomputed counts, the origin counts and any accepted differences.

For a local failure, start with `uv run pytest --lf -x`, fix the cause and run `make check`. Run the complete regression before tagging and follow the replay frequency in AGENTS.md. The verification timings cover testing and evidence validation. They do not certify serial recourse latency.
