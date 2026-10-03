"""Regression coverage for empty evaluation samples and valid JSON reporting."""

import json
from pathlib import Path

from prescriptxai.config import load_config
from prescriptxai.evaluation.metrics import calculate_metrics
from prescriptxai.evaluation.report import write_evaluation_report
from prescriptxai.evaluation.runner import EvaluationRun


def test_empty_evaluation_remains_unmeasured_and_json_serializable(tmp_path: Path) -> None:
    """No high-risk query must not turn missing measurements into zeros or NaN."""
    config = load_config(Path("configs/default.yaml"))
    summary = calculate_metrics((), 0, None, None, config.evaluation)
    run = EvaluationRun((), summary)
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    write_evaluation_report(run, json_path, markdown_path)
    document = json.loads(json_path.read_text(encoding="utf-8"))

    assert summary.recourse_validity_rate.value is None
    assert summary.physical_plausibility_rate.value is None
    assert summary.latency["ingestion"].mean_ms is None
    assert document["summary"]["evaluated_states"] == 0
    assert "Unmeasured" in markdown_path.read_text(encoding="utf-8")
