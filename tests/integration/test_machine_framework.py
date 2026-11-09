"""Contracts for the registered archive and a generated synthetic machine."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from fastapi.testclient import TestClient
from typer.testing import CliRunner, Result

from prescriptxai.adapters.base import DatasetAdapter
from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import DEFAULT_MACHINE, MachineRegistry
from prescriptxai.adapters.tabular import TabularAdapter
from prescriptxai.api import create_app
from prescriptxai.cli import app
from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.core.data_quality import RecommendationWithheld, check_window
from prescriptxai.core.decision import MachineDecision, action_adherence
from prescriptxai.data.cmapss import load_cmapss_archive
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.machine_schema import (
    FeedbackRecord,
    MachineRecourseResult,
    migrate_recourse_result,
)
from prescriptxai.machine_spec import MachineSpec, load_machine_spec
from prescriptxai.machines import (
    FittedMachine,
    fit_machine,
    load_machine_decision,
    machine_settings,
    machine_taxonomy,
    record_feedback,
    save_machine_fit,
    scope_archive_runtime,
)
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import RecourseResult

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def toy(tmp_path_factory: pytest.TempPathFactory) -> DatasetAdapter:
    """Register a toy using only local YAML and generated CSV."""
    root = tmp_path_factory.mktemp("machines")
    machine = root / "configs/machines/toy"
    machine.mkdir(parents=True)
    path = root / "readings.csv"
    rows = pd.DataFrame(
        [
            (f"unit-{unit:02}", time, time + unit / 100, (unit % 3) / 10, 9 - time)
            for unit in range(18)
            for time in range(10)
        ],
        columns=["device", "tick", "setting", "ambient", "rul"],
    )
    rows.to_csv(path, index=False)
    default = MachineRegistry(ROOT / "configs/machines", ROOT).get(DEFAULT_MACHINE)
    spec = {
        "schema_version": 1,
        "machine_id": "toy",
        "display_name": "Synthetic contract machine",
        "unit_word": "unit",
        "unit_plural": "units",
        "data_source": "Generated CSV in the contract test",
        "license_note": "Synthetic test fixture",
        "synthetic": True,
        "dataset": {
            "adapter": "tabular",
            "path": "readings.csv",
            "unit_column": "device",
            "time_column": "tick",
            "remaining_life_column": "rul",
        },
        "features": [
            {
                "id": "feed",
                "column": "setting",
                "label": "Feed setting",
                "unit": "1",
                "role": "controllable",
                "bounds": {"minimum": 0, "maximum": 9.3, "source": "manual"},
                "step_limit": {"absolute": 9},
                "why": "Reduce the model input.",
            },
            {
                "id": "ambient",
                "column": "ambient",
                "label": "Ambient reading",
                "unit": "1",
                "role": "frozen",
                "bounds": {"minimum": 0, "maximum": 0.2, "source": "manual"},
                "why": "Observed reference only.",
            },
        ],
        "failure": {
            "horizon": 2,
            "label_source": "remaining_life",
            "tau_safe": 0.25,
            "tau_danger": 0.7,
        },
        "validation": {
            "plausibility": {"v1": 5},
            "bound_estimation": default.validation.bound_estimation.model_dump(),
            "rate_assumption": "One synthetic time step.",
            "intervention_steps": 1,
            "coupling_rules": [
                {
                    "name": "feed_above_reference",
                    "feature_a": "feed",
                    "feature_b": "ambient",
                    "relation": "greater_than",
                    "tolerance": 0.25,
                }
            ],
        },
        "quality": {
            "max_time_gap": 1,
            "stuck_window": 3,
            "stuck_tolerance": 0,
            "stuck_features": ["feed"],
        },
        "delta_min": 0.3,
        "k_max": 1,
        "latency_budgets": {
            name: item.model_dump() for name, item in default.latency_budgets.items()
        },
        "confirmation": {},
        "sentences": default.sentences.model_dump(),
    }
    (machine / "machine.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    return MachineRegistry(root / "configs/machines", root).open("toy")


@pytest.fixture(params=["archive", "toy"])
def adapter(request: pytest.FixtureRequest, toy: DatasetAdapter) -> DatasetAdapter:
    """Exercise the same loading, split and label contract for both machines."""
    if request.param == "archive":
        return MachineRegistry(ROOT / "configs/machines", ROOT).open(DEFAULT_MACHINE)
    return toy


def test_dataset_contract(adapter: DatasetAdapter) -> None:
    """Each split is exhaustive and labels follow the spec's horizon."""
    spec = adapter.spec
    rows = adapter.load()
    names = {feature.id for feature in spec.measurement_features}
    assert set(rows) >= {"unit_id", "time_index", *names}
    split = adapter.split(1729, frame=rows)
    train, validation, test = map(set, split.units)
    assert all((train, validation, test))
    assert not (train & validation or train & test or validation & test)
    assert train | validation | test == set(rows["unit_id"])
    assert adapter.split(1729, frame=rows).units == split.units
    remaining = adapter.remaining_life(frame=rows)
    expected = (remaining <= spec.failure.horizon).astype("int8")
    assert np.array_equal(adapter.failure_labels(spec.failure.horizon, frame=rows), expected)
    assert {0, 1} == set(expected)
    assert len(spec.spec_hash) == 64


