"""Every executable artifact reader shares the explicit local trust boundary."""

import ast
import importlib.util
import json
from pathlib import Path

import pytest


def test_no_deserialization_bypasses_in_package_or_diagnostic_scripts() -> None:
    """New persistence code cannot silently reintroduce direct pickle/joblib readers."""
    paths = [*Path("src").rglob("*.py"), *Path("scripts").rglob("*.py")]
    for path in paths:
        if path.as_posix() == "src/prescriptxai/artifacts.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = node.func.value
                assert not (
                    isinstance(owner, ast.Name)
                    and owner.id in {"joblib", "pickle"}
                    and node.func.attr in {"load", "loads"}
                ), f"unsafe direct deserialization: {path}:{node.lineno}"
            if isinstance(node, ast.ImportFrom) and node.module in {"pickle", "joblib"}:
                assert not {item.name for item in node.names} & {"load", "loads"}, str(path)


def test_review_bundle_copies_saved_evidence_and_refuses_overwrite(tmp_path: Path) -> None:
    """The replacement review tool copies values; it cannot invent fallback rates or verdicts."""
    spec = importlib.util.spec_from_file_location(
        "review_bundle", "scripts/diagnostics/make_bundle.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "source"
    source.mkdir()
    manifest = {"run_id": "test-only-fixture", "git_hash": "test-only-source"}
    (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (source / "summary.json").write_text(
        json.dumps({"manifest": manifest, "complete": True, "groups": {}}), encoding="utf-8"
    )
    stages = {
        name: {"complete": True, "source": manifest["git_hash"]}
        for name in ("quality", "diagnostics", "reference", "latency")
    }
    (source / "stages.json").write_text(json.dumps(stages), encoding="utf-8")
    (source / "report.md").write_text("Actual test-fixture report\n", encoding="utf-8")
    (source / "metrics.csv").write_text("name,value\ntest-only,0.123\n", encoding="utf-8")
    output = tmp_path / "review"
    result = module.create_review_bundle(source, output)
    assert result["measurement_source"] == manifest["git_hash"]
    assert result["raw_records_copied"] is False
    for name in module.REQUIRED:
        assert (output / name).read_bytes() == (source / name).read_bytes()
    with pytest.raises(FileExistsError):
        module.create_review_bundle(source, output)
    with pytest.raises(ValueError, match="outside"):
        module.create_review_bundle(source, source / "child")
    (source / "summary.json").write_text('{"complete":false}', encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete"):
        module.create_review_bundle(source, tmp_path / "incomplete")
