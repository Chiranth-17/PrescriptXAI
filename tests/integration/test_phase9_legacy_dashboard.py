"""Legacy public rendering helpers retain actual measured risks and reject diagnostic actions."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from fixtures.operator_artifacts import write_operator_fixture
from prescriptxai.dashboard.charts import delta_chart, risk_comparison_chart
from prescriptxai.pipeline import PrescriptXAI


def render_actual_legacy(profile: str, state: dict[str, float]) -> None:
    """Render an actual solver result, with all imports in the AppTest function scope."""
    from prescriptxai.dashboard.components import show_recommendation
    from prescriptxai.pipeline import PrescriptXAI

    service = PrescriptXAI.from_config(profile)
    show_recommendation(
        service.engine.recommend(state), service.config.tau_danger, service.config.tau_safe
    )


@pytest.mark.parametrize("actuator,sensor", [(-2.0, 2.0), (-2.0, 100.0), (2.0, 2.0)])
def test_legacy_components_render_real_success_failure_and_no_changes(
    tmp_path: Path,
    actuator: float,
    sensor: float,
) -> None:
    """Keep pure chart code in coverage and inspect risk thresholds and actual raw deltas."""
    write_operator_fixture(tmp_path)
    profile = tmp_path / "pipeline.yaml"
    service = PrescriptXAI.from_config(profile)
    state = {"actuator": actuator, "sensor": sensor}
    result = service.engine.recommend(state)
    risk = risk_comparison_chart(result, service.config.tau_danger, service.config.tau_safe)
    assert list(risk.data[0].y) == [
        result.optimization.initial_risk,
        result.optimization.final_risk,
    ]
    assert [shape.y0 for shape in risk.layout.shapes] == [0.8, 0.2]
    changes = delta_chart(result)
    if result.optimization.deltas:
        assert list(changes.data[0].y) == [delta.raw_delta for delta in result.optimization.deltas]
        if not result.outcome.success:
            assert "Diagnostic" in changes.layout.title.text
            assert "Prescribed" not in changes.layout.title.text
    else:
        assert changes is None
    app = AppTest.from_function(
        render_actual_legacy, args=(str(profile), state), default_timeout=40
    ).run()
    assert not app.exception
    assert bool(app.success) == result.outcome.success
    assert bool(app.warning) >= (not result.outcome.success)
    assert len(app.get("plotly_chart")) == (2 if changes is not None else 1)
    assert any("Assumption:" in item.value for item in app.caption)
    assert app.expander and app.metric
