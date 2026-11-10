"""Boundary failures remain typed for library and HTTP callers."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from integration.test_phase8_backend import preview_service  # noqa: F401
from prescriptxai.api import create_app
from prescriptxai.models.torch_models import LSTMFailureModel
from prescriptxai.pipeline import FeatureError, HistoryError, InputError, PrescriptXAI


@pytest.mark.parametrize("context", [False, [], 0, np.zeros((2, 2))])
def test_malformed_context_is_a_typed_error(
    preview_service: PrescriptXAI,  # noqa: F811
    context: object,
) -> None:
    """Context validation never coerces false values to an empty valid context."""
    with pytest.raises(InputError, match="context"):
        preview_service.assess({"actuator": 2.0, "sensor": 2.0}, context)  # type: ignore[arg-type]


def test_mixed_column_names_are_a_typed_feature_error(preview_service: PrescriptXAI) -> None:  # noqa: F811
    """An error message cannot raise TypeError while sorting mixed unknown key types."""
    with pytest.raises(FeatureError, match="string"):
        preview_service.assess({"actuator": 2.0, "sensor": 2.0, 7: 0, "未知": 0})  # type: ignore[dict-item]


@pytest.mark.parametrize("value", [np.complex128(1 + 2j), np.complex64(1 + 0j)])
def test_complex_measurements_never_silently_lose_their_imaginary_part(
    preview_service: PrescriptXAI,  # noqa: F811
    value: complex,
) -> None:
    """A wrong numerical dtype is rejected before NumPy's permissive float conversion."""
    with pytest.raises(InputError, match="complex"):
        preview_service.assess({"actuator": value, "sensor": 2.0})  # type: ignore[dict-item]
    with pytest.raises(InputError, match="complex"):
        preview_service.validate_controls(
            {"actuator": -2.0, "sensor": 2.0}, {"actuator": value}  # type: ignore[dict-item]
        )


@pytest.mark.parametrize("value", [np.bool_(True), np.complex128(2 + 1j)])
def test_context_measurements_preserve_numpy_type_before_coercion(
    preview_service: PrescriptXAI,  # noqa: F811
    value: object,
) -> None:
    """Context telemetry cannot bypass raw measurement checks through Pydantic coercion."""
    with pytest.raises(InputError, match="boolean|complex"):
        preview_service.assess({"actuator": 2.0}, {"telemetry": {"sensor": value}})


def test_extreme_finite_lstm_history_is_rejected_before_prediction(
    preview_service: PrescriptXAI,  # noqa: F811
) -> None:
    """Every observed prefix row receives the latest state's numeric-range protection."""
    estimator = LSTMFailureModel(window=3, hidden_dims=(4,), epochs=2, batch_size=8, seed=17)
    estimator.fit(np.random.default_rng(17).normal(size=(8, 3, 2)), np.asarray([0, 1] * 4))
    preview_service.engine.model.estimator = estimator
    state = {"actuator": 2.0, "sensor": 2.0}
    history = [[1e308, 2.0], [1.0, 2.0]]
    with pytest.raises(HistoryError, match="numeric range"):
        preview_service.assess(state, {"history": history})
    client = TestClient(create_app(preview_service, local_demo=True), raise_server_exceptions=False)
    response = client.post("/assess", json={"state": state, "context": {"history": history}})
    assert response.status_code == 422 and response.json()["error_type"] == "HistoryError"
