"""Artifact readiness must validate fitting identities before set-based compatibility checks."""

from dataclasses import replace
from pathlib import Path

import pytest

from integration.test_phase6_artifacts_cli import fitted_config  # noqa: F401
from prescriptxai.artifacts import ArtifactLoadError
from prescriptxai.config import load_config
from prescriptxai.models.registry import load_model_bundle, save_model_bundle
from prescriptxai.validation.pipeline import load_mahalanobis_validator, save_mahalanobis_validator


@pytest.mark.parametrize("ids", [(True, 2, 3, 4), (1.5, 2, 3, 4), (1, 1, 2, 3, 4), (0, 2, 3, 4)])
@pytest.mark.parametrize("component", ["model_and_scaler", "mahalanobis", "calibration"])
def test_model_and_scaler_cannot_share_the_same_invalid_fitting_ids(
    fitted_config: Path,  # noqa: F811
    ids: tuple[object, ...],
    component: str,
) -> None:
    """Two matching invalid ID sets are corrupt metadata, not evidence of a valid split."""
    config = load_config(fitted_config)
    if component == "mahalanobis":
        path = config.artifacts.mahalanobis
        validator = load_mahalanobis_validator(path)
        validator = replace(validator, training_engine_ids=ids)
        save_mahalanobis_validator(validator, path)
        load = load_mahalanobis_validator
    else:
        path = config.artifacts.model
        bundle = load_model_bundle(path)
        if component == "model_and_scaler":
            bundle.training_engine_ids = bundle.scaler.training_engine_ids = ids
        else:
            bundle.metrics["calibration"]["fit_engine_ids"] = ids
        save_model_bundle(bundle, path)
        load = load_model_bundle
    with pytest.raises(ArtifactLoadError, match="invalid engine IDs"):
        load(path)
