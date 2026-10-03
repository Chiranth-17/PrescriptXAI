.PHONY: lint typecheck test check

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

test:
	uv run pytest --cov=prescriptxai --cov-report=term-missing

check: lint typecheck test
