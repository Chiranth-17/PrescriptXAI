"""Provision only registered verification bytes from an operator-trusted workspace."""

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
from contextlib import closing
from datetime import UTC, datetime
from itertools import chain
from pathlib import Path

import yaml


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_path(root, name):
    relative = Path(name)
    if relative.anchor or ".." in relative.parts or ":" in name or "\\" in name:
        raise ValueError(f"Verification asset path must be portable and relative: {name}")
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"Verification asset leaves the selected workspace: {name}")
    return target


def registered_assets(root):
    science = json.loads(
        (root / "tests/regression/cmapss_baseline.json").read_text(encoding="utf-8")
    )["input_hashes"]
    quality = yaml.safe_load(
        (root / "configs/experiments/phase12-clean-clone-gate-attempt2-v1.yaml").read_text(
            encoding="utf-8"
        )
    )["supplemental_required_inputs"]
    assets = dict(science)
    dashboard = yaml.safe_load(
        (root / "configs/experiments/phase18-verification-inputs-v1.yaml").read_text(
            encoding="utf-8"
        )
    )["required_inputs"]
    for name, value in chain(quality.items(), dashboard.items()):
        if name in assets and assets[name] != value["sha256"]:
            raise ValueError(f"Conflicting registered asset: {name}")
        assets[name] = value["sha256"]
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--reuse-cache",
        action="store_true",
        help="Copy local authenticated cache for exact-key revalidation by the gate",
    )
    args = parser.parse_args()
    root, source = Path.cwd().resolve(), args.source.resolve(strict=True)
    if root == source:
        raise ValueError("Select a separate trusted source workspace")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Provisioning requires a clean committed destination")
    assets = registered_assets(root)
    if registered_assets(source) != assets:
        raise ValueError("Source verification registrations differ from this checkout")
    tracked = set(subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0"))
    restore = []
    for name, expected in assets.items():
        origin, target = safe_path(source, name), safe_path(root, name)
        if file_hash(origin) != expected:
            raise ValueError(f"Trusted source asset SHA-256 differs: {name}")
        if target.exists() and file_hash(target) != expected:
            if name not in tracked:
                raise ValueError(f"Existing destination differs, preserve and inspect it: {name}")
            actual_blob = subprocess.check_output(
                ["git", "hash-object", "--path", name, str(origin)], text=True
            ).strip()
            head_blob = subprocess.check_output(
                ["git", "rev-parse", "HEAD:" + name], text=True
            ).strip()
            if actual_blob != head_blob:
                raise ValueError(f"Registered asset differs from committed source: {name}")
            restore.append(name)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = root / "artifacts/phase18" / ("provision-" + stamp)
    output.mkdir(parents=True, exist_ok=False)
    copied = []
    for name, expected in assets.items():
        origin, target = safe_path(source, name), safe_path(root, name)
        if target.is_file() and file_hash(target) == expected:
            continue
        if target.exists():
            backup = output / "originals" / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
        if file_hash(target) != expected:
            raise ValueError(f"Copied asset differs: {name}")
        copied.append(name)
    if restore:
        subprocess.run(["git", "add", "--", *restore], check=True)
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Provisioning changed source semantics, inspect retained files")
    cache_receipt = None
    if args.reuse_cache:
        cache = source / "artifacts/regression-cache/records.sqlite3"
        key = cache.with_suffix(".key")
        destination = root / "artifacts/regression-cache/records.sqlite3"
        if destination.exists() or destination.with_suffix(".key").exists():
            raise ValueError("Destination cache already exists, preserve it")
        if len(key.read_bytes()) != 32:
            raise ValueError("Source cache authentication key is invalid")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with (
            closing(sqlite3.connect(cache.as_uri() + "?mode=ro", uri=True)) as original,
            closing(sqlite3.connect(destination)) as target,
        ):
            original.backup(target)
            if target.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Cache snapshot integrity failure")
            entries = target.execute("SELECT count(*) FROM entries").fetchone()[0]
        shutil.copy2(key, destination.with_suffix(".key"))
        cache_receipt = {
            "source": str(cache),
            "snapshot_sha256": file_hash(destination),
            "entries": entries,
            "admission": "Every hit remains subject to normal signature, exact context and scientific comparison checks",
        }
    receipt = {
        "passed": True,
        "source_workspace": str(source),
        "required_assets": len(assets),
        "registered_sha256": assets,
        "copied": copied,
        "tracked_byte_restoration": restore,
        "source_tree_unchanged": True,
        "cache": cache_receipt,
        "new_solves": 0,
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"passed": True, "assets": len(assets), "receipt": str(output / "complete.json")}
        )
    )


if __name__ == "__main__":
    main()
