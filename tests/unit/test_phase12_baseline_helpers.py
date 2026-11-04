"""Regression-freeze verification must reject lost cases and relaxed numerical comparisons."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from fixtures.experiments import fitted_experiment
from prescriptxai.evaluation.experiments import ExperimentStore, QueryCase
from prescriptxai.evaluation.runner import make_cases, observed_alert_cohort, run_experiment_case
from prescriptxai.pipeline import PrescriptXAI


def helper_module() -> ModuleType:
    """Read the diagnostic helper without executing any scientific measurement."""
    spec = importlib.util.spec_from_file_location(
        "phase12_baseline", Path("scripts/diagnostics/phase12_baseline.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("expected", "actual", "matches"),
    [
        (0.2, 0.2000009, True),
        (0.2, 0.200002, False),
        (1000.0, 1000.00001, False),
        (True, 1, False),
        (False, True, False),
        (3, 3.0, False),
        (None, 0, False),
        ([0.5, True], [0.5, True], True),
        ({"risk": 0.5}, {"risk": 0.5, "extra": 1}, False),
        ([0.5], [], False),
        (0.5, float("nan"), False),
        (0.5, float("inf"), False),
    ],
)
def test_exact_discrete_absolute_only_comparison(
    expected: object, actual: object, matches: bool
) -> None:
    """No relative tolerance, integer coercion, NaN, or missing field may hide a change."""
    module = helper_module()
    assert (module.differences(expected, actual) == []) is matches


def test_portable_paths_preserve_numerical_settings_and_original_mapping() -> None:
    """Normalize path separators on a copy without retuning any setting."""
    module = helper_module()
    original = {"path": "artifacts\\profile\\model.joblib", "settings": [0.2, 8, True]}
    mapped = module.portable(original)
    assert mapped == {"path": "artifacts/profile/model.joblib", "settings": [0.2, 8, True]}
    assert original["path"] == "artifacts\\profile\\model.joblib"


def test_comparison_rejects_an_unsupported_value() -> None:
    """An unexpected type fails explicitly instead of becoming an implicit pass."""
    with pytest.raises(TypeError, match="Unsupported comparison"):
        helper_module().differences({1}, {1})


def checkpoint_case(tmp_path: Path) -> tuple[QueryCase, Path]:
    """Create one actual test-only solve, never a fabricated C-MAPSS result."""
    config, frame = fitted_experiment(tmp_path)
    alerts, contexts, _ = observed_alert_cohort(PrescriptXAI.from_config(config), frame)
    case = next(make_cases(
        config, tmp_path / "config.yaml", alerts, contexts,
        dataset="test_fixture", model="mlp", population="test", protocol="v1",
        variant="full", mode="fast", seeds=[config.seed], free_rate_fraction=1,
    ))
    output = tmp_path / "checkpoint"
    store = ExperimentStore(output, {"test_only": True})
    store.register_case(case)
    store.save(run_experiment_case(case))
    store.close()
    return case, output


@pytest.mark.parametrize(
    "mutation",
    ["case_id", "config_hash", "config_path", "group", "seed", "mode", "original", "tier3",
     "tier1", "settings", "registered_case", "foreign_case"],
)
def test_resume_rejects_identity_verdict_and_policy_corruption(
    tmp_path: Path, mutation: str
) -> None:
    """A schema-valid but swapped saved result/case must never bypass execution guards."""
    module = helper_module()
    case, output = checkpoint_case(tmp_path)
    store = ExperimentStore(output, {"test_only": True})
    encoded = store.connection.execute("SELECT payload FROM records").fetchone()[0]
    value = json.loads(encoded)
    if mutation == "registered_case":
        wrong = case.model_dump(mode="json")
        wrong["rul"] += 1
        store.connection.execute("UPDATE cases SET payload=?", (json.dumps(wrong),))
    elif mutation == "foreign_case":
        store.connection.execute(
            "INSERT INTO cases VALUES (?,?)", ("foreign", case.model_dump_json())
        )
    else:
        if mutation == "original":
            value["original"]["sensor_1"] += 0.5
        elif mutation == "tier3":
            value["tier3"] = not value["tier3"]
        elif mutation == "tier1":
            check = value["validation"]["tier1_model_safety"]
            check["passed"] = not check["passed"]
        elif mutation == "settings":
            value["solver_settings"]["max_iter"] += 1
        elif mutation == "seed":
            value["seed"] += 1
        elif mutation == "mode":
            value["mode"] = "THOROUGH"
        else:
            value[mutation] = "foreign"
        store.connection.execute("UPDATE records SET payload=?", (json.dumps(value),))
    store.connection.commit()
    store.close()
    with pytest.raises(ValueError, match="changed|foreign|inconsistent|settings"):
        module.run_cases([case], {"test_only": True}, output, resume=True)


@pytest.mark.parametrize("serialized", [False, True])
def test_resume_preserves_a_completed_actual_payload(tmp_path: Path, serialized: bool) -> None:
    """A compatible checkpoint returns the original full payload including every timing."""
    module = helper_module()
    case, output = checkpoint_case(tmp_path)
    store = ExperimentStore(output, {"test_only": True})
    original = json.loads(store.connection.execute("SELECT payload FROM records").fetchone()[0])
    store.close()
    cases = {case.case_id: case.model_dump_json()} if serialized else [case]
    assert module.run_cases(cases, {"test_only": True}, output, resume=True) == [original]


@pytest.mark.parametrize("mutation", ["source", "design", "asset", "code", "runtime"])
def test_finish_check_reads_current_files_and_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """Changed bytes or execution identity cannot receive a completed-study receipt."""
    module = helper_module()
    paths = {}
    for name in ("design", "historical_manifest", "database", "asset", "code"):
        path = tmp_path / name
        path.write_text("original bytes", encoding="utf-8")
        paths[name] = path
    manifest = {
        "source": "source-before", "design_path": str(paths["design"]),
        "design_sha256": module.file_hash(paths["design"]),
        "design": {"historical_manifest": str(paths["historical_manifest"]),
                   "historical_database": str(paths["database"])},
        "historical_manifest_sha256": module.file_hash(paths["historical_manifest"]),
        "historical_database_sha256": module.file_hash(paths["database"]),
        "input_hashes": {str(paths["asset"]): module.file_hash(paths["asset"])},
        "code_hashes": {str(paths["code"]): module.file_hash(paths["code"])},
        "runtime": {"version": "original"},
    }
    monkeypatch.setattr(module, "source_revision", lambda **_: "source-before")
    monkeypatch.setattr(module, "runtime_manifest", lambda: {"version": "original"})
    module.verify_unchanged(manifest)
    if mutation == "source":
        monkeypatch.setattr(module, "source_revision", lambda **_: "source-after")
    elif mutation == "runtime":
        monkeypatch.setattr(module, "runtime_manifest", lambda: {"version": "changed"})
    else:
        paths[mutation].write_text("changed bytes", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        module.verify_unchanged(manifest)
