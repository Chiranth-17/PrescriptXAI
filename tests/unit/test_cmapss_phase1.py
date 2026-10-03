"""Unit coverage for canonical C-MAPSS validation, labels, and preprocessing."""

from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from fixtures.cmapss import make_cmapss_frame, write_cmapss_archive
from prescriptxai.data.cmapss import (
    add_test_labels,
    load_cmapss_archive,
    verify_row_counts,
)
from prescriptxai.data.preprocess import (
    RegimeAwarePreprocessor,
    add_training_labels,
)
from prescriptxai.data.splits import split_engines


def test_canonical_loader_returns_typed_columns_and_contiguous_cycles(tmp_path: Path) -> None:
    """Loader output has canonical names, integer provenance, and complete cycle sequences."""
    archive = write_cmapss_archive(tmp_path / "CMAPSSData.zip")

    dataset = load_cmapss_archive(archive, "FD001")

    assert dataset.train.columns.tolist() == [
        "unit_id",
        "cycle",
        "op_setting_1",
        "op_setting_2",
        "op_setting_3",
        *[f"s{i}" for i in range(1, 22)],
    ]
    assert dataset.train["unit_id"].dtype == np.dtype("int64")
    assert dataset.train["cycle"].dtype == np.dtype("int64")
    assert dataset.train["s1"].dtype == np.dtype("float64")
    assert dataset.train.notna().all().all()
    assert (
        dataset.train.groupby("unit_id")["cycle"]
        .apply(lambda cycles: np.array_equal(cycles.to_numpy(), np.arange(1, len(cycles) + 1)))
        .all()
    )
    assert (
        verify_row_counts(
            dataset, {"train": len(dataset.train), "test": len(dataset.test), "test_rul": 3}
        )["passed"]
        is True
    )


def test_row_count_integrity_rejects_mismatched_published_counts(tmp_path: Path) -> None:
    """A row-count mismatch signals an incomplete or unexpected source archive."""
    dataset = load_cmapss_archive(write_cmapss_archive(tmp_path / "archive.zip"), "FD001")
    with pytest.raises(ValueError, match="row counts do not match"):
        verify_row_counts(dataset, {"train": 1, "test": 90, "test_rul": 3})


def test_loader_rejects_noncontiguous_cycles_and_corrupted_archive(tmp_path: Path) -> None:
    """Malformed cycles and invalid ZIP files fail with actionable parser errors."""
    bad_cycle = tmp_path / "bad_cycle.zip"
    row1 = " ".join(str(value) for value in [1, 1, *range(3, 27)])
    row3 = " ".join(str(value) for value in [1, 3, *range(3, 27)])
    with ZipFile(bad_cycle, "w") as archive:
        archive.writestr("train_FD001.txt", f"{row1}\n{row3}\n")
        archive.writestr("test_FD001.txt", f"{row1}\n")
        archive.writestr("RUL_FD001.txt", "2\n")
    with pytest.raises(ValueError, match="contiguous"):
        load_cmapss_archive(bad_cycle, "FD001")

    corrupted = tmp_path / "corrupted.zip"
    corrupted.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="not a valid"):
        load_cmapss_archive(corrupted, "FD001")


@pytest.mark.parametrize(
    ("train_row", "message"),
    [
        ("1 1 2 3", "has 4 columns; expected 26"),
        ("1 1 nan " + " ".join(str(value) for value in range(4, 27)), "missing or non-numeric"),
    ],
)
def test_loader_rejects_wrong_column_count_and_nan(
    tmp_path: Path, train_row: str, message: str
) -> None:
    """A malformed schema or non-finite source value cannot enter preprocessing."""
    archive_path = tmp_path / "malformed.zip"
    valid_row = " ".join(str(value) for value in [1, 1, *range(3, 27)])
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("train_FD001.txt", f"{train_row}\n")
        archive.writestr("test_FD001.txt", f"{valid_row}\n")
        archive.writestr("RUL_FD001.txt", "1\n")
    with pytest.raises(ValueError, match=message):
        load_cmapss_archive(archive_path, "FD001")


def test_rul_and_failure_labels_are_exact_and_include_horizon_boundary() -> None:
    """Training labels use max cycle minus current cycle and include RUL == H."""
    telemetry = pd.DataFrame(
        {
            "unit_id": [1, 1, 1, 1, 2, 2],
            "cycle": [1, 2, 3, 4, 1, 2],
            "s1": [10.0, 11.0, 12.0, 13.0, 20.0, 21.0],
        }
    )

    labeled = add_training_labels(telemetry, rul_cap=None, failure_horizon=2)

    assert labeled["rul"].tolist() == [3, 2, 1, 0, 1, 0]
    assert labeled["y"].tolist() == [0, 1, 1, 1, 1, 1]
    assert labeled["failure_label"].tolist() == labeled["y"].tolist()


