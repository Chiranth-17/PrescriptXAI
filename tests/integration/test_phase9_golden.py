"""Real fitted output goldens, independent process restarts and precision checks."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from fixtures.golden_operator import actual_snapshot, assert_snapshot, update_golden
from fixtures.operator_artifacts import write_operator_fixture
from prescriptxai.pipeline import PrescriptXAI

GOLDEN = Path("tests/golden/operator-v1.json")


@pytest.mark.slow
def test_actual_fitted_goldens_two_runs_and_two_process_restarts(tmp_path: Path) -> None:
    """Four real triage outcomes repeat in one process and across two fresh interpreters."""
    write_operator_fixture(tmp_path)
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    first, second = actual_snapshot(tmp_path), actual_snapshot(tmp_path)
    assert_snapshot(first, expected)
    assert first == second
    assert {result["status"] for result in first.values()} == {
        "RECOVERABLE",
        "PARTIAL",
        "ESCALATE",
        "NO_INTERVENTION",
    }
    environment = {**os.environ, "PYTHONPATH": str(Path("tests").resolve())}
    restarted = []
    for _ in range(2):
        process = subprocess.run(
            [sys.executable, "-m", "fixtures.golden_operator", "--artifacts", str(tmp_path)],
            env=environment,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        restarted.append(json.loads(process.stdout))
    assert restarted[0] == restarted[1] == first


def test_golden_write_requires_explicit_flag_and_cannot_silently_replace(tmp_path: Path) -> None:
    """Normal checks cannot create or replace an expected output file."""
    path = tmp_path / "golden.json"
    with pytest.raises(PermissionError, match="--update-golden"):
        update_golden(path, {"value": 1})
    assert not path.exists()
    update_golden(path, {"value": 1}, update=True)
    before = path.read_bytes()
    with pytest.raises(PermissionError):
        update_golden(path, {"value": 2})
    assert path.read_bytes() == before


def test_float32_float64_actual_decisions_and_inputs_agree_away_from_threshold(
    tmp_path: Path,
) -> None:
    """Test exact and rounded measurements without claiming equality on numerical boundaries."""
    write_operator_fixture(tmp_path)
    service = PrescriptXAI.from_config(tmp_path / "pipeline.yaml")
    for actuator in (-2.0, 2.0, 0.7, -1.3):
        state64 = np.asarray([actuator, 2.0], dtype=np.float64)
        state32 = state64.astype(np.float32)
        left, right = service.recommend(state64), service.recommend(state32)
        assert left.status == right.status
        assert left.risk_before == pytest.approx(right.risk_before, abs=1e-6, rel=1e-5)
        assert left.risk_after == pytest.approx(right.risk_after, abs=1e-6, rel=1e-5)
        np.testing.assert_allclose(
            list(left.new_state.values()), list(right.new_state.values()), atol=1e-6, rtol=1e-5
        )
        assert left.validation_report.joint == right.validation_report.joint
