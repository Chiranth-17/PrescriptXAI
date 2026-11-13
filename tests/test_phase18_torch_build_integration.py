"""Guard the diagnostic bridge before testing genuine fixed surrogate inputs."""

import ctypes
from unittest.mock import Mock

import numpy as np
import pytest
import torch
from scripts.diagnostics.phase18_torch_build_integration import (
    aligned_layers,
    finite_tree,
    linear_forward,
    linear_vjp,
)


def reference_sgemm() -> ctypes._CFuncPtr:
    """Use exact small integers to check the C ABI, not to certify native parity."""
    fp, ip, cp = (ctypes.POINTER(t) for t in (ctypes.c_float, ctypes.c_int, ctypes.c_char))
    prototype = ctypes.CFUNCTYPE(None, cp, cp, ip, ip, ip, fp, fp, ip, fp, ip, fp, fp, ip)

    def reference(
        ta: cp,
        tb: cp,
        mm: ip,
        nn: ip,
        kk: ip,
        alpha: fp,
        aa: fp,
        lda: ip,
        bb: fp,
        ldb: ip,
        beta: fp,
        cc: fp,
        ldc: ip,
    ) -> None:
        for column in range(nn[0]):
            for row in range(mm[0]):
                value = sum(
                    aa[index + row * lda[0] if ta[0] == b"T" else row + index * lda[0]]
                    * bb[index + column * ldb[0]]
                    for index in range(kk[0])
                )
                position = row + column * ldc[0]
                cc[position] = alpha[0] * value + beta[0] * cc[position]

    return prototype(reference)


def test_nonuniform_upstream_vjp_and_bias_preserve_original_operands() -> None:
    """Full backprop uses actual upstream values, rather than substituting ones."""
    function = reference_sgemm()
    weight = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float32)
    bias = np.ones(3, dtype=np.float32)
    values = np.array([[2, 3]], dtype=np.float32)
    before = [a.copy() for a in (weight, bias, values)]
    assert linear_forward(function, weight, bias, values).tolist() == [[9, 19, 29]]
    upstream = np.array([[2, 3, 4]], dtype=np.float32)
    assert linear_vjp(function, weight, upstream).tolist() == [[31, 40]]
    assert all(np.array_equal(a, b) for a, b in zip((weight, bias, values), before, strict=True))


def test_autograd_chain_matches_input_gradient_and_restores_layer_methods() -> None:
    """A temporary bridge must preserve fixed weights and leave its network restored."""
    network = torch.nn.Sequential(
        torch.nn.Linear(2, 3),
        torch.nn.ReLU(),
        torch.nn.Linear(3, 2),
        torch.nn.ReLU(),
        torch.nn.Linear(2, 1),
    )
    with torch.no_grad():
        for i, layer in enumerate(network):
            if isinstance(layer, torch.nn.Linear):
                layer.weight.fill_(i + 1)
                layer.bias.fill_(1)
    values = torch.tensor([[2.0, 3.0]], requires_grad=True)
    expected = network(values)
    derivative = torch.autograd.grad(expected.sum(), values)[0]
    original = {name: p.detach().clone() for name, p in network.named_parameters()}
    counters = {"forward": 0, "backward": 0}
    with aligned_layers(network, reference_sgemm(), counters):
        actual = network(values)
        gradient = torch.autograd.grad(actual.sum(), values)[0]
        assert torch.equal(expected, actual) and torch.equal(derivative, gradient)
    assert counters == {"forward": 3, "backward": 3}
    assert all("forward" not in layer.__dict__ for layer in network.children())
    assert all(torch.equal(p, original[name]) for name, p in network.named_parameters())
    assert all(p.grad is None for p in network.parameters())


@pytest.mark.parametrize("bad", ["precision", "batch", "upstream"])
def test_bridge_rejects_unregistered_shapes_and_precision_before_native_call(bad: str) -> None:
    """Pointer dimensions and precision cannot be silently converted to pass."""
    forbidden = Mock(side_effect=AssertionError("No native call expected"))
    weight = np.ones((3, 2), dtype=np.float32)
    if bad == "precision":
        with pytest.raises(ValueError, match="float32"):
            linear_forward(
                forbidden,
                weight.astype(np.float64),
                np.ones(3, dtype=np.float32),
                np.ones((1, 2), dtype=np.float32),
            )
    elif bad == "batch":
        with pytest.raises(ValueError, match="one recorded row"):
            linear_forward(
                forbidden, weight, np.ones(3, dtype=np.float32), np.ones((2, 2), dtype=np.float32)
            )
    else:
        with pytest.raises(ValueError, match="upstream row"):
            linear_vjp(forbidden, weight, np.ones((1, 2), dtype=np.float32))
    forbidden.assert_not_called()


def test_nonfinite_partial_trace_cannot_be_accepted() -> None:
    """A nested infinity must fail even when its repeat is also infinite."""
    assert finite_tree({"output": [[1.0]], "label": "finite"})
    assert not finite_tree({"output": [[float("inf")]]})
    assert not finite_tree({"output": [[float("nan")]]})
