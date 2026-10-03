"""Integration checks for repository-level configuration files."""

from pathlib import Path

from prescriptxai.config import load_config
from prescriptxai.constraints.taxonomy import load_taxonomy


def test_application_configuration_and_taxonomy_load_together() -> None:
    """Default app and taxonomy configs consistently expose C-MAPSS fields."""
    config = load_config(Path("configs/default.yaml"))
    taxonomy = load_taxonomy(Path("configs/features.yaml"))
    declared = {
        feature
        for group in taxonomy.feature_groups.model_dump().values()
        for feature in group["features"]
    }

    assert config.data.dataset.startswith("FD00")
    assert taxonomy.dataset == "CMAPSS"
    assert {"engine_id", "cycle"}.issubset(declared)
