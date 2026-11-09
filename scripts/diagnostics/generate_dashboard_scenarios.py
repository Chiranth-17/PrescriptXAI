"""Select real archive replay presets from saved case evidence without new solves."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.provenance import source_identity


def generate(config_path: Path) -> dict[str, Any]:
    """Return case identifiers selected by the registered first-alert and example rules."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    machine_id = config["machine_id"]
    adapter = MachineRegistry().open(machine_id)
    if not isinstance(adapter, CmapssAdapter) or adapter.spec.dataset.subset != config["dataset"]:
        raise ValueError("This saved scenario source requires its registered archive adapter")
    source = Path(config["saved_results"])
    metadata = ("dataset", "model", "protocol", "population", "variant", "mode")
    rows = []
    checksum = hashlib.sha256()
    with source.open("rb") as stream:
        for line in stream:
            checksum.update(line)
            result = json.loads(line)
            if all(result[key] == config[key] for key in metadata):
                rows.append(result)
    policy = config["case_study"]
    case_study = [
        row
        for row in rows
        if row["first_alert"] is policy["first_alert"]
        and row["returned"]
        and len(row["changed_features"]) >= policy["min_changed_features"]
    ]
    chosen = []
    if case_study:
        best = min(
            case_study, key=lambda r: (abs(r["risk_before"] - policy["target_risk"]), r["case_id"])
        )
        chosen.append(("Case study (selected by rule)", best))
    for status in config["example_statuses"]:
        candidates = [row for row in rows if row["status"] == status]
        if candidates:
            chosen.append(
                (f"Replay example {len(chosen) + 1}", min(candidates, key=lambda r: r["case_id"]))
            )
    telemetry = adapter.load_official().set_index(["unit_id", "time_index"])
    entries = []
    for name, row in chosen:
        unit = int(row["engine_id"]) - config["archive_id_offset"]
        cycle = int(row["cycle"])
        observed = telemetry.loc[(unit, cycle)]
        if any(
            float(observed[feature.id]) != float(row["original"][feature.id])
            for feature in adapter.spec.measurement_features
            if feature.id in row["original"]
        ):
            raise ValueError("Saved preset differs from the observed archive row")
        entries.append({"name": name, "unit": str(unit), "time": cycle, "case_id": row["case_id"]})
    return {
        "schema_version": 1,
        "machine_id": machine_id,
        "spec_hash": adapter.spec.spec_hash,
        "population": "test",
        "source_scope": {key: config[key] for key in metadata},
        "saved_run": config["saved_run"],
        "saved_results_sha256": checksum.hexdigest(),
        "selection_config": config_path.as_posix(),
        "selection_config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "selection_source": source_identity()["git_commit"],
        "scenarios": entries,
    }


def main() -> None:
    """Write scenario metadata without overwriting an existing registration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/experiments/phase17-dashboard-v1.yaml")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = generate(args.config)
    output = args.output or Path("configs/machines") / result["machine_id"] / "scenarios.yaml"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        yaml.safe_dump(result, stream, sort_keys=False)


if __name__ == "__main__":
    main()
