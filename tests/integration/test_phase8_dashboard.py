"""AppTest exercises real model decisions, widgets, failure rendering and all pages."""

import ast
import json
from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

from fixtures.operator_artifacts import write_operator_fixture
from fixtures.operator_evidence import write_operator_evidence
from fixtures.recourse_models import make_recourse_fixture
from prescriptxai.config import load_config
from prescriptxai.dashboard.pages import PAGES
from prescriptxai.dashboard.state import load_settings
from prescriptxai.models.registry import load_model_bundle
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import RecourseResult
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, save_mahalanobis_validator

APP = Path("src/prescriptxai/dashboard/app.py").resolve()


@pytest.fixture
def operator_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fit actual portable artifacts once for each independent widget workflow."""
    settings = write_operator_fixture(tmp_path)
    monkeypatch.setenv("PRESCRIPTXAI_DASHBOARD_CONFIG", str(settings))
    return settings


def test_operator_selection_risk_solve_slider_and_exports(operator_settings: Path) -> None:
    """Engine/cycle edits change live scores; manual edits re-run every tier and reset safely."""
    app = AppTest.from_file(str(APP), default_timeout=40).run()
    assert not app.exception and not app.error, [v.value for v in app.error]
    initial = app.metric[0].value
    service = PrescriptXAI.from_config(
        next(iter(load_settings(operator_settings).profiles["FD001"].values()))
    )
    assert any(service.config_hash in item.value for item in app.caption)
    assert any(service.model_version in item.value for item in app.caption)
    app.selectbox(key="engine").set_value(8).run()
    assert not app.exception and app.metric[0].value != initial
    assert app.warning and any("ALERT" in v.value for v in app.warning)
    app.button(key="recommend").click().run()
    assert not app.exception and not app.error
    solved = RecourseResult.model_validate_json(app.session_state["solver_result"])
    assert solved.status == "RECOVERABLE"
    assert len(app.slider) == 2  # Replay cycle plus one genuinely recommended control.
    assert len(app.get("download_button")) == 3
    app.slider(key="control:actuator").set_value(-2.0).run()
    assert not app.exception
    preview = RecourseResult.model_validate_json(app.session_state["preview_result"])
    assert preview.risk_after != solved.risk_after and preview.status == "ESCALATE"
    assert any("ESCALATE" in v.value for v in app.error)
    app.slider(key="cycle").set_value(1).run()
    assert not app.exception
    assert "solver_result" not in app.session_state
    assert app.metric[0].value == initial


@pytest.mark.parametrize("page", PAGES[1:])
def test_every_page_loads_with_explicit_missing_evidence(
    operator_settings: Path, page: str
) -> None:
    """Absent measured sources are honestly unavailable; every page remains usable."""
    app = AppTest.from_file(str(APP), default_timeout=40).run()
    app.radio(key="page").set_value(page).run()
    assert not app.exception
    assert any(page == header.value for header in app.header)
    if page == "Fleet Overview":
        assert len(app.dataframe[0].value) == 2
        assert set(app.dataframe[0].value.triage) == {"Not assessed"}
        app.selectbox(key="fleet_engine").set_value(8).run()
        app.button(key="fleet_recommend").click().run()
        assert not app.exception
        assert app.radio(key="page").value == PAGES[0]
        assert (
            RecourseResult.model_validate_json(app.session_state["solver_result"]).status
            == "RECOVERABLE"
        )
    elif page != "About and Limitations":
        assert app.warning and "unavailable" in app.warning[-1].value


def render_triage(result_json: str) -> None:
    """Render an actual public result through the shared operator banner component."""
    from prescriptxai.dashboard.operator import triage_banner
    from prescriptxai.schemas import RecourseResult

    triage_banner(RecourseResult.model_validate_json(result_json))


def test_all_triage_states_render_actual_fitted_predictions(operator_settings: Path) -> None:
    """No forged result labels: generate RECOVERABLE/PARTIAL/ESCALATE/NO_INTERVENTION live."""
    settings = load_settings(operator_settings)
    profile = next(iter(settings.profiles["FD001"].values()))
    service = PrescriptXAI.from_config(profile)
    state = {"actuator": -2.0, "sensor": 2.0}
    solved = service.recommend(state)
    lower, upper = -2.0, 2.0
    for _ in range(45):
        midpoint = (lower + upper) / 2
        risk = service.assess({**state, "actuator": midpoint}).risk
        if risk > 0.4:
            lower = midpoint
        else:
            upper = midpoint
    partial = service.validate_controls(state, {"actuator": (lower + upper) / 2})
    failure = service.validate_controls(state, {"actuator": 100.0})
    safe = service.recommend({"actuator": 2.0, "sensor": 2.0})
    assert [r.status for r in (solved, partial, failure, safe)] == [
        "RECOVERABLE",
        "PARTIAL",
        "ESCALATE",
        "NO_INTERVENTION",
    ]
    for result in (solved, partial, failure, safe):
        app = AppTest.from_function(render_triage, args=(result.model_dump_json(),)).run()
        assert not app.exception
        assert any(
            result.status in item.value
            for item in [*app.success, *app.warning, *app.error, *app.info]
        )


def test_empty_corrupt_source_is_an_operator_error(operator_settings: Path) -> None:
    """Invalid telemetry is an actionable message rather than a raw Streamlit traceback."""
    settings = load_settings(operator_settings)
    settings.telemetry_path.write_text("engine_id,cycle,actuator,sensor\n", encoding="utf-8")
    app = AppTest.from_file(str(APP), default_timeout=40).run()
    assert not app.exception and app.error
    assert "Operator request unavailable" in app.error[0].value


@pytest.mark.parametrize("page", PAGES[2:4])
def test_evidence_pages_display_actual_saved_fixture_records(
    operator_settings: Path, page: str
) -> None:
    """Save actual computed fixture outcomes, then compare displayed measured values/engine CIs."""
    summary = write_operator_evidence(operator_settings)
    app = AppTest.from_file(str(APP), default_timeout=40).run()
    app.radio(key="page").set_value(page).run()
    assert not app.exception and not app.error
    assert app.dataframe and app.get("plotly_chart") if page == PAGES[2] else app.dataframe
    if page == PAGES[3]:
        table = app.dataframe[0].value
        group = next(iter(summary["groups"].values()))
        actual = group["metrics"]["validity"]["ci"]["estimate"]
        assert set(table.loc[table.metric == "validity", "measured"]) == {actual}
        assert set(table.engines) == {group["engines"]}


def test_protocol_curves_and_ladder_do_not_mix_saved_groups(operator_settings: Path) -> None:
    """Evaluate both fixture D_max profiles, then retain only the explicitly selected protocol."""
    summary = write_operator_evidence(operator_settings)
    settings = load_settings(operator_settings)
    config = load_config(next(iter(settings.profiles["FD001"].values())))
    bundle = load_model_bundle(config.artifacts.model)
    _, _, training = make_recourse_fixture()
    config.validation.mahalanobis_max = 8.0
    config.artifacts.mahalanobis = config.paths.mahalanobis = (
        operator_settings.parent / "validator-v2.joblib"
    )
    save_mahalanobis_validator(
        fit_mahalanobis_validator(training, bundle, bundle.training_engine_ids, config),
        config.artifacts.mahalanobis,
    )
    profile = operator_settings.parent / "pipeline-v2.yaml"
    profile.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    alternate = settings.model_copy(deep=True)
    alternate.profiles = {"FD001": {"Fixture MLP / v2": profile}}
    alternate_path = operator_settings.parent / "dashboard-v2.yaml"
    alternate_path.write_text(yaml.safe_dump(alternate.model_dump(mode="json")), encoding="utf-8")
    second = write_operator_evidence(alternate_path, "v2", write=False)
    summary["groups"].update(second["groups"])
    (settings.report_directory / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    app = AppTest.from_file(str(APP), default_timeout=40).run()
    app.radio(key="page").set_value(PAGES[2]).run()
    assert not app.exception
    assert set(app.dataframe[-1].value.protocol) == {"v1"}
    assert len(app.dataframe[-1].value) == 1
    assert app.selectbox(key="ladder_metric")
    group = "FD001/mlp/v2/fixture_observations/fast/full"
    app.selectbox(key="diagnostic_group").set_value(group).run()
    assert not app.exception
    assert set(app.dataframe[-1].value.protocol) == {"v2"}
    assert set(app.dataframe[-1].value.D_max) == {"8.0"}


def test_fleet_handoff_preserves_cycle_across_unequal_lifetimes(operator_settings: Path) -> None:
    """Selecting a ranked engine must solve the ranked cycle, not that engine's last cycle."""
    import pandas as pd

    settings = load_settings(operator_settings)
    frame = pd.read_csv(settings.telemetry_path)
    added = frame.loc[frame.engine_id == 8].iloc[-1:].copy()
    added["cycle"] = 4
    pd.concat([frame, added], ignore_index=True).to_csv(settings.telemetry_path, index=False)
    app = AppTest.from_file(str(APP), default_timeout=40).run()
    app.slider(key="cycle").set_value(2).run()
    app.radio(key="page").set_value(PAGES[1]).run()
    app.selectbox(key="fleet_engine").set_value(8).run()
    app.button(key="fleet_recommend").click().run()
    assert not app.exception
    assert app.selectbox(key="engine").value == 8
    assert app.slider(key="cycle").value == 2
    result = RecourseResult.model_validate_json(app.session_state["solver_result"])
    assert result.original_state["actuator"] == float(
        frame.loc[(frame.engine_id == 8) & (frame.cycle == 2), "actuator"].iloc[0]
    )


def test_ui_source_has_no_embedded_measured_results() -> None:
    """Reject historic illustrative/results literals and imports of fitting experiment modules."""
    source = "\n".join(path.read_text(encoding="utf-8") for path in APP.parent.glob("*.py"))
    for forbidden in ("0.88", "0.17", "3.2%", "1.1%", "55.8201", "2339.074", "import models.train"):
        assert forbidden not in source
    for path in APP.parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                assert node.value not in {0.8, 0.2, 0.95, 0.9}, path
