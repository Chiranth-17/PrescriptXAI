"""Taxonomy validation tests."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from prescriptxai.constraints.taxonomy import (
    FeatureTaxonomy,
    bound_vectors,
    classification_masks,
    load_taxonomy,
)
from prescriptxai.data.preprocess import fit_feature_scaler


def test_features_yaml_loads_with_controllable_proxies_and_coupling_rules() -> None:
    """Default C-MAPSS taxonomy classifies FD001 channels and marks controllable proxies."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))

    assert taxonomy.feature_groups.controllable_actuators.features
    assert taxonomy.coupling_rules
    assert taxonomy.coupling is not None
    proxies = [spec for spec in taxonomy.features if spec.controllable_proxy]
    assert proxies
    assert all(spec.proxy_note for spec in proxies)
    assert {spec.name for spec in proxies} == {
        "sensor_8",
        "sensor_9",
        "sensor_12",
        "sensor_15",
        "sensor_17",
        "sensor_20",
        "sensor_21",
    }
    for index in range(1, 22):
        assert taxonomy.feature_by_name()[f"sensor_{index}"].cmapss_column == f"s{index}"
    assert taxonomy.feature_groups.immutable_operational.features == [
        "op_setting_1",
        "op_setting_2",
        "op_setting_3",
    ]


def test_overlapping_feature_groups_are_rejected() -> None:
    """A feature cannot be controllable and immutable at once."""
    with pytest.raises(ValidationError, match="features must appear once"):
        FeatureTaxonomy.model_validate(
            {
                "schema_version": 1,
                "dataset": "test",
                "feature_groups": {
                    "controllable_actuators": {"features": ["x"]},
                    "immutable_operational": {"features": ["x"]},
                    "immutable_environmental": {"features": []},
                    "dependent_sensors": {"features": []},
                    "context": {"features": []},
                },
                "actuator_constraints": {
                    "x": {"minimum": 0, "maximum": 1, "max_change_per_step": 0.1}
                },
                "coupling_rules": [],
            }
        )


def test_unknown_coupling_feature_is_rejected() -> None:
    """Coupling rules may only reference known telemetry fields."""
    raw = {
        "schema_version": 1,
        "dataset": "test",
        "feature_groups": {
            "controllable_actuators": {"features": []},
            "immutable_operational": {"features": []},
            "immutable_environmental": {"features": []},
            "dependent_sensors": {"features": ["sensor_a"]},
            "context": {"features": []},
        },
        "actuator_constraints": {},
        "coupling_rules": [
            {
                "name": "bad",
                "feature_a": "sensor_a",
                "feature_b": "unknown",
                "relation": "less_than",
                "tolerance": 0,
            }
        ],
    }

    with pytest.raises(ValidationError, match="references an unknown feature"):
        FeatureTaxonomy.model_validate(raw)


def test_v2_yaml_rejects_min_not_below_max() -> None:
    """Feature bounds must define a nonempty interval."""
    payload = {
        "schema_version": 2,
        "dataset": "test",
        "features": [
            {
                "name": "sensor_1",
                "label": "s1",
                "unit": "-",
                "cmapss_column": "s1",
                "group": "dependent",
                "bounds": {"minimum": 2.0, "maximum": 1.0},
            }
        ],
        "coupling_rules": [],
    }
    with pytest.raises(ValidationError, match="minimum must be below maximum"):
        load_taxonomy_from_dict(payload)


def test_masks_align_with_configured_groups() -> None:
    """Classification masks follow the configured taxonomy groups."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    feature_names = (
        "op_setting_1",
        "sensor_12",
        "sensor_3",
    )
    masks = classification_masks(taxonomy, feature_names)
    assert masks.controllable.tolist() == [False, True, False]
    assert masks.frozen.tolist() == [True, False, False]
    assert masks.dependent.tolist() == [False, False, True]


def test_bound_vectors_round_trip_raw_scaled() -> None:
    """Raw/scaled bound conversion is consistent with the training scaler."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    training = pd.DataFrame(
        {
            "engine_id": [1] * 8,
            "op_setting_1": np.linspace(-0.004, 0.004, 8),
            "sensor_12": np.linspace(520, 522, 8),
            "sensor_3": np.linspace(1580, 1600, 8),
        }
    )
    scaler = fit_feature_scaler(training, tuple(training.columns))
    taxonomy = taxonomy.fit_training_bounds(
        training, columns=("op_setting_1", "sensor_12", "sensor_3")
    )
    bounds = bound_vectors(taxonomy, scaler)
    for index, _name in enumerate(bounds.feature_names):
        mean = scaler.scaler.mean_[index]
        scale = scaler.scaler.scale_[index]
        scaled_min = (bounds.raw_minimum[index] - mean) / scale
        scaled_max = (bounds.raw_maximum[index] - mean) / scale
        assert bounds.scaled_minimum[index] == pytest.approx(min(scaled_min, scaled_max))
        assert bounds.scaled_maximum[index] == pytest.approx(max(scaled_min, scaled_max))


def test_training_percentile_bounds_use_configured_margin() -> None:
    """Automatic bounds are computed from train percentiles and their configured margin."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    training = pd.DataFrame(
        {
            "op_setting_1": np.arange(100, dtype=float),
            "sensor_12": np.arange(100, dtype=float),
        }
    )
    fitted = taxonomy.fit_training_bounds(
        training, columns=("op_setting_1", "sensor_12")
    )
    spec = fitted.feature_by_name()["sensor_12"]
    expected = np.percentile(training["sensor_12"], [1.0, 99.0])
    margin = (expected[1] - expected[0]) * 0.02
    assert spec.bounds.minimum == pytest.approx(expected[0] - margin)
    assert spec.bounds.maximum == pytest.approx(expected[1] + margin)


def test_manual_bounds_outside_observed_range_plus_margin_are_rejected() -> None:
    """Explicit bounds cannot silently extend far beyond the training operating range."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    training = pd.DataFrame({"sensor_12": np.linspace(10.0, 20.0, 50)})
    manual = taxonomy.with_resolved_bounds({"sensor_12": (-100.0, 100.0)})
    with pytest.raises(ValueError, match="observed training range plus margin"):
        manual.validate_bounds_against_observed(training, columns=("sensor_12",))


def load_taxonomy_from_dict(payload: dict[str, object]) -> FeatureTaxonomy:
    """Exercise YAML-less taxonomy validation paths in tests."""
    import yaml

    path = Path("tests/unit/_tmp_features.yaml")
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    try:
        return load_taxonomy(path)
    finally:
        path.unlink(missing_ok=True)
