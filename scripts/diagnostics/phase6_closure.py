"""Verify final CLI/API delivery against saved real development states, without tuning."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from prescriptxai.api import create_app
from prescriptxai.pipeline import PrescriptXAI

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts/phase6"


def run() -> None:
    source = json.loads((OUTPUT / "pipeline.json").read_text(encoding="utf-8"))
    if "oof_latency_v2" not in source:
        raise ValueError("serial population benchmark must finish before closure checks")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    document = {
        "run_id": "phase6-closure-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "git_hash": commit,
        "main_run_id": source["run_id"],
        "scope": "delivery smoke checks on saved development states, not new population estimates",
        "api_cli": [],
    }
    destination = OUTPUT / "closure_checks.json"
    if destination.exists():
        raise FileExistsError("preserve previous closure evidence before another execution")
    for version in ("v1", "v2"):
        config = ROOT / f"configs/experiments/phase6-pipeline-{version}.yaml"
        pipeline = PrescriptXAI.from_config(config)
        records = next(
            r for r in source["reports"]
            if r["metadata"]["protocol_version"] == version
            and r["metadata"]["population"] == "development_first_alert"
        )["results"]["FAST"]
        for status in ("RECOVERABLE", "PARTIAL", "ESCALATE"):
            matches = sorted(
                (r for r in records if r["status"] == status),
                key=lambda r: (r["original_state"]["engine_id"], r["original_state"]["cycle"]),
            )
            if not matches:
                continue
            state = matches[0]["original_state"]
            with TestClient(create_app(pipeline)) as client:
                response = client.post("/recommend", json={"state": state, "mode": "fast"})
            command = [
                "uv", "run", "prescriptxai", "recommend", "--engine-id",
                str(int(state["engine_id"])), "--cycle", str(int(state["cycle"])),
                "--config", str(config), "--mode", "fast",
            ]
            cli = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            if response.status_code != 200 or cli.returncode != 0:
                raise ValueError(f"CLI/API gate failed: {response.text} {cli.stdout} {cli.stderr}")
            result = response.json()
            cli_result = json.loads(cli.stdout)
            for field in ("status", "new_state", "risk_after", "config_hash", "mode"):
                if cli_result[field] != result[field]:
                    raise ValueError(f"CLI/API mismatch in {field}")
            if result["status"] != status:
                raise ValueError("final source differs from saved development triage; investigate")
            document["api_cli"].append({
                "protocol": version, "population": "development_first_alert_delivery_smoke",
                "config_path": str(config.relative_to(ROOT)), "state": state,
                "api": result, "cli": cli_result,
            })
        if version == "v1":
            csv = OUTPUT / "closure_state.csv"
            pd.DataFrame([records[0]["original_state"]]).to_csv(csv, index=False)
            latency_path = OUTPUT / "closure_latency.json"
            cli = subprocess.run([
                "uv", "run", "prescriptxai", "latency-bench", str(csv), "--config", str(config),
                "--output", str(latency_path),
            ], cwd=ROOT, capture_output=True, text=True, check=False)
            if cli.returncode != 0:
                raise ValueError(f"CLI latency-bench failed: {cli.stdout} {cli.stderr}")
            measured = json.loads(cli.stdout)
            if measured != json.loads(latency_path.read_text(encoding="utf-8")):
                raise ValueError("latency CLI stdout/file mismatch")
            document["latency_cli"] = measured
            document["latency_scope"] = "one development engine; delivery demonstration only"
    destination.write_text(json.dumps(document, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    run()
