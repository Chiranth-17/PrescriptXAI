.PHONY: install lint typecheck test cov data train evaluate dashboard api docs clean all-checks

install:
	uv sync --all-groups --locked

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

test:
	uv run pytest

cov:
	uv run pytest --cov=prescriptxai --cov-report=term-missing --cov-report=json --cov-report=xml
	uv run python scripts/quality/coverage_gate.py

data:
	uv run prescriptxai data prepare --subset FD001

train:
	uv run prescriptxai train

evaluate:
	uv run prescriptxai evaluate

dashboard:
	uv run streamlit run src/prescriptxai/dashboard/app.py

api:
	uv run prescriptxai serve

docs:
	uv run mkdocs build --strict

clean:
	uv run python -c "import shutil; from pathlib import Path; [shutil.rmtree(Path(name), ignore_errors=True) for name in ['build', 'dist', 'htmlcov', '.pytest_cache', '.mypy_cache', '.ruff_cache']]; Path('.coverage').unlink(missing_ok=True)"

all-checks: lint typecheck cov docs
