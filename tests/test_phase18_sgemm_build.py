"""Check the direct BLAS ABI and orientation before using genuine saved operands."""

import ctypes
from unittest.mock import Mock

import numpy as np
import pytest
from scripts.diagnostics.phase18_sgemm_build import gemm_pair


def test_sgemm_abi_preserves_forward_bias_and_ones_vjp() -> None:
    """An exact integer fixture verifies column-major pointers, leading dims and beta."""
    fp = ctypes.POINTER(ctypes.c_float)
    ip = ctypes.POINTER(ctypes.c_int)
    cp = ctypes.POINTER(ctypes.c_char)
    prototype = ctypes.CFUNCTYPE(None, cp, cp, ip, ip, ip, fp, fp, ip, fp, ip, fp, fp, ip)
    calls = []

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
        m, n, k = mm[0], nn[0], kk[0]
        calls.append((ta[0], tb[0], m, n, k, lda[0], ldb[0], ldc[0], alpha[0], beta[0]))
        for column in range(n):
            for row in range(m):
                value = 0.0
                for index in range(k):
                    a_position = (index + row * lda[0]) if ta[0] == b"T" else (row + index * lda[0])
                    value += aa[a_position] * bb[index + column * ldb[0]]
                position = row + column * ldc[0]
                cc[position] = alpha[0] * value + beta[0] * cc[position]

    callback = prototype(reference)
    weight = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float32)
    bias = np.ones(3, dtype=np.float32)
    values = np.array([[2, 3]], dtype=np.float32)
    result = gemm_pair(callback, weight, bias, values)
    assert result == {"output": [[9.0, 19.0, 29.0]], "ones_vjp": [[9.0, 12.0]]}
    assert calls == [
        (b"T", b"N", 3, 1, 2, 2, 2, 3, 1.0, 1.0),
        (b"N", b"N", 2, 1, 3, 2, 3, 2, 1.0, 0.0),
    ]
    assert np.array_equal(weight, [[1, 2], [3, 4], [5, 6]])
    assert np.array_equal(bias, [1, 1, 1])
    assert np.array_equal(values, [[2, 3]])


def test_sgemm_rejects_wrong_precision_before_native_call() -> None:
    """The diagnostic must not silently change precision to improve agreement."""
    forbidden = Mock(side_effect=AssertionError("Native call must not occur"))
    with pytest.raises(ValueError, match="original float32"):
        gemm_pair(forbidden, np.ones((2, 2)), np.ones(2), np.ones((1, 2)))
    forbidden.assert_not_called()


def test_sgemm_rejects_wrong_dimensions_before_native_call() -> None:
    """Incorrect pointers/leading dimensions fail closed without entering BLAS."""
    forbidden = Mock(side_effect=AssertionError("Native call must not occur"))
    with pytest.raises(ValueError, match="dimensions changed"):
        gemm_pair(
            forbidden,
            np.ones((2, 2), dtype=np.float32),
            np.ones(3, dtype=np.float32),
            np.ones((1, 2), dtype=np.float32),
        )
    forbidden.assert_not_called()