def test_fd001_spec_keeps_legacy_numeric_configuration() -> None:
    """Keep source feature labels, bounds, rates and validation thresholds exact."""
    spec = load_machine_spec(ROOT / "configs/machines/cmapss_fd001/machine.yaml")
    legacy = load_taxonomy(ROOT / "configs/features.yaml")
    config = load_config(ROOT / "configs/default.yaml")
    projection = machine_taxonomy(spec)
    assert projection.features == tuple(item for item in legacy.features if item.group != "context")
    assert projection.coupling_rules == legacy.coupling_rules
    assert projection.coupling == legacy.coupling
    assert projection.bound_estimation == legacy.bound_estimation
    assert spec.failure.horizon == config.horizon_H
    assert (spec.failure.tau_safe, spec.failure.tau_danger) == (config.tau_safe, config.tau_danger)
    assert spec.validation.plausibility["v1"] == config.validation.mahalanobis_max
    assert spec.validation.plausibility["v2"] == 8.0
    assert spec.k_max == config.recourse.k_max
    assert spec.validation.intervention_steps == config.recourse.rate_horizon_steps
    assert spec.latency_budgets["FAST"] == config.latency_budget
    assert spec.latency_budgets["THOROUGH"] == config.latency_budget
    assert not spec.confirmation.confirmed
    packaged = ROOT / "src/prescriptxai/resources/machines/cmapss_fd001/machine.yaml"
    assert load_machine_spec(packaged) == spec


def test_archive_adapter_preserves_rows_and_uncapped_labels() -> None:
    """Compare the adapter with the direct archive parser and label function."""
    adapter = MachineRegistry(ROOT / "configs/machines", ROOT).open(DEFAULT_MACHINE)
    original = load_cmapss_archive(adapter.path, "FD001").train
    rows = adapter.load()
    assert np.array_equal(rows["sensor_12"], original["s12"])
    assert np.array_equal(rows["time_index"], original["cycle"])
    legacy = add_training_labels(original, None, adapter.spec.failure.horizon)
    assert np.array_equal(
        adapter.failure_labels(adapter.spec.failure.horizon, frame=rows), legacy["y"]
    )


