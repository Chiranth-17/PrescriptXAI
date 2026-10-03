"""Unit tests for C-MAPSS parsing, engine splits, labels, and scaling."""

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from prescriptxai.data.cmapss import load_cmapss_archive
from prescriptxai.data.download import DatasetDownloadError, download_archive, verify_archive
from prescriptxai.data.preprocess import add_training_labels, fit_feature_scaler
from prescriptxai.data.splits import split_engines


def _engine_frame(engine_count: int = 12) -> pd.DataFrame:
    """Build small deterministic telemetry for logic tests only."""
    return pd.DataFrame(
        [
            {"engine_id": engine, "cycle": cycle, "sensor": float(engine + cycle), "constant": 5.0}
            for engine in range(1, engine_count + 1)
            for cycle in range(1, 5)
        ]
    )


def _archive_bytes() -> bytes:
    """Create a minimal structurally valid FD001 archive fixture."""
    rows = (
        "\n".join(" ".join(str(value) for value in [1, cycle, *range(3, 27)]) for cycle in (1, 2))
        + "\n"
    )
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("CMAPSSData/train_FD001.txt", rows)
        archive.writestr("CMAPSSData/test_FD001.txt", rows)
        archive.writestr("CMAPSSData/RUL_FD001.txt", "3\n")
    return stream.getvalue()


def test_download_rejects_non_http_url(tmp_path: Path) -> None:
    """Dataset URLs must use an HTTP scheme."""
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        download_archive("file:///tmp/data.zip", tmp_path / "data.zip", 10)


def test_download_rejects_invalid_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An HTTP response containing non-ZIP bytes is not accepted."""
    monkeypatch.setattr(
        "prescriptxai.data.download.urlopen", lambda *_args, **_kwargs: BytesIO(b"bad")
    )

    with pytest.raises(DatasetDownloadError, match="not a valid ZIP") as captured:
        download_archive("https://example.invalid/data.zip", tmp_path / "data.zip", 10)

    assert "Manual download required" in str(captured.value)
    assert "No substitute data was created" in str(captured.value)
    assert not (tmp_path / "data.zip.part").exists()


def test_download_success_checks_zip_and_configured_sha256(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Successful download writes the archive only after ZIP and digest verification."""
    payload = _archive_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(
        "prescriptxai.data.download.urlopen", lambda *_args, **_kwargs: BytesIO(payload)
    )

    destination = download_archive(
        "https://example.invalid/data.zip", tmp_path / "data.zip", 10, digest
    )

    assert destination.is_file()
    assert verify_archive(destination, digest) == digest


def test_archive_integrity_records_digest_and_rejects_wrong_expected_digest(tmp_path: Path) -> None:
    """ZIP CRC and optional configured SHA-256 are checked before use."""
    archive_path = tmp_path / "verified.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("member.txt", "integrity test")

    digest = verify_archive(archive_path)

    assert len(digest) == 64
    with pytest.raises(DatasetDownloadError, match="SHA-256 mismatch"):
        verify_archive(archive_path, expected_sha256="0" * 64)


def test_cmapss_archive_parser_checks_table_schema(tmp_path: Path) -> None:
    """The parser maps the canonical 26 columns and joins test RUL by engine."""
    archive_path = tmp_path / "fixture.zip"
    archive_path.write_bytes(_archive_bytes())

    dataset = load_cmapss_archive(archive_path, "FD001")

    assert dataset.train.shape == (2, 26)
    assert dataset.test.shape == (2, 26)
    assert dataset.test_rul.to_dict("records") == [{"unit_id": 1, "rul": 3}]
    assert dataset.train.columns.tolist() == [
        "unit_id",
        "cycle",
        "op_setting_1",
        "op_setting_2",
        "op_setting_3",
        *[f"s{i}" for i in range(1, 22)],
    ]


def test_cmapss_parser_reads_nasa_nested_archive(tmp_path: Path) -> None:
    """The official outer ZIP wrapper may contain the telemetry ZIP as a member."""
    archive_path = tmp_path / "nasa_wrapper.zip"
    with zipfile.ZipFile(archive_path, "w") as outer_archive:
        outer_archive.writestr("Dataset/CMAPSSData.zip", _archive_bytes())

    dataset = load_cmapss_archive(archive_path, "FD001")

    assert dataset.subset == "FD001"
    assert len(dataset.train) == 2


