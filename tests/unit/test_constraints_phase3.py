"""Phase 3 bounds, taxonomy, and coupling behavior tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from prescriptxai.constraints.bounds import (
    check_rate_violations,
    project_feature_to_bounds,
    project_state_to_bounds,
    project_vector_to_bounds,
    raw_bounds_to_scaled,
    scaled_bounds_to_raw,
)
from prescriptxai.constraints.coupling import SensorCouplingModel, evaluate_rule
from prescriptxai.constraints.taxonomy import (
    ActuatorConstraint,
    CouplingRule,
    FeatureGroup,
    FeatureGroups,
    FeatureTaxonomy,
    load_taxonomy,
)
from prescriptxai.data.preprocess import fit_feature_scaler


@pytest.fixture(name="taxonomy")
def fixture_taxonomy() -> FeatureTaxonomy:
    """Load the C-MAPSS taxonomy and resolve its bounds on test-only telemetry."""
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    frame = _synthetic_coupling_frame()
    columns = tuple(name for name in taxonomy.feature_by_name() if name in frame.columns)
    return taxonomy.fit_training_bounds(frame, columns=columns)


def test_yaml_duplicate_feature_rejected() -> None:
    """Duplicate feature names fail taxonomy validation."""
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
                "bounds": {"minimum": 0.0, "maximum": 1.0},
            },
            {
                "name": "sensor_1",
                "label": "dup",
                "unit": "-",
                "cmapss_column": "s1",
                "group": "dependent",
                "bounds": {"minimum": 0.0, "maximum": 2.0},
            },
        ],
        "coupling_rules": [],
    }
    import yaml

    path = Path("tests/unit/_dup_features.yaml")
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="duplicate feature names"):
            load_taxonomy(path)
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.parametrize(
    "bounds, message",
    [
        ({"maximum": 1.0, "source": "manual"}, "minimum"),
        ({"minimum": 1.0, "maximum": 1.0, "source": "manual"}, "below maximum"),
    ],
)
def test_yaml_rejects_missing_or_invalid_physical_bounds(
    tmp_path: Path, bounds: dict[str, object], message: str
) -> None:
    """A feature must explicitly carry both valid manual or train-derived bounds."""
    import yaml

    payload = {
        "schema_version": 2,
        "dataset": "test",
        "bound_estimation": {
            "lower_percentile": 1,
            "upper_percentile": 99,
            "margin_fraction": 0.02,
            "degenerate_half_width": 0.000001,
        },
        "features": [
            {
                "name": "sensor_1",
                "label": "sensor",
                "unit": "-",
                "cmapss_column": "s1",
                "group": "dependent",
                "bounds": bounds,
            }
        ],
        "coupling_rules": [],
    }
    path = tmp_path / "invalid_features.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_taxonomy(path)


def test_bounds_projection_idempotent(taxonomy: FeatureTaxonomy) -> None:
    """Projecting twice does not further move values."""
    spec = taxonomy.feature_by_name()["sensor_12"]
    value = 600.0
    once = project_feature_to_bounds(value, spec)
    twice = project_feature_to_bounds(once, spec)
    assert once == pytest.approx(twice)


def test_rate_of_change_boundary(taxonomy: FeatureTaxonomy) -> None:
    """Allowed interval respects absolute actuator rate limits at the boundary."""
    constraint = taxonomy.actuator_constraints["sensor_12"]
    lower, upper = __import__(
        "prescriptxai.constraints.bounds", fromlist=["allowed_interval"]
    ).allowed_interval(520.0, constraint)
    assert lower <= 520.0 <= upper
    assert upper - lower <= 2 * constraint.max_change_per_step + 1e-9
    initial = {name: 520.0 for name in taxonomy.actuator_constraints}
    initial.update({
        "sensor_8": 2388.0,
        "sensor_9": 9100.0,
        "sensor_15": 8.45,
        "sensor_17": 392.0,
        "sensor_20": 38.7,
        "sensor_21": 23.2,
    })
    candidate = dict(initial)
    candidate["sensor_12"] = upper
    assert not check_rate_violations(
        initial, candidate, taxonomy
    )
    candidate["sensor_12"] = upper + 1e-4
    assert check_rate_violations(
        initial, candidate, taxonomy
    )


def test_raw_scaled_bound_round_trip() -> None:
    """Raw and scaled bound transforms invert each other."""
    mean, scale = 100.0, 5.0
    raw_min, raw_max = 90.0, 110.0
    scaled_min, scaled_max = raw_bounds_to_scaled(raw_min, raw_max, mean=mean, scale=scale)
    back_min, back_max = scaled_bounds_to_raw(scaled_min, scaled_max, mean=mean, scale=scale)
    assert (back_min, back_max) == pytest.approx((raw_min, raw_max))


def _synthetic_coupling_frame() -> pd.DataFrame:
    """Build a small frame with a deterministic controllable-to-dependent relationship."""
    rows = 80
    phi = np.linspace(520.0, 522.0, rows)
    bpr = np.linspace(8.4, 8.5, rows)
    t30 = 1500.0 + 0.8 * phi + 10.0 * bpr + np.random.default_rng(3).normal(0, 0.05, rows)
    return pd.DataFrame(
        {
            "engine_id": np.repeat([1, 2], rows // 2),
            "cycle": np.tile(np.arange(1, rows // 2 + 1), 2),
            "rul": np.linspace(120, 40, rows),
            "op_setting_1": 0.0,
            "op_setting_2": 0.0,
            "op_setting_3": 100.0,
            "sensor_12": phi,
            "sensor_15": bpr,
            "sensor_8": 2388.0,
            "sensor_9": 9100.0,
            "sensor_17": 392.0,
            "sensor_20": 38.7,
            "sensor_21": 23.2,
            "sensor_3": t30,
            "sensor_2": 642.0,
            "sensor_4": 1400.0,
            "sensor_6": 21.605,
            "sensor_7": 553.0,
            "sensor_11": 47.5,
            "sensor_13": 2388.0,
            "sensor_14": 8150.0,
        }
    )


def test_coupling_model_r2_and_propagation(taxonomy: FeatureTaxonomy) -> None:
    """Coupling fit reports R² and propagation updates only dependent sensors."""
    frame = _synthetic_coupling_frame()
    model = SensorCouplingModel.fit(
        frame,
        taxonomy,
        training_engine_ids=(1, 2),
        failure_horizon=30,
    )
    assert model.metrics.r2["sensor_3"] > taxonomy.coupling.min_r2  # type: ignore[union-attr]
    initial = frame.iloc[0].to_dict()
    initial["sensor_12"] = 521.0
    propagated = model.propagate(initial)
    assert propagated["sensor_12"] == pytest.approx(521.0)
    assert propagated["sensor_3"] != pytest.approx(initial["sensor_3"])
    assert propagated["op_setting_1"] == pytest.approx(initial["op_setting_1"])
    for name, value in initial.items():
        if name not in model.dependent_features:
            assert propagated[name] == value
    assert set(model.metrics.below_r2_floor) == {
        name for name, value in model.metrics.r2.items() if value < model.metrics.r2_floor
    }


def test_coupling_rules_pass_healthy_and_fail_inconsistent(taxonomy: FeatureTaxonomy) -> None:
    """A real healthy C-MAPSS sample passes, while a deliberately broken state fails."""
    import json

    healthy = json.loads(
        Path("tests/fixtures/cmapss_healthy_state.json").read_text(encoding="utf-8-sig")
    )
    healthy.pop("source")
    for rule in taxonomy.coupling_rules:
        assert evaluate_rule(healthy, rule).passed
    broken = {**healthy, "sensor_2": 1650.0}
    failed = [evaluate_rule(broken, rule) for rule in taxonomy.coupling_rules]
    assert any(not item.passed for item in failed)


def test_torch_propagation_runs(taxonomy: FeatureTaxonomy) -> None:
    """Differentiable propagation replaces dependent columns in torch tensors."""
    frame = _synthetic_coupling_frame()
    model = SensorCouplingModel.fit(
        frame,
        taxonomy,
        training_engine_ids=(1, 2),
        failure_horizon=30,
    )
    feature_names = tuple(frame.columns.intersection(taxonomy.feature_by_name()))
    module = model.propagate_torch_module(feature_names)
    base = torch.tensor([frame.iloc[0][name] for name in feature_names], dtype=torch.float64)
    base = base.unsqueeze(0)
    base.requires_grad_(True)
    output = module(base)
    loss = output.sum()
    loss.backward()
    assert base.grad is not None
    assert torch.isfinite(base.grad).all()


def test_scaled_torch_propagation_has_finite_control_gradients(
    taxonomy: FeatureTaxonomy,
) -> None:
    """Raw/scaled conversions preserve a differentiable proxy-to-dependent path."""
    frame = _synthetic_coupling_frame()
    model = SensorCouplingModel.fit(
        frame, taxonomy, training_engine_ids=(1, 2), failure_horizon=30
    )
    scaler = fit_feature_scaler(frame, model.feature_names)
    module = model.propagate_scaled_torch_module(scaler)
    scaled = torch.tensor(
        scaler.transform(frame.loc[:1, list(model.feature_names)]), dtype=torch.float32
    )
    scaled.requires_grad_(True)
    output = module(scaled)
    dependent_index = model.feature_names.index("sensor_3")
    output[:, dependent_index].sum().backward()
    control_index = model.feature_names.index("sensor_12")
    assert scaled.grad is not None
    assert torch.isfinite(scaled.grad).all()
    assert scaled.grad[:, control_index].abs().sum() > 0


def test_coupling_artifact_and_visual_diagnostics_round_trip(
    tmp_path: Path, taxonomy: FeatureTaxonomy
) -> None:
    """Fitted relations persist and emit inspectable fit-quality diagnostics."""
    from PIL import Image

    frame = _synthetic_coupling_frame()
    model = SensorCouplingModel.fit(
        frame, taxonomy, training_engine_ids=(1, 2), failure_horizon=30
    )
    restored = SensorCouplingModel.load(model.save(tmp_path / "coupling.joblib"))
    state = frame.iloc[0].to_dict()
    assert restored.propagate(state) == pytest.approx(model.propagate(state))
    html_path, png_path = restored.write_diagnostic_report(tmp_path / "fit", frame)
    assert "engine-grouped out-of-fold" in html_path.read_text(encoding="utf-8")
    with Image.open(png_path) as image:
        assert image.format == "PNG"
        assert image.size == (1100, 560)


@pytest.mark.parametrize("backend", ["gradient_boosting", "mlp"])
def test_nonlinear_coupling_backends_have_differentiable_surrogates(
    taxonomy: FeatureTaxonomy, backend: str
) -> None:
    """Nonlinear sklearn coupling backends are distilled to torch propagation modules."""
    frame = _synthetic_coupling_frame()
    assert taxonomy.coupling is not None
    coupling_config = taxonomy.coupling.model_copy(
        update={
            "backend": backend,
            "gradient_boosting_estimators": 3,
            "mlp_hidden_dims": (8,),
            "mlp_max_iter": 8,
            "torch_hidden_dims": (8,),
            "torch_epochs": 8,
        }
    )
    selected_taxonomy = taxonomy.model_copy(update={"coupling": coupling_config})
    model = SensorCouplingModel.fit(
        frame, selected_taxonomy, training_engine_ids=(1, 2), failure_horizon=30, seed=9
    )
    module = model.propagate_torch_module(model.feature_names)
    values = torch.tensor(
        [[frame.iloc[0][name] for name in model.feature_names]],
        dtype=torch.float64,
        requires_grad=True,
    )
    output = module(values)
    output[:, model.feature_names.index("sensor_3")].sum().backward()
    assert values.grad is not None
    assert torch.isfinite(values.grad).all()
    assert model.metrics.torch_surrogate_mae is not None
    assert np.isfinite(list(model.metrics.torch_surrogate_mae.values())).all()


def test_coupling_propagation_rejects_nonfinite_predictors(
    taxonomy: FeatureTaxonomy,
) -> None:
    """Invalid telemetry cannot enter fitted propagation silently."""
    frame = _synthetic_coupling_frame()
    model = SensorCouplingModel.fit(
        frame, taxonomy, training_engine_ids=(1, 2), failure_horizon=30
    )
    state = frame.iloc[0].to_dict()
    state["sensor_12"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        model.propagate(state)


def test_bound_vectors_projection_with_scaler(taxonomy: FeatureTaxonomy) -> None:
    """Vector projection respects per-feature raw bounds derived from taxonomy."""
    frame = _synthetic_coupling_frame()
    scaler = fit_feature_scaler(frame, ("sensor_12", "sensor_3"))
    bounds = __import__(
        "prescriptxai.constraints.taxonomy", fromlist=["bound_vectors"]
    ).bound_vectors(taxonomy, scaler)
    vector = np.array([600.0, 1200.0])
    projected = project_vector_to_bounds(vector, bounds)
    assert projected[0] == pytest.approx(bounds.raw_maximum[0])
    assert projected[1] == pytest.approx(bounds.raw_minimum[1])


def test_project_state_to_bounds_only_selected_features(taxonomy: FeatureTaxonomy) -> None:
    """State projection leaves unspecified keys untouched."""
    state = {"sensor_12": 600.0, "sensor_3": 1200.0}
    projected = project_state_to_bounds(state, taxonomy, features=("sensor_12",))
    assert projected["sensor_12"] < 600.0
    assert projected["sensor_3"] == 1200.0


def test_legacy_fixture_taxonomy_still_validates() -> None:
    """Synthetic recourse fixtures keep the legacy taxonomy schema."""
    taxonomy = FeatureTaxonomy(
        schema_version=1,
        dataset="unit-test-fixture",
        feature_groups=FeatureGroups(
            controllable_actuators=FeatureGroup(features=["actuator"]),
            immutable_operational=FeatureGroup(features=[]),
            immutable_environmental=FeatureGroup(features=[]),
            dependent_sensors=FeatureGroup(features=["sensor"]),
            context=FeatureGroup(features=[]),
        ),
        actuator_constraints={
            "actuator": ActuatorConstraint(minimum=-2.0, maximum=2.0, max_change_per_step=4.0)
        },
        coupling_rules=[
            CouplingRule(
                name="actuator_below_sensor",
                feature_a="actuator",
                feature_b="sensor",
                relation="less_than",
                tolerance=0.0,
            )
        ],
    )
    assert taxonomy.actuator_constraints["actuator"].maximum == 2.0


@pytest.mark.skipif(
    not Path("data/processed/FD001_train.csv").is_file(),
    reason="processed FD001 training CSV required",
)
def test_taxonomy_validates_on_real_fd001_feature_list(taxonomy: FeatureTaxonomy) -> None:
    """Repository taxonomy covers the real FD001 model feature list."""
    from prescriptxai.data.cmapss import to_model_frame

    frame = to_model_frame(pd.read_csv("data/processed/FD001_train.csv"))
    feature_names = (
        "op_setting_1",
        "op_setting_2",
        "sensor_2",
        "sensor_3",
        "sensor_4",
        "sensor_6",
        "sensor_7",
        "sensor_8",
        "sensor_9",
        "sensor_11",
        "sensor_12",
        "sensor_13",
        "sensor_14",
        "sensor_15",
        "sensor_17",
        "sensor_20",
        "sensor_21",
        "op_setting_3",
    )
    raw_taxonomy = load_taxonomy(Path("configs/features.yaml"))
    raw_taxonomy.validate_model_feature_coverage(feature_names)
    fitted_taxonomy = raw_taxonomy.fit_training_bounds(frame, columns=feature_names)
    fitted_taxonomy.validate_bounds_against_observed(frame, columns=feature_names)
    assert set(raw_taxonomy.feature_by_name()) >= set(feature_names)