@pytest.mark.parametrize(
    ("field", "values", "code"),
    [
        ("feed", [None, 2, 3], "missing_value"),
        ("feed", [float("nan"), 2, 3], "missing_value"),
        ("feed", [1, float("inf"), 3], "nonfinite_value"),
        ("feed", [1, 2, 11], "out_of_range"),
        ("feed", [2, 2, 2], "stuck_sensor"),
        ("time_index", [1, 2, 4], "time_gap"),
    ],
)
def test_quality_faults(
    toy: DatasetAdapter,
    field: str,
    values: list[float | None],
    code: str,
) -> None:
    """Injected input faults produce stable reasons before inference."""
    clean = pd.DataFrame({"time_index": [1, 2, 3], "feed": [1, 2, 3], "ambient": [0.1] * 3})
    assert check_window(clean, toy.spec) == ()
    fault = clean.assign(**{field: values})
    assert [(issue.code, issue.field) for issue in check_window(fault, toy.spec)] == [(code, field)]


@pytest.fixture(scope="module")
def trained_toy(toy: DatasetAdapter) -> FittedMachine:
    """Fit the real shared predictor once for the synthetic contract."""
    config = load_config(ROOT / "configs/default.yaml")
    config.model.xgb_n_estimators = 16
    config.model.torch_epochs = 5
    config.model.torch_hidden_dims = [8]
    config.model.torch_batch_size = 16
    return fit_machine(toy, config, "v1", "xgb")


def test_toy_training_scoring_and_fail_closed_recommendation(
    toy: DatasetAdapter,
    trained_toy: FittedMachine,
) -> None:
    """Use the real fitted toy predictor and withhold unconfirmed advice."""
    trained = trained_toy
    service = trained.decision()
    unit = toy.load().query("unit_id == 'unit-17'")
    healthy, high = unit.iloc[:3], unit.iloc[-3:]
    assert service.assess(high).risk > service.assess(healthy).risk
    observed = {"feed": float(high["feed"].iloc[-1]), "ambient": float(high["ambient"].iloc[-1])}
    direct = trained.training.bundle.predict_risk(pd.DataFrame([observed]))[0]
    assert service.assess(high).risk == direct
    with pytest.raises(RecommendationWithheld, match="limits not yet confirmed"):
        service.recommend(high)
    with pytest.raises(RecommendationWithheld, match="out_of_range"):
        service.recommend(high.assign(feed=100))
    assert action_adherence({"feed": 9.0}, {"feed": 5.0}, {"feed": 7.0}) == {"feed": 0.5}
    with pytest.raises(ValueError, match="unknown protocol"):
        MachineDecision(toy.spec, service._runtime, service.features, "missing")
    with pytest.raises(ValueError, match="unknown protocol"):
        machine_settings(toy.spec, trained.config, "missing")
    sequence = MachineDecision(toy.spec, service._runtime, service.features, "v1", history_rows=2)
    with pytest.raises(RecommendationWithheld, match="missing history"):
        sequence.assess(high.iloc[-1:])
    _, context = sequence._observed(high)
    assert len(context.history) == 2


def test_spec_validation_rejects_ambiguous_inputs(toy: DatasetAdapter) -> None:
    """Bad versions, partial confirmation and wrong column mappings fail at load."""
    document = toy.spec.model_dump(mode="python")
    with pytest.raises(ValueError, match="schema_version"):
        MachineSpec.model_validate({**document, "schema_version": 2})
    with pytest.raises(ValueError, match="limits confirmation"):
        MachineSpec.model_validate({**document, "confirmation": {"role": "reviewer"}})
    with pytest.raises(ValueError, match="collides"):
        MachineSpec.model_validate(
            {
                **document,
                "dataset": {**document["dataset"], "unit_column": "setting"},
            }
        )


def test_core_has_no_machine_specific_names() -> None:
    """Enforce the machine-free core source boundary."""
    forbidden = re.compile(
        r"(?i)(?<![a-z0-9])(?:c[-_]?mapss|fd00[1-4]|s(?:[1-9]|1[0-9]|2[01])|"
        r"sensor_[0-9]+|engine|turbofan|op_setting_[123])(?![a-z0-9])"
    )
    for file in (ROOT / "src/prescriptxai/core").glob("*.py"):
        assert forbidden.search(file.read_text(encoding="utf-8")) is None, file