def test_cmapss_parser_rejects_empty_or_wrong_subset(tmp_path: Path) -> None:
    """Missing archive files and unsupported subset identifiers fail explicitly."""
    archive_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive_path, "w"):
        pass
    with pytest.raises(ValueError, match="complete FD001"):
        load_cmapss_archive(archive_path, "FD001")
    with pytest.raises(ValueError, match="subset must be"):
        load_cmapss_archive(archive_path, "FD005")


def test_engine_splits_are_disjoint_reproducible_and_complete() -> None:
    """Each engine appears in one deterministic partition only."""
    frame = _engine_frame()
    first = split_engines(frame, 0.7, 0.15, 0.15, seed=42)
    second = split_engines(frame, 0.7, 0.15, 0.15, seed=42)
    train_ids, validation_ids, test_ids = map(
        set, (first.train_engine_ids, first.validation_engine_ids, first.test_engine_ids)
    )

    assert train_ids.isdisjoint(validation_ids | test_ids)
    assert validation_ids.isdisjoint(test_ids)
    assert train_ids | validation_ids | test_ids == set(frame.engine_id.unique())
    assert first.train_engine_ids == second.train_engine_ids
    assert len(first.train) + len(first.validation) + len(first.test) == len(frame)


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (pd.DataFrame(), "empty dataframe"),
        (pd.DataFrame({"other": [1, 2, 3]}), "missing engine identifier"),
        (_engine_frame(2), "at least three engines"),
        (_engine_frame().assign(engine_id=np.nan), "must not be missing"),
    ],
)
def test_engine_split_rejects_invalid_data(frame: pd.DataFrame, message: str) -> None:
    """Empty, malformed, or too-small engine input is rejected."""
    with pytest.raises(ValueError, match=message):
        split_engines(frame, 0.7, 0.15, 0.15, seed=7)


def test_training_labels_use_uncapped_horizon_semantics() -> None:
    """Failure labels use exact RUL while returned RUL is capped."""
    frame = pd.DataFrame(
        {"engine_id": [1, 1, 1, 1], "cycle": [1, 8, 9, 10], "sensor": [0.0, 1.0, 2.0, 3.0]}
    )

    labeled = add_training_labels(frame, rul_cap=5, failure_horizon=2)

    assert labeled["rul"].tolist() == [5, 2, 1, 0]
    assert labeled["failure_label"].tolist() == [0, 1, 1, 1]


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (pd.DataFrame(), "empty dataframe"),
        (pd.DataFrame({"engine_id": [1], "cycle": [np.nan]}), "must not be missing"),
        (pd.DataFrame({"engine_id": [1, 1], "cycle": [1, 1]}), "duplicate"),
    ],
)
def test_rul_labeling_rejects_invalid_inputs(frame: pd.DataFrame, message: str) -> None:
    """Empty, NaN, and duplicate cycle rows cannot produce labels."""
    with pytest.raises(ValueError, match=message):
        add_training_labels(frame, rul_cap=125, failure_horizon=30)


def test_scaler_uses_train_only_and_handles_constant_columns() -> None:
    """Fitted means and constant-column outputs depend only on supplied training engines."""
    train = _engine_frame().query("engine_id <= 3")
    scaler = fit_feature_scaler(train, ("sensor", "constant"))
    held_out = _engine_frame().query("engine_id == 12")
    transformed = scaler.transform(held_out[["sensor", "constant"]])

    assert scaler.training_engine_ids == (1, 2, 3)
    assert scaler.scaler.mean_[0] == pytest.approx(train.sensor.mean())
    assert scaler.scaler.mean_[0] != pytest.approx(held_out.sensor.mean())
    assert np.isfinite(transformed).all()
    assert np.all(transformed[:, 1] == 0.0)


@pytest.mark.parametrize(
    ("frame", "feature_names", "message"),
    [
        (pd.DataFrame(), ("x",), "must not be empty"),
        (_engine_frame().assign(sensor=np.nan), ("sensor",), "must be finite"),
        (_engine_frame().drop(columns="sensor"), ("sensor",), "missing features"),
    ],
)
def test_scaler_rejects_bad_training_features(
    frame: pd.DataFrame, feature_names: tuple[str, ...], message: str
) -> None:
    """Scaler fit rejects empty, NaN, and absent features."""
    with pytest.raises(ValueError, match=message):
        fit_feature_scaler(frame, feature_names)


def test_scaler_transform_rejects_wrong_feature_order() -> None:
    """Feature mapping cannot silently reorder columns."""
    train = _engine_frame().query("engine_id <= 3")
    scaler = fit_feature_scaler(train, ("sensor", "constant"))

    with pytest.raises(ValueError, match="feature columns/order"):
        scaler.transform(train[["constant", "sensor"]])
