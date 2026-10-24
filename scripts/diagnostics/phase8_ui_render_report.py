"""Audit and summarize the preregistered, actual-browser Operator UI build callbacks."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import yaml

from prescriptxai.config import load_config
from prescriptxai.evaluation.metrics import engine_bootstrap_interval


def summarize(study_path: Path, directory: Path) -> dict:
    study = yaml.safe_load(study_path.read_text(encoding="utf-8"))
    config_hash = hashlib.sha256(study_path.read_bytes()).hexdigest()
    records = [
        json.loads(line)
        for line in (directory / "samples.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {
        (int(engine), int(cycle), repeat)
        for engine, cycle in study["observations"].items()
        for repeat in range(1, study["repeats_per_engine"] + 1)
    }
    observed = [(r["engine_id"], r["cycle"], r["repeat"]) for r in records]
    if len(records) != study["expected_samples"] or len(observed) != len(set(observed)):
        raise ValueError("missing or duplicate registered UI callback records")
    if set(observed) != expected:
        raise ValueError("UI callback population differs from preregistration")
    if any(
        r["run_id"] != study["run_id"]
        or r["study_sha256"] != config_hash
        or r["measurement_source"] != study["measurement_source"]
        for r in records
    ):
        raise ValueError("UI callback provenance differs from preregistration")
    failures = sum(r["status"] != "complete" for r in records)
    if failures:
        raise ValueError(
            f"{failures} UI callback failures retained; no complete performance verdict"
        )
    values = np.asarray([r["server_ui_build_ms"] for r in records], dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("UI timing records must be finite and nonnegative")
    bootstrap = study["bootstrap"]
    interval = engine_bootstrap_interval(
        [r["engine_id"] for r in records],
        values.tolist(),
        seed=bootstrap["seed"],
        replicates=bootstrap["replicates"],
        confidence=bootstrap["confidence"],
        statistic=lambda sample: float(np.quantile(sample, study["quantile"])),
    )
    budget = load_config(Path(study["profile"])).latency_budget.dashboard_max_ms
    result = {
        "run_id": study["run_id"],
        "study_path": str(study_path),
        "study_sha256": config_hash,
        "measurement_source": study["measurement_source"],
        "profile": study["profile"],
        "mode": study["mode"],
        "population": study["population"],
        "count": len(records),
        "engine_count": interval.engine_count,
        "failures": failures,
        "discarded_samples": study["warmups_discarded"],
        "p50_ms": float(np.quantile(values, 0.5)),
        "p95_ms": interval.estimate,
        "p99_ms": float(np.quantile(values, 0.99)),
        "p95_engine_ci": asdict(interval),
        "upper_budget_ms": budget,
        "passed": interval.estimate <= budget,
        "precision_ms": 0.01,
        "scope": study["scope"],
        "assumptions": study["assumptions"],
        "records_sha256": hashlib.sha256((directory / "samples.jsonl").read_bytes()).hexdigest(),
    }
    (directory / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--study", type=Path, default=Path("configs/experiments/phase8-ui-render.yaml")
    )
    parser.add_argument(
        "--directory", type=Path, default=Path("artifacts/phase8/ui-render-20261024-v1")
    )
    args = parser.parse_args()
    try:
        result = summarize(args.study, args.directory)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