def test_toy_offline_solver_validation_and_schema(
    toy: DatasetAdapter,
    trained_toy: FittedMachine,
) -> None:
    """Exercise actual bounded search without representing the fixture as approved advice."""
    runtime = trained_toy.decision()._runtime
    state = {"feed": 9.0, "ambient": 0.1}
    fast = runtime.recommend(state, None, "fast")
    thorough = runtime.recommend(state, None, "thorough")
    assert fast.alert and thorough.alert
    for result in (fast, thorough):
        assert result.new_state["ambient"] == state["ambient"]
        assert 0 <= result.new_state["feed"] <= 9.3
        assert abs(result.new_state["feed"] - state["feed"]) <= 9
        assert result.triage in {"RECOVERABLE", "PARTIAL", "ESCALATE"}
        if result.status == "RECOVERABLE":
            applied = runtime.validate_controls(
                state, {"feed": result.new_state["feed"]}, None, "fast"
            )
            assert applied.risk_after == result.risk_after
            assert applied.validation_report.joint == result.validation_report.joint
    assert fast.status == thorough.status == "RECOVERABLE"
    assert fast.validation_report.joint and thorough.validation_report.joint
    assert fast.action_features == thorough.action_features == ("feed",)
    migrated = migrate_recourse_result(fast.model_dump(mode="json"))
    assert migrated.schema_version == "3.0.0" and migrated.machine_id == DEFAULT_MACHINE
    assert migrated.spec_hash is None and migrated.validation_report == fast.validation_report
    scoped = MachineRecourseResult.from_decision(
        fast,
        machine_id=toy.spec.machine_id,
        spec_hash=toy.spec.spec_hash,
        protocol_version="v1",
        synthetic=True,
    )
    assert migrate_recourse_result(scoped.model_dump(mode="json")) == scoped
    service = trained_toy.decision()
    assert service._checked_result(fast) == scoped
    explanation = service._explanation(scoped)
    assert explanation.actions[0].startswith("Decrease Feed setting")
    assert explanation.verdict["joint"]
    with pytest.raises(RecommendationWithheld, match="Alerts only"):
        service.explain_result(scoped)
    with pytest.raises(RecommendationWithheld, match="withheld"):
        service._checked_result(runtime.validate_controls(state, {"feed": 9.0}, None, "fast"))
    frozen = json.loads(
        (ROOT / "docs/schemas/RecourseResult-2.0.0.json").read_text(encoding="utf-8")
    )
    assert RecourseResult.model_json_schema(mode="serialization") == frozen


