"""Select real archive replay presets from saved case evidence without new solves."""

from __future__ import annotations

import argparse
from pathlib import Path

from prescriptxai.scenarios import generate_scenarios as generate
from prescriptxai.scenarios import write_scenarios


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
    write_scenarios(result, output)


if __name__ == "__main__":
    main()
