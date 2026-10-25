"""Machine-readable and human-readable reports from measured evaluation objects."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from prescriptxai.evaluation.experiments import StudyConfig
from prescriptxai.evaluation.metrics import EvaluationSummary
from prescriptxai.evaluation.runner import (
    DirectionConsistency,
    EvaluationRun,
    fitted_engine_provenance,
)
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.provenance import source_identity


def sensitivity_comparison_variant(variant: str) -> str:
    """Keep quantile comparisons within the matching distribution-threshold method."""
    if variant.startswith("sensitivity-Dmax-"):
        return "ablation-Dmax-method-" + variant.removeprefix("sensitivity-Dmax-").split("-q-")[0]
    return "full"


def summarize_experiment_group(
    records: list[dict[str, Any]], study: StudyConfig, *, safe_threshold: float
) -> dict[str, Any]:
    """Pool seeds while resampling complete engines, disclosing solver-seed variation.

    An engine draw includes all its states and solver seeds. Across-seed standard deviation
    measures solver variability on these fixed fitted predictors, not training uncertainty.
    """
    from prescriptxai.evaluation.metrics import clustered_ratio_interval, experiment_metric_values

    ids = [int(r["engine_id"]) for r in records]
    vectors = experiment_metric_values(records, safe_threshold)
    metrics = {}
    seeds = sorted({r["seed"] for r in records})
    for name, (numerator, denominator) in vectors.items():
        interval = clustered_ratio_interval(
            ids,
            numerator,
            denominator,
            seed=study.diagnostic_seed,
            replicates=study.bootstrap_replicates,
            confidence=study.bootstrap_confidence,
        )
        by_seed = []
        for seed in seeds:
            indices = [i for i, row in enumerate(records) if row["seed"] == seed]
            total = sum(denominator[i] for i in indices)
            if total:
                by_seed.append(sum(numerator[i] for i in indices) / total)
        metrics[name] = {
            "ci": interval,
            "seed_values": by_seed,
            "seed_mean": float(np.mean(by_seed)) if by_seed else None,
            "seed_std": float(np.std(by_seed, ddof=1)) if len(by_seed) > 1 else None,
        }
    features = Counter(n for r in records for n in r["changed_features"])
    errors = [
        abs(r["surrogate_after"] - r["risk_after"])
        for r in records
        if r["surrogate_after"] is not None
    ]
    false_safe = [
        r
        for r in records
        if r["surrogate_after"] is not None
        and r["surrogate_after"] <= safe_threshold
        and r["risk_after"] > safe_threshold
    ]
    drop = [r["risk_before"] - r["risk_after"] for r in records]
    histogram, edges = np.histogram(drop, bins=study.risk_reduction_edges)
    strata: dict[str, Any] = {}
    for field, bins in (
        ("risk_before", study.risk_band_edges),
        ("rul", study.rul_bucket_edges),
        ("life_fraction", study.life_fraction_edges),
    ):
        groups = []
        for low, high in zip(bins, bins[1:], strict=False):
            selected = [r for r in records if low <= r[field] < high]
            if selected:
                v = experiment_metric_values(selected, safe_threshold)
                groups.append(
                    {
                        "lower": low,
                        "upper": high,
                        "queries": len(selected),
                        "metrics": {
                            name: clustered_ratio_interval(
                                [r["engine_id"] for r in selected],
                                *v[name],
                                seed=study.diagnostic_seed,
                                replicates=study.bootstrap_replicates,
                                confidence=study.bootstrap_confidence,
                            )
                            for name in ("validity", "plausibility_all", "tier3", "tier4", "joint")
                        },
                    }
                )
        strata[field] = groups
    funnel = {}
    strata["first_alert_versus_all_same_mode"] = {}
    for label, selected in (
        ("all_alerts", records),
        ("first_alert", [r for r in records if r["first_alert"]]),
    ):
        vectors_subset = experiment_metric_values(selected, safe_threshold)
        strata["first_alert_versus_all_same_mode"][label] = {
            name: clustered_ratio_interval(
                [r["engine_id"] for r in selected],
                *vectors_subset[name],
                seed=study.diagnostic_seed,
                replicates=study.bootstrap_replicates,
                confidence=study.bootstrap_confidence,
            )
            for name in (
                "validity",
                "plausibility_all",
                "tier3",
                "tier4",
                "joint",
                "risk_reduction",
            )
        }
    active = np.ones(len(records))
    for label, flags in (
        ("alerts", np.ones(len(records))),
        ("nonzero_feasible_counterfactual_returned", [r["returned"] for r in records]),
        ("tier1", [r["risk_after"] <= safe_threshold for r in records]),
        ("tier2", [r["tier2"] for r in records]),
        ("tier3", [r["tier3"] for r in records]),
        ("tier4", [r["tier4"] for r in records]),
        ("joint", [r["action_feasible"] for r in records]),
    ):
        active *= np.asarray(flags, dtype=float)
        funnel[label] = {
            "count": int(active.sum()),
            "ci": clustered_ratio_interval(
                ids,
                active.tolist(),
                [1.0] * len(ids),
                seed=study.diagnostic_seed,
                replicates=study.bootstrap_replicates,
                confidence=study.bootstrap_confidence,
            ),
        }
    distances = np.asarray([r["mahalanobis_after"] for r in records])
    return {
        "query_seed_observations": len(records),
        "unique_engine_cycle_queries": len({(r["engine_id"], r["cycle"]) for r in records}),
        "engines": len(set(ids)),
        "seeds": seeds,
        "metrics": metrics,
        "funnel": funnel,
        "strata": strata,
        "first_alert_queries": sum(r["first_alert"] for r in records),
        "per_feature_change_frequency": {k: v / len(records) for k, v in features.items()},
        "failure_reasons": dict(Counter(r["reason"] for r in records if r["reason"])),
        "triage_target_relative": dict(Counter(r["status"] for r in records)),
        "risk_reduction_histogram": {"edges": edges.tolist(), "counts": histogram.tolist()},
        "surrogate_MAE": float(np.mean(errors)) if errors else None,
        "surrogate_false_safe_share_all": len(false_safe) / len(records) if records else None,
        "model_safe_and_distance_increased_share": sum(
            r["risk_after"] <= safe_threshold and r["mahalanobis_after"] > r["mahalanobis_before"]
            for r in records
        )
        / len(records)
        if records
        else None,
        "D_M_quantiles": dict(
            zip(
                ("p50", "p95", "p99"),
                map(float, np.quantile(distances, [0.5, 0.95, 0.99]))
                if len(distances)
                else [None] * 3,
                strict=True,
            )
        ),
        "coupling_margin_min": min(
            (r["tier4_margin"] for r in records if r["tier4_margin"] is not None), default=None
        ),
    }


def write_study_report(
    directory: Path, study: StudyConfig, *, safe_threshold: float
) -> dict[str, Any]:
    """Generate reproducible JSON/CSV and standalone Markdown/HTML from saved checkpoints."""
    import html
    import sqlite3

    import plotly.graph_objects as go

    from prescriptxai.evaluation.experiments import audit_stage_completion, file_hash, load_study

    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest["configuration"] != study.model_dump(mode="json")
        or manifest["headline_safe_threshold"] != safe_threshold
    ):
        raise ValueError("report study/headline threshold differs from measurement manifest")
    if (
        file_hash(Path(manifest["study_path"])) != manifest["study_file_sha256"]
        or load_study(Path(manifest["study_path"])) != study
    ):
        raise ValueError("study file differs from measurement manifest")
    if file_hash(Path(manifest["frozen_config_path"])) != manifest["frozen_config_sha256"]:
        raise ValueError("frozen config hash differs from measurement manifest")
    connection = sqlite3.connect(directory / "records.sqlite3")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    try:
        with (directory / "records.jsonl").open("w", encoding="utf-8") as stream:
            for (payload,) in connection.execute("SELECT payload FROM records ORDER BY case_id"):
                row = json.loads(payload)
                stream.write(payload + "\n")
                grouped[row["group"]].append(row)
    finally:
        connection.close()
    summaries = {}
    csv_rows = []
    lines = [
        "# Phase 7 experimental report",
        "",
        f"Run `{manifest['run_id']}`; source `{manifest['git_hash']}`.",
        "",
        "All intervals bootstrap whole engines, including their states and solver seeds.",
        "Means and sample standard deviations across seeds describe solver variability only.",
        "Triage and evidence in sensitivity runs are relative to their stated solver target;",
        f"headline model validity always uses {safe_threshold:g}.",
        "Saved diagnostics exist for every query; returns mean nonzero feasible action.",
        "",
        "## Assumptions and evidence",
        "",
        *[f"- {s}" for s in study.assumptions],
        "",
        "Evidence reaches at most E3 under sensor-proxy assumptions. Simulated trajectory health:",
        "**not evaluated**. No RUL extension is claimed. UI/startup are unmeasured.",
        "",
    ]
    computed = {
        group: summarize_experiment_group(rows, study, safe_threshold=safe_threshold)
        for group, rows in grouped.items()
    }
    for group, rows in sorted(grouped.items()):
        summary = computed[group]
        labels = {
            key: sorted({str(r[key]) for r in rows})
            for key in (
                "config_hash",
                "config_path",
                "protocol",
                "k_max",
                "K",
                "D_max",
                "population",
                "solver_tau_safe",
                "evidence_level",
            )
        }
        summaries[group] = {"labels": labels, **summary}
        lines += [
            f"## {group}",
            "",
            f"Run `{manifest['run_id']}`; git `{manifest['git_hash']}`.",
            "",
            f"Labels: `{json.dumps(labels, sort_keys=True)}`.",
            f"Solver seeds: `{summary['seeds']}`; training seeds: model_metadata.json.",
            "",
            "| Metric | Engine CI (engines) | Mean/std | Difference | Target | Gap | Diagnosis |",
            "|---|---|---|---|---|---|---|",
        ]
        for name, metric in summary["metrics"].items():
            ci = metric["ci"]
            target = study.targets.get(name)
            value = ci["estimate"]
            variant = rows[0]["variant"]
            comparison = sensitivity_comparison_variant(variant)
            baseline = computed.get(group.rsplit("/", 1)[0] + "/" + comparison)
            baseline_value = baseline["metrics"][name]["ci"]["estimate"] if baseline else None
            difference = (
                value - baseline_value if value is not None and baseline_value is not None else None
            )
            gap = (
                None
                if target is None or value is None
                else (
                    max(0.0, value - target)
                    if name.startswith("sparsity")
                    else max(0.0, target - value)
                )
            )
            diagnosis = (
                "Not evaluated: denominator is zero."
                if value is None
                else "No design target for this diagnostic."
                if target is None
                else "Met."
                if gap == 0
                else f"Not met; Tier2={summary['metrics']['plausibility_all']['ci']['estimate']}, "
                f"Tier4={summary['metrics']['tier4']['ci']['estimate']}; see ladder and margins."
            )
            lines.append(
                f"| {name} | {value} [{ci['lower']}, {ci['upper']}] ({ci['engine_count']} engines)"
                f" | {metric['seed_mean']} ± {metric['seed_std']} | {difference} | {target} | {gap}"
                f" | {diagnosis} |"
            )
            csv_rows.append(
                {
                    "run_id": manifest["run_id"],
                    "git_hash": manifest["git_hash"],
                    "group": group,
                    **{k: json.dumps(v) for k, v in labels.items()},
                    "metric": name,
                    **ci,
                    "seed_mean": metric["seed_mean"],
                    "seed_std": metric["seed_std"],
                    "target": target,
                    "gap": gap,
                    "diagnosis": diagnosis,
                    "comparison_variant": comparison,
                    "difference_vs_comparison": difference,
                }
            )
        lines += [
            "",
            "Comparison is the matching method at its preregistered quantile for quantile",
            "sensitivity, and paired full search for other variants.",
            "Funnel, strata, change frequencies, failure reasons, surrogate errors, D_M and",
            "coupling margins are retained in summary.json with this group's labels.",
            "",
        ]
    reference_path, latency_path = directory / "reference.json", directory / "latency.json"
    reference = (
        json.loads(reference_path.read_text(encoding="utf-8")) if reference_path.exists() else {}
    )
    latency = (
        json.loads(latency_path.read_text(encoding="utf-8")) if latency_path.exists() else None
    )
    reference_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in reference.values():
        if "oracle" in item:
            reference_groups[item["oracle"]["group"]].append(item["oracle"])
    oracle_summary: dict[str, Any] = {}
    from prescriptxai.evaluation.metrics import clustered_ratio_interval

    for group, items in reference_groups.items():
        labels = summaries[group]["labels"]
        lines += [
            f"## Finite reference: {group}",
            "",
            f"Run `{manifest['run_id']}`; git `{manifest['git_hash']}`; "
            f"labels `{json.dumps(labels)}`.",
            "",
            "| Per-failed-query classification | Count | Engine CI (engines) |",
            "|---|---|---|",
        ]
        oracle_summary[group] = {}
        for classification in sorted({item["classification"] for item in items}):
            flags = [float(item["classification"] == classification) for item in items]
            ci = clustered_ratio_interval(
                [item["engine_id"] for item in items],
                flags,
                [1.0] * len(items),
                seed=study.diagnostic_seed,
                replicates=study.bootstrap_replicates,
                confidence=study.bootstrap_confidence,
            )
            oracle_summary[group][classification] = ci
            lines.append(
                f"| {classification} | {int(sum(flags))}/{len(items)} | "
                f"{ci['estimate']} [{ci['lower']}, {ci['upper']}] ({ci['engine_count']} engines) |"
            )
        lines += [
            "",
            "A finite miss is unresolved. Only reproduced-search empty actuator intervals",
            "are algebraic infeasibility certificates under the configured proxy assumptions.",
            "",
        ]
    if latency is not None:
        lines += [
            "## Serial latency",
            "",
            f"Run `{manifest['run_id']}`; git `{manifest['git_hash']}`; "
            f"labels `{json.dumps(latency['labels'])}`.",
            "",
            "| Mode / stage | Calls | p50/p95/p99 ms | p95 engine CI (engines) | Budget | Pass |",
            "|---|---|---|---|---|---|",
        ]
        for mode, stages in latency["modes"].items():
            for stage, values in stages.items():
                lines.append(
                    f"| {mode}/{stage} | {values['count']} | "
                    f"{values['p50_ms']} / {values['p95_ms']} / {values['p99_ms']} | "
                    f"{values['p95_engine_ci']} ({values['engine_count']} engines) | "
                    f"{values['upper_budget_ms']} | {values['passed']} |"
                )
    stages_path = directory / "stages.json"
    stage_status = (
        json.loads(stages_path.read_text(encoding="utf-8")) if stages_path.exists() else {}
    )
    verified_stages = audit_stage_completion(directory, manifest, study)
    complete = all(verified_stages.values())
    lines.insert(
        2,
        "Status: complete measured study."
        if complete
        else "Status: PARTIAL; required stages remain unfinished.",
    )
    document = {
        "manifest": manifest,
        "groups": summaries,
        "stage_status": stage_status,
        "verified_stages": verified_stages,
        "complete": complete,
        "reference": reference,
        "oracle_summary": oracle_summary,
        "latency": latency,
        "trajectory_health": "not evaluated",
        "no_RUL_extension": True,
    }
    (directory / "model_metadata.json").write_text(
        json.dumps(manifest.get("model_metadata", {}), indent=2, allow_nan=False), encoding="utf-8"
    )
    (directory / "summary.json").write_text(
        json.dumps(document, indent=2, allow_nan=False), encoding="utf-8"
    )
    pd.DataFrame(csv_rows).to_csv(directory / "metrics.csv", index=False)
    markdown = "\n".join(lines)
    (directory / "report.md").write_text(markdown, encoding="utf-8")
    figure = go.Figure()
    curves: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for group, summary in summaries.items():
        if "sensitivity-horizon-K-" in group:
            curves[group.rsplit("/", 1)[0]].append((int(summary["labels"]["K"][0]), summary))
    for group, points in sorted(curves.items()):
        ordered = sorted(points)
        cis = [s["metrics"]["validity"]["ci"] for _, s in ordered]
        figure.add_scatter(
            x=[k for k, _ in ordered],
            y=[ci["estimate"] for ci in cis],
            error_y={
                "type": "data",
                "symmetric": False,
                "array": [ci["upper"] - ci["estimate"] for ci in cis],
                "arrayminus": [ci["estimate"] - ci["lower"] for ci in cis],
            },
            mode="lines+markers",
            name=group,
        )
    figure.update_layout(
        title="Validity versus assumed K (sensitivity; headline K=1)",
        xaxis_title="Assumed intervention steps K",
        yaxis_title="True-model validity",
    )
    figure.write_html(directory / "K_curve.html", include_plotlyjs=True)
    histogram_figure = go.Figure()
    for group, summary in sorted(summaries.items()):
        histogram = summary["risk_reduction_histogram"]
        edges = histogram["edges"]
        histogram_figure.add_bar(
            x=[f"[{a:g}, {b:g})" for a, b in zip(edges, edges[1:], strict=False)],
            y=histogram["counts"],
            name=group,
        )
    histogram_figure.update_layout(
        title="Full risk-reduction histogram; failures retained",
        xaxis_title="True calibrated risk reduction",
        yaxis_title="Query × solver-seed observations",
    )
    histogram_figure.write_html(directory / "risk_reduction.html", include_plotlyjs=True)
    (directory / "report.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Phase 7 report</title>"
        "<style>body{max-width:1200px;margin:2rem auto;font:14px monospace}"
        "pre{white-space:pre-wrap}</style>"
        f"<pre>{html.escape(markdown)}</pre><h2>Metric tables</h2>"
        + pd.DataFrame(csv_rows).to_html(index=False, escape=True)
        + figure.to_html(full_html=False, include_plotlyjs=True)
        + histogram_figure.to_html(full_html=False, include_plotlyjs=False),
        encoding="utf-8",
    )
    return document


def build_evaluation_provenance(
    engine: PrescriptXAIEngine,
    held_out_rows: pd.DataFrame,
    artifact_paths: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Snapshot effective settings and fingerprint the exact benchmark inputs/artifacts."""
    fitted = fitted_engine_provenance(engine)
    config = engine.config.model_dump(mode="json")
    taxonomy = engine.taxonomy.model_dump(mode="json")
    config_json = json.dumps(config, sort_keys=True, allow_nan=False)
    identity = source_identity()
    source_commit = identity.get("git_commit")
    source_dirty = identity.get("tracked_source_dirty")
    fingerprints = {}
    for name, path in sorted((artifact_paths or {}).items()):
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        fingerprints[name] = {"path": str(path), "sha256": digest}
    ids = (
        sorted(int(value) for value in held_out_rows["engine_id"].unique())
        if "engine_id" in held_out_rows
        else []
    )
    warnings = [
        f"{name} engine provenance is unavailable; its disjointness is unverified"
        for name, values in fitted.items()
        if values is None
    ]
    versions: dict[str, str | None] = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost", "torch"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    metadata: dict[str, Any] = {
        "effective_configuration": config,
        "effective_configuration_sha256": hashlib.sha256(config_json.encode()).hexdigest(),
        "resolved_taxonomy": taxonomy,
        "feature_names": list(engine.model.feature_names),
        "fitted_engine_ids": fitted,
        "holdout_engine_ids": ids,
        "held_out_row_count": len(held_out_rows),
        "held_out_columns": list(held_out_rows.columns),
        "held_out_rows_sha256": hashlib.sha256(
            pd.util.hash_pandas_object(held_out_rows, index=False).to_numpy().tobytes()
        ).hexdigest(),
        "artifact_fingerprints": fingerprints,
        "model_training_configuration_sha256": engine.model.config_hash,
        "model_training_git_commit": engine.model.git_commit,
        "evaluation_git_commit": source_commit,
        "evaluation_source_identity": identity,
        "evaluation_tracked_source_dirty": source_dirty,
        "resolved_mahalanobis_max_distance": engine.mahalanobis.max_distance,
        "mahalanobis_threshold_method": engine.mahalanobis.threshold_method,
        "mahalanobis_threshold_quantile": engine.mahalanobis.threshold_quantile,
        "model_type": engine.model.model_type,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "dependency_versions": versions,
        "provenance_warnings": warnings,
        "sampling_policy": "seeded uniform sample from high-risk states with feasible intervals",
        "latency_scope": (
            "pipeline measures the backend recommendation call, including optimizer and validation;"
            " "
            "telemetry ingestion and dashboard rendering are not included or inferred"
        ),
    }
    return metadata


