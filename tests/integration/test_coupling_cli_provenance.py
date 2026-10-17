"""Coupling CLI consumes the complete prepared training partition exactly once."""

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import yaml
from typer.testing import CliRunner

from fixtures.cmapss import write_cmapss_archive
from prescriptxai.cli import app
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.data.prepare import PreparedCmapss, prepare_cmapss


@pytest.fixture
def prepared_config(tmp_path: Path) -> tuple[Path, PreparedCmapss]:
    """Prepare real files from an explicitly test-only C-MAPSS fixture."""
    archive = write_cmapss_archive(tmp_path / "raw" / "fixture.zip")
    prepared = prepare_cmapss(
        archive_path=archive,
        subset="FD001",
        processed_root=tmp_path / "processed",
        artifact_root=tmp_path / "artifacts",
        seed=1729,
        failure_horizon=30,
        rul_cap=None,
        variance_threshold=1e-8,
        regime_k=6,
        lifetime_buckets=6,
        train_fraction=0.7,
        validation_fraction=0.15,
        test_fraction=0.15,
    )
    payload: dict[str, Any] = yaml.safe_load(Path("configs/default.yaml").read_text())
    payload["paths"]["raw_data"] = str(archive.parent)
    payload["paths"]["processed_data"] = str(tmp_path / "processed")
    payload["data"].update(
        root=str(archive.parent), archive_name=archive.name,
        processed_root=str(tmp_path / "processed"), expected_row_counts={},
    )
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path, prepared


def test_coupling_cli_fits_every_prepared_training_engine(
    tmp_path: Path, prepared_config: tuple[Path, PreparedCmapss],
) -> None:
    """A second split must never silently discard prepared training engines."""
    config_path, prepared = prepared_config
    output_path = tmp_path / "coupling.joblib"
    result = CliRunner().invoke(
        app, ["constraints", "fit-coupling", "--config", str(config_path),
              "--output", str(output_path)],
    )
    assert result.exit_code == 0, result.output + repr(result.exception)
    model = SensorCouplingModel.load(output_path)
    assert model.training_engine_ids == prepared.splits.train_engine_ids
    assert set(model.training_engine_ids).isdisjoint(prepared.splits.validation_engine_ids)
    assert set(model.training_engine_ids).isdisjoint(prepared.splits.test_engine_ids)
    assert output_path.with_name("coupling-diagnostics.html").is_file()


def test_coupling_cli_rejects_contaminated_training_partition(
    tmp_path: Path, prepared_config: tuple[Path, PreparedCmapss],
) -> None:
    """A holdout engine inserted into the training CSV is rejected before fitting."""
    config_path, prepared = prepared_config
    frame = pd.read_csv(prepared.partition_paths["train"])
    frame.loc[frame.unit_id == prepared.splits.train_engine_ids[0], "unit_id"] = (
        prepared.splits.test_engine_ids[0]
    )
    contaminated = tmp_path / "contaminated.csv"
    frame.to_csv(contaminated, index=False)
    output_path = tmp_path / "bad-coupling.joblib"
    result = CliRunner().invoke(
        app, ["constraints", "fit-coupling", "--config", str(config_path),
              "--train-csv", str(contaminated), "--output", str(output_path)],
    )
    assert result.exit_code != 0
    assert "coupling CSV must contain exactly the configured training" in result.output
    assert not output_path.exists()
