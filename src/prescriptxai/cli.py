"""Typer command-line interface for dataset, model, recourse, and evaluation workflows."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import typer

from prescriptxai.config import AppConfig, load_config
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
from prescriptxai.evaluation.report import write_evaluation_report
from prescriptxai.evaluation.runner import evaluate_states
from prescriptxai.logging_utils import configure_logging
from prescriptxai.models.registry import save_model_bundle
from prescriptxai.models.train import train_risk_model
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.validation.pipeline import (
    fit_mahalanobis_validator,
    save_mahalanobis_validator,
)

app = typer.Typer(no_args_is_help=True, help="PrescriptXAI maintenance recourse tools")
data_app = typer.Typer(no_args_is_help=True, help="C-MAPSS data acquisition and preparation")
app.add_typer(data_app, name="data")
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


@app.command("train")
def train_model(
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path = typer.Option(Path("configs/features.yaml"), "--features"),
) -> None:
    """Train calibrated risk model and training-only plausibility validator."""
    config = load_config(config_path)
    archive_path = config.data.root / config.data.archive_name
    dataset = load_cmapss_archive(archive_path, config.data.dataset)
    result = train_risk_model(dataset.train, config, load_taxonomy(taxonomy_path))
    validator = fit_mahalanobis_validator(
        result.splits.train,
        result.bundle,
        result.splits.train_engine_ids,
        config,
    )
    save_model_bundle(result.bundle, config.artifacts.model)
    save_mahalanobis_validator(validator, config.artifacts.mahalanobis)
    typer.echo(
        json.dumps(
            {
                "dataset": dataset.subset,
                "training_engines": len(result.splits.train_engine_ids),
                "validation_engines": len(result.splits.validation_engine_ids),
                "internal_holdout_engines": len(result.splits.test_engine_ids),
                "model_artifact": str(config.artifacts.model),
                "mahalanobis_artifact": str(config.artifacts.mahalanobis),
            },
            indent=2,
        )
    )


@app.command("recommend")
def recommend_state(
    state_path: Path = typer.Argument(..., exists=True, readable=True),
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path = typer.Option(Path("configs/features.yaml"), "--features"),
) -> None:
    """Recommend and validate an intervention for a JSON machine state."""
    engine = PrescriptXAIEngine.from_files(config_path, taxonomy_path)
    result = engine.recommend(_read_state(state_path))
    payload = {
        "outcome": result.outcome.model_dump(mode="json"),
        "optimizer": {
            "solver_success": result.optimization.solver_success,
            "message": result.optimization.message,
            "objective_value": result.optimization.objective_value,
            "optimization_ms": result.optimization_ms,
            "validation_ms": result.validation_ms,
        },
        "tiers": {
            name: {
                "valid": tier.valid,
                "diagnostics": tier.diagnostics,
                "measurement": tier.measurement,
                "limit": tier.limit,
            }
            for name, tier in {
                "tier1_model": result.validation.tier1_model,
                "tier2_plausibility": result.validation.tier2_plausibility,
                "tier3_engineering": result.validation.tier3_engineering,
                "tier4_coupling": result.validation.tier4_coupling,
            }.items()
        },
    }
    typer.echo(json.dumps(payload, indent=2, allow_nan=False))


@app.command("evaluate")
def evaluate_model(
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path = typer.Option(Path("configs/features.yaml"), "--features"),
) -> None:
    """Evaluate high-risk states from the engine-held-out split and write reports."""
    config = load_config(config_path)
    engine = PrescriptXAIEngine.from_files(config_path, taxonomy_path)
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
    markdown_path = config.artifacts.evaluation_report.with_suffix(".md")
    write_evaluation_report(run, config.artifacts.evaluation_report, markdown_path)
    typer.echo(
        json.dumps(
            {
                "eligible_high_risk_states": run.summary.eligible_high_risk_states,
                "evaluated_states": run.summary.evaluated_states,
                "model_validity_rate": run.summary.recourse_validity_rate.value,
                "physical_plausibility_rate": run.summary.physical_plausibility_rate.value,
                "json_report": str(config.artifacts.evaluation_report),
                "markdown_report": str(markdown_path),
            },
            indent=2,
        )
    )


@app.command("serve")
def serve_api(
    config_path: Path = typer.Option(Path("configs/default.yaml"), "--config"),
    taxonomy_path: Path = typer.Option(Path("configs/features.yaml"), "--features"),
) -> None:
    """Start the optional FastAPI service using configured bind settings."""
    try:
        import uvicorn

        from prescriptxai.api import create_app
    except ImportError as error:
        raise typer.BadParameter("install the optional API extra before running serve") from error
    config = load_config(config_path)
    engine = PrescriptXAIEngine.from_files(config_path, taxonomy_path)
    uvicorn.run(create_app(engine), host=config.api.host, port=config.api.port)


def main() -> None:
    """Run the Typer CLI with standard library logging enabled."""
    configure_logging()
    app()


if __name__ == "__main__":
    main()
