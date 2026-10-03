# PrescriptXAI

PrescriptXAI is a research and decision-support package for generating sparse, bounded
maintenance recourse and checking model safety separately from physical plausibility.

> C-MAPSS is static run-to-failure data. It cannot establish that an intervention extends RUL
> or is safe on a real engine. Dynamic simulator validation is optional and disabled by default.

The implementation is under active development. See [PROGRESS.md](PROGRESS.md) for verified
capabilities and blockers. The project synopsis is preserved at [docs/synopsis.pdf](docs/synopsis.pdf).

## Development setup

Install [uv](https://docs.astral.sh/uv/) and run:

```powershell
uv sync --all-extras
uv run ruff check .
uv run mypy src
uv run pytest --cov=prescriptxai
```

Generated datasets belong under `data/` and fitted models under `artifacts/`; both are ignored
by Git.
