"""Typer command-line interface for dataset, model, recourse, and evaluation workflows."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import typer

from prescriptxai.config import AppConfig, load_config
from prescriptxai.constraints.coupling import fit_and_persist_coupling
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.data.cmapss import (
    SUBSETS,
    CmapssSubset,
    load_cmapss_archive,
    to_model_frame,
    verify_row_counts,
)
from prescriptxai.data.download import DatasetDownloadError, download_archive, verify_archive
from prescriptxai.data.prepare import prepare_cmapss
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.data.splits import split_engines
from prescriptxai.evaluation.calibration_plot import write_calibration_plots
from prescriptxai.evaluation.report import build_evaluation_provenance, write_evaluation_report
from prescriptxai.evaluation.runner import evaluate_states
from prescriptxai.logging_utils import configure_logging
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.models.train import train_risk_model
from prescriptxai.pipeline import PrescriptXAI, PrescriptXAIEngine
from prescriptxai.schemas import InputContext
from prescriptxai.validation.pipeline import (
    fit_mahalanobis_validator,
    save_mahalanobis_validator,
)

app = typer.Typer(no_args_is_help=True, help="PrescriptXAI maintenance recourse tools")
data_app = typer.Typer(no_args_is_help=True, help="C-MAPSS data acquisition and preparation")
constraints_app = typer.Typer(no_args_is_help=True, help="Feature taxonomy and coupling artifacts")
app.add_typer(data_app, name="data")
app.add_typer(constraints_app, name="constraints")
LOGGER = logging.getLogger(__name__)


@app.callback()
def initialize_cli_logging() -> None:
    """Assign a JSON-formatted per-invocation ID before dispatching commands."""
    configure_logging()


def _read_state(path: Path) -> dict[str, float]:
    """Read one JSON object containing a raw-unit state."""
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("state JSON root must be an object")
    try:
        return {str(name): float(value) for name, value in raw.items()}
    except (TypeError, ValueError) as error:
        raise ValueError("state JSON values must be numeric") from error


@app.command("download")
def download_data(
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
) -> None:
    """Download and verify the configured C-MAPSS ZIP archive."""
    config = load_config(config_path)
    _download_subset_archive(config, config.data.dataset)


def _download_subset_archive(config: AppConfig, subset: CmapssSubset) -> Path:
    """Use a validated local archive or retrieve the configured real dataset."""
    if subset not in SUBSETS:
        raise typer.BadParameter(f"subset must be one of {', '.join(SUBSETS)}")
    archive_path = config.data.root / config.data.archive_name
    if archive_path.is_file():
        try:
            digest = verify_archive(archive_path, config.data.dataset_sha256)
            dataset = load_cmapss_archive(archive_path, subset)
            expected = config.data.expected_row_counts.get(subset)
            verify_row_counts(dataset, expected.model_dump() if expected is not None else None)
            typer.echo(f"Verified existing C-MAPSS archive: {archive_path} (sha256={digest})")
            return archive_path
        except (DatasetDownloadError, ValueError):
            LOGGER.warning("Existing archive failed validation; attempting configured download")
    try:
        verified = download_archive(
            config.data.dataset_url,
            archive_path,
            config.data.download_timeout_seconds,
            config.data.dataset_sha256,
        )
        dataset = load_cmapss_archive(verified, subset)
        expected = config.data.expected_row_counts.get(subset)
        verify_row_counts(dataset, expected.model_dump() if expected is not None else None)
    except DatasetDownloadError as error:
        typer.echo(f"DATASET_DOWNLOAD_UNAVAILABLE: {error}", err=True)
        raise typer.Exit(code=2) from error
    except (ValueError, FileNotFoundError) as error:
        typer.echo(f"DATASET_ARCHIVE_INVALID: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(f"Downloaded and verified C-MAPSS archive: {verified}")
    return verified


@data_app.command("download")
def download_cmapss_data(
    subset: CmapssSubset = typer.Option("FD001", "--subset"),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
) -> None:
    """Download NASA C-MAPSS or validate the existing local archive for a subset."""
    _download_subset_archive(load_config(config_path), subset)


@data_app.command("prepare")
def prepare_cmapss_data(
    subset: CmapssSubset = typer.Option("FD001", "--subset"),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
) -> None:
    """Label, split, scale, and report one real NASA C-MAPSS subset."""
    if subset not in SUBSETS:
        raise typer.BadParameter(f"subset must be one of {', '.join(SUBSETS)}")
    config = load_config(config_path)
    archive_path = config.data.root / config.data.archive_name
    if not archive_path.is_file():
        typer.echo(
            "DATASET_NOT_FOUND: run `prescriptxai data download --subset "
            f"{subset}` to retrieve the configured NASA archive into {archive_path}.",
            err=True,
        )
        raise typer.Exit(code=2)
    try:
        prepared = prepare_cmapss(
            archive_path=archive_path,
            subset=subset,
            processed_root=config.data.processed_root,
            artifact_root=config.paths.model.parent,
            seed=config.seed,
            failure_horizon=config.data.failure_horizon,
            rul_cap=config.data.rul_cap,
            variance_threshold=config.data.variance_threshold,
            regime_k=config.data.regime_k,
            lifetime_buckets=config.data.lifetime_buckets,
            train_fraction=config.data.train_fraction,
            validation_fraction=config.data.validation_fraction,
            test_fraction=config.data.test_fraction,
            rolling_features=config.data.rolling_features,
            rolling_window=config.data.rolling_window,
            expected_sha256=config.data.dataset_sha256,
            expected_row_counts=(
                config.data.expected_row_counts[subset].model_dump()
                if subset in config.data.expected_row_counts
                else None
            ),
        )
    except (DatasetDownloadError, ValueError, OSError) as error:
        typer.echo(f"DATASET_PREPARE_FAILED: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "subset": subset,
                "rows": prepared.report["row_counts"],
                "engines": prepared.report["engine_counts"],
                "retained_features": prepared.report["feature_set"]["retained_model_features"],
                "dropped_sensors": prepared.report["feature_set"]["dropped_sensors"],
                "quality_report": str(prepared.report_path),
                "preprocessor": str(prepared.preprocessor_path),
            },
            indent=2,
        )
    )


@constraints_app.command("fit-coupling")
def fit_coupling_model(
    subset: CmapssSubset = typer.Option("FD001", "--subset"),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path = typer.Option(Path("configs/features.yaml"), "--features"),
    processed_train: Path | None = typer.Option(None, "--train-csv"),
    output_path: Path | None = typer.Option(None, "--output"),
    report_stem: Path | None = typer.Option(None, "--report"),
) -> None:
    """Fit and persist the sensor coupling model on training-engine telemetry."""
    config = load_config(config_path)
    taxonomy = load_taxonomy(taxonomy_path)
    if taxonomy.coupling is None:
        raise typer.BadParameter("features.yaml does not define coupling settings")
    train_csv = processed_train or (config.data.processed_root / f"{subset}_train.csv")
    if not train_csv.is_file():
        typer.echo(
            f"TRAIN_CSV_NOT_FOUND: run `prescriptxai data prepare --subset {subset}` first.",
            err=True,
        )
        raise typer.Exit(code=2)
    frame = add_training_labels(
        to_model_frame(pd.read_csv(train_csv)),
        config.data.rul_cap,
        config.data.failure_horizon,
    )
    # The prepared CSV is already the training partition. Reconstruct its provenance
    # from the complete source trajectories instead of splitting the CSV a second time.
    source = load_cmapss_archive(config.data.root / config.data.archive_name, subset)
    splits = split_engines(
        to_model_frame(source.train),
        config.data.train_fraction,
        config.data.validation_fraction,
        config.data.test_fraction,
        config.seed,
        lifetime_buckets=config.data.lifetime_buckets,
    )
    observed_ids = tuple(sorted(int(value) for value in frame["engine_id"].unique()))
    if observed_ids != splits.train_engine_ids:
        raise typer.BadParameter(
            "coupling CSV must contain exactly the configured training engine IDs; "
            f"expected {splits.train_engine_ids}, observed {observed_ids}"
        )
    artifact_name = taxonomy.coupling.artifact_name.format(subset=subset)
    artifact_path = output_path or config.paths.model.parent / artifact_name
    diagnostic_stem = report_stem or artifact_path.with_name(f"{artifact_path.stem}-diagnostics")
    model = fit_and_persist_coupling(
        frame,
        taxonomy_path,
        artifact_path,
        training_engine_ids=splits.train_engine_ids,
        failure_horizon=config.data.failure_horizon,
        report_stem=diagnostic_stem,
        seed=config.seed,
    )
    typer.echo(
        json.dumps(
            {
                "artifact": str(artifact_path),
                "dependent_features": list(model.dependent_features),
                "predictor_features": list(model.predictor_features),
                "training_engine_ids": list(model.training_engine_ids),
                "training_engine_count": model.metrics.training_engine_count,
                "r2": model.metrics.r2,
                "residual_std": model.metrics.residual_std,
                "r2_floor": taxonomy.coupling.min_r2,
                "below_r2_floor": list(model.metrics.below_r2_floor),
                "torch_surrogate_mae": model.metrics.torch_surrogate_mae,
                "diagnostics_html": str(diagnostic_stem.with_suffix(".html")),
                "diagnostics_png": str(diagnostic_stem.with_suffix(".png")),
            },
            indent=2,
            allow_nan=False,
        )
    )


@app.command("train")
def train_model(
    subset: CmapssSubset = typer.Option("FD001", "--subset"),
    model_name: Literal["xgb", "mlp", "lstm"] = typer.Option("xgb", "--model"),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path = typer.Option(Path("configs/features.yaml"), "--features"),
) -> None:
    """Train, calibrate, and evaluate a risk model on engine-disjoint partitions."""
    config = load_config(config_path)
    if subset not in config.dataset_subsets:
        raise typer.BadParameter(f"subset must be one of {', '.join(config.dataset_subsets)}")
    if config.data.dataset != subset:
        config = config.model_copy(
            update={"data": config.data.model_copy(update={"dataset": subset})}
        )
    archive_path = config.data.root / config.data.archive_name
    if not archive_path.is_file():
        typer.echo(
            f"DATASET_NOT_FOUND: run `prescriptxai data download --subset {subset}` first.",
            err=True,
        )
        raise typer.Exit(code=2)
    dataset = load_cmapss_archive(archive_path, subset)
    result = train_risk_model(dataset.train, config, load_taxonomy(taxonomy_path), model_name)
    validator = fit_mahalanobis_validator(
        result.splits.train,
        result.bundle,
        result.splits.train_engine_ids,
        config,
    )
    model_label = {"xgb": "xgboost", "mlp": "mlp", "lstm": "lstm"}[model_name]
    stem = f"{subset}-{model_label}"
    model_path = config.artifacts.model.with_name(f"{stem}.joblib")
    validator_name = (
        f"{subset}-mahalanobis.joblib" if model_label == "xgboost" else f"{stem}-mahalanobis.joblib"
    )
    validator_path = config.artifacts.mahalanobis.with_name(validator_name)
    metrics_path = config.artifacts.evaluation_report.with_name(f"{stem}-metrics.json")
    plot_path = config.artifacts.evaluation_report.with_name(f"{stem}-calibration")
    calibration = result.metrics.get("calibration")
    if not isinstance(calibration, dict):
        raise ValueError("training result is missing calibration diagnostics")
    png_path, html_path = write_calibration_plots(
        plot_path,
        calibration["test_before"],
        calibration["test_after"],
        f"{subset} {model_label}: held-out reliability",
    )
    metrics_document = {
        **result.metrics,
        "artifacts": {
            "model": str(model_path),
            "mahalanobis": str(validator_path),
            "calibration_png": str(png_path),
            "calibration_html": str(html_path),
        },
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics_document, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    result.bundle.metrics = metrics_document
    result.bundle.scaler_reference = f"{model_path}#scaler"
    save_model_bundle(result.bundle, model_path)
    save_mahalanobis_validator(validator, validator_path)
    typer.echo(
        json.dumps(
            {
                "dataset": subset,
                "model": model_name,
                "training_engines": len(result.splits.train_engine_ids),
                "validation_engines": len(result.splits.validation_engine_ids),
                "internal_holdout_engines": len(result.splits.test_engine_ids),
                "features": list(result.bundle.feature_names),
                "holdout_metrics": result.metrics["test_holdout"],
                "model_artifact": str(model_path),
                "mahalanobis_artifact": str(validator_path),
                "metrics_json": str(metrics_path),
                "calibration_png": str(png_path),
                "calibration_html": str(html_path),
            },
            indent=2,
            allow_nan=False,
        )
    )


def _select_state(
    state_path: Path | None, engine_id: int | None, cycle: int | None, config: AppConfig
) -> dict[str, float]:
    """Read an explicit state or select one real engine-cycle from the archive."""
    if state_path is not None:
        if engine_id is not None or cycle is not None:
            raise typer.BadParameter("provide a state file or engine-id/cycle, not both")
        return _read_state(state_path)
    if engine_id is None or cycle is None:
        raise typer.BadParameter("provide a state JSON or both --engine-id and --cycle")
    frame = to_model_frame(
        load_cmapss_archive(config.data.root / config.data.archive_name, config.data.dataset).train
    )
    row = frame.loc[(frame.engine_id == engine_id) & (frame.cycle == cycle)]
    if len(row) != 1:
        raise typer.BadParameter("engine/cycle not found exactly once")
    return {str(name): float(value) for name, value in row.iloc[0].items()}


def _select_context(
    context_path: Path | None,
    engine_id: int | None,
    cycle: int | None,
    pipeline: PrescriptXAI,
) -> InputContext | None:
    """Read supplied observed context or derive actual preceding archive cycles for an LSTM."""
    if context_path is not None:
        return InputContext.model_validate_json(context_path.read_text(encoding="utf-8"))
    window = getattr(pipeline.engine.model.estimator, "window", 1)
    if window == 1 or engine_id is None or cycle is None:
        return None
    config = pipeline.config
    frame = to_model_frame(
        load_cmapss_archive(config.data.root / config.data.archive_name, config.data.dataset).train
    )
    prefix = frame.loc[
        (frame.engine_id == engine_id) & (frame.cycle < cycle) & (frame.cycle >= cycle - window + 1)
    ].sort_values("cycle")
    if len(prefix) != window - 1:
        raise ValueError(
            f"LSTM requires {window - 1} actual preceding cycles; history cannot be padded"
        )
    return InputContext(
        feature_names=pipeline.engine.model.feature_names,
        history=prefix.loc[:, pipeline.engine.model.feature_names].to_numpy(dtype=float).tolist(),
    )


@app.command("recommend")
def recommend_state(
    state_path: Path | None = typer.Argument(None, exists=True, readable=True),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path | None = typer.Option(None, "--features"),
    engine_id: int | None = typer.Option(None, "--engine-id"),
    cycle: int | None = typer.Option(None, "--cycle"),
    context_path: Path | None = typer.Option(None, "--context", exists=True),
    mode: Literal["fast", "thorough"] | None = typer.Option(None, "--mode"),
) -> None:
    """Return the public result for JSON telemetry or a real engine/cycle."""
    config = load_config(config_path)
    if taxonomy_path is not None:
        config.pipeline.taxonomy_path = taxonomy_path
    pipeline = PrescriptXAI.from_config(config)
    try:
        result = pipeline.recommend(
            _select_state(state_path, engine_id, cycle, config),
            _select_context(context_path, engine_id, cycle, pipeline),
            mode=mode,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(result.model_dump_json(indent=2))


@app.command("assess")
def assess_state(
    state_path: Path | None = typer.Argument(None, exists=True, readable=True),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    engine_id: int | None = typer.Option(None, "--engine-id"),
    cycle: int | None = typer.Option(None, "--cycle"),
    context_path: Path | None = typer.Option(None, "--context", exists=True),
) -> None:
    """Assess true calibrated alert risk without recourse."""
    config = load_config(config_path)
    try:
        pipeline = PrescriptXAI.from_config(config)
        result = pipeline.assess(
            _select_state(state_path, engine_id, cycle, config),
            _select_context(context_path, engine_id, cycle, pipeline),
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(result.model_dump_json(indent=2))


@app.command("batch")
def batch_states(
    csv_path: Path = typer.Argument(..., exists=True),
    output: Path = typer.Option(..., "--output"),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    mode: Literal["fast", "thorough"] | None = typer.Option(None, "--mode"),
    workers: int = typer.Option(1, "--workers", min=1),
    contexts_path: Path | None = typer.Option(None, "--contexts", exists=True),
) -> None:
    """Read raw CSV telemetry and write input-ordered public results as JSON."""
    try:
        pipeline = PrescriptXAI.from_config(config_path)
        contexts = None
        if contexts_path is not None:
            payload = json.loads(contexts_path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("contexts JSON must be a list matching CSV rows")
            contexts = [
                InputContext.model_validate(item) if item is not None else None for item in payload
            ]
        results = pipeline.recommend_batch(
            pd.read_csv(csv_path), mode, workers=workers, contexts=contexts
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([r.model_dump(mode="json") for r in results], allow_nan=False, indent=2),
        encoding="utf-8",
    )
    typer.echo(
        json.dumps(
            {
                "rows": len(results),
                "output": str(output),
                "mode": (mode or pipeline.config.pipeline.default_mode).upper(),
            }
        )
    )


@app.command("info")
def pipeline_info(
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
) -> None:
    """Describe loaded artifacts, thresholds, groups, raw units and assumptions."""
    typer.echo(json.dumps(PrescriptXAI.from_config(config_path).info(), indent=2))


@app.command("latency-bench")
def latency_bench(
    csv_path: Path = typer.Argument(..., exists=True),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    """Measure both modes with p50/p95/p99 and engine-bootstrap p95 intervals."""
    from prescriptxai.evaluation.latency import benchmark_pipeline

    result = benchmark_pipeline(PrescriptXAI.from_config(config_path), pd.read_csv(csv_path))
    encoded = result.model_dump_json(indent=2)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    typer.echo(encoded)


@app.command("evaluate")
def evaluate_model(
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path = typer.Option(Path("configs/features.yaml"), "--features"),
    queries: int | None = typer.Option(None, "--queries", min=1),
) -> None:
    """Evaluate high-risk states from the engine-held-out split and write reports."""
    config = load_config(config_path)
    engine = PrescriptXAIEngine.from_files(config_path, taxonomy_path)
    if queries is not None:
        config.evaluation.max_queries = queries
        engine.config.evaluation.max_queries = queries
    archive_path = config.data.root / config.data.archive_name
    dataset = load_cmapss_archive(archive_path, config.data.dataset)
    labeled = add_training_labels(
        to_model_frame(dataset.train),
        config.data.rul_cap,
        config.data.failure_horizon,
    )
    splits = split_engines(
        labeled,
        config.data.train_fraction,
        config.data.validation_fraction,
        config.data.test_fraction,
        config.seed,
        lifetime_buckets=config.data.lifetime_buckets,
    )
    # Archive parsing is dataset setup, not the synopsis' per-state telemetry ingestion stage.
    run = evaluate_states(engine, splits.test)
    source_paths = {
        "configuration": config_path,
        "feature_taxonomy": taxonomy_path,
        "model": config.artifacts.model,
        "mahalanobis": config.artifacts.mahalanobis,
        "dataset_archive": archive_path,
    }
    if engine.coupling is not None and engine.taxonomy.coupling is not None:
        source_paths["coupling"] = config.artifacts.model.parent / (
            engine.taxonomy.coupling.artifact_name.format(subset=config.data.dataset)
        )
    provenance = build_evaluation_provenance(engine, splits.test, source_paths)
    markdown_path = config.artifacts.evaluation_report.with_suffix(".md")
    write_evaluation_report(
        run,
        config.artifacts.evaluation_report,
        markdown_path,
        run_configuration=config.recourse.model_dump(mode="json"),
        provenance=provenance,
    )
    typer.echo(
        json.dumps(
            {
                "eligible_high_risk_states": run.summary.eligible_high_risk_states,
                "infeasible_high_risk_states": run.infeasible_high_risk_states,
                "actionable_high_risk_states": (
                    run.summary.eligible_high_risk_states - run.infeasible_high_risk_states
                ),
                "evaluated_states": run.summary.evaluated_states,
                "recourse_search_configuration": config.recourse.model_dump(mode="json"),
                "mean_risk_drop": run.summary.mean_risk_reduction.value,
                "mean_optimization_ms": run.summary.latency["optimization"].mean_ms,
                "mean_time_ms": run.summary.latency["pipeline"].mean_ms,
                "mean_sparsity": run.summary.average_sparsity.value,
                "mean_returned_action_sparsity": (
                    sum(record.changed_features for record in run.records) / len(run.records)
                    if run.records
                    else None
                ),
                "direction_consistency": run.direction_consistency.__dict__,
                "model_validity_rate": run.summary.recourse_validity_rate.value,
                "recourse_feasibility_rate": run.summary.recourse_feasibility_rate.value,
                "successful_recourse_count": run.summary.successful_recourse_count,
                "successful_recourse_rate": run.summary.successful_recourse_rate.value,
                "physical_plausibility_rate": run.summary.physical_plausibility_rate.value,
                "frozen_feature_violations": sum(
                    record.frozen_feature_violations for record in run.records
                ),
                "actuator_bound_violations": sum(
                    record.actuator_bound_violations for record in run.records
                ),
                "rate_limit_violations": sum(
                    record.rate_limit_violations for record in run.records
                ),
                "json_report": str(config.artifacts.evaluation_report),
                "markdown_report": str(markdown_path),
            },
            indent=2,
        )
    )


@app.command("serve")
def serve_api(
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path | None = typer.Option(None, "--features"),
) -> None:
    """Start the optional FastAPI service using configured bind settings."""
    try:
        import uvicorn

        from prescriptxai.api import create_app
    except ImportError as error:
        raise typer.BadParameter("install the optional API extra before running serve") from error
    config = load_config(config_path)
    if taxonomy_path is not None:
        config.pipeline.taxonomy_path = taxonomy_path
    engine = PrescriptXAI.from_config(config)
    uvicorn.run(create_app(engine), host=config.api.host, port=config.api.port)


def main() -> None:
    """Run the Typer CLI with standard library logging enabled."""
    configure_logging()
    app()


if __name__ == "__main__":
    main()
