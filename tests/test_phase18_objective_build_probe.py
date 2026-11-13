"""Test native-check boundaries and failure retention in the diagnostic wrapper."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.diagnostics.phase18_objective_build_probe import (
    compare_rows,
    retain_failed_values,
    solver_phase_bridge,
)


def test_each_case_restores_native_checks_before_its_solver_phase() -> None:
    """A previous case's temporary graph must never leak into the next teacher check."""
    network = SimpleNamespace(mode="native")
    bundle = SimpleNamespace(surrogate=SimpleNamespace(network_=network))
    seen = []

    class Pipeline:
        @classmethod
        def from_config(cls, name: str) -> SimpleNamespace:
            assert network.mode == "native"
            seen.append(name)
            return SimpleNamespace(bundle=bundle)

    class Solver:
        def __init__(self, model: SimpleNamespace) -> None:
            assert model is bundle and network.mode == "native"

    @contextmanager
    def enter(model: SimpleNamespace) -> Iterator[None]:
        assert model is network
        network.mode = "aligned"
        try:
            yield
        finally:
            network.mode = "native"

    factory, initializer = Pipeline.from_config, Solver.__init__
    with pytest.raises(ValueError, match="stop"), solver_phase_bridge(Pipeline, Solver, enter):
        Pipeline.from_config("first")
        Solver(bundle)
        assert network.mode == "aligned"
        Pipeline.from_config("second")
        assert network.mode == "native"
        Solver(bundle)
        assert network.mode == "aligned"
        raise ValueError("stop")
    assert network.mode == "native" and seen == ["first", "second"]
    assert Pipeline.from_config == factory and Solver.__init__ is initializer


def test_exact_comparison_keeps_small_differences_unaccepted(tmp_path: Path) -> None:
    """The predeclared envelope is classification only, never an acceptance policy."""
    old = [{"case_id": str(i), "vertex": "original", "value": 1.0} for i in range(159)]
    new = [dict(row) for row in old]
    new[0]["value"] += 1e-7
    new[1]["value"] += 1e-4
    paths = [tmp_path / name for name in ("old.jsonl", "new.jsonl")]
    for path, rows in zip(paths, (old, new), strict=True):
        path.write_text("\n".join(json.dumps(row) for row in rows))
    result = compare_rows(paths[1], paths[0], tmp_path / "comparison.json")
    assert result["exact_rows"] == 157 and result["different_rows"] == 2
    assert result["outside_existing_envelope_rows"] == 1
    assert len(result["details"]) == 2


def test_failed_numerical_attempt_keeps_raw_traceback(tmp_path: Path) -> None:
    """Retaining an exception must not turn it into a successful numerical receipt."""
    try:
        raise ValueError("raw failed control")
    except ValueError as error:
        retain_failed_values(error, tmp_path / "failure.json")
    record = json.loads((tmp_path / "failure.json").read_text())
    assert "raw failed control" in record["error"] and "ValueError" in record["traceback"]
