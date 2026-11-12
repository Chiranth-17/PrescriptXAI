"""Diagnostic interception must never execute SciPy or retain its patch."""

from unittest.mock import Mock, patch

import numpy as np
import pytest
from scripts.diagnostics.phase18_gradient_probe import capture_first_objective


def test_diagnostic_stops_before_scipy_and_restores_callback() -> None:
    """Capture the actual bound callback without a numerical solver iteration."""
    from prescriptxai.recourse import optimizer

    class Callback:
        def evaluate(self, values: object) -> None:
            raise AssertionError("Capturing the callback must not evaluate it")

    callback = Callback()

    class Solver:
        def solve(self, state: object, config: object) -> None:
            optimizer.minimize(callback.evaluate, np.array([0.0]), bounds=((0.0, 1.0),))
            raise AssertionError("Interception must terminate the optimizer")

    forbidden = Mock(side_effect=AssertionError("SciPy must not execute"))
    with patch.object(optimizer, "minimize", forbidden):
        result = capture_first_objective(Solver(), {}, None)
        assert result["objective"] is callback
        assert result["start"].tolist() == [0.0]
        assert optimizer.minimize is forbidden
        forbidden.assert_not_called()


def test_missing_objective_fails_and_restores_callback() -> None:
    """A pre-search return cannot be misreported as a gradient observation."""
    from prescriptxai.recourse import optimizer

    original = optimizer.minimize
    with pytest.raises(ValueError, match="never reached"):
        capture_first_objective(Mock(), {}, None)
    assert optimizer.minimize is original


def test_unexpected_error_propagates_and_restores_callback() -> None:
    """Failures preserve the real exception and leave no process-wide patch."""
    from prescriptxai.recourse import optimizer

    original = optimizer.minimize
    solver = Mock()
    solver.solve.side_effect = ValueError("damaged asset")
    with pytest.raises(ValueError, match="damaged asset"):
        capture_first_objective(solver, {}, None)
    assert optimizer.minimize is original
