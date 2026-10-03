"""Unit tests for XGBoost, PyTorch, and grouped calibration."""

import numpy as np
import pytest
from numpy.typing import NDArray

from prescriptxai.config import ModelConfig
from prescriptxai.models.base import validate_binary_labels, validate_feature_matrix
from prescriptxai.models.calibration import fit_group_calibrator
from prescriptxai.models.torch_models import TorchMLPClassifier
from prescriptxai.models.xgb_model import build_xgb_estimator


def _classification_data() -> tuple[NDArray[np.float64], NDArray[np.int64], NDArray[np.int64]]:
    """Build deterministic binary data with grouped engine identities."""
    engine_ids = np.repeat(np.arange(1, 13, dtype=np.int64), 8)
    cycles = np.tile(np.arange(1, 9, dtype=np.float64), 12)
    features = np.column_stack((engine_ids, cycles)).astype(np.float64)
    labels = (cycles >= 5).astype(np.int64)
    return features, labels, engine_ids


@pytest.mark.parametrize(
    ("features", "message"),
    [
        (np.empty((0, 2), dtype=np.float64), "at least one row"),
        (np.empty((2, 0), dtype=np.float64), "at least one row"),
        (np.array([1.0, 2.0]), "two-dimensional"),
        (np.array([[1.0, np.nan]]), "must be finite"),
    ],
)
def test_feature_matrix_validation_rejects_bad_shape_and_nan(
    features: NDArray[np.float64], message: str
) -> None:
    """Empty, one-dimensional, and non-finite feature matrices are rejected."""
    with pytest.raises(ValueError, match=message):
        validate_feature_matrix(features)


@pytest.mark.parametrize(
    ("labels", "row_count", "message"),
    [
        (np.array([0, 1]), 3, "match the feature row count"),
        (np.array([[0, 1]]), 2, "one-dimensional"),
        (np.array([0, 2]), 2, "only 0 and 1"),
        (np.array([1, 1]), 2, "both classes"),
    ],
)
def test_binary_label_validation_rejects_invalid_labels(
    labels: NDArray[np.int64], row_count: int, message: str
) -> None:
    """Wrong length, rank, domain, and constant labels are rejected."""
    with pytest.raises(ValueError, match=message):
        validate_binary_labels(labels, row_count)


def test_xgboost_returns_deterministic_binary_probabilities() -> None:
    """Configured XGBoost fit/predict is deterministic and finite."""
    features, labels, _ = _classification_data()
    config = ModelConfig(
        danger_threshold=0.8,
        safe_threshold=0.2,
        calibration_method="sigmoid",
        xgb_n_estimators=12,
        xgb_max_depth=2,
    )
    first = build_xgb_estimator(seed=4, config=config).fit(features, labels)
    second = build_xgb_estimator(seed=4, config=config).fit(features, labels)
    probabilities = first.predict_proba(features)

    assert probabilities.shape == (len(features), 2)
    assert np.isfinite(probabilities).all()
    np.testing.assert_allclose(probabilities, second.predict_proba(features))


def test_group_calibrator_keeps_grouped_engine_folds() -> None:
    """Calibrator fits probability maps using engine-grouped cross-validation."""
    features, labels, engine_ids = _classification_data()
    config = ModelConfig(
        danger_threshold=0.8,
        safe_threshold=0.2,
        calibration_method="sigmoid",
        calibration_folds=3,
        xgb_n_estimators=8,
        xgb_max_depth=2,
    )

    calibrated = fit_group_calibrator(
        build_xgb_estimator(seed=8, config=config), features, labels, engine_ids, config
    )

    assert len(calibrated.calibrated_classifiers_) == 3
    risk = calibrated.predict_proba(features)[:, 1]
    assert np.isfinite(risk).all()
    assert ((risk >= 0) & (risk <= 1)).all()


def test_group_calibrator_rejects_too_few_engines() -> None:
    """Calibration fails instead of silently reducing the configured fold count."""
    features, labels, engine_ids = _classification_data()
    config = ModelConfig(
        danger_threshold=0.8,
        safe_threshold=0.2,
        calibration_method="sigmoid",
        calibration_folds=13,
    )

    with pytest.raises(ValueError, match="at least calibration_folds"):
        fit_group_calibrator(
            build_xgb_estimator(seed=8, config=config), features, labels, engine_ids, config
        )


def test_torch_estimator_fits_and_rejects_wrong_feature_count() -> None:
    """PyTorch MLP exposes probabilities and verifies prediction feature width."""
    features, labels, _ = _classification_data()
    model = TorchMLPClassifier(hidden_dims=(8,), epochs=3, batch_size=16, seed=9)
    model.fit(features, labels)
    probabilities = model.predict_proba(features[:4])

    assert probabilities.shape == (4, 2)
    assert np.isfinite(probabilities).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)
    with pytest.raises(ValueError, match="expected 2 features"):
        model.predict_proba(features[:4, :1])


def test_torch_estimator_rejects_nan_and_empty_features() -> None:
    """Malformed Torch inputs fail before model execution."""
    features, labels, _ = _classification_data()
    model = TorchMLPClassifier(hidden_dims=(4,), epochs=1)
    with pytest.raises(ValueError, match="must be finite"):
        model.fit(features.copy() * np.nan, labels)
    with pytest.raises(ValueError, match="at least one row"):
        model.fit(np.empty((0, 2)), np.empty((0,), dtype=np.int64))
