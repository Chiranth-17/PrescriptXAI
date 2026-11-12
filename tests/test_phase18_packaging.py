"""Packaging failure paths preserve owned workspaces and reject stale demo files."""

import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from scripts.packaging.demo import DESIGN, file_hash, prepare
from scripts.packaging.provision import safe_path

from prescriptxai.machine_spec import MachineSpec, load_machine_spec, migrate_machine_spec_v1


def test_sample_spec_has_explicit_demonstration_and_synthetic_provenance() -> None:
    """The extra sample declares its source and has no engineer confirmation."""
    spec = load_machine_spec(Path("templates/sample_csv/machine.yaml"))
    assert spec.synthetic and spec.limits_status == "demonstration"
    assert not spec.confirmation.confirmed
    assert spec.machine_id == "sample_csv"
    assert spec.schema_version == 2


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


@pytest.mark.parametrize("name", ["../outside", "/absolute", "C:/other", "data\\other"])
def test_verification_assets_cannot_escape_the_selected_workspace(
    tmp_path: Path, name: str
) -> None:
    """A supplied asset name must stay portable and inside the trusted roots."""
    with pytest.raises(ValueError, match="portable and relative"):
        safe_path(tmp_path, name)


def test_v2_spec_identity_is_portable_and_v1_keeps_its_saved_identity() -> None:
    """Separator spelling shares v2 identity, while actual saved v1 identities remain readable."""
    document = yaml.safe_load(Path("templates/sample_csv/machine.yaml").read_text(encoding="utf-8"))
    first = MachineSpec.model_validate(document)
    windows = deepcopy(document)
    windows["dataset"]["path"] = "data\\raw\\sample.csv"
    second = MachineSpec.model_validate(windows)
    assert first.spec_hash == second.spec_hash
    assert second.dataset.path.as_posix() == "data/raw/sample.csv"
    legacy = MachineSpec.model_validate({**document, "schema_version": 1})
    saved_hash = {
        "nt": "e43329662532cafbb127e50955bf97e74c091e45e781e78209009a7f40d53d61",
        "posix": "f969d5b37179036169419b215b0aa09a8aacf6d8e0bf0d6bc730ea082bc02caa",
    }
    assert legacy.spec_hash == saved_hash[os.name]


def test_explicit_spec_migration_preserves_policies_and_the_original_document() -> None:
    """A new version gets a new identity without mutating a legacy spec or its policies."""
    document = yaml.safe_load(Path("templates/sample_csv/machine.yaml").read_text(encoding="utf-8"))
    document["schema_version"] = 1
    original = deepcopy(document)
    migrated = migrate_machine_spec_v1(document)
    assert document == original
    assert migrated["schema_version"] == 2
    before = MachineSpec.model_validate(document).model_dump(mode="json")
    before["schema_version"] = 2
    before["dataset"]["path"] = "data/raw/sample.csv"
    assert migrated == before
    with pytest.raises(ValueError, match="requires schema version 1"):
        migrate_machine_spec_v1(migrated)


@pytest.mark.parametrize("location", ["/absolute.csv", "C:\\data\\input.csv", "../escape.csv"])
def test_v2_spec_rejects_a_dataset_outside_its_workspace(location: str) -> None:
    """Portable specs cannot silently change root directories across operating systems."""
    document = yaml.safe_load(Path("templates/sample_csv/machine.yaml").read_text(encoding="utf-8"))
    document["dataset"]["path"] = location
    with pytest.raises(ValueError, match="workspace-relative"):
        MachineSpec.model_validate(document)


def test_container_runtime_constraints_match_the_lockfile() -> None:
    """The container must use the lockfile's transitive versions for the runtime extras."""
    exported = subprocess.check_output(
        [
            "uv",
            "export",
            "--locked",
            "--no-default-groups",
            "--extra",
            "api",
            "--extra",
            "dashboard",
            "--no-emit-project",
            "--no-hashes",
            "--format",
            "requirements-txt",
        ],
        text=True,
    )
    checked = Path("runtime-requirements.txt").read_text(encoding="utf-8")
    assert [line for line in exported.splitlines() if line and not line.startswith("#")] == [
        line for line in checked.splitlines() if line and not line.startswith("#")
    ]
