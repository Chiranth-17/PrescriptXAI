"""Taxonomy validation tests."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from prescriptxai.constraints.taxonomy import FeatureTaxonomy, load_taxonomy


def test_features_yaml_loads_with_no_unverified_actuators() -> None:
    """Default C-MAPSS taxonomy does not infer actuator status from telemetry."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))

    assert taxonomy.feature_groups.controllable_actuators.features == []
    assert taxonomy.actuator_constraints == {}
    assert taxonomy.coupling_rules == []


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
