"""Run the prescribed packaging gate with source-bound native receipts for each stage."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


def source():
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise ValueError("make verify requires a clean committed checkout")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reuse-only", action="store_true")
    args = parser.parse_args()
    revision = source()
    make = shutil.which("mingw32-make") or shutil.which("make")
    if not make:
        raise FileNotFoundError("Install make or mingw32-make")
    output = args.output or Path("artifacts/phase18") / (
        "verify-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + f"-{os.getpid()}"
    )
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    environment = dict(os.environ)
    environment["PSX_QUALITY_SUBSET_RECEIPT"] = str(output / "subset-location.json")
    environment["COVERAGE_FILE"] = str(output / ".coverage")
    if not args.reuse_only:
        environment.pop("PSX_QUALITY_REGRESSION_REUSE_ONLY", None)
    stages = []
    started = time.perf_counter()
    receipt = {
        "source": revision,
        "started_utc": datetime.now(UTC).isoformat(),
        "actual_success": False,
        "stages": stages,
    }
    (output / "launch.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    commands = [
        ("check", [make, "check", "REUSE_ONLY=1" if args.reuse_only else "REUSE_ONLY=0"]),
        ("security", [make, "security", f"SECURITY_OUTPUT={(output / 'security').as_posix()}"]),
        ("build", [sys.executable, "-m", "build", "--outdir", str(output / "dist")]),
        ("smoke", None),
        ("docs", [make, "docs"]),
    ]
    try:
        for name, command in commands:
            if name == "smoke":
                wheels = list((output / "dist").glob("*.whl"))
                if len(wheels) != 1:
                    raise ValueError("Build must produce exactly one wheel")
                command = [
                    sys.executable,
                    "scripts/packaging/smoke.py",
                    "--wheel",
                    str(wheels[0]),
                    "--output",
                    str(output / "wheel-smoke.json"),
                ]
            clock = time.perf_counter()
            with (
                (output / f"{name}.stdout.log").open("x", encoding="utf-8") as stdout,
                (output / f"{name}.stderr.log").open("x", encoding="utf-8") as stderr,
            ):
                result = subprocess.run(command, env=environment, stdout=stdout, stderr=stderr)
            stages.append(
                {
                    "name": name,
                    "command": command,
                    "native_exit": result.returncode,
                    "elapsed_seconds": time.perf_counter() - clock,
                }
            )
            (output / f"{name}.exit").write_text(str(result.returncode) + "\n", encoding="utf-8")
            if result.returncode:
                raise RuntimeError(f"{name} exited {result.returncode}. Inspect {output}")
            if source() != revision:
                raise ValueError("Source changed during packaging verification")
            if name == "check":
                shutil.copy2("coverage.json", output / "coverage.json")
                subset = Path(json.loads((output / "subset-location.json").read_text())["path"])
                evidence = json.loads(subset.read_text())
                if (
                    not evidence["actual_success"]
                    or evidence["source"] != revision
                    or evidence["requested"] != 15525
                    or evidence["reused"] + evidence["recomputed"] != 15525
                    or evidence["accepted_known_differences"]
                    or evidence["float_exact_different_cases"]
                ):
                    raise ValueError("Fixed subset evidence differs from this verify gate")
                receipt["subset"] = {
                    "path": str(subset),
                    "sha256": hashlib.sha256(subset.read_bytes()).hexdigest(),
                    **{
                        key: evidence[key]
                        for key in ("requested", "reused", "recomputed", "context_sha256")
                    },
                }
            if name == "security":
                scan = json.loads((output / "security/complete.json").read_text())
                if (
                    not scan["passed"]
                    or scan["source"] != revision
                    or scan["blocking_findings"]
                    or scan["errors"]
                ):
                    raise ValueError("Security receipt did not pass for this source")
        receipt["actual_success"] = True
    except BaseException as error:
        receipt["error"] = str(error)
        raise
    finally:
        receipt.update(
            elapsed_seconds=time.perf_counter() - started, ended_utc=datetime.now(UTC).isoformat()
        )
        (output / "complete.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        print(
            json.dumps({"actual_success": receipt["actual_success"], "output": str(output)}),
            flush=True,
        )


if __name__ == "__main__":
    main()
