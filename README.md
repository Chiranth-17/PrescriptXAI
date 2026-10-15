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

To score a raw-unit machine-state JSON file, provide model features plus configured context
(`engine_id`, `cycle`, and `op_setting_3` for default FD001):

```powershell
uv run prescriptxai recommend .\state.json
```

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

## Verify changes

```powershell
uv run ruff check .
uv run mypy src
uv run pytest --cov=prescriptxai
```

Technical details: [architecture](docs/architecture.md), [math and units](docs/math.md),
[limitations](docs/limitations.md), and [defense Q&A](docs/defense_qa.md).
