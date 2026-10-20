"""Preregistered full-population study recipes and immutable run manifests."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from prescriptxai.config import AppConfig, load_config
from prescriptxai.evaluation.ablations import SearchPolicy, ablation_policies, ladder_policies
from prescriptxai.evaluation.assets import dataset_frames, seal_preparation_inputs
from prescriptxai.evaluation.experiments import (
    ExperimentStore,
    QueryCase,
    StudyConfig,
    audit_stage_completion,
    content_hash,
    file_hash,
    mark_stage_complete,
    runtime_manifest,
    source_revision,
)
from prescriptxai.evaluation.runner import (
    execute_experiment_cases,
    make_cases,
    observed_alert_cohort,
    validate_evaluation_provenance,
)
from prescriptxai.models.registry import load_model_bundle
from prescriptxai.pipeline import PrescriptXAI
from prescriptxai.schemas import InputContext
from prescriptxai.validation.pipeline import fit_mahalanobis_validator, save_mahalanobis_validator


@dataclass
class Cohort:
    """Frozen artifact configuration and all supported alerts from one named population."""

    key: str
    dataset: str
    model: str
    population: str
    protocol: str
    config_path: Path
    config: AppConfig
    rows: pd.DataFrame
    contexts: dict[tuple[int, int], InputContext]
    accounting: dict[str, int]
    fit_rows: pd.DataFrame
    first_alert_rows: pd.DataFrame


def effective_asset_config(
    base: AppConfig,
    assets: dict[str, Any],
    protocol: str,
) -> AppConfig:
    """Resolve persisted artifact paths while retaining every frozen solver parameter."""
    config = base.model_copy(deep=True)
    paths = assets["paths"]
    config.artifacts.model = config.paths.model = Path(paths["model"])
    config.artifacts.mahalanobis = config.paths.mahalanobis = Path(paths["mahalanobis_" + protocol])
    config.artifacts.coupling = Path(paths["coupling"])
    return config


def build_cohorts(study: StudyConfig, asset_index: dict[str, Any]) -> list[Cohort]:
    """Select every actual alert, retaining empty actuator intersections and all failure states."""
    verify_asset_index(study, asset_index)
    seal_preparation_inputs(study, asset_index)
    cohorts = []
    scored: dict[str, tuple[pd.DataFrame, dict[tuple[int, int], InputContext], dict[str, int]]] = {}
    for subset, models in study.datasets.items():
        for model in models:
            first_config = load_config(Path(f"configs/experiments/phase7-{subset}-{model}-v1.yaml"))
            frame, official = dataset_frames(first_config)
            for protocol in study.d_max_versions:
                config_path = Path(f"configs/experiments/phase7-{subset}-{model}-{protocol}.yaml")
                base = load_config(config_path)
                frozen = load_config(study.frozen_solver_config)
                if (
                    base.recourse != frozen.recourse
                    or base.tau_safe != frozen.tau_safe
                    or base.tau_danger != frozen.tau_danger
                    or base.validation.mahalanobis_max != study.d_max_versions[protocol]
                ):
                    raise ValueError(
                        "base profile differs from the preregistered frozen solver/cutoffs"
                    )
                for fold in ["base", *[f"fold-{i}" for i in range(1, study.grouped_folds + 1)]]:
                    asset = asset_index["models"][f"{subset}/{model}/{fold}"]
                    config = effective_asset_config(base, asset, protocol)
                    pipeline = PrescriptXAI.from_config(config)
                    populations = [
                        (
                            "grouped_oof_all_alerts"
                            if fold != "base"
                            else "internal_heldout_all_alerts",
                            frame.loc[frame.engine_id.isin(asset["test_ids"])],
                        )
                    ]
                    if fold == "base":
                        populations += [
                            ("official_test_all_alerts", official),
                            (
                                "development_all_alerts",
                                frame.loc[frame.engine_id.isin(asset["validation_ids"])],
                            ),
                        ]
                    for population, original in populations:
                        if population != "development_all_alerts":
                            validate_evaluation_provenance(pipeline.engine, original)
                        scoring_key = "/".join((subset, model, fold, population))
                        if scoring_key not in scored:
                            scored[scoring_key] = observed_alert_cohort(pipeline, original)
                        all_alerts, contexts, counts = scored[scoring_key]
                        alerts, accounting = all_alerts.copy(), dict(counts)
                        first_alert_rows = alerts.loc[alerts.first_alert].copy()
                        if (
                            population == "development_all_alerts"
                            and len(alerts) > study.development_max_queries
                        ):
                            alerts = alerts.sample(
                                study.development_max_queries, random_state=study.diagnostic_seed
                            ).sort_values(["engine_id", "cycle"])
                        accounting["selected_alerts"] = len(alerts)
                        key = "/".join((subset, model, protocol, fold, population))
                        cohorts.append(
                            Cohort(
                                key,
                                subset,
                                model,
                                population,
                                protocol,
                                config_path,
                                config,
                                alerts,
                                contexts,
                                accounting,
                                frame.loc[frame.engine_id.isin(asset["fit_ids"])],
                                first_alert_rows,
                            )
                        )
    return cohorts


def verify_asset_index(study: StudyConfig, index: dict[str, Any]) -> None:
    """Reject incomplete preparations and every changed fitted file before cohort scoring."""
    required = {
        f"{subset}/{model}/{fold}"
        for subset, models in study.datasets.items()
        for model in models
        for fold in ["base", *[f"fold-{i}" for i in range(1, study.grouped_folds + 1)]]
    }
    required |= {
        f"{name}/H-{h}"
        for name in study.diagnostic_models
        for h in study.horizon_H_grid
        if h != load_config(study.frozen_solver_config).horizon_H
    }
    missing = required - set(index["models"])
    if missing:
        raise ValueError(f"asset preparation is incomplete: {sorted(missing)}")
    for key, asset in index["models"].items():
        fit, validation, test = (
            set(asset[name]) for name in ("fit_ids", "validation_ids", "test_ids")
        )
        if not all((fit, validation, test)) or fit & validation or fit & test or validation & test:
            raise ValueError(f"prepared asset engine leakage: {key}")
        for name, path in asset["paths"].items():
            if file_hash(Path(path)) != asset["hashes"][name]:
                raise ValueError(f"prepared artifact changed: {key}/{name}")
    for subset, models in study.datasets.items():
        for model in models:
            base = index["models"][f"{subset}/{model}/base"]
            expected = sorted(base["fit_ids"] + base["validation_ids"] + base["test_ids"])
            covered = sorted(
                unit
                for i in range(1, study.grouped_folds + 1)
                for unit in index["models"][f"{subset}/{model}/fold-{i}"]["test_ids"]
            )
            if covered != expected:
                raise ValueError(
                    f"outer folds must cover each engine exactly once: {subset}/{model}"
                )


def study_manifest(
    study: StudyConfig,
    study_path: Path,
    asset_index: dict[str, Any],
    cohorts: list[Cohort],
    run_id: str,
) -> dict[str, Any]:
    """Fingerprint committed inputs, exact populations, artifacts, versions and hardware."""
    revision = source_revision()
    frozen = load_config(study.frozen_solver_config)
    model_metadata = {}
    for key, asset in asset_index["models"].items():
        model = load_model_bundle(Path(asset["paths"]["model"]))
        model_metadata[key] = {
            "actual_training_seed": model.seed,
            "training_git_hash": model.git_commit,
            "training_config_hash": model.config_hash,
            "model_type": model.model_type,
            "metrics": model.metrics,
        }
    return {
        "run_id": run_id,
        "study_version": study.study_version,
        "git_hash": revision,
        "study_path": str(study_path),
        "study_file_sha256": file_hash(study_path),
        "frozen_config_path": str(study.frozen_solver_config),
        "frozen_config_sha256": file_hash(study.frozen_solver_config),
        "protocol_sha256": file_hash(Path("docs/evaluation_protocol.md")),
        "archive_sha256": file_hash(frozen.data.root / frozen.data.archive_name),
        "taxonomy_sha256": file_hash(frozen.pipeline.taxonomy_path),
        "configuration": study.model_dump(mode="json"),
        "headline_safe_threshold": frozen.tau_safe,
        "alert_scoring": "authoritative singleton snapshot or genuine LSTM window",
        "assets": asset_index,
        "model_metadata": model_metadata,
        "model_seed_scope": "model_seed governs new fits; frozen assets retain stored seeds",
        "cohorts": {
            c.key: {
                "accounting": c.accounting,
                "config_path": str(c.config_path),
                "config_file_sha256": file_hash(c.config_path),
                "effective_config_hash": content_hash(c.config.model_dump(mode="json")),
                "rows_sha256": content_hash(c.rows.to_dict(orient="records")),
                "first_alert_rows_sha256": content_hash(
                    c.first_alert_rows.to_dict(orient="records")
                ),
                "context_sha256": content_hash(
                    {
                        f"{k[0]}/{k[1]}": v.model_dump(mode="json")
                        for k, v in sorted(c.contexts.items())
                    }
                ),
                "engine_ids": sorted(map(int, c.rows.engine_id.unique())),
            }
            for c in cohorts
        },
        "runtime": runtime_manifest(),
        "dice_available": study.dice_enabled and find_spec("dice_ml") is not None,
        "trajectory_health": "not evaluated: no validated simulator or emulator",
        "evidence_limit": "E3 sensor-proxy assumptions; no RUL extension",
    }


def quality_cases(cohorts: list[Cohort], study: StudyConfig) -> Iterator[QueryCase]:
    """Run full FAST alert populations and true first-alert THOROUGH subsets for every seed."""
    for cohort in cohorts:
        for mode in ("fast", "thorough"):
            rows = cohort.rows if mode == "fast" else cohort.first_alert_rows
            population = (
                cohort.population
                if mode == "fast"
                else cohort.population.replace("all_alerts", "first_alert")
            )
            yield from make_cases(
                cohort.config,
                cohort.config_path,
                rows,
                cohort.contexts,
                dataset=cohort.dataset,
                model=cohort.model,
                population=population,
                protocol=cohort.protocol,
                variant="full",
                mode=mode,
                seeds=study.solver_seeds,
                free_rate_fraction=study.unconstrained_free_rate_fraction,
            )


def _diagnostic_rows(cohort: Cohort, study: StudyConfig) -> pd.DataFrame:
    """Use a seeded ordering without consulting optimizer outcomes."""
    return (
        cohort.rows.sample(frac=1, random_state=study.diagnostic_seed)
        .head(study.diagnostic_max_queries)
        .sort_values(["engine_id", "cycle"])
    )


def _validator_variant(
    cohort: Cohort,
    *,
    method: str | None = None,
    quantile: float | None = None,
    reference: Literal["all_cycles", "healthy_to_moderate"] | None = None,
) -> AppConfig:
    """Fit a labeled distribution sensitivity on training rows only."""
    config = cohort.config.model_copy(deep=True)
    if method is not None:
        config.validation.d_max_threshold_method = (
            "empirical_quantile" if method == "empirical" else "chi_square_quantile"
        )
    if quantile is not None:
        config.validation.d_max_quantile = quantile
    if reference is not None:
        config.validation.reference_distribution = reference
    pipeline = PrescriptXAI.from_config(cohort.config)
    label = content_hash(config.validation.model_dump())
    path = cohort.config.artifacts.mahalanobis.parent / f"ablation-validator-{label}.joblib"
    if not path.exists():
        validator = fit_mahalanobis_validator(
            cohort.fit_rows,
            pipeline.engine.model,
            pipeline.engine.model.training_engine_ids,
            config,
        )
        save_mahalanobis_validator(validator, path)
    config.artifacts.mahalanobis = config.paths.mahalanobis = path
    return config


def diagnostic_cases(
    cohorts: list[Cohort],
    study: StudyConfig,
    assets: dict[str, Any],
) -> Iterator[QueryCase]:
    """Actual baselines, ladder, component removals and one-factor paired sensitivities."""
    for cohort in cohorts:
        if (
            f"{cohort.dataset}/{cohort.model}" not in study.diagnostic_models
            or cohort.population != "internal_heldout_all_alerts"
        ):
            continue
        rows = _diagnostic_rows(cohort, study)
        variants: list[tuple[str, AppConfig, SearchPolicy | None]] = [
            ("unconstrained", cohort.config, None),
            ("bounded_without_plausibility", cohort.config, SearchPolicy(validation_in_loop=False)),
            *[(name, cohort.config, policy) for name, policy in ablation_policies().items()],
            *[(name, cohort.config, policy) for name, policy in ladder_policies().items()],
        ]
        if study.dice_enabled and find_spec("dice_ml") is not None:
            variants.append(("dice", cohort.config, None))
        for field_name, values, path in (
            ("tau_safe", study.tau_safe_grid, "threshold"),
            ("k_max", study.k_max_grid, "sparsity"),
            ("K", study.K_grid, "horizon"),
            ("alpha", study.alpha_grid, "weight"),
            ("beta", study.beta_grid, "weight"),
            ("gamma", study.gamma_grid, "weight"),
        ):
            for value in values:
                config = cohort.config.model_copy(deep=True)
                if field_name == "tau_safe":
                    config.tau_safe = config.model.safe_threshold = float(value)
                elif field_name == "k_max":
                    config.recourse.max_changed_features = int(value)
                elif field_name == "K":
                    config.recourse.rate_horizon_steps = int(value)
                elif field_name == "alpha":
                    config.recourse.prediction_weight = float(value)
                else:
                    setattr(config.recourse, field_name, float(value))
                variants.append(
                    (f"sensitivity-{path}-{field_name}-{value}", config, SearchPolicy())
                )
        for method in study.d_max_methods:
            variants.append(
                (
                    f"ablation-Dmax-method-{method}",
                    _validator_variant(cohort, method=method),
                    SearchPolicy(),
                )
            )
            for q in study.d_max_quantile_grid:
                variants.append(
                    (
                        f"sensitivity-Dmax-{method}-q-{q}",
                        _validator_variant(cohort, method=method, quantile=q),
                        SearchPolicy(),
                    )
                )
        for reference in study.reference_distributions:
            variants.append(
                (
                    f"ablation-reference-{reference}",
                    _validator_variant(cohort, reference=reference),
                    SearchPolicy(),
                )
            )
        for horizon in study.horizon_H_grid:
            config = cohort.config.model_copy(deep=True)
            if horizon != config.horizon_H:
                config.horizon_H = config.data.failure_horizon = horizon
                asset = assets["models"][f"{cohort.dataset}/{cohort.model}/H-{horizon}"]
                config = effective_asset_config(config, asset, cohort.protocol)
            variants.append((f"sensitivity-label-H-{horizon}", config, SearchPolicy()))
        for variant, config, policy in variants:
            yield from make_cases(
                config,
                cohort.config_path,
                rows,
                cohort.contexts,
                dataset=cohort.dataset,
                model=cohort.model,
                population="paired_internal_diagnostic",
                protocol=cohort.protocol,
                variant=variant,
                mode="fast",
                seeds=[study.diagnostic_solver_seed],
                free_rate_fraction=study.unconstrained_free_rate_fraction,
                policy=policy,
            )


def run_quality_stage(
    study: StudyConfig,
    study_path: Path,
    run_id: str,
    stage: Literal["quality", "diagnostics"],
) -> Path:
    """Create or exactly resume a declared study stage and retain every completed query."""
    index = json.loads((study.artifact_root / "index.json").read_text(encoding="utf-8"))
    cohorts = build_cohorts(study, index)
    # Fit every preregistered validator before freezing the measurement manifest.
    diagnostics = list(diagnostic_cases(cohorts, study, index))
    manifest = study_manifest(study, study_path, index, cohorts, run_id)
    manifest["diagnostic_validator_hashes"] = {
        str(c.config.artifacts.mahalanobis): file_hash(c.config.artifacts.mahalanobis)
        for c in diagnostics
    }
    manifest["expected_queries"] = {
        "quality": sum(
            (len(c.rows) + len(c.first_alert_rows)) * len(study.solver_seeds) for c in cohorts
        ),
        "diagnostics": len(diagnostics),
    }
    manifest["expected_reference_case_ids"] = sorted(
        case.case_id for case in diagnostics if case.variant == "full"
    )
    directory = study.output_root / run_id
    store = ExperimentStore(directory, manifest)
    try:
        cases = quality_cases(cohorts, study) if stage == "quality" else iter(diagnostics)
        expected: set[str] = set()

        def tracked_cases() -> Iterator[QueryCase]:
            """Track all requested identities, including completed cases on resume."""
            for case in cases:
                expected.add(case.case_id)
                yield case

        execute_experiment_cases(
            tracked_cases(), store, workers=study.workers, cpu_threads=study.cpu_threads_per_worker
        )
        if len(expected) != manifest["expected_queries"][stage] or expected - store.completed():
            raise RuntimeError("stage is incomplete or duplicate query identities were generated")
        mark_stage_complete(directory, stage, manifest["git_hash"], len(expected))
    finally:
        store.close()
    return directory


def run_reference_stage(study: StudyConfig, directory: Path) -> None:
    """Checkpoint finite oracle and endpoint leverage on the preregistered diagnostic cohort."""
    from prescriptxai.evaluation.diagnostics import controllable_leverage, reference_search
    from prescriptxai.evaluation.experiments import ExperimentObservation

    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if source_revision() != manifest["git_hash"]:
        raise ValueError("reference source differs from production measurement")
    if not audit_stage_completion(directory, manifest, study)["diagnostics"]:
        raise ValueError("reference requires complete verified diagnostic measurements")
    store = ExperimentStore(directory, manifest)
    path = directory / "reference.json"
    saved = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    counts: dict[str, int] = {}
    for item in saved.values():
        if "oracle" in item:
            group = item["oracle"]["group"]
            counts[group] = counts.get(group, 0) + 1
    try:
        rows = store.connection.execute(
            "SELECT r.payload,c.payload FROM records r JOIN cases c USING(case_id) "
            "WHERE json_extract(r.payload,'$.variant')='full' "
            "AND json_extract(r.payload,'$.population')='paired_internal_diagnostic' "
            "ORDER BY r.case_id"
        ).fetchall()
        expected = set(manifest["expected_reference_case_ids"])
        if {json.loads(payload)["case_id"] for payload, _ in rows} != expected:
            raise ValueError("reference production rows differ from preregistered coverage")
        for payload, query in rows:
            record = ExperimentObservation.model_validate_json(payload)
            case = QueryCase.model_validate_json(query)
            if case.case_id in saved:
                continue
            result: dict[str, Any] = {"leverage": controllable_leverage(case)}
            if not record.joint and counts.get(record.group, 0) < study.oracle_max_failed_queries:
                result["oracle"] = reference_search(case, record, study)
                counts[record.group] = counts.get(record.group, 0) + 1
            saved[case.case_id] = result
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(saved, indent=2, allow_nan=False), encoding="utf-8")
            temporary.replace(path)
    finally:
        store.close()
    if set(saved) != expected:
        raise RuntimeError("reference stage is incomplete")
    mark_stage_complete(directory, "reference", manifest["git_hash"], len(saved))
