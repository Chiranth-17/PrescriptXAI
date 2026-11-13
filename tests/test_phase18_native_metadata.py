"""Per-platform byte pins must coexist with an exact complete metadata binding."""

import hashlib
import json
from pathlib import Path

import pytest
from scripts.diagnostics.phase18_sgemm_build_v2 import verify_native_metadata


def test_native_metadata_requires_both_raw_and_canonical_pins(tmp_path: Path) -> None:
    """Line endings may be independently registered; arbitrary whitespace is rejected."""
    value = {"inputs": {"asset": "unchanged"}, "threshold": 0.2}
    encoded = json.dumps(value, indent=2) + "\n"
    win, linux = tmp_path / "windows.json", tmp_path / "linux.json"
    win.write_bytes(encoded.replace("\n", "\r\n").encode())
    linux.write_bytes(encoded.encode())
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    design = {
        "baseline_metadata_native_sha256": {
            "windows": hashlib.sha256(win.read_bytes()).hexdigest(),
            "linux": hashlib.sha256(linux.read_bytes()).hexdigest(),
        },
        "baseline_metadata_canonical_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    assert verify_native_metadata(win, design, "windows") == value
    assert verify_native_metadata(linux, design, "linux") == value
    with pytest.raises(ValueError, match="raw bytes changed"):
        verify_native_metadata(win, design, "linux")
    linux.write_bytes((encoded + " ").encode())
    with pytest.raises(ValueError, match="raw bytes changed"):
        verify_native_metadata(linux, design, "linux")


def test_native_metadata_canonical_pin_rejects_value_changes(tmp_path: Path) -> None:
    """Registering different native bytes cannot admit a changed metadata value."""
    path = tmp_path / "metadata.json"
    path.write_text('{"threshold":0.3}', encoding="utf-8")
    design = {
        "baseline_metadata_native_sha256": {"linux": hashlib.sha256(path.read_bytes()).hexdigest()},
        "baseline_metadata_canonical_sha256": hashlib.sha256(b'{"threshold":0.2}').hexdigest(),
    }
    with pytest.raises(ValueError, match="full parsed metadata changed"):
        verify_native_metadata(path, design, "linux")
