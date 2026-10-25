"""Deterministic actual fitted decisions and an explicit golden update command."""

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import RecourseResult


def canonical_result(result: RecourseResult) -> dict[str, Any]:
    """Keep scientific/decision fields; omit only timing and path/content/run identities."""
    value = result.model_dump(mode="json")
    for key in ("run_id", "config_hash", "model_version", "timings"):
        value.pop(key, None)
    return value


def actual_snapshot(directory: Path) -> dict[str, Any]:
    """Run genuine fitted CPU MLP decisions for safe, solvable and rejected actions."""
    service = PrescriptXAI.from_config(directory / "pipeline.yaml")
    state = {"actuator": -2.0, "sensor": 2.0}
    recoverable = service.recommend(state)
    low, high = -2.0, 2.0
    for _ in range(45):
        middle = (low + high) / 2
        if service.assess({**state, "actuator": middle}).risk > 0.4:
            low = middle
        else:
            high = middle
    results = {
        "recoverable": recoverable,
        "partial": service.validate_controls(state, {"actuator": (low + high) / 2}),
        "escalate": service.validate_controls(state, {"actuator": 100.0}),
        "safe": service.recommend({"actuator": 2.0, "sensor": 2.0}),
    }
    return {name: canonical_result(result) for name, result in results.items()}


def assert_snapshot(actual: object, expected: object, *, path: str = "root") -> None:
    """Compare exact discrete structure and documented abs/relative numeric tolerances."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and actual.keys() == expected.keys(), path
        for key in expected:
            assert_snapshot(actual[key], expected[key], path=f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), path
        for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
            assert_snapshot(left, right, path=f"{path}[{index}]")
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        assert isinstance(actual, (int, float)) and not isinstance(actual, bool), path
        assert np.isfinite(actual) and np.isfinite(expected), path
        assert np.isclose(actual, expected, atol=1e-6, rtol=1e-5), (path, actual, expected)
    else:
        assert actual == expected, (path, actual, expected)


def update_golden(path: Path, snapshot: dict[str, Any], *, update: bool = False) -> None:
    """Refuse any golden write without the explicit update flag, including first creation."""
    if not update:
        raise PermissionError("golden changes require --update-golden")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    """Emit actual results, compare a stored golden, or explicitly update it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--golden", type=Path)
    parser.add_argument("--update-golden", action="store_true")
    args = parser.parse_args()
    if args.update_golden and args.golden is None:
        parser.error("--update-golden requires --golden")
    snapshot = actual_snapshot(args.artifacts)
    if args.golden:
        if args.update_golden:
            update_golden(args.golden, snapshot, update=True)
        else:
            assert_snapshot(snapshot, json.loads(args.golden.read_text(encoding="utf-8")))
    else:
        print(json.dumps(snapshot, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
