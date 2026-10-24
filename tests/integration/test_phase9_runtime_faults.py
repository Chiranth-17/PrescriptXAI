"""Actual post-load faults return typed failures instead of raw operator errors."""

from pathlib import Path

import pandas as pd
import pytest
import torch
from fastapi.testclient import TestClient

from fixtures.recourse_models import make_recourse_fixture
from integration.test_phase6_artifacts_cli import fitted_config  # noqa: F401
from integration.test_phase8_backend import preview_service  # noqa: F401
from prescriptxai.api import create_app
from prescriptxai.config import load_config
from prescriptxai.models.registry import load_model_bundle
from prescriptxai.pipeline import ArtifactError, InputError, PrescriptXAI
from prescriptxai.validation.pipeline import fit_mahalanobis_validator


def test_postload_predictor_fault_is_typed_for_library_and_operator(fitted_config: Path) -> None:  # noqa: F811
    """A real fitted predictor damaged in memory fails closed at every public request boundary."""
    service = PrescriptXAI.from_config(fitted_config)
    service.engine.model.estimator.network_ = None
    state = {"actuator": -2.0, "sensor": 2.0}
    operations = [
        lambda: service.assess(state),
        lambda: service.recommend(state),
        lambda: service.validate_controls(state, {"actuator": 1.0}),
        lambda: service.recommend_batch(pd.DataFrame([state])),
    ]
    for operation in operations:
        with pytest.raises(ArtifactError, match="verified artifacts"):
            operation()
    client = TestClient(create_app(service), raise_server_exceptions=False)
    response = client.post("/assess", json={"state": state})
    assert response.status_code == 503
    assert response.json()["error_type"] == "ArtifactError"
    assert "Traceback" not in response.text


def test_corrupt_neural_output_width_cannot_silently_expand_risk_rows(fitted_config: Path) -> None:  # noqa: F811
    """Duplicate a real trained output head to expose the missing batch-length check."""
    bundle = load_model_bundle(load_config(fitted_config).artifacts.model)
    original = bundle.estimator.network_[-1]
    replacement = torch.nn.Linear(original.in_features, 2)
    with torch.no_grad():
        replacement.weight.copy_(original.weight.expand(2, -1))
        replacement.bias.copy_(original.bias.expand(2))
    bundle.estimator.network_[-1] = replacement
    with pytest.raises(ValueError, match="probabilities.*rows"):
        bundle.predict_risk(pd.DataFrame([{"actuator": 2.0, "sensor": 2.0}]))


def test_validator_cannot_relabel_evaluation_engines_as_fitting_engines() -> None:
    """Declared covariance IDs cannot override the embedded predictor/scaler training split."""
    bundle, _, training = make_recourse_fixture()
    wrong_partition = training.copy()
    wrong_partition.engine_id = 7
    with pytest.raises(ValueError, match="model.*training engines"):
        fit_mahalanobis_validator(
            wrong_partition, bundle, (7,), load_config(Path("configs/default.yaml"))
        )


@pytest.mark.parametrize("workers", [True, 1.5, float("nan"), "1"])
def test_batch_workers_cannot_bypass_integer_limits(
    preview_service: PrescriptXAI,  # noqa: F811
    workers: object,
) -> None:
    """Malformed direct-library worker counts fail before creating any process pool."""
    with pytest.raises(InputError, match="workers"):
        preview_service.recommend_batch(
            pd.DataFrame([{"actuator": 2.0, "sensor": 2.0}]),
            workers=workers,  # type: ignore[arg-type]
        )
