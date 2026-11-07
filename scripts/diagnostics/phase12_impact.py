"""Recompute complete old/new headline intervals from immutable audited observations."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter
from contextlib import closing
from itertools import groupby
from pathlib import Path

import yaml
from scripts.diagnostics.phase12_baseline import atomic_json, read_design
from scripts.diagnostics.phase12_regression import native_margins, verify_files

from prescriptxai.evaluation.experiments import file_hash, source_revision
from prescriptxai.evaluation.metrics import clustered_ratio_interval, experiment_metric_values


def summarize(records: list[dict], config: dict) -> dict:
    vectors = experiment_metric_values(records, config["headline_safe_threshold"])
    settings = config["bootstrap"]
    intervals = {}
    for name in config["metrics"]:
        numerator, denominator = vectors[name]
        intervals[name] = {
            **clustered_ratio_interval(
                [r["engine_id"] for r in records],
                numerator,
                denominator,
                seed=settings["seed"],
                replicates=settings["replicates"],
                confidence=settings["confidence"],
            ),
            "numerator": sum(numerator),
        }
    return {
        "all_queries": len(records),
        "returned": sum(r["returned"] for r in records),
        "not_returned": sum(not r["returned"] for r in records),
        "failed_model_validity": sum(
            r["risk_after"] > config["headline_safe_threshold"] for r in records
        ),
        "failed_joint": sum(not r["joint"] for r in records),
        "triage_counts": dict(Counter(r["status"] for r in records)),
        "metrics": intervals,
    }


def interval_text(interval: dict) -> str:
    if interval["estimate"] is None:
        return f"undefined; N={interval['engine_count']}; denominator=0"
    return (
        f"{interval['estimate']:.9g} [{interval['lower']:.9g}, {interval['upper']:.9g}]; "
        f"N={interval['engine_count']}; d={interval['denominator']:g}"
    )


def generate(config_path: Path, output: Path) -> None:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    source = source_revision(require_clean=True)
    if output.exists():
        raise FileExistsError("Impact output exists; preserve the previous report")
    if config["bootstrap"]["cluster"] != "whole_engine":
        raise ValueError("Every confidence interval must bootstrap whole engines")
    audit_path = Path(config["independent_audit"])
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["passed"] is not True or audit["fixture_promotion_go"] is not True:
        raise ValueError("Complete independent pair audit has not passed")
    pin_path = audit_path.with_name("pin.json")
    verify_files({pin_path.as_posix(): audit["pin_sha256"]})
    pin = json.loads(pin_path.read_text(encoding="utf-8"))
    approved_hashes = {
        name.replace("\\", "/"): digest for name, digest in pin["evidence_hashes"].items()
    }
    design_path = Path(config["baseline_design"])
    design = read_design(design_path)
    databases = [
        Path(config["historical_database"]),
        *[Path(run) / "records.sqlite3" for run in config["corrected_runs"]],
    ]
    approved = [*databases, design_path]
    for run in config["corrected_runs"]:
        approved.extend([Path(run) / "manifest.json", Path(run) / "complete.json"])
    verify_files({path.as_posix(): approved_hashes[path.as_posix()] for path in approved})
    for run in config["corrected_runs"]:
        manifest = json.loads((Path(run) / "manifest.json").read_text(encoding="utf-8"))
        complete = json.loads((Path(run) / "complete.json").read_text(encoding="utf-8"))
        if (
            manifest["source"] != config["corrected_source"]
            or manifest["run_id"] != Path(run).name
            or complete["actual_success"] is not True
            or complete["source"] != manifest["source"]
            or complete["queries"] != 32116
            or manifest["design"]["historical_source"] != config["historical_source"]
        ):
            raise ValueError(f"Audited source/completion labels differ: {run}")
    pinned = {
        path.as_posix(): file_hash(path)
        for path in (
            *approved,
            config_path,
            audit_path,
            pin_path,
        )
    }
    result = {
        "run_id": config["run_id"],
        "analysis_source": source,
        "analysis_config": config_path.as_posix(),
        "config_sha256": file_hash(config_path),
        "config": config,
        "input_hashes": pinned,
        "groups": {},
        "borderline_counts": {},
        "evidence_limit": "E1 validity; E2 distribution; at most E3 proxy assumptions",
        "scope": "Reused test engines; reproducibility analysis, not fresh generalization",
    }
    text = [
        "# Complete C-MAPSS arithmetic-repair impact",
        "",
        f"Analysis run `{config['run_id']}`; source `{source}`; config SHA256 `{file_hash(config_path)}`.",
        "",
        "Real benchmark: NASA C-MAPSS FD001 and FD002. Results stay separate by dataset, model, protocol and population.",
        "Each interval is a 95% whole-engine bootstrap (2,000 replicates, seed 1729); N is engines, d is the disclosed denominator.",
        "Validity is calibrated risk <=0.20 (E1). Tier 2 is statistical plausibility (E2); Tiers 3–4 use legacy proxy assumptions (at most E3).",
        "Joint is an additional stricter metric. Failed queries remain in all-query denominators. No physical benefit, safety certification or RUL-extension claim.",
        "Intervals equal to [1,1] describe the empirical bootstrap sample and do not establish certainty for unseen engines.",
        "Parallel replay timings are retained in the source archives and do not certify serial latency.",
        "",
        f"Historical run `{design['historical_run']}` / source `{config['historical_source']}` remains immutable.",
        f"Corrected runs `{Path(config['corrected_runs'][0]).name}` and `{Path(config['corrected_runs'][1]).name}` / source `{config['corrected_source']}`.",
        "Earlier failed Phase 12 intermediate arithmetic runs are superseded for headline use by the demonstrated graph/layout repair; their records remain preserved.",
        "",
    ]
    output.mkdir(parents=True)
    border_path = output / "borderline.csv"
    borderline_counts = Counter()
    with (
        closing(
            sqlite3.connect(databases[0].resolve().as_uri() + "?mode=ro", uri=True)
        ) as connection,
        border_path.open("w", encoding="utf-8", newline="") as border_stream,
    ):
        writer = csv.writer(border_stream)
        writer.writerow(
            ["run", "case_id", "group", "predicate", "margin", "passed", "feature", "units"]
        )
        for alias, database in zip(("a", "b"), databases[1:], strict=True):
            connection.execute(
                f"ATTACH DATABASE ? AS {alias}", (database.resolve().as_uri() + "?mode=ro",)
            )
            if connection.execute(f"SELECT COUNT(*) FROM {alias}.records").fetchone()[0] != 32116:
                raise ValueError(f"Audited full corpus count differs: {alias}")
        rows = connection.execute(
            "SELECT json_extract(a.payload,'$.group'),h.payload,a.payload,b.payload,c.payload "
            "FROM a.records a JOIN main.records h USING(case_id) JOIN b.records b USING(case_id) "
            "JOIN a.cases c USING(case_id) "
            "ORDER BY json_extract(a.payload,'$.group'),a.case_id"
        )
        for group, joined in groupby(rows, key=lambda row: row[0]):
            columns = [[], [], []]
            for row in joined:
                delta_min = json.loads(row[4])["config"]["pipeline"]["delta_min"]
                for label, column, payload in zip(
                    ("historical", "corrected_a", "corrected_b"), columns, row[1:4], strict=True
                ):
                    record = json.loads(payload)
                    column.append(record)
                    for name, margin, passed, feature in native_margins(
                        record, delta_min=delta_min
                    ):
                        if abs(margin) <= config["borderline_absolute_margin"]:
                            borderline_counts[f"{label}/{name}"] += 1
                            writer.writerow(
                                [
                                    label,
                                    record["case_id"],
                                    group,
                                    name,
                                    margin,
                                    passed,
                                    feature,
                                    "native units of the named predicate",
                                ]
                            )
            if len(columns[0]) != design["group_counts"][group]:
                raise ValueError(f"Complete registered group missing: {group}")
            first = columns[1][0]
            configs = {
                label: {r["config_path"].replace("\\", "/"): r["config_hash"] for r in column}
                for label, column in zip(
                    ("historical", "corrected_a", "corrected_b"), columns, strict=True
                )
            }
            labels = {
                key: first[key]
                for key in (
                    "dataset",
                    "model",
                    "protocol",
                    "population",
                    "mode",
                    "seed",
                    "k_max",
                    "K",
                    "D_max",
                )
            }
            labels.update(
                machine_id="cmapss_" + first["dataset"].lower(),
                spec_hash="not yet applicable: legacy feature taxonomy before Phase13",
                effective_config_hashes=configs,
            )
            reports = dict(
                zip(
                    ("historical", "corrected_a", "corrected_b"),
                    [summarize(column, config) for column in columns],
                    strict=True,
                )
            )
            for report in reports.values():
                if (
                    report["metrics"]["validity"]["engine_count"]
                    != design["group_engine_counts"][group]
                ):
                    raise ValueError(f"Engine population differs: {group}")
            result["groups"][group] = {"labels": labels, "runs": reports}
            text.extend(
                [
                    f"## {group}",
                    "",
                    "Labels: `" + json.dumps(labels, sort_keys=True) + "`.",
                    "",
                    "| Metric | Historical estimate [CI]; N; d | Corrected A | Corrected B |",
                    "|---|---|---|---|",
                ]
            )
            for metric in config["metrics"]:
                cells = [interval_text(report["metrics"][metric]) for report in reports.values()]
                text.append("| " + " | ".join([metric, *cells]) + " |")
            for name, report in reports.items():
                counts = {key: value for key, value in report.items() if key != "metrics"}
                text.append(f"\n{name} query denominators: `{json.dumps(counts, sort_keys=True)}`.")
            text.append("")
    if len(result["groups"]) != design["expected_groups"]:
        raise ValueError("Impact analysis is missing registered groups")
    for name, digest in pinned.items():
        if file_hash(Path(name)) != digest:
            raise ValueError(f"Impact input changed: {name}")
    if source_revision(require_clean=True) != source:
        raise ValueError("Impact analysis source changed")
    result["borderline_counts"] = dict(borderline_counts)
    result["borderline_file"] = border_path.name
    result["borderline_sha256"] = file_hash(border_path)
    text.extend(
        [
            "## Borderline predicates",
            "",
            "Every tier, individual check, alert/safety gate and triage-improvement margin within the registered1e-6 native-unit envelope is retained in the adjacent `borderline.csv`.",
            "No margin is rounded for classification and no verdict changes. Counts include structural zero margins; these do not imply a failed check.",
            "",
            f"Borderline export SHA256 `{result['borderline_sha256']}`; counts by run/predicate:",
            "",
            "```json",
            json.dumps(result["borderline_counts"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    atomic_json(output / "report.json", result)
    (output / "report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    atomic_json(
        output / "complete.json",
        {
            "actual_success": True,
            "groups": len(result["groups"]),
            "queries_each": sum(
                report["runs"]["corrected_a"]["all_queries"] for report in result["groups"].values()
            ),
            "report_sha256": file_hash(output / "report.json"),
            "source": source,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/experiments/phase12-impact-v1.yaml")
    )
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    generate(arguments.config, arguments.output)
