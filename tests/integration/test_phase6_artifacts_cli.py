"""Load actual fitted fixture artifacts through public factories and CLI commands."""

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml
from typer.testing import CliRunner

from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.cli import app
from prescriptxai.config import load_config
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.models.torch_models import MLPFailureModel
from prescriptxai.pipeline import ArtifactError, PrescriptXAI
from prescriptxai.schemas import RecourseResult, ValidationReport
from prescriptxai.validation.pipeline import (
    fit_mahalanobis_validator,
    save_mahalanobis_validator,
)


@pytest.fixture
def fitted_config(tmp_path: Path) -> Path:
    """Train a genuine small MLP, persist its scaler and empirical validator for CLI tests."""
    bundle, taxonomy, training = make_recourse_fixture()
    config = load_config(Path("configs/default.yaml"))
    config.model_choice = "torch"
    config.model.risk_estimator = "torch"
    config.pipeline.benchmark_warmups = 0
    config.evaluation.bootstrap_replicates = 100
    config.recourse.max_iterations = 2
    config.recourse.alpha_steps = config.recourse.restarts = 1
    config.recourse.l1_escalation_steps = 1
    bundle.estimator = MLPFailureModel(hidden_dims=(4,), epochs=2, seed=17)
    bundle.estimator.fit(
        bundle.scaler.transform(training[list(bundle.feature_names)]),
        (training.actuator < 0).astype(int).to_numpy(),
    )
    bundle.model_type = "mlp"
    bundle.metrics = {"dataset": "FD001", "horizon_H": 30}
    config.artifacts.model = config.paths.model = tmp_path / "model.joblib"
    config.artifacts.mahalanobis = config.paths.mahalanobis = tmp_path / "validator.joblib"
    config.artifacts.coupling = None
    config.pipeline.taxonomy_path = tmp_path / "features.yaml"
    config.pipeline.taxonomy_path.write_text(
        yaml.safe_dump(taxonomy.model_dump(mode="json")), encoding="utf-8"
    )
    save_model_bundle(bundle, config.artifacts.model)
    validator = fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config)
    save_mahalanobis_validator(validator, config.artifacts.mahalanobis)
    path = tmp_path / "pipeline.yaml"
    path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    return path


def test_factory_cache_and_corrupt_artifacts(fitted_config: Path) -> None:
    """Factories share immutable artifact access, isolate configs and fail on bad metadata."""
    first = PrescriptXAI.from_artifacts(fitted_config.parent)
    second = PrescriptXAI.from_config(fitted_config)
    assert first.engine is second.engine
    first.config.pipeline.default_mode = "thorough"
    assert second.config.pipeline.default_mode == "fast"
    config = load_config(fitted_config)
    config.model_choice = "xgboost"
    with pytest.raises(ArtifactError, match="configured"):
        PrescriptXAI.from_config(config)
    config.model_choice = "torch"
    config.horizon_H = 20
    with pytest.raises(ArtifactError, match="horizon_H"):
        PrescriptXAI.from_config(config)
    config.horizon_H = 30
    config.artifacts.model = fitted_config.parent / "absent.joblib"
    with pytest.raises(ArtifactError):
        PrescriptXAI.from_config(config)


def test_cli_assess_recommend_batch_info_and_benchmark(fitted_config: Path, tmp_path: Path) -> None:
    """Invoke actual command parsing, artifact loading, inference and JSON serialization."""
    runner = CliRunner()
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"actuator": 2.0, "sensor": 2.0}), encoding="utf-8")
    for command in ("assess", "recommend"):
        result = runner.invoke(app, [command, str(state), "--config", str(fitted_config)])
        assert result.exit_code == 0, result.output
        assert "risk" in result.output
    info = runner.invoke(app, ["info", "--config", str(fitted_config)])
    assert info.exit_code == 0 and json.loads(info.output)["assumptions"]
    csv = tmp_path / "rows.csv"
    pd.DataFrame([{"actuator": 2.0, "sensor": 2.0}]).to_csv(csv, index=False)
    output = tmp_path / "batch.json"
    batch = runner.invoke(
        app,
        [
            "batch",
            str(csv),
            "--output",
            str(output),
            "--config",
            str(fitted_config),
            "--mode",
            "thorough",
        ],
    )
    assert batch.exit_code == 0, batch.output
    assert json.loads(output.read_text(encoding="utf-8"))[0]["mode"] == "THOROUGH"
    # Benchmark requires genuine engine provenance; lack of it is a precise failure.
    bench = runner.invoke(app, ["latency-bench", str(csv), "--config", str(fitted_config)])
    assert bench.exit_code != 0 and isinstance(bench.exception, ValueError)
    malformed = tmp_path / "bad.json"
    malformed.write_text('{"actuator": 0}', encoding="utf-8")
    bad = runner.invoke(app, ["recommend", str(malformed), "--config", str(fitted_config)])
    assert bad.exit_code != 0 and "missing" in bad.output
    selection = runner.invoke(app, ["assess", "--config", str(fitted_config)])
    assert selection.exit_code != 0


def test_frozen_serialization_schemas_match_snapshot() -> None:
    """Require deliberate versioned migration for either public serialization contract."""
    for schema in (RecourseResult, ValidationReport):
        path = Path("docs/schemas") / f"{schema.__name__}-2.0.0.json"
        assert schema.model_json_schema(mode="serialization") == json.loads(
            path.read_text(encoding="utf-8")
        )
