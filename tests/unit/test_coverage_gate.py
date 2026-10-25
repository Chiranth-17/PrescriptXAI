"""Coverage exclusions must not hide a full-package regression or an unmeasured module."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def test_scoped_coverage_cannot_override_full_package_ratchets() -> None:
    """A rendering exclusion can reach 90% while the separate full-library floor still fails."""
    spec = spec_from_file_location("coverage_gate", Path("scripts/quality/coverage_gate.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    document = {
        "files": {
            name: {
                "summary": {
                    "covered_lines": covered,
                    "num_statements": total,
                    "covered_branches": 0,
                    "num_branches": 0,
                }
            }
            for name, covered, total in [
                ("src/prescriptxai/logic.py", 9, 10),
                ("src/prescriptxai/dashboard/app.py", 0, 10),
            ]
        }
    }
    config = {
        "rendering_exclusions": ["src/prescriptxai/dashboard/app.py"],
        "required_scoped_line_percent": 90,
        "full_package_line_floor": 80,
        "full_package_branch_inclusive_floor": 80,
    }
    result = module.check_coverage(document, config)
    assert result["scoped"]["line_percent"] == 90
    assert result["full"]["line_percent"] == 45 and not result["passed"]
    with pytest.raises(ValueError, match="no source"):
        module.check_coverage({}, config)
    document["files"]["src/prescriptxai/logic.py"]["summary"]["covered_lines"] = 11
    with pytest.raises(ValueError, match="numerator exceeds"):
        module.check_coverage(document, config)
