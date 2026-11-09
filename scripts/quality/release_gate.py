"""Measure the real check, full-regression and documentation targets once each, in order."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


def source_revision():
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("Release verification requires a clean checkout")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def pin(path):
    with path.open("rb") as stream:
        return {"path": str(path), "sha256": hashlib.file_digest(stream, "sha256").hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-only", action="store_true")
    args = parser.parse_args()
    make = shutil.which("mingw32-make") or shutil.which("make")
    if make is None:
        raise FileNotFoundError("A compatible make executable is required")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = Path("artifacts/quality") / f"release-{stamp}-{os.getpid()}"
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    if args.reuse_only:
        environment["PRESCRIPTXAI_REGRESSION_REUSE_ONLY"] = "1"
    source = source_revision()
    context_sha = None
    environment["PRESCRIPTXAI_SUBSET_RECEIPT"] = str((output / "subset-location.json").resolve())
    total, stages = time.perf_counter(), []
    for target in ("check", "regression-full", "docs"):
        command = [make, target] + (["REUSE_ONLY=1"] if args.reuse_only else [])
        if target == "regression-full":
            command.append(f"REGRESSION_OUTPUT={(output / 'full').as_posix()}")
        started = time.perf_counter()
        with (
            (output / f"{target}.stdout.log").open("x", encoding="utf-8") as stdout,
            (output / f"{target}.stderr.log").open("x", encoding="utf-8") as stderr,
        ):
            result = subprocess.run(command, env=environment, stdout=stdout, stderr=stderr)
        (output / f"{target}.exit").write_text(f"{result.returncode}\n", encoding="utf-8")
        stages.append(
            {
                "target": target,
                "command": command,
                "native_exit": result.returncode,
                "elapsed_seconds": time.perf_counter() - started,
            }
        )
        if result.returncode == 0:
            if source_revision() != source:
                raise ValueError("Source changed across release stages")
            if target in {"check", "regression-full"}:
                if target == "check":
                    location = json.loads(
                        (output / "subset-location.json").read_text(encoding="utf-8")
                    )
                    path = Path(location["path"])
                    coverage = output / "coverage.json"
                    shutil.copyfile("coverage.json", coverage)
                    stages[-1]["coverage"] = pin(coverage)
                    expected_tier = "subset"
                else:
                    path = output / "full/complete.json"
                    expected_tier = "full"
                evidence = json.loads(path.read_text(encoding="utf-8"))
                if (
                    evidence["actual_success"] is not True
                    or evidence["source"] != source
                    or evidence["tier"] != expected_tier
                    or evidence["reused"] + evidence["recomputed"] != evidence["requested"]
                    or (expected_tier == "full" and evidence["requested"] != 32116)
                    or (args.reuse_only and (not evidence["reuse_only"] or evidence["recomputed"]))
                ):
                    raise ValueError("Regression stage receipt does not bind this release")
                stages[-1]["evidence"] = pin(path)
                stages[-1].update({k: evidence[k] for k in ("requested", "reused", "recomputed")})
                if target == "regression-full" and evidence["context_sha256"] != context_sha:
                    raise ValueError("Regression execution context changed between release stages")
                context_sha = evidence["context_sha256"]
        (output / "stages.json").write_text(json.dumps(stages, indent=2) + "\n", encoding="utf-8")
        print(
            f"{target}: native{result.returncode}, {stages[-1]['elapsed_seconds']:.2f}s ({output})",
            flush=True,
        )
        if result.returncode:
            raise SystemExit(result.returncode)
    receipt = {
        "actual_success": True,
        "source": source,
        "context_sha256": context_sha,
        "stages": stages,
        "elapsed_seconds": time.perf_counter() - total,
        "reuse_only": args.reuse_only,
        "completed_utc": datetime.now(UTC).isoformat(),
    }
    (output / "complete.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
