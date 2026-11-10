.PHONY: install lint typecheck test cov data train evaluate dashboard api docs clean all-checks check regression-full release-gate security

ifeq ($(REUSE_ONLY),1)
export PSX_QUALITY_REGRESSION_REUSE_ONLY = 1
endif

install:
	uv sync --all-groups --locked

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

test:
	uv run pytest

cov:
	uv run python scripts/quality/check_inputs.py
	uv run pytest --cov=prescriptxai --cov-report=term-missing --cov-report=json --cov-report=xml
	uv run python scripts/quality/coverage_gate.py
	uv run python scripts/quality/coverage_gate.py --config configs/experiments/phase12-quality.yaml

data:
	uv run prescriptxai data prepare --subset FD001

train:
	uv run prescriptxai train

evaluate:
	uv run prescriptxai evaluate

dashboard:
	uv run prescriptxai dashboard

api:
	uv run prescriptxai serve

docs:
	uv run mkdocs build --strict

clean:
	uv run python -c "import shutil; from pathlib import Path; [shutil.rmtree(Path(name), ignore_errors=True) for name in ['build', 'dist', 'htmlcov', '.pytest_cache', '.mypy_cache', '.ruff_cache']]; Path('.coverage').unlink(missing_ok=True)"

check: lint typecheck cov

all-checks: check

regression-full:
	uv run python -m scripts.diagnostics.regression_tiers --tier full $(if $(filter 1,$(REUSE_ONLY)),--reuse-only,) $(if $(RESUME),--resume "$(RESUME)",) $(if $(REGRESSION_OUTPUT),--output "$(REGRESSION_OUTPUT)",)

release-gate:
	uv run python scripts/quality/release_gate.py $(if $(filter 1,$(REUSE_ONLY)),--reuse-only,)

security:
	uv run --locked python scripts/quality/security.py $(if $(SECURITY_OUTPUT),--output "$(SECURITY_OUTPUT)",)
