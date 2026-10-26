# Reproduction and deployment

The README five-command workflow starts in an empty operator directory, installs the source
distribution, creates three packaged YAML configurations, downloads the registered NASA ZIP,
then runs preparation, predictor fitting/calibration, validators, evaluation and reporting.
Use a trusted checkout/distribution. Joblib files are trusted executable artifacts, not a safe
interchange format. Keep the generated `artifacts/` tree in the operator workspace.

## Registered profile and scope

`configs/experiments/phase10-reproduce-v1.yaml` was committed at
`10d546474e7b211155d2fe190c671cab6ff8d3df` before the real reproduction. It retains the
scientific settings of the FD001 XGBoost baseline, with portable output paths and an explicitly
registered sample of at most 20 alerts. This short workflow demonstrates reproducibility; it
does not replace the complete [Phase 7 results](results.md).

The run uses seed 1729, THOROUGH search, protocol v1, k_max=3, assumed K=1 and D_max=5.
Training/calibration/internal-test partitions contain 69/16/15 engines under the existing
nonempty-first split allocation. The nominal fractions .70/.15/.15 are not exact engine counts.
The calibrator uses validation engines; scaler, predictor, covariance and coupling fitting
use training engines. Evaluation uses the internal held-out engines only. These public engines
have been used before; the run is not fresh generalization evidence.

Run `reproduce-20261025T062618591382Z` completed all five stages in **616.7122392 seconds**
on the Windows host recorded in its manifest. Preparation took 20.2733 s, training/calibration
29.1798 s, fitting validators 0.5052 s, evaluation 566.4814 s and reporting 0.0737 s.
Allow roughly 10–20 minutes on comparable hardware, plus installation/download time; this is an
operational estimate, not a latency budget measurement. Actual hardware and dependency versions
are retained in `artifacts/reproduction/manifest.json`.

It retained 20/20 queries from 378 alerts, with 0 interval pre-screen exclusions and 11 sampled
engines. Validity was 12/20, Tier 2 was 12/20 over both all and returned candidates, and joint
success was 10/20. The canonical whole-engine intervals and all eight metrics are saved in
`measured_metrics.json`; the dashboard presents these separate denominators and intervals.
The upper evidence limit is E3 under documented proxy assumptions. Model risk reduction alone
does not show physical efficacy.

## Manifest and interruption behavior

`manifest.json` records source commit, exact packaged source hashes, effective configuration,
config/taxonomy/archive hashes, installed dependencies, hardware, stage status, timings and
output hashes. `selected_queries.csv` is saved before solving; each completed record is flushed
to `query_results.jsonl`. A failed stage leaves its manifest and completed records intact.
The command refuses to overwrite an existing output directory, including a failed run. To make
a separate deliberate reproduction, initialize a new operator directory. There is no automatic
resume or replacement of failed queries in this command.

Source identity comes from the distribution build, independent of the operator's working
directory. The verified Windows distribution has CRLF in some packaged files: runtime profile
SHA256 `b7089ac81d50010792662b6632c587353f0b442735c6479b3e80af8e010f8b8e`
differs from the committed Git blob only by 169 CRLF line endings. Parsed YAML and LF-normalized
bytes match. Both source hashes and original bytes are retained; no claim of literal Git-blob
byte identity is made. Rebuilding a modified source archive marks its source identity dirty.

## Docker

From the checkout, with an already initialized/reproduced operator workspace:

```powershell
uv sync --all-groups --locked
uv run python -m build
$env:PRESCRIPTXAI_WORKSPACE = 'C:/absolute/path/to/operator-workspace'
docker compose build
docker compose up -d
docker compose ps
```

The multistage image installs the built wheel, retaining its source metadata. Linux uses the
official CPU Torch wheel. Runtime UID/GID is 10001, and telemetry/config/artifacts are mounted
read-only. API and dashboard bind host loopback ports 8000 and 8501. Healthchecks probe their
actual HTTP health endpoints. Open `http://localhost:8501` for the dashboard and
`http://localhost:8000/docs` for the API. Use `docker compose down` to stop these services;
the operator workspace remains on the host. Docker verification results are recorded in
[the Phase 10 report](phase10_changes.md).

## Development and publication

```powershell
uv sync --all-groups --locked
mingw32-make all-checks
uv run mkdocs build --strict
uv run python -m build
```

On Unix, use `make`. The docs command builds Material pages and Python API references from
docstrings into ignored `site/`. The raw historical study is intentionally not distributed.
To regenerate the committed derived publication tables and figures from preserved evidence:

```powershell
uv run python scripts/docs_results.py artifacts/experiments/phase7-20261020T102540Z/summary.json
```

This only renders saved measurements. It never runs an experiment or substitutes target values.
See [the evaluation protocol](evaluation_protocol.md) before any new scientific study. No
hosted package, hosted CI success, DOI, public repository URL or deployment certification is
claimed. MIT covers this project's code; datasets and dependencies retain their own terms.
