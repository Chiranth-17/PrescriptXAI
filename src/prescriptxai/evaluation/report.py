"""Machine-readable and human-readable reports from measured evaluation objects."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from prescriptxai.evaluation.metrics import EvaluationSummary
from prescriptxai.evaluation.runner import (
    DirectionConsistency,
    EvaluationRun,
    fitted_engine_provenance,
)
from prescriptxai.pipeline import PrescriptXAIEngine


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
    source_commit: str | None = None
    source_dirty: bool | None = None
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        source_commit = revision.stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            check=True,
        )
        source_dirty = bool(dirty.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        pass
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
                "Pairwise sign agreement: "
                f"{_format_metric(direction.pairwise_sign_agreement)}",
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
        lines.extend(
            f"- `{name}`: `{value}`" for name, value in sorted(run_configuration.items())
        )
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
    lines.extend((
        "", "## Latency", "",
        "| Stage | Mean ms | P95 ms | Target range | Upper budget |",
        "|---|---:|---:|---|---|",
    ))
    for name, metric in summary.latency.items():
        status = "unmeasured" if metric.passed is None else ("pass" if metric.passed else "fail")
        if metric.below_target_range:
            status = "below expected range"
        budget = (
            "unmeasured" if metric.upper_budget_passed is None
            else ("pass" if metric.upper_budget_passed else "fail")
        )
        lines.append(
            f"| {name} | {_format_metric(metric.mean_ms)} | "
            f"{_format_metric(metric.p95_ms)} | {status} | {budget} |"
        )
    lines.extend((
        "",
        "The pipeline timing covers the backend recommendation call. Telemetry ingestion and "
        "dashboard rendering remain unmeasured, so total operator-visible latency is unmeasured.",
        "Expected-range conformance and the upper latency budget are shown separately; "
        "finishing below a range does not require adding delay.",
    ))
    if provenance:
        lines.extend((
            "", "## Reproducibility", "",
            "Effective configuration SHA-256: "
            f"`{provenance.get('effective_configuration_sha256')}`",
            f"Evaluation source commit: `{provenance.get('evaluation_git_commit')}`",
            "Tracked source changes present: "
            f"`{provenance.get('evaluation_tracked_source_dirty')}`",
            "The JSON report contains effective configuration, resolved taxonomy, fitted/held-out "
            "engine IDs, input/artifact hashes, dependency versions, and sampled engine/cycle IDs.",
        ))
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
