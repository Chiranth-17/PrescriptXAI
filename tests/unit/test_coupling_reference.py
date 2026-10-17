"""Reference-preserving coupling cannot erase observed degradation without an action."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import torch

from fixtures.cmapss import make_cmapss_frame
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.data.cmapss import to_model_frame
from prescriptxai.data.preprocess import add_training_labels, fit_feature_scaler


@pytest.fixture(scope="module")
def coupling_data() -> tuple[SensorCouplingModel, pd.DataFrame]:
    """Fit actual Ridge relations using two training engines from a test-only fixture."""
    frame = add_training_labels(
        to_model_frame(make_cmapss_frame(3, min_cycles=90, max_cycles=93)), None, 30
    )
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    coupling = SensorCouplingModel.fit(
        frame, taxonomy, training_engine_ids=(1, 2), failure_horizon=30
    )
    return coupling, frame


def test_zero_action_preserves_observed_dependent_residuals(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],
) -> None:
    """No control action preserves a deliberately inconsistent observation and its failed rule."""
    coupling, frame = coupling_data
    original = frame.iloc[0].to_dict()
    original["sensor_3"] += 200.0
    propagated = coupling.propagate(original, reference_state=original)
    assert propagated == original
    assert coupling.evaluate_learned_constraints(propagated) == (
        coupling.evaluate_learned_constraints(original)
    )
    assert not next(
        rule for rule in coupling.evaluate_learned_constraints(propagated)
        if rule.name == "learned_sensor_3"
    ).passed


def test_reference_propagation_matches_batch_and_torch_with_gradients(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],
) -> None:
    """NumPy and torch agree on a real fitted relation and the control derivative."""
    coupling, frame = coupling_data
    names = coupling.feature_names
    reference = frame.loc[0, list(names)].to_numpy(dtype=float, copy=True)
    reference[names.index("sensor_3")] += 20.0
    candidate = np.repeat(reference[None, :], 2, axis=0)
    control_index = names.index("sensor_12")
    candidate[:, control_index] += np.asarray([0.1, -0.2])
    dependent_index = names.index("sensor_3")
    propagated = coupling.propagate_batch(candidate, names, reference_state=reference)
    for index, row in enumerate(candidate):
        one = coupling.propagate(
            dict(zip(names, row, strict=True)),
            reference_state=dict(zip(names, reference, strict=True)),
        )
        np.testing.assert_allclose(propagated[index], [one[name] for name in names], atol=1e-10)
    tensor = torch.tensor(candidate, dtype=torch.float64, requires_grad=True)
    module = coupling.propagate_torch_module(names)
    output = module(tensor, torch.tensor(reference, dtype=torch.float64))
    np.testing.assert_allclose(output.detach().numpy(), propagated, atol=1e-10)
    output[:, dependent_index].sum().backward()
    assert tensor.grad is not None
    assert torch.isfinite(tensor.grad).all()
    expected_gradient = coupling.models["sensor_3"].coef_[
        coupling.predictor_features.index("sensor_12")
    ]
    assert abs(expected_gradient) > 1e-6
    np.testing.assert_allclose(tensor.grad[:, control_index].numpy(), expected_gradient, atol=1e-10)
    untouched = [names.index(name) for name in names if name not in coupling.dependent_features]
    np.testing.assert_array_equal(propagated[:, untouched], candidate[:, untouched])


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_scaled_reference_identity_and_raw_scaled_mapping(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame], dtype: torch.dtype,
) -> None:
    """An unchanged scaled observation stays exactly unchanged, with reversible action mapping."""
    coupling, frame = coupling_data
    names = coupling.feature_names
    scaler = fit_feature_scaler(frame[frame.engine_id.isin((1, 2))], names)
    scaled = torch.tensor(scaler.transform(frame.loc[:1, list(names)]), dtype=dtype)
    module = coupling.propagate_scaled_torch_module(scaler)
    np.testing.assert_array_equal(module(scaled, scaled).numpy(), scaled.numpy())
    candidate = scaled.clone()
    candidate[:, names.index("sensor_12")] += 0.2
    result = module(candidate, scaled).numpy()
    reference_raw = scaled.double().numpy() * scaler.scaler.scale_ + scaler.scaler.mean_
    candidate_raw = candidate.double().numpy() * scaler.scaler.scale_ + scaler.scaler.mean_
    expected_raw = coupling.propagate_batch(candidate_raw, names, reference_state=reference_raw)
    actual_raw = result * scaler.scaler.scale_ + scaler.scaler.mean_
    np.testing.assert_allclose(actual_raw, expected_raw, rtol=1e-7, atol=1e-8)


@pytest.mark.parametrize("invalid", [np.asarray([]), np.ones((3, 2)), np.asarray([np.nan])])
def test_reference_propagation_rejects_invalid_references(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame], invalid: np.ndarray,
) -> None:
    """Malformed and nonfinite reference data cannot silently enter propagation."""
    coupling, frame = coupling_data
    names = coupling.feature_names
    values = frame.loc[:1, list(names)].to_numpy(dtype=float)
    with pytest.raises(ValueError, match="reference"):
        coupling.propagate_batch(values, names, reference_state=invalid)
    with pytest.raises(ValueError, match="reference"):
        coupling.propagate_torch_module(names)(
            torch.tensor(values), torch.tensor(invalid)
        )
    bad_state = dict(zip(names, values[0], strict=True))
    bad_state["sensor_3"] = float("nan")
    with pytest.raises(ValueError, match="reference values must be finite"):
        coupling.propagate(dict(zip(names, values[0], strict=True)), reference_state=bad_state)


def test_coupling_persists_engine_ids_and_warns_on_legacy_provenance(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Artifacts record actual training engines; missing historical provenance is explicit."""
    coupling, _ = coupling_data
    restored = SensorCouplingModel.load(coupling.save(tmp_path / "coupling.joblib"))
    assert restored.training_engine_ids == (1, 2)
    assert restored.fit_engine_ids == (1, 2)
    del restored.training_engine_ids
    joblib.dump(restored, tmp_path / "legacy.joblib")
    legacy = SensorCouplingModel.load(tmp_path / "legacy.joblib")
    assert legacy.training_engine_ids == ()
    assert "no training-engine provenance" in caplog.text


@pytest.mark.parametrize("engine_ids", [(1, 4), (1, 1), ()])
def test_coupling_rejects_missing_or_duplicate_training_provenance(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame], engine_ids: tuple[int, ...],
) -> None:
    """Unobserved or duplicate engine IDs cannot be silently dropped from provenance."""
    _, frame = coupling_data
    with pytest.raises(ValueError, match="training"):
        SensorCouplingModel.fit(
            frame, load_taxonomy(Path("configs/features.yaml")),
            training_engine_ids=engine_ids, failure_horizon=30,
        )
