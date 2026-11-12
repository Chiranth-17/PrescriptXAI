"""Prepare a recorded FD001 and explicitly synthetic CSV demo, then serve both locally."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import ExitStack, suppress
from datetime import UTC, datetime
from pathlib import Path

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "configs/experiments/phase18-packaging-v1.yaml"


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".pending.json")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def prepare(workspace: Path, archive: Path | None = None) -> dict:
    """Refuse partial replacements and verify every reused demo input and fitted file."""
    from prescriptxai.adapters.registry import MachineRegistry
    from prescriptxai.config import load_config
    from prescriptxai.data.download import download_archive, verify_archive
    from prescriptxai.machines import fit_machine, load_machine_decision, save_machine_fit
    from prescriptxai.provenance import source_identity
    from prescriptxai.reproduce import reproduce
    from prescriptxai.workspace import initialize_workspace

    design = yaml.safe_load(DESIGN.read_text(encoding="utf-8"))
    receipt_path = workspace / "demo.json"
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (
            receipt.get("actual_success") is not True
            or receipt["design_sha256"] != file_hash(DESIGN)
            or any(
                not (workspace / name).is_file() or file_hash(workspace / name) != sha
                for name, sha in receipt["files"].items()
            )
        ):
            raise ValueError(
                "Demo files changed. Preserve this workspace and choose a new DEMO_WORKSPACE."
            )
        return receipt
    if workspace.exists():
        raise ValueError("Incomplete demo workspace. Preserve it and choose a new DEMO_WORKSPACE.")
    initialize_workspace(workspace)
    sample = workspace / "configs/machines" / design["sample_machine"]
    sample.mkdir(parents=True)
    shutil.copy2(ROOT / "templates/sample_csv/machine.yaml", sample / "machine.yaml")
    from prescriptxai.machine_spec import load_machine_spec

    if load_machine_spec(sample / "machine.yaml").schema_version != design["sample_machine_schema"]:
        raise ValueError("Sample machine schema differs from the registered packaging design")
    with (workspace / "data/raw/sample.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("device", "tick", "setting", "ambient", "remaining"))
        for unit in range(design["sample_units"]):
            for step in range(design["sample_steps"]):
                writer.writerow(
                    (
                        f"unit-{unit:02}",
                        step,
                        step + unit / 100,
                        (unit % 3) / 10,
                        design["sample_steps"] - 1 - step,
                    )
                )
    previous = Path.cwd()
    started = time.perf_counter()
    try:
        os.chdir(workspace)
        config = load_config(Path("configs/default.yaml"))
        target = config.data.root / config.data.archive_name
        if archive is not None:
            verify_archive(archive, design["cmapss_archive_sha256"])
            shutil.copy2(archive, target)
        else:
            download_archive(
                config.data.dataset_url,
                target,
                config.data.download_timeout_seconds,
                design["cmapss_archive_sha256"],
            )
        verify_archive(target, design["cmapss_archive_sha256"])
        print(
            "Preparing the registered FD001 reproduction. First preparation can take 10–20 minutes.",
            flush=True,
        )
        reproduce(Path("configs/default.yaml"))
        print("Fitting the separately labeled synthetic CSV sample.", flush=True)
        sample_config = config.model_copy(deep=True)
        sample_config.model.xgb_n_estimators = design["sample_model_estimators"]
        fit = fit_machine(
            MachineRegistry().open(design["sample_machine"]), sample_config, "v1", "xgb"
        )
        save_machine_fit(fit)
        load_machine_decision(fit.spec, "v1")
        names = [
            path
            for directory in (Path("configs"), Path("data/raw"), Path("artifacts"))
            for path in directory.rglob("*")
            if path.is_file()
        ]
        receipt = {
            "actual_success": True,
            "prepared_utc": datetime.now(UTC).isoformat(),
            "design_sha256": file_hash(DESIGN),
            "source": source_identity(),
            "machines": [spec.machine_id for spec in MachineRegistry().list()],
            "synthetic_machines": [design["sample_machine"]],
            "elapsed_seconds": time.perf_counter() - started,
            "files": {path.as_posix(): file_hash(path) for path in sorted(names)},
            "evidence_scope": "Local demonstration. FD001 replay and synthetic CSV are distinct populations. No physical efficacy measurement.",
        }
        write_json(receipt_path, receipt)
        return receipt
    finally:
        os.chdir(previous)


def request_json(url: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def wait_ready(url: str, process: subprocess.Popen, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Demo listener exited {process.returncode}. Inspect its log.")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    raise TimeoutError(f"Demo listener did not become ready at {url}")


def serve(workspace: Path, smoke: bool) -> None:
    """Own two loopback listeners and terminate only these children on completion or Ctrl+C."""
    design = yaml.safe_load(DESIGN.read_text(encoding="utf-8"))
    ports = [
        int(os.environ.get(name, design[key]))
        for name, key in (
            ("PSX_DEMO_API_PORT", "api_port"),
            ("PSX_DEMO_DASHBOARD_PORT", "dashboard_port"),
        )
    ]
    if ports[0] == ports[1] or any(not 1 <= port <= 65535 for port in ports):
        raise ValueError("Demo API and dashboard need distinct ports between 1 and 65535")
    for port in ports:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("PRESCRIPTXAI_")
    }
    environment.update(PRESCRIPTXAI_API__HOST="127.0.0.1", PRESCRIPTXAI_API__PORT=str(ports[0]))
    environment["PYTHONUNBUFFERED"] = "1"
    output = workspace / "logs" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    commands = [
        [sys.executable, "-m", "prescriptxai.cli", "serve", "--local-demo"],
        [
            sys.executable,
            "-m",
            "prescriptxai.cli",
            "dashboard",
            "--local-demo",
            "--port",
            str(ports[1]),
        ],
    ]
    children = []
    with ExitStack() as stack:
        try:
            for name, command in zip(("api", "dashboard"), commands, strict=True):
                log = stack.enter_context((output / f"{name}.log").open("x", encoding="utf-8"))
                children.append(
                    subprocess.Popen(
                        command,
                        cwd=workspace,
                        env=environment,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    )
                )
            api = f"http://127.0.0.1:{ports[0]}"
            dashboard = f"http://127.0.0.1:{ports[1]}"
            wait_ready(api + "/machines", children[0], design["startup_timeout_seconds"])
            wait_ready(
                dashboard + "/_stcore/health", children[1], design["startup_timeout_seconds"]
            )
            print(
                f"API {api}/docs\nDashboard {dashboard}\nLogs {output}\nCtrl+C stops both listeners.",
                flush=True,
            )
            if smoke:
                from prescriptxai.adapters.registry import MachineRegistry

                previous = Path.cwd()
                checks = []
                try:
                    os.chdir(workspace)
                    for spec in MachineRegistry().list():
                        window = MachineRegistry().open(spec.machine_id).load().iloc[:5]
                        score = request_json(
                            api + f"/machines/{spec.machine_id}/assess",
                            {"rows": window.to_dict(orient="records")},
                        )
                        checks.append(
                            {
                                "machine_id": spec.machine_id,
                                "synthetic": spec.synthetic,
                                "assessment": score,
                            }
                        )
                finally:
                    os.chdir(previous)
                write_json(
                    output / "smoke.json",
                    {
                        "passed": True,
                        "checks": checks,
                        "dashboard_http_health": True,
                        "browser_rendering": "separate acceptance evidence",
                    },
                )
                print(
                    json.dumps({"passed": True, "machines": [x["machine_id"] for x in checks]}),
                    flush=True,
                )
            else:
                while all(child.poll() is None for child in children):
                    time.sleep(0.5)
                raise RuntimeError(f"A demo listener stopped. Inspect {output}")
        finally:
            owned = []
            for child in children:
                if child.poll() is None:
                    try:
                        parent = psutil.Process(child.pid)
                        owned.extend(reversed(parent.children(recursive=True)))
                        owned.append(parent)
                    except psutil.NoSuchProcess:
                        pass
            for process in owned:
                with suppress(psutil.NoSuchProcess):
                    process.terminate()
            _, alive = psutil.wait_procs(owned, timeout=10)
            for process in alive:
                with suppress(psutil.NoSuchProcess):
                    process.kill()
            for child in children:
                child.wait(timeout=10)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path("artifacts/demo"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    prepare(workspace, args.archive.resolve() if args.archive else None)
    if not args.prepare_only:
        try:
            serve(workspace, args.smoke)
        except KeyboardInterrupt:
            print("Stopped the local demo listeners.", flush=True)


if __name__ == "__main__":
    main()
