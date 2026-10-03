"""CLI recovery behavior when the configured dataset source is unreachable."""

from pathlib import Path
from urllib.error import URLError

import pytest
import yaml
from typer.testing import CliRunner

from prescriptxai.cli import app


def test_data_download_reports_manual_steps_and_specific_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Offline download returns code 2 with file placement instructions, without fake data."""
    config_path = tmp_path / "config.yaml"
    values = yaml.safe_load(Path("configs/default.yaml").read_text(encoding="utf-8"))
    raw_directory = tmp_path / "raw"
    values["data"]["root"] = str(raw_directory)
    values["paths"]["raw_data"] = str(raw_directory)
    config_path.write_text(yaml.safe_dump(values, sort_keys=False), encoding="utf-8")

    def fail_offline(*_args: object, **_kwargs: object) -> None:
        raise URLError("offline")

    monkeypatch.setattr("prescriptxai.data.download.urlopen", fail_offline)

    result = CliRunner().invoke(
        app,
        ["data", "download", "--subset", "FD001", "--config", str(config_path)],
    )

    assert result.exit_code == 2
    assert "DATASET_DOWNLOAD_UNAVAILABLE" in result.output
    assert "Manual download required" in result.output
    assert str(raw_directory / "CMAPSSData.zip") in result.output
    assert "No substitute data was created" in result.output
    assert not (raw_directory / "CMAPSSData.zip").exists()
