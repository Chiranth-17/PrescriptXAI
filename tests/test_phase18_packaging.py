"""Packaging failure paths preserve owned workspaces and reject stale demo files."""

import json
from pathlib import Path

import pytest
from scripts.packaging.demo import DESIGN, file_hash, prepare

from prescriptxai.machine_spec import load_machine_spec


def test_sample_spec_has_explicit_demonstration_and_synthetic_provenance() -> None:
    """The extra sample declares its source and has no engineer confirmation."""
    spec = load_machine_spec(Path("templates/sample_csv/machine.yaml"))
    assert spec.synthetic and spec.limits_status == "demonstration"
    assert not spec.confirmation.confirmed
    assert spec.machine_id == "sample_csv"


def test_demo_refuses_an_incomplete_workspace_without_changing_it(tmp_path: Path) -> None:
    """An interrupted preparation cannot silently replace the operator's files."""
    owned = tmp_path / "owned.txt"
    owned.write_text("original", encoding="utf-8")
    with pytest.raises(ValueError, match="Incomplete demo workspace"):
        prepare(tmp_path)
    assert owned.read_text(encoding="utf-8") == "original"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["owned.txt"]


def test_demo_rechecks_all_saved_files_before_reuse(tmp_path: Path) -> None:
    """A changed saved file fails before any listener or training starts."""
    fitted = tmp_path / "owned.bin"
    fitted.write_bytes(b"owned-file")
    receipt = {
        "actual_success": True,
        "design_sha256": file_hash(DESIGN),
        "files": {"owned.bin": file_hash(fitted)},
    }
    (tmp_path / "demo.json").write_text(json.dumps(receipt), encoding="utf-8")
    assert prepare(tmp_path) == receipt
    fitted.write_bytes(b"changed-file")
    with pytest.raises(ValueError, match="Demo files changed"):
        prepare(tmp_path)
    assert fitted.read_bytes() == b"changed-file"
