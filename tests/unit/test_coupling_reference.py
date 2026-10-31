"""Reference-preserving coupling cannot erase observed degradation without an action."""

from __future__ import annotations

import copy
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
from prescriptxai.models.registry import ModelBundle
from prescriptxai.recourse.objective import RecourseObjective
from prescriptxai.validation.feasibility import build_feasibility_penalty
from prescriptxai.validation.tier2_mahalanobis import MahalanobisValidator


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


@pytest.mark.parametrize("omit_dependent", [False, True])
@pytest.mark.parametrize("nonlinear", [False, True])
def test_shared_objective_matches_separate_actual_coupling_graphs(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],
    omit_dependent: bool, nonlinear: bool,
) -> None:
    """Sharing production scaling/coupling and feasibility preserves values and gradients."""
    fitted, frame = coupling_data
    coupling = copy.deepcopy(fitted)
    if nonlinear:
        for name, model in coupling.torch_models.items():
            # Raw sensor outputs are tens/hundreds: avoid a saturated, zero-gradient Tanh.
            rescale = torch.nn.Linear(1, 1, bias=False, dtype=torch.float64)
            with torch.no_grad():
                rescale.weight.fill_(0.01)
            coupling.torch_models[name] = torch.nn.Sequential(model, rescale, torch.nn.Tanh())
    names = tuple(name for name in coupling.feature_names
                  if not omit_dependent or name != "sensor_4")
    training = frame[frame.engine_id.isin((1, 2))]
    scaler = fit_feature_scaler(training, names)
    bundle = ModelBundle(
        estimator=None, scaler=scaler, feature_names=names, training_engine_ids=(1, 2),
        model_type="test-only-gradient", seed=17,
    )
    initial = frame.iloc[0].to_dict()
    initial["sensor_3"] += 20.0
    original = torch.tensor(
        scaler.transform(pd.DataFrame([initial], columns=names)), dtype=torch.float64,
    )
    module = coupling.propagate_scaled_torch_module(scaler)
    validator = MahalanobisValidator.fit(
        scaler.transform(training.loc[:, list(names)]), names,
        training.engine_id.to_numpy(dtype=np.int64),
        (1, 2), max_distance=5.0, regularization=1e-6,
    )
    penalty = build_feasibility_penalty(
        bundle, load_taxonomy(Path("configs/features.yaml")), validator, coupling, initial,
    )
    support = torch.tensor([names.index("sensor_12"), names.index("sensor_9")])

    def lift(delta: torch.Tensor) -> torch.Tensor:
        row = original.index_copy(1, support, original[:, support] + delta)
        return module(row, original)

    def risk(features: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(features.float().mean())

    probe = torch.tensor([0.1, -0.2], dtype=torch.float64, requires_grad=True)
    dependent_gradient = torch.autograd.grad(lift(probe)[:, names.index("sensor_3")].sum(),
                                            probe)[0]
    assert torch.linalg.vector_norm(dependent_gradient) > 1e-10

    common = dict(
        lower_change=np.array([-0.5, -0.5]), upper_change=np.array([0.5, 0.5]),
        safe_threshold=0.2, safety_margin=0.01, alpha=12.0, beta=1000.0, gamma=9.0,
        l1_weight=0.8, l1_mode="smooth", smoothing_epsilon=1e-5,
        prediction_loss="squared_hinge", feasibility_weight=7.0,
    )
    legacy = RecourseObjective(
        lambda delta: risk(lift(delta)),
        feasibility_function=lambda delta: penalty(lift(delta)), **common,
    )
    shared = RecourseObjective(risk, feasibility_function=penalty, feature_function=lift, **common)
    for decision in (np.array([0.1, -0.2]), np.array([-0.5, 0.5]), np.array([0.0, 0.0])):
        expected_value, expected_gradient = legacy.value_and_grad(decision)
        for _ in range(2):
            actual_value, actual_gradient = shared.value_and_grad(decision)
            assert actual_value == pytest.approx(expected_value, rel=1e-13, abs=1e-9)
            np.testing.assert_allclose(actual_gradient, expected_gradient, rtol=1e-9, atol=1e-8)


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


def test_torch_propagation_ignores_dependent_features_absent_from_model_order(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],
) -> None:
    """A fold may drop constant targets while retaining all required coupling predictors."""
    coupling, frame = coupling_data
    omitted = coupling.dependent_features[0]
    names = tuple(name for name in coupling.feature_names if name != omitted)
    values = frame.loc[:2, list(names)].to_numpy(dtype=float)
    tensor = torch.tensor(values, dtype=torch.float64, requires_grad=True)

    output = coupling.propagate_torch_module(names)(tensor, tensor.detach())

    np.testing.assert_array_equal(output.detach().numpy()[:, :], values)
    output.sum().backward()
    assert tensor.grad is not None
    assert torch.isfinite(tensor.grad).all()


def test_torch_propagation_still_requires_every_predictor(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],
) -> None:
    """Missing a required model input is an explicit configuration error."""
    coupling, _ = coupling_data
    names = tuple(name for name in coupling.feature_names if name != coupling.predictor_features[0])
    with pytest.raises(ValueError, match="missing coupling predictors"):
        coupling.propagate_torch_module(names)


def test_batch_propagation_ignores_absent_dependent_targets(
    coupling_data: tuple[SensorCouplingModel, pd.DataFrame],
) -> None:
    """Vectorized true-model search supports folds that omit constant dependent channels."""
    coupling, frame = coupling_data
    omitted = coupling.dependent_features[0]
    names = tuple(name for name in coupling.feature_names if name != omitted)
    values = frame.loc[:2, list(names)].to_numpy(dtype=float)

    propagated = coupling.propagate_batch(
        values, names, reference_state=values
    )

    np.testing.assert_allclose(propagated, values, rtol=1e-10, atol=1e-10)
    missing_predictor = coupling.predictor_features[0]
    predictor_names = tuple(name for name in names if name != missing_predictor)
    predictor_values = values[:, [names.index(name) for name in predictor_names]]
    with pytest.raises(ValueError, match="missing coupling predictors"):
        coupling.propagate_batch(predictor_values, predictor_names)


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
