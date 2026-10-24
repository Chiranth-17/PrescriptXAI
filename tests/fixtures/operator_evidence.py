"""Build portable saved-evidence fixtures from actual independent fitted-model calls."""

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from prescriptxai.dashboard.state import load_settings
from prescriptxai.evaluation.metrics import clustered_ratio_interval
from prescriptxai.pipeline import PrescriptXAI


def write_operator_evidence(
    settings_path: Path, protocol: str = "v1", *, write: bool = True
) -> dict[str, object]:
    """Save actual fixture outcomes/CIs; this is explicitly not a Phase 7 benchmark run."""
    settings = load_settings(settings_path)
    path = next(iter(settings.profiles["FD001"].values()))
    service = PrescriptXAI.from_config(path)
    observed = pd.read_csv(settings.telemetry_path)
    results = [
        service.recommend({"actuator": float(row.actuator), "sensor": float(row.sensor)})
        for row in observed.itertuples()
    ]
    ids = observed.engine_id.tolist()

    def ci(values: list[float]) -> dict[str, float | int | None]:
        return clustered_ratio_interval(
            ids, values, [1.0] * len(values), seed=17, replicates=100, confidence=0.95
        )

    vectors = {
        "validity": [float(r.risk_after <= r.tau_safe) for r in results],
        "plausibility_all": [float(r.plausible) for r in results],
        "risk_reduction": [r.risk_before - r.risk_after for r in results],
        "sparsity_all": [float(len(r.action_features)) for r in results],
        "joint": [float(r.joint) for r in results],
    }
    funnel = {
        "observed_queries": [1.0] * len(results),
        "model_safe": vectors["validity"],
        "joint": vectors["joint"],
    }
    labels = {
        "evidence_level": sorted({r.evidence_level for r in results}),
        "config_path": [str(path)],
        "config_hash": [service.config_hash],
        "protocol": [protocol],
        "k_max": [str(service.config.recourse.k_max)],
        "K": ["1"],
        "D_max": [str(service.engine.mahalanobis.max_distance)],
        "population": ["actual_fixture_observations_not_benchmark"],
    }
    distances = [r.validation_report.tier2_distributional.measurement for r in results]
    group = {
        "labels": labels,
        "engines": len(set(ids)),
        "query_seed_observations": len(results),
        "metrics": {name: {"ci": ci(values)} for name, values in vectors.items()},
        "funnel": {
            name: {"count": sum(values), "ci": ci(values)} for name, values in funnel.items()
        },
        "D_M_quantiles": dict(
            zip(
                ("p50", "p95", "p99"),
                np.quantile(distances, [0.5, 0.95, 0.99]).tolist(),
                strict=True,
            )
        ),
    }
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    summary = {
        "manifest": {
            "run_id": "actual-operator-test-fixture",
            "git_hash": commit,
            "study_path": str(path),
            "configuration": {
                "targets": {
                    "validity": service.config.evaluation.recourse_validity_rate,
                    "plausibility_all": service.config.evaluation.physical_plausibility_rate,
                    "sparsity_all": service.config.evaluation.average_sparsity_max,
                }
            },
        },
        "groups": {
            f"FD001/mlp/{protocol}/fixture_observations/fast/full": group,
            f"FD001/mlp/{protocol}/fixture_observations/fast/L7_coupling": group,
            f"FD001/mlp/{protocol}/fixture_observations/fast/sensitivity-horizon-K-1": group,
        },
        "complete": True,
        "latency": {},
    }
    if write:
        settings.report_directory.mkdir()
        (settings.report_directory / "summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )
    return summary
