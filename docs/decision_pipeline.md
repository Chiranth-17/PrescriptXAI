# Decision support API (schema 2.0.0)

```python
from prescriptxai import PrescriptXAI

pipeline = PrescriptXAI.from_config("configs/experiments/phase6-pipeline-v1.yaml")
assessment = pipeline.assess(raw_state)
result = pipeline.recommend(raw_state, mode="fast")
explanation = pipeline.explain_result(result)
results = pipeline.recommend_batch(raw_dataframe, mode="thorough", workers=1)
```

`from_artifacts(directory)` reads `directory/pipeline.yaml`; a YAML file is also accepted.
Artifact paths are explicit configuration entries. Snapshot vectors follow the saved feature order;
dicts and pandas Series use names. Recommendations require all declared raw telemetry/context fields,
including channels excluded from prediction. Supply observed omitted fields with `InputContext.telemetry`.
Units, if supplied, must match `info()["units"]`. NaN, infinity, booleans, missing/extra columns,
conflicting context and wrong shapes produce typed `InputError` subclasses. Model-loading failures
produce `ArtifactError`. Missing LSTM history is an error: provide exactly window-1 observed raw rows
in saved feature order. Only the latest timestep changes. Window one requires no earlier history.

Risk below tau_danger yields zero action and `NO_INTERVENTION`, triage=null. This can still exceed
tau_safe. RECOVERABLE requires Tiers 1-4 and feasible sparse action; PARTIAL requires Tiers 2-4,
feasible sparse action and at least configured delta_min risk reduction while above tau_safe.
ESCALATE includes the closest diagnostic state, failed checks and maintenance escalation text.
Diagnostic candidates must not be treated as accepted actions.

Model validity, Tier 2 plausibility and Tiers 3-4 constraints remain separate. Evidence reaches E3
at most with current artifacts. Proxy limits and intervention horizon K are documented assumptions;
C-MAPSS does not establish causal efficacy or RUL extension. The simulator is skipped.

FAST uses the existing certified support-ordered grid; THOROUGH evaluates its full grid. Both retain
the frozen solver settings and true calibrated final scoring. The measured benchmark determines
budget pass/fail; a mode name does not certify its latency. Timings are milliseconds, unpadded.
Public totals include request normalization and lock wait; benchmark totals surround the full call.
UI rendering and cold startup are unmeasured. See `phase6_changes.md` for real results.

## CLI

```powershell
uv run prescriptxai info --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai assess --engine-id 1 --cycle 1 --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai recommend state.json --mode fast --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai recommend --engine-id 1 --cycle 1 --mode thorough --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai batch telemetry.csv --output decisions.json --mode fast
uv run prescriptxai latency-bench telemetry.csv --output latency.json
uv run prescriptxai serve --config configs/experiments/phase6-pipeline-v1.yaml
```

`recommend` and `assess` engine/cycle selection reads training archive telemetry; official test
states can be supplied as JSON/CSV. `recommend` and `assess` accept `--context observed_context.json`;
`batch` accepts `--contexts contexts.json` with one observed context or null per CSV row.
For LSTM engine/cycle selection, the CLI derives actual preceding archive cycles and rejects
insufficient history. It never pads or fabricates a sequence. Omitted modes use the YAML default. Library multiprocessing uses isolated CPU artifact workers,
bounded by YAML worker/batch limits. This is a throughput option, excluded from serial latency claims.
Cached artifacts are fingerprinted; shared predictor access is locked. Requests copy mode settings.

## HTTP

POST `/assess`, `/recommend` accept `{"state": {...}, "context": {...}, "mode": "fast"}`.
POST `/recommend/batch` accepts `{"states": [{...}], "mode": "thorough", "contexts": [null]}`.
Omitted API modes use `pipeline.default_mode`; explicit modes override it.
GET `/health`, `/config`, `/version` describe loaded artifacts and schema. `/docs` and `/openapi.json`
describe the contracts. No model loaded returns 503; invalid payloads return 422. Actual streamed
payload bytes above the configured limit return 413. When the environment variable named by
`api.api_key_env` is set, `X-API-Key` must match; invalid keys return 401. Never place keys in YAML.
YAML controls CORS origins, headers and methods. Request IDs are isolated per request and returned
in `X-Request-ID`; recommendation run_id uses that ID. The CLI and API use the same pipeline.

## Freeze and migration

Serialization snapshots are `docs/schemas/RecourseResult-2.0.0.json` and
`ValidationReport-2.0.0.json`. See `schema_changelog.md`. After closure, changes require a version
bump, changelog and agreement from the library, CLI, API and dashboard owners. Historical 1.1
Phase 5 result files are retained. The read-only `outcome` and `tiers` aliases carry the same checks;
they are verified on JSON round trips and cannot override the independent verdicts.
