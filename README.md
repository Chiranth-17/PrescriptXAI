# PrescriptXAI

PrescriptXAI is a research library and decision-support prototype for actuator-only algorithmic
recourse. It searches for sparse, bounded state changes and checks model safety separately from
three empirical/engineering plausibility tiers. The authoritative project synopsis is preserved at
[docs/synopsis.pdf](docs/synopsis.pdf).

> **Scope:** NASA C-MAPSS is static run-to-failure data. It cannot establish that a proposed
> intervention extends RUL or is safe on a real engine. The default feature map exposes seven
> measured channels as configurable controllable proxies, not direct actuator commands. Learned
> sensor coupling captures observed co-variation, not causal physics. Recommendations remain
> research outputs pending domain review. Dynamic simulator support is an optional interface,
> disabled by default.

## Install

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required. Dependencies are pinned in
`uv.lock`.

```powershell
uv sync --all-groups --locked
```

Dependencies are exact-pinned in the `core`, `dev`, `dashboard`, and `api` groups. Select only the
groups needed for a deployment. For the library and HTTP service only, run
`uv sync --no-default-groups --group core --group api --locked`. Dataset and fitted artifacts are
ignored by Git.

## Run

The configured NASA archive is stored at `data/raw/CMAPSSData.zip`. Preparation reports sensor
filtering, creates engine-disjoint partitions, and persists train-only regime/scaling statistics:

```powershell
uv run prescriptxai data download --subset FD001
uv run prescriptxai data prepare --subset FD001
uv run prescriptxai train --subset FD001 --model xgb
uv run prescriptxai train --subset FD001 --model mlp
uv run prescriptxai train --subset FD001 --model lstm
```

See [C-MAPSS ingestion and preprocessing](docs/data_pipeline.md) for the canonical schema, RUL
label semantics, optional cap, data-quality report, and manual download recovery steps.
See [predictive models](docs/predictive_models.md) for engine-disjoint fitting, validation-only
calibration, held-out metrics, sequence window semantics, and artifact outputs.

To score a raw-unit machine-state JSON file, provide the declared telemetry and context.
The public pipeline checks names, units, finite values and artifact compatibility. Actual omitted
telemetry and observed LSTM history can be supplied as context; missing measurements are errors.
With the existing fitted Phase 5 artifacts:

```powershell
uv run prescriptxai info --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai assess --engine-id 1 --cycle 1 --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai recommend .\state.json --mode fast --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai batch telemetry.csv --output decisions.json --config configs/experiments/phase6-pipeline-v1.yaml
uv run prescriptxai latency-bench telemetry.csv --output latency.json --config configs/experiments/phase6-pipeline-v1.yaml
```

The library exports `PrescriptXAI.from_config(...)`, `assess`, `recommend`, `recommend_batch` and
`explain_result`. CLI and HTTP use the same versioned result with independent tier verdicts,
RECOVERABLE/PARTIAL/ESCALATE triage, raw/scaled changes, metadata and measured timings.
Below the alert threshold, the state is unchanged and status is NO_INTERVENTION.
FAST and THOROUGH modes are explicit; FAST's name does not certify its latency budget.
See [decision pipeline and HTTP usage](docs/decision_pipeline.md),
[schema migration](docs/schema_changelog.md) and [Phase 6 measurements](docs/phase6_changes.md).

Run deterministic held-out evaluation, producing JSON and Markdown reports under `artifacts/`:

```powershell
uv run prescriptxai evaluate
```

Launch the local dashboard or optional HTTP service:

```powershell
uv run streamlit run src/prescriptxai/dashboard/app.py
uv run prescriptxai serve
```

Thresholds, feature groups, model parameters, bounds, rate limits, coupling rules, recourse limits,
and evaluation targets live in [`configs/default.yaml`](configs/default.yaml) and
[`configs/features.yaml`](configs/features.yaml). The C-MAPSS proxy choices are configurable and
must not be interpreted as verified actuator commands. A domain review must establish the
telemetry-to-control mapping and safe operating envelope before operational use.

## Evaluation status

The latest measured predictor and coupling metrics, including below-floor coupling relations, are
recorded in [`PROGRESS.md`](PROGRESS.md) and the generated `artifacts/` reports. Those measurements
do not establish that the proxy adjustments are physically realizable or safe on a real engine.
Evaluation target statuses use measured run outputs; synopsis case-study values are illustrative.

## Multi-tier validation

Validation reports true-model validity (Tier 1), distributional plausibility (Tier 2), proxy
engineering/coupling constraints (Tiers 3–4), and their joint verdict separately. Each tier includes
status, evidence and signed margins. Unavailable dynamics report **skipped**, never pass; the
highest available static evidence is E3, conditional on C-MAPSS sensor-proxy assumptions.

Phase 5 covariance artifacts use training-only Ledoit–Wolf shrinkage with Cholesky solves.
Precision-only older artifacts require refitting. Learned residual thresholds must be calibrated
on disjoint validation engines before Tier 4 can pass; `calibrate_coupling_thresholds` is the
library preparation function. The existing frozen Phase 4 artifact/state comparison is run with:

```powershell
uv run python scripts/diagnostics/phase5_validate.py
```

It uses committed configs under `configs/experiments/`, preserves both D_max protocols and all
query denominators, and writes fitted validation artifacts plus engine-bootstrap funnels.
See [the evaluation protocol](docs/evaluation_protocol.md), [Phase 5 changes](docs/phase5_changes.md),
and [assumptions](docs/assumptions.md). Replay of existing states is not fresh generalization
or validated real-engine intervention evidence.

## Verify changes

```powershell
uv run ruff check .
uv run mypy src
uv run pytest --cov=prescriptxai
```

Technical details: [architecture](docs/architecture.md), [math and units](docs/math.md),
[limitations](docs/limitations.md), and [defense Q&A](docs/defense_qa.md).
