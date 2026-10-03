"""End-to-end preprocessing checks over test-only C-MAPSS-shaped fixtures."""

from __future__ import annotations

from pathlib import Path

from fixtures.cmapss import write_cmapss_archive
from prescriptxai.data.prepare import prepare_cmapss


def test_prepare_writes_auditable_outputs_and_is_idempotent(tmp_path: Path) -> None:
    """Repeated fixture preparation yields the same report and partition CSV bytes."""
    archive = write_cmapss_archive(tmp_path / "raw" / "fixture.zip", subset="FD001")
    processed = tmp_path / "processed"
    artifacts = tmp_path / "artifacts"
    kwargs = {
        "archive_path": archive,
        "subset": "FD001",
        "processed_root": processed,
        "artifact_root": artifacts,
        "seed": 1729,
        "failure_horizon": 30,
        "rul_cap": None,
        "variance_threshold": 1e-8,
        "regime_k": 6,
        "lifetime_buckets": 6,
        "train_fraction": 0.7,
        "validation_fraction": 0.15,
        "test_fraction": 0.15,
    }

    first = prepare_cmapss(**kwargs)
    report_bytes = first.report_path.read_bytes()
    csv_bytes = {name: path.read_bytes() for name, path in first.partition_paths.items()}
    second = prepare_cmapss(**kwargs)

    assert second.report_path.read_bytes() == report_bytes
    assert {name: path.read_bytes() for name, path in second.partition_paths.items()} == csv_bytes
    assert first.report["row_counts"]["raw_train"] == sum(
        first.report["row_counts"][name] for name in ("train", "validation", "holdout")
    )
    assert first.report["feature_set"]["dropped_sensors"] == ["s2"]
    assert first.report["feature_set"]["retained_model_features"] == [
        "op_setting_1",
        "op_setting_2",
        "op_setting_3",
        *[f"s{i}" for i in range(1, 22) if i != 2],
    ]
    assert first.report["checks"]["scalers_and_clusters_fit_engine_ids"] == list(
        first.splits.train_engine_ids
    )
    assert first.report_path.name == "FD001_report.json"
    assert first.preprocessor_path.is_file()
    assert first.dropped_sensors_path.is_file()