def test_named_api_uses_toy_runtime(
    toy: DatasetAdapter,
    trained_toy: FittedMachine,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolve one isolated fitted model, score real rows, and refuse advice through HTTP."""
    monkeypatch.setenv("PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS", str(tmp_path))
    registry = MachineRegistry(toy.path.parent / "configs/machines", toy.path.parent)
    save_machine_fit(trained_toy, tmp_path)
    client = TestClient(
        create_app(
            config=load_config(ROOT / "configs/default.yaml"),
            registry=registry,
            machine_artifacts=tmp_path,
        )
    )
    machines = client.get("/machines").json()
    assert [machine["machine_id"] for machine in machines] == [DEFAULT_MACHINE, "toy"]
    assert machines[1]["synthetic"] and machines[1]["alerts_only"]
    rows = toy.load().query("unit_id == 'unit-17'").iloc[-3:].to_dict(orient="records")
    response = client.post("/machines/toy/assess", json={"rows": rows})
    assert response.status_code == 200, response.text
    score = response.json()
    assert score["risk"] == trained_toy.decision().assess(pd.DataFrame(rows)).risk
    assert score["spec_hash"] == toy.spec.spec_hash and score["synthetic"] is True
    assert score["machine_id"] == "toy" and score["protocol_version"] == "v1"
    assert client.post("/machines/unknown/assess", json={"rows": rows}).status_code == 404
    assert (
        client.post(
            "/machines/toy/assess",
            json={"rows": rows, "protocol_version": "unknown"},
        ).status_code
        == 503
    )
    assert (
        client.post(
            "/machines/toy/assess",
            json={"rows": [{"time_index": 1, "feed": 100, "ambient": 0.1}]},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/machines/toy/validate-controls",
            json={"rows": rows, "controls": {"feed": True}},
        ).status_code
        == 422
    )
    preview = client.post(
        "/machines/toy/validate-controls",
        json={"rows": rows, "controls": {"feed": 5}},
    )
    assert preview.status_code == 422 and "Alerts only" in preview.json()["detail"]
    scoped = trained_toy.decision()._scoped(
        trained_toy.decision()._runtime.recommend({"feed": 9.0, "ambient": 0.1}, None, "fast")
    )
    follow_up = client.post(
        "/machines/toy/feedback",
        json={
            "rows": rows,
            "result": scoped.model_dump(mode="json"),
            "applied": {"feed": 5},
        },
    )
    assert follow_up.status_code == 422 and "Alerts only" in follow_up.json()["detail"]
    response = client.post("/machines/toy/recommend", json={"rows": rows})
    assert response.status_code == 422 and "limits not yet confirmed" in response.json()["detail"]
    rows[-1]["feed"] = 100.0
    response = client.post("/machines/toy/recommend", json={"rows": rows})
    assert response.status_code == 422 and "out_of_range" in response.json()["detail"]


def test_named_cli_quality_uses_registry(
    toy: DatasetAdapter,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validate a local machine through the CLI and reject a bad window."""
    monkeypatch.chdir(toy.path.parent)
    window = tmp_path / "window.json"
    window.write_text('{"time_index": 1, "feed": 1, "ambient": 0.1}', encoding="utf-8")
    result = CliRunner().invoke(app, ["--machine", "toy", "check", str(window)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["quality"] == "pass"
    window.write_text('{"time_index": 1, "feed": 99, "ambient": 0.1}', encoding="utf-8")
    result = CliRunner().invoke(app, ["--machine", "toy", "check", str(window)])
    assert result.exit_code != 0 and "Recommendation withheld" in result.output


def test_archive_scoped_score_and_alerts_only() -> None:
    """Reuse real retained FD001 artifacts while enforcing the named machine policy."""
    adapter = MachineRegistry(ROOT / "configs/machines", ROOT).open(DEFAULT_MACHINE)
    rows = adapter.load().iloc[:3]
    legacy = PrescriptXAI.from_config(ROOT / "configs/default.yaml")
    scoped = scope_archive_runtime(adapter.spec, "v1", legacy)
    state = {
        feature.id: float(rows[feature.id].iloc[-1])
        for feature in adapter.spec.measurement_features
    }
    assert scoped.assess(rows).risk == legacy.assess(state).risk
    with pytest.raises(RecommendationWithheld, match="Alerts only"):
        scoped.recommend(rows)


def test_parquet_and_event_labels(
    toy: DatasetAdapter,
    tmp_path: Path,
) -> None:
    """Use the same canonical fields for Parquet and reject incomplete event trajectories."""
    csv = pd.read_csv(toy.path)
    csv["broken"] = (csv["rul"] == 0).astype(int)
    data = tmp_path / "data.parquet"
    csv.to_parquet(data)
    spec_doc = toy.spec.model_dump(mode="python")
    spec_doc["dataset"].update(
        {
            "path": data.name,
            "remaining_life_column": None,
            "event_column": "broken",
        }
    )
    spec_doc["failure"]["label_source"] = "terminal_event"
    tabular = TabularAdapter(MachineSpec.model_validate(spec_doc), tmp_path)
    loaded = tabular.load()
    assert tabular.failure_labels(2, frame=loaded).equals(toy.failure_labels(2))
    with pytest.raises(ValueError, match="terminal failure"):
        tabular.failure_labels(2, frame=loaded.assign(event=0))
    csv.loc[1, "tick"] = csv.loc[0, "tick"]
    csv.to_parquet(data)
    with pytest.raises(ValueError, match="duplicate"):
        tabular.load()


def test_synthetic_feedback_uses_actual_validation(
    trained_toy: FittedMachine,
    tmp_path: Path,
) -> None:
    """Measure and persist explicitly simulated feedback without issuing a prescription."""
    service = trained_toy.decision()
    state = {"feed": 9.0, "ambient": 0.1}
    rows = pd.DataFrame([{"time_index": 9, **state}])
    runtime = service._runtime
    computed = runtime.recommend(state, None, "fast")
    scoped = service._scoped(computed)
    applied = {"feed": scoped.new_state["feed"]}
    with pytest.raises(RecommendationWithheld, match="Alerts only"):
        service.feedback(rows, scoped, applied, "simulated_operator")
    feedback = service._measure_feedback(rows, scoped, applied, "simulated_operator")
    assert feedback.machine_id == "toy" and feedback.synthetic
    assert feedback.source == "simulated_operator"
    assert feedback.adherence == 1.0 and all(feedback.applied_tier_passes.values())
    assert feedback.applied_risk == scoped.risk_after
    log = tmp_path / "feedback.sqlite3"
    record_feedback(feedback, log)
    with sqlite3.connect(log) as db:
        payload = db.execute("SELECT payload FROM feedback").fetchone()[0]
    assert FeedbackRecord.model_validate_json(payload) == feedback
    with pytest.raises(ValueError, match="observed values differ"):
        service._measure_feedback(rows.assign(feed=8), scoped, applied, "simulated_operator")
    with pytest.raises(ValueError, match="provenance"):
        service._measure_feedback(
            rows, scoped.model_copy(update={"machine_id": "other"}), applied, "simulated_operator"
        )


@pytest.mark.parametrize(
    ("section", "changes", "message"),
    [
        ("failure", {"tau_safe": 0.9}, "less than"),
        ("dataset", {"unit_column": "tick"}, "distinct"),
        ("dataset", {"subset": "FD001"}, "subset"),
        ("dataset", {"split_fractions": [0.1, 0.1, 0.1]}, "sum"),
        ("dataset", {"remaining_life_column": None}, "label source"),
        ("validation", {"plausibility": {"v1": 0}}, "plausibility limit"),
        ("quality", {"stuck_features": ["unknown"]}, "stuck checks"),
    ],
)
def test_nested_policy_errors(
    toy: DatasetAdapter,
    section: str,
    changes: dict[str, object],
    message: str,
) -> None:
    """Reject invalid threshold, labeling, window and split policies at load time."""
    document = toy.spec.model_dump(mode="python")
    document[section].update(changes)
    with pytest.raises(ValueError, match=message):
        MachineSpec.model_validate(document)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"step_limit": None}, "requires a step limit"),
        ({"role": "frozen"}, "has a control policy"),
        ({"legacy_group": "context"}, "legacy group disagree"),
        ({"bounds": {"minimum": 0, "maximum": float("inf")}}, "bounds must be finite"),
        ({"id": "time_index"}, "metadata field"),
    ],
)
def test_invalid_feature_policy(
    toy: DatasetAdapter,
    changes: dict[str, object],
    message: str,
) -> None:
    """Reject unsafe bounds, missing rates and metadata collisions."""
    document = toy.spec.model_dump(mode="python")
    first, second = document["features"]
    document["features"] = [{**first, **changes}, second]
    with pytest.raises(ValueError, match=message):
        MachineSpec.model_validate(document)


