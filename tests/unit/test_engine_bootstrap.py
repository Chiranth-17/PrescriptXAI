"""Engine-cluster bootstrap coverage and failure cases."""

from statistics import NormalDist

import numpy as np
import pytest

from prescriptxai.evaluation.metrics import engine_bootstrap_interval


def test_engine_bootstrap_interval_is_deterministic_and_clustered() -> None:
    """Differing engine-level rates produce wider intervals than row-level binomial CIs."""
    engine_ids = np.repeat(np.arange(10), 10)
    outcomes = np.concatenate(
        [np.ones(50, dtype=bool), np.zeros(50, dtype=bool)]
    )
    clustered = engine_bootstrap_interval(
        engine_ids, outcomes, seed=1729, replicates=2_000
    )
    repeated = engine_bootstrap_interval(
        engine_ids, outcomes, seed=1729, replicates=2_000
    )
    p = float(outcomes.mean())
    z = NormalDist().inv_cdf(0.975)
    n = len(outcomes)
    denom = 1.0 + z**2 / n
    binomial_half_width = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    binomial_width = 2 * binomial_half_width

    assert clustered == repeated
    assert clustered.engine_count == 10
    assert clustered.observation_count == 100
    assert clustered.lower <= clustered.estimate <= clustered.upper
    assert clustered.upper - clustered.lower > binomial_width


@pytest.mark.parametrize(
    ("engine_ids", "values", "message"),
    [([], [], "at least one"), ([1, 2], [True], "matching"), ([1], [float("nan")], "finite")],
)
def test_engine_bootstrap_rejects_invalid_samples(
    engine_ids: list[int], values: list[float | bool], message: str
) -> None:
    """Reject empty, mismatched, or non-finite clustered observations."""
    with pytest.raises(ValueError, match=message):
        engine_bootstrap_interval(engine_ids, values, seed=1)
