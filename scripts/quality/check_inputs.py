"""Require the supplemental files used by the coverage suite."""

from hashlib import file_digest
from pathlib import Path

import yaml


def main():
    registration = Path("configs/experiments/phase12-clean-clone-gate-attempt2-v1.yaml")
    assets = yaml.safe_load(registration.read_text(encoding="utf-8"))[
        "supplemental_required_inputs"
    ]
    for name, metadata in assets.items():
        with Path(name).open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != metadata["sha256"]:
                raise ValueError(f"Quality input SHA-256 differs: {name}")


if __name__ == "__main__":
    main()
