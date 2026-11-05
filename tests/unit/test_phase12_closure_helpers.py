"""Independent scoring and threshold-margin reporting for closure diagnostics."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml
from sklearn.linear_model import LogisticRegression

from prescriptxai.models.calibration import ProbabilityCalibrator

SPEC = spec_from_file_location(
    "closure_diagnostics", Path("scripts/diagnostics/phase12_closure.py")
)
HELPER = module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


@pytest.mark.parametrize("method", ["sigmoid", "temperature", "isotonic"])
def test_audit_scorer_uses_primary_model_and_calibration(method: str) -> None:
    """A fitted primary classifier is scored independently with all calibration methods."""
    classifier = LogisticRegression().fit(np.array([[-2.0], [-1.0], [1.0], [2.0]]), [0, 0, 1, 1])
    calibration = ProbabilityCalibrator(method).fit(
        np.array([0.1, 0.3, 0.7, 0.9]), np.array([0, 0, 1, 1])
    )
    bundle = SimpleNamespace(
        feature_names=("control",),
        scaler=SimpleNamespace(
            scaler=SimpleNamespace(mean_=np.array([10.0]), scale_=np.array([2.0]))
        ),
        estimator=SimpleNamespace(estimator=classifier), calibrator=calibration,
    )
    candidate = {"control": 11.0, "ignored_context": 900.0}
    expected = calibration.transform(classifier.predict_proba(np.array([[0.5]]))[:, 1])[0]
    assert HELPER.audit_risk(bundle, candidate) == pytest.approx(expected, abs=1e-12, rel=0)


def test_csv_preserves_nested_margins_and_unrounded_values(tmp_path: Path) -> None:
    """CSV retains precise values and a machine-readable threshold object."""
    path = tmp_path / "classification.csv"
    HELPER.write_csv(path, [{"case": "x", "margin": -1e-12, "details": {"passed": False}}])
    row = pd.read_csv(path).iloc[0]
    assert row["margin"] == -1e-12
    assert row["details"] == '{"passed": false}'


def test_flat_preserves_candidate_support_as_structural_data() -> None:
    """Changed support lists remain discrete, even when numeric differences are tiny."""
    result = HELPER.flat({"candidate": {"x": 0.2}, "changed_features": ["x"]})
    assert result == {"/candidate/x": 0.2, "/changed_features": ["x"]}


@pytest.mark.parametrize("key,value", [("expected_cases", 711), ("repeats", 1),
                                      ("relative_tolerance", 1e-5), ("order", "random")])
def test_incomplete_or_relaxed_diagnostic_design_is_rejected(key: str, value: object) -> None:
    """Population caps, fewer repeats, relaxed tolerances and unstable order fail before calls."""
    design = yaml.safe_load(
        Path("configs/experiments/phase12-closure-712-v1.yaml").read_text(encoding="utf-8")
    )
    HELPER.validate_design(design)
    design[key] = value
    with pytest.raises(ValueError, match="preregistered"):
        HELPER.validate_design(design)
