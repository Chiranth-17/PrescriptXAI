"""Run the registered finite FD001 telemetry spoofing sample with the deployed checks."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from hashlib import file_digest
from pathlib import Path

import yaml

from prescriptxai.adapters.cmapss import CmapssAdapter
from prescriptxai.adapters.registry import MachineRegistry
from prescriptxai.core.data_quality import RecommendationWithheld
from prescriptxai.evaluation.runner import _worker_threads
from prescriptxai.machines import scope_archive_runtime
from prescriptxai.pipeline import PrescriptXAI

PLAN = Path("configs/experiments/phase16-spoofing-v1.yaml")


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def decision_receipt(result):
    return {
        "alert": result.alert,
        "status": result.status,
        "action_feasible": result.action_feasible,
        "risk_before": result.risk_before,
        "risk_after": result.risk_after,
        "config_hash": result.config_hash,
        "run_id": result.run_id,
        "validation": result.validation_report.model_dump(mode="json"),
    }


def attempt(decision, observed, candidate):
    try:
        state, context = decision._observed(candidate)
    except RecommendationWithheld as error:
        return {"outcome": "input_withheld", "reason": str(error)}
    result = decision._runtime.recommend(state, context, "fast")
    evidence = decision_receipt(result)
    if not result.alert:
        return {"outcome": "no_alert", "spoofed_decision": evidence}
    try:
        issued = decision._checked_result(result)
    except RecommendationWithheld as error:
        return {"outcome": "decision_withheld", "reason": str(error), "spoofed_decision": evidence}
    controls = {name: issued.new_state[name] for name in issued.action_features}
    if not controls:
        raise RuntimeError("a published alert recommendation had no actionable settings")
    reapplied = decision.validate_controls(observed, controls, "fast")
    return {
        "outcome": "unsafe_on_original" if not reapplied.joint else "passes_on_original",
        "spoofed_decision": evidence,
        "applied_controls": controls,
        "original_recheck": decision_receipt(reapplied),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    target = parser.parse_args().output
    if subprocess.check_output(["git", "status", "--porcelain"]).strip():
        raise ValueError("register the design and run from clean committed source")
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    design = yaml.safe_load(PLAN.read_text(encoding="utf-8"))
    for name, expected in design["input_sha256"].items():
        if digest(Path(name)) != expected:
            raise ValueError(f"registered input has changed: {name}")
    target.mkdir(parents=True, exist_ok=False)
    scope = {
        "plan_sha256": digest(PLAN),
        "plan": PLAN.as_posix(),
        "source": source,
        "started_utc": datetime.now(UTC).isoformat(),
        "machine_id": design["machine_id"],
        "spec_hash": design["spec_hash"],
        "protocol": design["protocol"],
        "population": design["population"],
        "K": design["K"],
        "max_changes": design["max_changes"],
        "planned_attacks": len(design["case_ids"]) * len(design["features"]) * 2,
    }
    (target / "launch.json").write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")
    _worker_threads(design["cpu_threads"])
    adapter = MachineRegistry().open(design["machine_id"])
    if not isinstance(adapter, CmapssAdapter) or adapter.spec.spec_hash != design["spec_hash"]:
        raise ValueError("machine spec does not match the preregistration")
    archive = adapter.load_official()
    runtime = PrescriptXAI.from_config(Path(design["profile"]))
    decision = scope_archive_runtime(adapter.spec, design["protocol"], runtime)
    bounds = {feature.name: feature.bounds for feature in runtime.engine.taxonomy.features}
    if set(design["features"]) - runtime.engine.taxonomy.dependent_feature_names():
        raise ValueError("the spoofing features must be declared dependent sensors")
    scenarios = yaml.safe_load(Path(design["scenarios"]).read_text(encoding="utf-8"))["scenarios"]
    by_case = {item["case_id"]: item for item in scenarios}
    totals, caught, missed = Counter(), Counter(), Counter()
    units = set()
    with (target / "cases.jsonl").open("x", encoding="utf-8") as stream:
        for case_id in design["case_ids"]:
            item = by_case[case_id]
            unit, cycle = item["unit"], item["time"]
            units.add(unit)
            observed = archive.loc[
                (archive["unit_id"].astype(str) == unit) & (archive["time_index"] <= cycle)
            ].copy()
            if observed.empty or observed["time_index"].iloc[-1] != cycle:
                raise ValueError("the registered observation is missing")
            base_state, base_context = decision._observed(observed)
            baseline = decision_receipt(
                decision._runtime.recommend(base_state, base_context, "fast")
            )
            for name in design["features"]:
                lower, upper = bounds[name].minimum, bounds[name].maximum
                if lower is None or upper is None:
                    raise ValueError("spoofing bounds are unresolved")
                before = float(observed[name].iloc[-1])
                if not lower <= before <= upper:
                    raise ValueError("registered observation lies outside the attack bounds")
                for endpoint in (lower, upper):
                    spoofed = observed.copy()
                    # Choose one bounded sensor edit, leaving the entire history and controls alone.
                    after = before + design["step_fraction"] * (endpoint - before)
                    spoofed.loc[spoofed.index[-1], name] = after
                    record = attempt(decision, observed, spoofed)
                    outcome = record["outcome"]
                    totals[outcome] += 1
                    if outcome == "decision_withheld":
                        caught.update(record["spoofed_decision"]["validation"]["failing_tiers"])
                    if outcome == "unsafe_on_original":
                        missed.update(record["original_recheck"]["validation"]["failing_tiers"])
                    stream.write(
                        json.dumps(
                            {
                                "case_id": case_id,
                                "unit": unit,
                                "cycle": cycle,
                                "sensor": name,
                                "original": before,
                                "spoofed": after,
                                "bound": endpoint,
                                "baseline": baseline,
                                **record,
                            },
                            allow_nan=False,
                        )
                        + "\n"
                    )
                    stream.flush()
    count = sum(totals.values())
    if count != scope["planned_attacks"] or digest(PLAN) != scope["plan_sha256"]:
        raise ValueError("registered attack count or design has changed")
    for name, expected in design["input_sha256"].items():
        if digest(Path(name)) != expected:
            raise ValueError(f"registered input changed during execution: {name}")
    (target / "complete.json").write_text(
        json.dumps(
            {
                **scope,
                "completed_utc": datetime.now(UTC).isoformat(),
                "observed_units": len(units),
                "attempts": count,
                "counts": totals,
                "tier_blocks_on_spoofed_input": caught,
                "tier_failures_on_original_input": missed,
                "unsafe_publication_rate": totals["unsafe_on_original"] / count,
                "evidence": "FD001 simulated archive and proxy checks",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
