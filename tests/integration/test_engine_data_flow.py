"""End-to-end in-memory checks for split and preprocessing leakage barriers."""

import pandas as pd

from prescriptxai.data.preprocess import add_training_labels, fit_feature_scaler
from prescriptxai.data.splits import split_engines


def test_engine_split_precedes_labels_and_scaler_fit() -> None:
    """Held-out engine telemetry does not influence training scaler or labels."""
    frame = pd.DataFrame(
        [
            {"engine_id": engine, "cycle": cycle, "sensor": float(engine * cycle)}
            for engine in range(1, 31)
            for cycle in range(1, 8)
        ]
    )
    partitioned = split_engines(frame, 0.7, 0.15, 0.15, seed=91)
    labeled_train = add_training_labels(partitioned.train, rul_cap=5, failure_horizon=2)
    scaler = fit_feature_scaler(labeled_train, ("sensor",))

    assert set(scaler.training_engine_ids) == set(partitioned.train_engine_ids)
    assert set(scaler.training_engine_ids).isdisjoint(partitioned.validation_engine_ids)
    assert set(scaler.training_engine_ids).isdisjoint(partitioned.test_engine_ids)
    assert labeled_train.groupby("engine_id")["rul"].min().eq(0).all()
