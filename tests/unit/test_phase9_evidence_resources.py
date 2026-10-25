"""Evidence audits must close real SQLite connections on both read paths."""

import sqlite3
from pathlib import Path

import pytest

from prescriptxai.evaluation.experiments import ExperimentStore, audit_stage_completion, load_study


def test_stage_audits_close_actual_record_and_latency_connections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observe genuine connections without substituting query results or a fake database."""
    manifest = {"git_hash": "fixture", "expected_queries": {"quality": 0, "diagnostics": 0}}
    store = ExperimentStore(tmp_path, manifest)
    store.close()
    connection = sqlite3.connect(tmp_path / "latency.sqlite3")
    connection.execute("CREATE TABLE samples (mode TEXT)")
    connection.commit()
    connection.close()
    (tmp_path / "latency.json").write_text("{}", encoding="utf-8")
    original = sqlite3.connect
    observed = []

    def connect(path: Path) -> sqlite3.Connection:
        """Retain references to the real handles solely to verify their closed state."""
        actual = original(path)
        observed.append(actual)
        return actual

    monkeypatch.setattr(sqlite3, "connect", connect)
    try:
        result = audit_stage_completion(
            tmp_path, manifest, load_study(Path("configs/experiments/phase7-study.yaml"))
        )
        assert not any(result.values()) and len(observed) == 2
        for actual in observed:
            with pytest.raises(sqlite3.ProgrammingError, match="closed"):
                actual.execute("SELECT 1")
    finally:
        for actual in observed:
            actual.close()
