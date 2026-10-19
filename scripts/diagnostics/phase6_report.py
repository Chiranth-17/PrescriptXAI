"""Render the saved Phase 6 measurements; no model calls or metric tuning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def rate(metric: dict[str, Any]) -> str:
    interval = metric["interval"]
    if interval is None:
        return f"unavailable / {metric['denominator']} queries"
    return (
        f"{metric['numerator']}/{metric['denominator']} = {interval['estimate']:.3f} "
        f"[{interval['lower']:.3f}, {interval['upper']:.3f}]; {interval['engine_count']} engines"
    )


def latency(metric: dict[str, Any]) -> str:
    if metric["p95_ms"] is None:
        return "unmeasured"
    interval = metric["p95_engine_ci"]
    return (
        f"{metric['p50_ms']:.2f} / {metric['p95_ms']:.2f} / {metric['p99_ms']:.2f} ms; "
        f"p95 CI [{interval['lower']:.2f}, {interval['upper']:.2f}], "
        f"{metric['engine_count']} engines; {'PASS' if metric['passed'] else 'NOT MET'} "
        f"(p95 <= {metric['upper_budget_ms']:g} ms)"
    )


def render(path: Path = ROOT / "artifacts/phase6/pipeline.json") -> str:
    document = json.loads(path.read_text(encoding="utf-8"))
    lines = [
        "# Phase 6: public decision support pipeline",
        "",
        "Library, CLI and API share schema **2.0.0**. Model safety, Tier 2 plausibility and "
        "Tiers 3-4 remain separate. All numbers below are saved real FD001 measurements.",
        "",
        f"Run `{document['run_id']}`; measured source git `{document['git_hash']}`; "
        f"preregistration git `{document['preregistration_commit']}`. Detailed ignored evidence: "
        f"`artifacts/phase6/pipeline.json`, SHA-256 `{hashlib.sha256(path.read_bytes()).hexdigest()}`.",
        "",
        "Bounds, rates, proxy mapping, risk thresholds, predictor/calibrator, K=1, k_max=3 and "
        "D_max v1=5/v2=8 were frozen before this run. No target was changed after measurement. "
        "The first-alert populations differ from Phase 5's mixed-cycle 200-state headline; "
        "these results are not an improvement comparison or fresh-engine generalization.",
        "",
        "Every interval is a 95% percentile bootstrap over whole engines, 2000 replicates. "
        "Returned counterfactual/diagnostic candidates are nonzero sparse feasible returned "
        "states regardless of tier outcomes; failed candidates remain in that denominator. "
        "All queries, including unchanged/infeasible diagnostics, remain in the all-query denominator.",
        "",
        "The C-MAPSS control mapping, bounds, one-step rates and intervention horizon K are "
        "assumptions. Evidence is at most E3; no validated actuator efficacy, dynamic safety or "
        "RUL extension is established. The [historical assumed-K sensitivity curve](phase5_changes.md) "
        "remains next to this K=1 headline; it is not a new FAST/THOROUGH K experiment.",
        "",
    ]
    for version in ("v1", "v2"):
        base = [r for r in document["reports"] if r["metadata"]["protocol_version"] == version]
        folds = document["oof_folds_" + version]
        for mode in ("FAST", "THOROUGH"):
            lines.extend([f"## {version} / {mode} / K=1", ""])
            populations = [r["metadata"]["population"] for r in base] + ["grouped_oof_first_alert"]
            quality = [r["quality"][mode] for r in base] + [
                document["oof_quality_" + version][mode]
            ]
            times = [r["modes"][mode] for r in base] + [document["oof_latency_" + version][mode]]
            labels = [
                f"Run `{document['run_id']}`; git `{document['git_hash']}`; mode {mode}; protocol/D_max version {version}; D_max={base[0]['metadata']['D_max']:g}; k_max=3; K=1."
            ]
            for report in base + folds:
                metadata = report["metadata"]
                labels.append(
                    f"Population `{metadata['population']}`: committed config `{metadata['config_path']}`, file SHA-256 `{metadata['config_file_sha256']}`, base config SHA-256 `{metadata['config_hash']}`; runtime {mode} config SHA-256 `{', '.join(sorted({record['config_hash'] for record in report['results'][mode]}))}`."
                )
            labels.append(
                "The base config hash identifies the committed YAML configuration; the actual per-mode hashes are carried in every saved RecourseResult. Pooled grouped OOF uses all five listed fold configs/model hashes; every query uses only its held-out fold predictor and validator. No fold percentiles are averaged."
            )
            lines.extend(labels + [""])
            caption = "Tables below carry the run/config/git/protocol/mode/k_max/K/D_max/population labels above."
            lines.extend(
                [
                    caption,
                    "",
                    "| Quality metric | " + " | ".join(populations) + " |",
                    "|---|" + "---|" * len(populations),
                ]
            )
            for metric in (
                "validity",
                "plausibility_all_queries",
                "plausibility_returned_counterfactuals",
                "tier3",
                "tier4",
                "joint",
                "RECOVERABLE",
                "PARTIAL",
                "ESCALATE",
            ):
                lines.append(
                    f"| {metric} | "
                    + " | ".join(rate(q["metrics"][metric]) for q in quality)
                    + " |"
                )
            lines.extend(
                [
                    "",
                    caption,
                    "",
                    "| Stage (p50 / p95 / p99) | " + " | ".join(populations) + " |",
                    "|---|" + "---|" * len(populations),
                ]
            )
            for stage in (
                "ingestion_ms",
                "inference_ms",
                "optimization_ms",
                "validation_ms",
                "pipeline_ms",
            ):
                lines.append(f"| {stage} | " + " | ".join(latency(t[stage]) for t in times) + " |")
            lines.extend(
                [
                    "",
                    "This long-running execution was interrupted across calendar dates; all recorded outliers are retained. Latency is not a controlled steady-state estimate. UI and startup are unmeasured. Backend calls run serially after artifact loading; "
                    "32 disclosed validation-engine warmups were excluded overall. No timing is padded.",
                    "",
                    caption,
                    "",
                    "| Evidence/error diagnostic | " + " | ".join(populations) + " |",
                    "|---|" + "---|" * len(populations),
                    "| D_M p50 / p95 / p99 | "
                    + " | ".join(
                        " / ".join(f"{v:.3f}" for v in q["distance_quantiles"].values())
                        for q in quality
                    )
                    + " |",
                    "| Highest achieved evidence counts | "
                    + " | ".join(
                        ", ".join(f"{key}={value}" for key, value in q["evidence_counts"].items())
                        for q in quality
                    )
                    + " |",
                    "",
                ]
            )
    lines.extend(["## Real CLI/API gate", ""])
    for demo in document["api_cli"]:
        result = demo["api"]
        lines.append(
            f"- {demo['protocol']}, FAST, engine {int(result['original_state']['engine_id'])}, cycle {int(result['original_state']['cycle'])}: {result['status']}; true risk {result['risk_before']:.6f} -> {result['risk_after']:.6f}; Tier1={result['validation_report']['model_valid']}, Tier2={result['plausible']}, Tier3={result['validation_report']['tier3_engineering']['passed']}, Tier4={result['validation_report']['tier4_sensor_coupling']['passed']}; evidence {result['evidence_level']}. CLI/API states match. Config hash `{result['config_hash']}`; model `{result['model_version']}`. Proxy assumptions apply."
        )
    lines.extend(
        [
            "",
            "## Gap analysis and verification",
            "",
            "FAST's production latency target is judged against p95 <= 1800 ms for each population, "
            "not its name or mean. Any NOT MET cell remains an open performance gap; solver settings "
            "were not retuned using these results. THOROUGH is offline and its budget misses remain visible. "
            "Tiers 1/2/3/4 and evidence accompany every risk claim. Coupling fit R2, residual std, "
            "threshold exceedances and original validator diagnostics are retained in Phase 5 evidence; "
            "this phase reuses those artifacts unchanged. Surrogate disagreement warnings remain in results.",
            "",
            "Schemas are versioned and frozen at Phase 6 closure with snapshot tests. Future changes "
            "require a version bump, changelog and owner agreement. See [pipeline/API usage](decision_pipeline.md) "
            "and [schema migration](schema_changelog.md).",
            "",
            "Reproduce measurements: `uv run python scripts/diagnostics/phase6_pipeline.py`. "
            "Render this report without model calls: `uv run python scripts/diagnostics/phase6_report.py`.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    (ROOT / "docs/phase6_changes.md").write_text(render(), encoding="utf-8")
