"""Guard the causal diagnostic design and immutable source extraction, without solving."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
import yaml


def helper() -> ModuleType:
    """Load the registered diagnostic helper without running its main entry point."""
    path = Path("scripts/diagnostics/phase12_arithmetic.py")
    spec = importlib.util.spec_from_file_location("arithmetic_helper_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "change",
    [
        "drop_arm",
        "extra_arm",
        "case_count",
        "calls",
        "scores",
        "atol",
        "rtol",
        "threads",
        "historical_source",
    ],
)
def test_factorial_rejects_incomplete_or_redefined_design(change: str) -> None:
    """Reject incomplete arms and altered populations, tolerance or source."""
    module = helper()
    design = yaml.safe_load(Path("configs/experiments/phase12-arithmetic-v1.yaml").read_text())
    module.validate_design(design)
    corrupt = copy.deepcopy(design)
    if change == "drop_arm":
        del corrupt["arms"]["historical_both"]
    elif change == "extra_arm":
        corrupt["arms"]["unregistered"] = corrupt["arms"]["current"]
    else:
        key, value = {
            "case_count": ("expected_cases", 711),
            "calls": ("expected_search_calls", 2847),
            "scores": ("expected_score_rows", 1424),
            "atol": ("absolute_tolerance", 1e-5),
            "rtol": ("relative_tolerance", 1e-6),
            "threads": ("threads", 2),
            "historical_source": ("historical_source", "HEAD"),
        }[change]
        corrupt[key] = value
    with pytest.raises(ValueError, match="registered arithmetic factorial"):
        module.validate_design(corrupt)


def test_historical_method_is_exact_extraction_and_does_not_execute_module_body() -> None:
    """Extract source without evaluating unrelated historical module statements."""
    module = helper()
    source = (
        "raise RuntimeError('module body must not run')\nclass Example:\n"
        "    def calculate(self, x: MissingType):\n        return x * 3\n"
    )
    method, text = module.historical_method(source, "Example", "calculate", {})
    assert text == "def calculate(self, x: MissingType):\n        return x * 3"
    assert method(None, 7) == 21


def test_registered_inputs_cannot_change(tmp_path: Path) -> None:
    """Reject modified external inputs instead of silently using them."""
    module = helper()
    path = tmp_path / "input"
    path.write_bytes(b"frozen model bytes")
    hashes = {str(path): module.file_hash(path)}
    module.verify_inputs(hashes)
    path.write_bytes(b"altered model bytes")
    with pytest.raises(ValueError, match="input bytes changed"):
        module.verify_inputs(hashes)


def test_prior_registration_supplies_complete_immutable_file_manifest() -> None:
    """Use the actual preceding registration schema rather than a planned key."""
    design = yaml.safe_load(Path("configs/experiments/phase12-arithmetic-v1.yaml").read_text())
    prior = yaml.safe_load(Path(design["prior_design"]).read_text())
    files = prior["immutable_files"]
    assert len(files) == 102
    assert prior["historical_database"] in files
    assert prior["repaired_database"] in files
    assert prior["mismatches"] in files
    assert "uv.lock" in files


def test_control_requires_exact_outputs_even_inside_numeric_tolerance() -> None:
    """Never interpret an implementation arm if its baseline control has drifted."""
    module = helper()
    reference = {"candidate": {"control": 1.0}, "risk": 0.2, "tier2": True}
    module.verify_control(reference, copy.deepcopy(reference))
    modified = copy.deepcopy(reference)
    modified["candidate"]["control"] += 1e-10
    with pytest.raises(ValueError, match="exactly reproduce"):
        module.verify_control(reference, modified)
    modified = copy.deepcopy(reference)
    modified["tier2"] = False
    with pytest.raises(ValueError, match="exactly reproduce"):
        module.verify_control(reference, modified)
