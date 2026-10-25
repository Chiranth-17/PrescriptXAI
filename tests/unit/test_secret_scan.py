"""Security scan regressions use generated nonfunctional examples and never print matches."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "value,label",
    [
        (b"sk-" + b"a" * 48, "openai_key_shape"),
        (b"ghp_" + b"a" * 36, "github_classic_token_shape"),
        (b"AKIA" + b"A" * 16, "aws_access_key_shape"),
        (b"-----BEGIN " + b"PRIVATE KEY-----", "private_key"),
    ],
)
def test_scan_detects_sensitive_shapes_without_echoing_values(value: bytes, label: str) -> None:
    """Detect a secret-shaped example but return only its file and category."""
    spec = spec_from_file_location("secret_scan", Path("scripts/quality/secret_scan.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.findings(value, "fixture.txt")
    assert result == [{"source": "fixture.txt", "pattern": label}]
    assert value.decode() not in str(result)
    assert module.findings(b"ordinary source text", "fixture.txt") == []