@pytest.mark.parametrize(
    ("rows", "code"),
    [
        (pd.DataFrame(), "missing_value"),
        (pd.DataFrame([[1, 2]], columns=["time_index", "time_index"]), "missing_value"),
        (pd.DataFrame({"time_index": [1, 2], "unit_id": ["a", "b"]}), "missing_value"),
        (pd.DataFrame({"feed": [1], "ambient": [0.1]}), "missing_value"),
        (
            pd.DataFrame({"time_index": [float("inf")], "feed": [1], "ambient": [0.1]}),
            "nonfinite_value",
        ),
        (pd.DataFrame({"time_index": [1], "feed": [True], "ambient": [0.1]}), "nonfinite_value"),
    ],
)
def test_window_structure(toy: DatasetAdapter, rows: pd.DataFrame, code: str) -> None:
    """Identify invalid window structure before scoring."""
    assert check_window(rows, toy.spec)[0].code == code


def test_named_cli_runs_data_to_score(
    toy: DatasetAdapter,
    trained_toy: FittedMachine,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run local named commands against real synthetic rows and fitted artifacts."""
    monkeypatch.chdir(toy.path.parent)
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump(trained_toy.config.model_dump(mode="json")), encoding="utf-8")
    window = tmp_path / "window.json"
    window.write_text('{"time_index": 9, "feed": 9, "ambient": 0.1}', encoding="utf-8")
    runner = CliRunner()

    def invoke(*command: str) -> Result:
        return runner.invoke(app, ["--machine", "toy", *command])

    ready = invoke("data", "prepare", "--config", str(config))
    assert ready.exit_code == 0, ready.output
    prepared = json.loads(ready.stdout)
    assert prepared["rows"] == 180 and sum(prepared["units_per_partition"]) == 18
    download = invoke("data", "download", "--config", str(config))
    assert download.exit_code != 0 and "provide local tabular" in download.output
    trained = invoke("train", "--config", str(config))
    assert trained.exit_code == 0, trained.output
    info = invoke("info")
    assert info.exit_code == 0 and json.loads(info.stdout)["alerts_only"]
    result = invoke("assess", str(window))
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["synthetic"]
    withheld = invoke("recommend", str(window))
    assert withheld.exit_code != 0 and "Alerts only" in withheld.output
    bad_window = tmp_path / "invalid.json"
    bad_window.write_text("[]", encoding="utf-8")
    invalid = invoke("assess", str(bad_window))
    assert invalid.exit_code != 0 and "nonempty list" in invalid.output
    missing = invoke("assess")
    assert missing.exit_code != 0 and "provide a JSON window" in missing.output
    unsupported = invoke("batch")
    assert unsupported.exit_code != 0 and "requires the legacy workflow" in unsupported.output
    bad_machine = runner.invoke(app, ["--machine", "missing", "info"])
    assert bad_machine.exit_code != 0 and "unknown machine" in bad_machine.output


def test_official_test_labels_use_archive_remaining_life() -> None:
    """Use official remaining life rather than labeling truncated trajectories as failures."""
    archive = MachineRegistry(ROOT / "configs/machines", ROOT).open(DEFAULT_MACHINE)
    assert isinstance(archive, CmapssAdapter)
    rows = archive.load_official()
    last = rows.groupby("unit_id", sort=False).tail(1)
    legacy = load_cmapss_archive(archive.path, "FD001")
    assert last["remaining_life"].tolist() == legacy.test_rul["rul"].tolist()
    assert (rows["failure_label"] == (rows["remaining_life"] <= archive.spec.failure.horizon)).all()


def test_artifact_fingerprints_refuse_modified_or_partial_fit(
    trained_toy: FittedMachine,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve the loaded-model boundary when a fitted file is replaced."""
    monkeypatch.setenv("PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS", str(tmp_path))
    directory = save_machine_fit(trained_toy, tmp_path)
    assert load_machine_decision(trained_toy.spec, "v1", tmp_path).spec == trained_toy.spec
    manifest = directory / "complete.json"
    saved = json.loads(manifest.read_text(encoding="utf-8"))
    malformed = {**saved, "files": {}}
    manifest.write_text(json.dumps(malformed), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest is incomplete"):
        load_machine_decision(trained_toy.spec, "v1", tmp_path)
    manifest.write_text(json.dumps(saved), encoding="utf-8")
    with (directory / "model.joblib").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="changed after fingerprinting"):
        load_machine_decision(trained_toy.spec, "v1", tmp_path)
