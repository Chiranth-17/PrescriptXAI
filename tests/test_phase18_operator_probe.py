"""Fixed-operation diagnostics must retain production forward/backward values."""

from types import SimpleNamespace

import pytest
import torch
from scripts.diagnostics.phase18_operator_probe import operation, trace


def test_operator_probe_preserves_native_chain_and_shared_operands() -> None:
    """A test-only network checks native and shared-operation tracing without fitting."""
    layer = torch.nn.Linear(2, 1)
    with torch.no_grad():
        layer.weight.copy_(torch.tensor([[2.0, -3.0]]))
        layer.bias.fill_(0.5)
    network = torch.nn.Sequential(layer, torch.nn.ReLU())
    bundle = SimpleNamespace(
        surrogate=SimpleNamespace(network_=network),
        calibrator=None,
        torch_forward=lambda x: torch.sigmoid(network(x)).reshape(-1),
    )
    first = trace(bundle, [[1.0, 0.0]])
    second = trace(bundle, [[1.0, 0.0]], first["stages"])
    assert first == second
    assert first["stages"][0]["native"]["output"] == [[2.5]]
    assert first["stages"][0]["native"]["ones_vjp"] == [[2.0, -3.0]]
    assert operation(layer, [[0.0, 1.0]])["output"] == [[-2.5]]
    assert all(parameter.grad is None for parameter in network.parameters())


def test_operator_probe_rejects_a_chain_that_changes_public_score() -> None:
    """The trace must fail rather than silently substituting a different scoring path."""
    network = torch.nn.Sequential(torch.nn.Linear(2, 1))
    bundle = SimpleNamespace(
        surrogate=SimpleNamespace(network_=network),
        calibrator=None,
        torch_forward=lambda x: torch.sigmoid(network(x)).reshape(-1) + 1.0,
    )
    with pytest.raises(ValueError, match="changes the native"):
        trace(bundle, [[0.0, 0.0]])