def test_test_rul_is_extended_back_from_truncated_final_cycle() -> None:
    """Official RUL at the last observed cycle is added to earlier observed cycles."""
    test = pd.DataFrame({"unit_id": [7, 7, 7], "cycle": [1, 2, 3]})
    labels = add_test_labels(test, pd.DataFrame({"unit_id": [7], "rul": [5]}), 6)

    assert labels["rul"].tolist() == [7, 6, 5]
    assert labels["y"].tolist() == [0, 1, 1]


def test_engine_split_is_reproducible_disjoint_and_lifetime_stratified() -> None:
    """Complete unit trajectories stay in one split and repeated seeds give identical IDs."""
    frame = make_cmapss_frame()
    left = split_engines(frame, 0.7, 0.15, 0.15, seed=71, lifetime_buckets=6)
    right = split_engines(frame, 0.7, 0.15, 0.15, seed=71, lifetime_buckets=6)
    groups = [
        set(left.train_engine_ids),
        set(left.validation_engine_ids),
        set(left.test_engine_ids),
    ]

    assert groups[0].isdisjoint(groups[1] | groups[2])
    assert groups[1].isdisjoint(groups[2])
    assert set.union(*groups) == set(frame.unit_id.unique())
    assert left.train_engine_ids == right.train_engine_ids
    assert (
        left.train.groupby("unit_id")
        .size()
        .equals(frame[frame.unit_id.isin(left.train_engine_ids)].groupby("unit_id").size())
    )


def test_preprocessor_drops_constant_sensor_and_round_trips_raw_units(
    tmp_path: Path,
) -> None:
    """Constant channels are listed and retained sensor values invert within 1e-8."""
    frame = make_cmapss_frame()
    train = frame[frame.unit_id <= 5].copy()
    preprocessor = RegimeAwarePreprocessor.fit(
        train,
        subset="FD001",
        variance_threshold=1e-8,
        regime_k=6,
        seed=7,
    )
    transformed = preprocessor.transform(frame[frame.unit_id > 5])
    restored = preprocessor.inverse_transform(transformed)

    assert "s2" in preprocessor.dropped_sensor_names
    assert "s2" not in transformed.columns
    assert "s2_scaled" not in transformed.columns
    assert preprocessor.training_engine_ids == (1, 2, 3, 4, 5)
    np.testing.assert_allclose(
        restored[list(preprocessor.retained_sensor_names)].to_numpy(),
        transformed[list(preprocessor.retained_sensor_names)].to_numpy(),
        rtol=0.0,
        atol=1e-8,
    )
    assert "operating_regime" in transformed
    saved = preprocessor.save(tmp_path / "preprocessor.pkl")
    restored_preprocessor = RegimeAwarePreprocessor.load(saved)
    pd.testing.assert_frame_equal(
        restored_preprocessor.transform(frame[frame.unit_id > 5]), transformed
    )


def test_regime_assignment_is_deterministic_for_multicondition_subset() -> None:
    """FD002 settings use fitted deterministic KMeans labels and per-regime stats."""
    frame = make_cmapss_frame(subset="FD002")
    train = frame[frame.unit_id <= 6]
    first = RegimeAwarePreprocessor.fit(train, "FD002", 1e-8, 6, 19)
    second = RegimeAwarePreprocessor.fit(train, "FD002", 1e-8, 6, 19)

    assert first.clusterer is not None
    assert first.settings_scaler is not None
    np.testing.assert_array_equal(first.assign_regimes(frame), second.assign_regimes(frame))
    assert first.regime_row_counts == second.regime_row_counts
    assert sum(first.regime_row_counts.values()) == len(train)


def test_rolling_features_are_opt_in_and_nan_inputs_are_rejected() -> None:
    """Snapshot features stay default; enabled rolling means remain unit-local."""
    frame = make_cmapss_frame()
    default = RegimeAwarePreprocessor.fit(frame, "FD001", 1e-8, 6, 3)
    rolling = RegimeAwarePreprocessor.fit(
        frame, "FD001", 1e-8, 6, 3, rolling_features=True, rolling_window=3
    )
    assert "s1_rollmean_3" not in default.transform(frame).columns
    assert "s1_rollmean_3" in rolling.transform(frame).columns
    with pytest.raises(ValueError, match="finite"):
        default.transform(frame.assign(s1=np.nan))


def test_preprocessor_rejects_empty_and_all_constant_sensor_inputs() -> None:
    """Empty data and a feature set removed entirely by variance filtering are rejected."""
    frame = make_cmapss_frame()
    with pytest.raises(ValueError, match="must not be empty"):
        RegimeAwarePreprocessor.fit(frame.iloc[:0], "FD001", 0.0, 6, 1)
    constant = frame.copy()
    for name in (f"s{i}" for i in range(1, 22)):
        constant[name] = 1.0
    with pytest.raises(ValueError, match="removed every sensor"):
        RegimeAwarePreprocessor.fit(constant, "FD001", 0.0, 6, 1)