def write_evaluation_report(
    run: EvaluationRun,
    json_path: Path,
    markdown_path: Path,
    run_configuration: Mapping[str, Any] | None = None,
    *,
    provenance: Mapping[str, Any] | None = None,
) -> None:
    """Write records and computed metrics to JSON and Markdown files."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_document = {
        "summary": run.summary.to_dict(),
        "counterfactual_direction_consistency": run.direction_consistency.__dict__,
        "infeasible_high_risk_states": run.infeasible_high_risk_states,
        "actionable_high_risk_states": (
            run.summary.eligible_high_risk_states - run.infeasible_high_risk_states
        ),
        "recourse_search_configuration": dict(run_configuration or {}),
        "provenance": dict(provenance or {}),
        "records": [record.__dict__ for record in run.records],
    }
    json_path.write_text(json.dumps(json_document, indent=2, allow_nan=False), encoding="utf-8")
    markdown_path.write_text(
        render_markdown(
            run.summary,
            run.direction_consistency,
            (
                sum(record.changed_features for record in run.records) / len(run.records)
                if run.records
                else None
            ),
            run.infeasible_high_risk_states,
            run_configuration,
            (
                sum(record.true_model_grid_ms for record in run.records) / len(run.records)
                if run.records
                else None
            ),
            (
                sum(record.true_model_evaluations for record in run.records) / len(run.records)
                if run.records
                else None
            ),
            provenance=provenance,
        ),
        encoding="utf-8",
    )


def _format_metric(value: float | None) -> str:
    """Display missing values as unmeasured and numeric outcomes to four places."""
    return "Unmeasured" if value is None else f"{value:.4f}"


def render_markdown(
    summary: EvaluationSummary,
    direction: DirectionConsistency | None = None,
    mean_returned_action_sparsity: float | None = None,
    infeasible_high_risk_states: int | None = None,
    run_configuration: Mapping[str, Any] | None = None,
    mean_true_model_grid_ms: float | None = None,
    mean_true_model_evaluations: float | None = None,
    *,
    provenance: Mapping[str, Any] | None = None,
) -> str:
    """Render dynamically computed measurements and target statuses."""
    lines = [
        "# PrescriptXAI Evaluation",
        "",
        f"Eligible high-risk held-out states: {summary.eligible_high_risk_states}",
        f"Evaluated states: {summary.evaluated_states}",
        f"Model-valid candidates: {summary.model_valid_count}",
        f"Physically plausible candidates: {summary.physically_plausible_count}",
        f"Successful sparse recourses: {summary.successful_recourse_count}",
        "",
        "| Metric | Measured | Target | Status |",
        "|---|---:|---:|---|",
    ]
    metrics: dict[str, Any] = {
        "Model validity rate": summary.recourse_validity_rate,
        "Optimizer sparse-action feasibility rate": summary.recourse_feasibility_rate,
        "Joint successful recourse rate": summary.successful_recourse_rate,
        "Joint physical plausibility rate (Tiers 2–4)": summary.physical_plausibility_rate,
        "Distributional plausibility rate (Tier 2)": summary.tier2_plausibility_rate,
        "Tier 3 engineering rate": summary.tier3_engineering_rate,
        "Tier 4 coupling rate": summary.tier4_coupling_rate,
        "Average sparsity": summary.average_sparsity,
        "Mean risk reduction": summary.mean_risk_reduction,
    }
    for name, metric in metrics.items():
        status = "unmeasured" if metric.passed is None else ("pass" if metric.passed else "fail")
        lines.append(f"| {name} | {_format_metric(metric.value)} | {metric.target} | {status} |")
    if direction is not None:
        lines.extend(
            (
                "",
                "## Counterfactual direction consistency",
                "",
                f"Similar state pairs (scaled distance ≤ {direction.similarity_radius:g}): "
                f"{direction.similar_pair_count}",
                f"Pairwise sign agreement: {_format_metric(direction.pairwise_sign_agreement)}",
            )
        )
    if mean_returned_action_sparsity is not None:
        lines.extend(
            (
                "Mean changed features across all returned candidates: "
                f"{mean_returned_action_sparsity:.4f}",
                "The target average sparsity metric above is computed over successful recourses.",
            )
        )
    if infeasible_high_risk_states is not None:
        lines.append(
            "High-risk inputs with no feasible physical/rate-limited one-step interval: "
            f"{infeasible_high_risk_states}"
        )
        lines.append(
            "Actionable high-risk states: "
            f"{summary.eligible_high_risk_states - infeasible_high_risk_states}"
        )
    if run_configuration:
        lines.extend(("", "## Recourse search configuration", ""))
        lines.extend(f"- `{name}`: `{value}`" for name, value in sorted(run_configuration.items()))
    if mean_true_model_grid_ms is not None and mean_true_model_evaluations is not None:
        lines.extend(
            (
                "",
                "Mean true-model grid-search time: "
                f"{mean_true_model_grid_ms:.4f} ms per evaluated state.",
                "Mean true-model grid candidates scored: "
                f"{mean_true_model_evaluations:.2f} per evaluated state.",
            )
        )
    lines.extend(
        (
            "",
            "## Latency",
            "",
            "| Stage | Mean ms | P95 ms | Target range | Upper budget |",
            "|---|---:|---:|---|---|",
        )
    )
    for name, metric in summary.latency.items():
        status = "unmeasured" if metric.passed is None else ("pass" if metric.passed else "fail")
        if metric.below_target_range:
            status = "below expected range"
        budget = (
            "unmeasured"
            if metric.upper_budget_passed is None
            else ("pass" if metric.upper_budget_passed else "fail")
        )
        lines.append(
            f"| {name} | {_format_metric(metric.mean_ms)} | "
            f"{_format_metric(metric.p95_ms)} | {status} | {budget} |"
        )
    lines.extend(
        (
            "",
            "The pipeline timing covers the backend recommendation call. Telemetry ingestion and "
            "dashboard rendering remain unmeasured; operator-visible latency is unmeasured.",
            "Expected-range conformance and the upper latency budget are shown separately; "
            "finishing below a range does not require adding delay.",
        )
    )
    if provenance:
        lines.extend(
            (
                "",
                "## Reproducibility",
                "",
                "Effective configuration SHA-256: "
                f"`{provenance.get('effective_configuration_sha256')}`",
                f"Evaluation source commit: `{provenance.get('evaluation_git_commit')}`",
                "Tracked source changes present: "
                f"`{provenance.get('evaluation_tracked_source_dirty')}`",
                "The JSON report contains configuration, taxonomy, fitted/held-out IDs, "
                "input/artifact hashes, package versions, and sampled engine/cycle IDs.",
            )
        )
        lines.extend(str(message) for message in provenance.get("provenance_warnings", ()))
    lines.extend(
        (
            "",
            "Model validity and physical plausibility are reported separately; "
            "sparse-action feasibility is shown independently.",
            "C-MAPSS is static run-to-failure data and does not establish RUL extension.",
            "",
        )
    )
    return "\n".join(lines)
