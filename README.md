# PrescriptXAI

PrescriptXAI is a research library and decision-support prototype for actuator-only algorithmic
recourse. It searches for sparse, bounded state changes and checks model safety separately from
three empirical/engineering plausibility tiers. The authoritative project synopsis is preserved at
[docs/synopsis.pdf](docs/synopsis.pdf).

> **Scope:** NASA C-MAPSS is static run-to-failure data. It cannot establish that a proposed
> intervention extends RUL or is safe on a real engine. The default FD001 feature map contains no
> verified controllable actuators or coupling rules, so its run correctly produces no actionable
> recourse. Dynamic simulator support is an optional interface, disabled by default.

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

The configured dataset archive downloads to `data/raw/CMAPSSData.zip`:

```powershell
uv run prescriptxai download
uv run prescriptxai train
```

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
[`configs/features.yaml`](configs/features.yaml). Only declare a feature as an actuator after a
domain review establishes the telemetry-to-control mapping and safe operating envelope.

## Evaluation status

The latest default FD001 run trains on 69 engines, uses 16 for validation, and holds out 15 engines.
The held-out set contains 354 states over the configured high-risk threshold; 100 are deterministically
sampled. In that run, model-valid recommendations were 0/100 and fully physically plausible
recommendations were 0/100 because no verified actuators or coupling rules are configured. Rates,
latency, and target statuses are measured in `artifacts/FD001-evaluation.md`; they are not the
illustrative synopsis case study. See [PROGRESS.md](PROGRESS.md) for exact current results and
open blockers.

## Verify changes

```powershell
uv run ruff check .
uv run mypy src
uv run pytest --cov=prescriptxai
```

Technical details: [architecture](docs/architecture.md), [math and units](docs/math.md),
[limitations](docs/limitations.md), and [defense Q&A](docs/defense_qa.md).
