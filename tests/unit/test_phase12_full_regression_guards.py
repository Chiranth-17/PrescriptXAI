"""Missing assets and scientific changes must fail the mandatory full-corpus replay."""

import copy
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from prescriptxai.evaluation.experiments import file_hash


def helper_module() -> ModuleType:
    """Load the replay helper without invoking inference or a partial benchmark."""
    root = Path.cwd()
    sys.path.insert(0, str(root))
    try:
        spec = importlib.util.spec_from_file_location(
            "phase12_regression", root / "scripts/diagnostics/phase12_regression.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_missing_and_modified_external_assets_fail(tmp_path: Path) -> None:
    """Byte verification occurs before deserialization and cannot silently skip."""
    helper = helper_module()
    asset = tmp_path / "external.joblib"
    asset.write_bytes(b"guard-only bytes, never a fitted benchmark model")
    hashes = {str(asset): file_hash(asset)}
    helper.verify_files(hashes)
    asset.write_bytes(b"modified")
    with pytest.raises(ValueError, match="SHA256 differs"):
        helper.verify_files(hashes)
    asset.unlink()
    with pytest.raises(FileNotFoundError, match="Required regression input missing"):
        helper.verify_files(hashes)


def test_missing_audited_manifest_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An ordinary test run with absent benchmark evidence fails instead of passing a toy."""
    helper = helper_module()
    monkeypatch.setattr(helper, "MANIFEST", tmp_path / "absent.json")
    with pytest.raises(FileNotFoundError, match="audited regression manifest missing"):
        helper.preflight()


def test_comparison_preserves_science_and_ignores_only_presentation() -> None:
    """A changed verdict, support, counter, margin or assumption remains visible."""
    helper = helper_module()
    original = {
        "config_path": "configs\\example.yaml",
        "timings": {"optimization_ms": 10.0},
        "changed_features": ["control"],
        "solver_settings": {"solver_calls": 7},
        "validation": {
            "tier2": {
                "passed": True,
                "status": "pass",
                "measurement": 5.0,
                "limit": 5.0,
                "margin": 0.0,
                "diagnostics": ["formatted 5.000"],
                "checks": [
                    {
                        "name": "distribution",
                        "passed": True,
                        "margin": 0.0,
                        "explanation": "formatted prose",
                    }
                ],
            },
            "assumptions": ["proxy assumption"],
            "joint": True,
        },
    }
    current = copy.deepcopy(original)
    current["timings"]["optimization_ms"] = 999.0
    current["config_path"] = "configs/example.yaml"
    current["validation"]["tier2"]["diagnostics"] = ["different rounding"]
    current["validation"]["tier2"]["checks"][0]["explanation"] = "different rounding"
    expected = helper.comparison_record(original)
    assert helper.differences(expected, helper.comparison_record(current)) == []
    assert original["validation"]["tier2"]["diagnostics"] == ["formatted 5.000"]
    for mutation in ("verdict", "support", "counter", "margin", "assumption"):
        changed = copy.deepcopy(current)
        if mutation == "verdict":
            changed["validation"]["tier2"]["passed"] = False
        elif mutation == "support":
            changed["changed_features"] = []
        elif mutation == "counter":
            changed["solver_settings"]["solver_calls"] += 1
        elif mutation == "margin":
            changed["validation"]["tier2"]["margin"] = 0.000002
        else:
            changed["validation"]["assumptions"] = []
        assert helper.differences(expected, helper.comparison_record(changed))


def test_existing_replay_output_is_preserved(tmp_path: Path) -> None:
    """No silent retry or replacement can overwrite an earlier partial run."""
    marker = tmp_path / "checkpoint"
    marker.write_bytes(b"retained")
    with pytest.raises(FileExistsError, match="preserve and inspect"):
        helper_module().replay(tmp_path)
    assert marker.read_bytes() == b"retained"


def test_borderline_export_includes_individual_and_triage_predicates() -> None:
    """Native tiny negative check margins retain their actual verdict, with no rounding."""
    record = {
        "risk_before": 0.8,
        "risk_after": 0.2,
        "solver_tau_danger": 0.8,
        "solver_tau_safe": 0.2,
        "validation": {
            "tier3": {
                "margin": 0.0,
                "passed": True,
                "checks": [
                    {"name": "rate", "margin": -1e-10, "passed": True, "feature": "control"}
                ],
            },
            "assumptions": ["proxy"],
        },
    }
    margins = list(helper_module().native_margins(record, delta_min=0.6))
    assert margins[1] == ("tier3/checks/0/rate", -1e-10, True, "control")
    assert {row[0] for row in margins} == {
        "tier3",
        "tier3/checks/0/rate",
        "alert_gate",
        "tier1_safe_gate",
        "triage_improvement",
    }
    assert all(abs(row[1]) <= 1e-6 for row in margins)
