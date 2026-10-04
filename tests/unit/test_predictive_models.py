"""Unit coverage for differentiable predictors, calibration, and held-out metrics."""

from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image
from sklearn.preprocessing import StandardScaler

from fixtures.cmapss import make_cmapss_frame
from prescriptxai.config import ModelConfig
from prescriptxai.evaluation.calibration_plot import write_calibration_plots
from prescriptxai.evaluation.metrics import predictor_metrics, surrogate_fidelity
from prescriptxai.models.calibration import (
    calibration_diagnostics,
    fit_probability_calibrator,
)
from prescriptxai.models.torch_models import LSTMFailureModel, MLPFailureModel
from prescriptxai.models.xgb_model import XGBFailureModel


def _snapshot_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build ordered degradation snapshots from independent engine-like groups."""
    engine_ids = np.repeat(np.arange(1, 17), 20)
    cycle = np.tile(np.arange(1, 21), 16)
    features = np.column_stack((cycle, engine_ids % 3)).astype(np.float64)
    labels = (cycle >= 14).astype(np.int64)
    train_mask = engine_ids <= 12
    return features[train_mask], labels[train_mask], features[~train_mask]


def _model_config() -> ModelConfig:
    """Use explicit small model settings for fast deterministic unit checks."""
    return ModelConfig(
        danger_threshold=0.8,
        safe_threshold=0.2,
        calibration_method="sigmoid",
        xgb_n_estimators=12,
        xgb_max_depth=2,
        xgb_early_stopping_rounds=3,
        torch_hidden_dims=[8],
        torch_epochs=8,
        torch_batch_size=32,
        torch_early_stopping_patience=3,
    )


def test_xgb_failure_model_returns_vector_and_round_trips(tmp_path: Path) -> None:
    """XGB probabilities are finite vectors and persist with exact inference behavior."""
    x_train, y_train, x_validation = _snapshot_data()
    model = XGBFailureModel(42, _model_config()).fit(
        x_train,
        y_train,
        (x_validation, (x_validation[:, 0] >= 14).astype(np.int64)),
    )
    risk = model.predict_proba(x_validation)

    assert risk.shape == (len(x_validation),)
    assert ((risk >= 0) & (risk <= 1)).all()
    model_path = model.save(tmp_path / "xgb.joblib")
    restored = XGBFailureModel.load(model_path)
    np.testing.assert_array_equal(risk, restored.predict_proba(x_validation))


def test_mlp_is_deterministic_and_has_finite_gradients(tmp_path: Path) -> None:
    """Identically seeded MLP fits match and its probability path differentiates."""
    x_train, y_train, x_validation = _snapshot_data()
    y_validation = (x_validation[:, 0] >= 14).astype(np.int64)
    first = MLPFailureModel(
        hidden_dims=(8,), epochs=8, batch_size=32, seed=42, early_stopping_patience=3
    ).fit(x_train, y_train, (x_validation, y_validation))
    second = MLPFailureModel(
        hidden_dims=(8,), epochs=8, batch_size=32, seed=42, early_stopping_patience=3
    ).fit(x_train, y_train, (x_validation, y_validation))
    risk = first.predict_proba(x_validation)
    input_tensor = torch.tensor(x_validation[:4], dtype=torch.float32, requires_grad=True)
    first.torch_forward(input_tensor).sum().backward()

    assert first.supports_gradients
    assert risk.shape == (len(x_validation),)
    np.testing.assert_allclose(risk, second.predict_proba(x_validation), atol=0, rtol=0)
    assert input_tensor.grad is not None
    assert torch.isfinite(input_tensor.grad).all()
    assert input_tensor.grad.abs().sum() > 0
    restored = MLPFailureModel.load(first.save(tmp_path / "mlp.joblib"))
    np.testing.assert_array_equal(risk, restored.predict_proba(x_validation))


def test_lstm_sequence_path_has_finite_gradients_and_round_trip(tmp_path: Path) -> None:
    """LSTM consumes fixed history windows and returns differentiable probabilities."""
    x_train, y_train, x_validation = _snapshot_data()
    window = 4
    train_sequences = np.repeat(x_train[:, None, :], window, axis=1)
    validation_sequences = np.repeat(x_validation[:, None, :], window, axis=1)
    train_sequences[:, :, 0] = np.maximum(1, x_train[:, 0, None] - np.arange(window - 1, -1, -1))
    validation_sequences[:, :, 0] = np.maximum(
        1, x_validation[:, 0, None] - np.arange(window - 1, -1, -1)
    )
    y_validation = (x_validation[:, 0] >= 14).astype(np.int64)
    model = LSTMFailureModel(
        window=window,
        hidden_dims=(6,),
        epochs=4,
        batch_size=32,
        seed=31,
        early_stopping_patience=2,
    ).fit(train_sequences, y_train, (validation_sequences, y_validation))
    input_tensor = torch.tensor(validation_sequences[:3], dtype=torch.float32, requires_grad=True)
    model.torch_forward(input_tensor).sum().backward()

    assert model.supports_gradients
    risk = model.predict_proba(validation_sequences)
    assert risk.shape == (len(validation_sequences),)
    assert ((risk >= 0) & (risk <= 1)).all()
    assert input_tensor.grad is not None and torch.isfinite(input_tensor.grad).all()
    assert input_tensor.grad[:, :-1, :].abs().sum() > 0
    restored = LSTMFailureModel.load(model.save(tmp_path / "lstm.joblib"))
    np.testing.assert_array_equal(
        model.predict_proba(validation_sequences), restored.predict_proba(validation_sequences)
    )


@pytest.mark.parametrize("method", ["isotonic", "sigmoid", "temperature"])
def test_validation_calibrators_are_monotone(method: str) -> None:
    """Every supported calibration map preserves score ordering."""
    probabilities = np.linspace(0.01, 0.99, 120)
    labels = (probabilities >= 0.67).astype(np.int64)
    calibrator = fit_probability_calibrator(probabilities, labels, method)
    calibrated = calibrator.transform(probabilities)

    assert np.isfinite(calibrated).all()
    assert ((calibrated >= 0) & (calibrated <= 1)).all()
    assert (np.diff(calibrated) >= -1e-10).all()


def test_metrics_include_high_risk_recall_reliability_and_surrogate_fidelity() -> None:
    """Measured metric helpers report requested calibration and teacher agreement details."""
    labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
    teacher = np.asarray([0.1, 0.25, 0.78, 0.92])
    student = np.asarray([0.15, 0.3, 0.72, 0.88])
    metrics = predictor_metrics(labels, teacher, 0.8)
    diagnostics = calibration_diagnostics(labels, teacher, bins=4)
    fidelity = surrogate_fidelity(teacher, student)

    assert metrics["high_risk_recall_at_tau_danger"] == 0.5
    assert metrics["confusion_matrix_labels_0_1"] == [[2, 0], [1, 1]]
    assert isinstance(diagnostics["brier_score"], float)
    assert isinstance(diagnostics["ece"], float)
    assert len(diagnostics["reliability_curve"]) > 0  # type: ignore[arg-type]
    assert fidelity["mae"] == pytest.approx(float(np.mean(np.abs(teacher - student))))
    assert fidelity["agreement_at_tau_danger"] == 1.0


def test_calibration_diagnostics_render_png_and_html(tmp_path: Path) -> None:
    """Reliability diagnostics produce a real raster image and standalone HTML chart."""
    labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
    before = calibration_diagnostics(labels, np.asarray([0.1, 0.4, 0.6, 0.9]), bins=4)
    after = calibration_diagnostics(labels, np.asarray([0.05, 0.2, 0.8, 0.95]), bins=4)
    png_path, html_path = write_calibration_plots(
        tmp_path / "reliability", before, after, "Measured test calibration"
    )

    with Image.open(png_path) as image:
        assert image.format == "PNG"
        assert image.size == (900, 700)
    assert "Measured test calibration" in html_path.read_text(encoding="utf-8")


def test_nan_and_wrong_shape_inputs_fail_clearly() -> None:
    """Model input validation rejects NaN snapshots and malformed LSTM sequences."""
    x_train, y_train, _ = _snapshot_data()
    model = MLPFailureModel(hidden_dims=(4,), epochs=1).fit(x_train, y_train)

    with pytest.raises(ValueError, match="finite"):
        model.predict_proba(np.full((1, x_train.shape[1]), np.nan))
    sequence = LSTMFailureModel(window=3, hidden_dims=(4,), epochs=1)
    with pytest.raises(ValueError, match="shape"):
        sequence.fit(x_train, y_train)


def test_degraded_fixture_engine_scores_higher_risk_late_than_early() -> None:
    """A test-only monotonic run-to-failure trajectory learns increasing failure risk."""
    frame = make_cmapss_frame(engine_count=12, min_cycles=60, max_cycles=60)
    train_mask = frame["unit_id"] <= 9
    raw_features = frame.loc[:, ["s3"]].to_numpy(dtype=np.float64)
    labels = (frame["cycle"].to_numpy() >= 45).astype(np.int64)
    scaler = StandardScaler().fit(raw_features[train_mask.to_numpy()])
    scaled_features = scaler.transform(raw_features)
    model = MLPFailureModel(
        hidden_dims=(8,), epochs=30, batch_size=64, seed=17, early_stopping_patience=6
    ).fit(scaled_features[train_mask.to_numpy()], labels[train_mask.to_numpy()])
    engine = frame.loc[frame["unit_id"] == 10].reset_index(drop=True)
    early_raw = engine.loc[engine["cycle"] == 5, ["s3"]].to_numpy(dtype=np.float64)
    late_raw = engine.loc[engine["cycle"] == 58, ["s3"]].to_numpy(dtype=np.float64)
    early = model.predict_proba(scaler.transform(early_raw))[0]
    late = model.predict_proba(scaler.transform(late_raw))[0]

    assert late > early
