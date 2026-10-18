"""Run the preregistered Phase 5 paired replay and integrated validation funnels on real FD001."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import pickle
import subprocess
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel

from prescriptxai.config import load_config
from prescriptxai.constraints.coupling import SensorCouplingModel
from prescriptxai.constraints.taxonomy import load_taxonomy
from prescriptxai.data.cmapss import load_cmapss_archive, to_model_frame
from prescriptxai.data.preprocess import add_training_labels
from prescriptxai.evaluation.metrics import engine_bootstrap_interval
from prescriptxai.logging_utils import configure_logging
from prescriptxai.models.registry import load_model_bundle
from prescriptxai.pipeline import PrescriptXAIEngine
from prescriptxai.validation.funnel import FunnelObservation, FunnelRun, build_funnel_report
from prescriptxai.validation.pipeline import (
    fit_mahalanobis_validator,
    save_mahalanobis_validator,
    validate_candidate,
)
from prescriptxai.validation.tier4_coupling import calibrate_coupling_thresholds

ROOT = Path(__file__).resolve().parents[2]

LOGGER = logging.getLogger("prescriptxai.phase5")

OUTPUT = ROOT / "artifacts/phase5"


def digest(path: Path) -> str:
    """Fingerprint exact committed configs and original saved artifacts."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def revision() -> str:
    """Return the committed implementation that is being measured."""

    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()


def write_json(path: Path, value: Any) -> None:
    """Atomically write finite JSON; numpy arrays are evidence, not hardcoded results."""

    def encode(item: Any) -> Any:

        if isinstance(item, np.ndarray):
            return item.tolist()

        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, BaseModel):
            return item.model_dump(mode="json")

        raise TypeError(type(item).__name__)

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(value, indent=2, default=encode, allow_nan=False), encoding="utf-8"
    )

    temporary.replace(path)


def state(row: pd.Series) -> dict[str, float]:
    """Retain raw telemetry/context and exclude labels from recommendation input."""

    return {
        name: float(value)
        for name, value in row.items()
        if name in {"engine_id", "cycle"} or name.startswith(("sensor_", "op_setting_"))
    }


def key(row: Any) -> tuple[int, int]:
    """Identify an exact engine-cycle input without row-order assumptions."""

    return int(row.engine_id), int(row.cycle)


def alert_rows(engine: PrescriptXAIEngine, frame: pd.DataFrame) -> pd.DataFrame:
    """Select alerts with the frozen true calibrated predictor."""

    risk = engine.model.predict_risk(frame[list(engine.model.feature_names)])

    return frame.loc[risk >= engine.config.tau_danger].copy()


def first_alerts(frame: pd.DataFrame) -> pd.DataFrame:
    """Return actual first alerts, never first sampled alerts."""

    return frame.sort_values(["engine_id", "cycle"]).groupby("engine_id", as_index=False).head(1)


def evidence(bits: tuple[bool, bool, bool, bool]) -> str:
    """Interpret saved static checks using the current E1/E2/E3 definitions."""

    if not bits[0]:
        return "none"

    if not bits[1]:
        return "E1"

    return "E3" if all(bits[2:]) else "E2"


class Experiment:
    """Frozen inputs, per-query resume cache, and independently fitted validation artifacts."""

    def __init__(self, paths: dict[str, Path]) -> None:

        self.config_paths = paths

        self.configs = {name: load_config(path) for name, path in paths.items()}

        config = self.configs["v1"]

        self.commit = revision()

        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT
        ).decode()

        if any(
            line.startswith(("src/", "scripts/", "configs/", "docs/evaluation_protocol"))
            for line in (entry[3:] for entry in dirty.splitlines())
        ):
            raise ValueError(
                "commit implementation, protocol and configs before real-data measurement"
            )

        self.preregistration_commit = (
            subprocess.check_output(
                ["git", "log", "-1", "--format=%H", "--", "docs/evaluation_protocol.md"], cwd=ROOT
            )
            .decode()
            .strip()
        )

        self.source = json.loads(
            (ROOT / "docs/phase4_full_diagnosis_results.json").read_text(encoding="utf-8")
        )

        self.input_paths = {
            name: ROOT / f"artifacts/phase4-final/checkpoints/{name}.pickle"
            for name in ("holdout", "sensitivity", "grouped-cv", "official-test")
        }

        self.checkpoints = {
            name: pickle.loads(path.read_bytes())["payload"]
            for name, path in self.input_paths.items()
        }

        archive_path = config.data.root / config.data.archive_name

        if digest(archive_path) != self.source["environment"]["dataset_archive_sha256"]:
            raise ValueError("archive differs from Phase 4: audit dataset provenance")

        self.input_fingerprints = {
            "archive": digest(archive_path),
            "phase4_report": digest(ROOT / "docs/phase4_full_diagnosis_results.json"),
            "taxonomy": digest(ROOT / "configs/features.yaml"),
            "folds": {
                f"fold-{fold}/{kind}": digest(
                    ROOT / f"artifacts/phase4-final/grouped-cv/fold-{fold}/{kind}.joblib"
                )
                for fold in range(1, 6)
                for kind in ("model", "coupling")
            },
        }

        self.archive = load_cmapss_archive(archive_path, "FD001")

        self.labeled = add_training_labels(
            to_model_frame(self.archive.train), None, config.horizon_H
        )

        self.originals = {
            key(row): state(pd.Series(row._asdict()))
            for row in self.labeled.itertuples(index=False)
        }

        self.context = hashlib.sha256(
            json.dumps(
                {
                    "source": self.commit,
                    "inputs": self.input_fingerprints,
                    "configs": {name: digest(path) for name, path in paths.items()},
                    "K_configs": {
                        str(K): digest(ROOT / f"configs/experiments/phase5-validation-v1-K{K}.yaml")
                        for K in (2, 3, 5, 10)
                    },
                    "checkpoints": {name: digest(path) for name, path in self.input_paths.items()},
                    "model": digest(config.artifacts.model),
                    "coupling": digest(ROOT / "artifacts/FD001-coupling.joblib"),
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        self.cache_root = OUTPUT / "cache" / self.context

        self.cache_root.mkdir(parents=True, exist_ok=True)

        run_file = self.cache_root / "run.json"

        self.run_id = (
            json.loads(run_file.read_text())["run_id"]
            if run_file.exists()
            else (datetime.now(UTC).strftime("phase5-%Y%m%dT%H%M%SZ"))
        )

        write_json(run_file, {"run_id": self.run_id, "context": self.context})

        configure_logging(run_id=self.run_id)

        self.engines: dict[tuple[str, str], PrescriptXAIEngine] = {}

        self.provenance: dict[str, Any] = {}

        self.funnels: list[dict[str, Any]] = []

        self.integrated: list[dict[str, Any]] = []

    def prepare(
        self,
        name: str,
        protocol: str,
        model_path: Path,
        coupling_path: Path,
        evaluation_ids: tuple[int, ...],
    ) -> PrescriptXAIEngine:
        """Refit only validators; preserve predictors, feature mappings, proxy bounds and rates."""

        config = self.configs[protocol]

        bundle = load_model_bundle(model_path)

        ids = bundle.training_engine_ids

        calibration_ids = tuple(
            int(value) for value in bundle.metrics["calibration"]["fit_engine_ids"]
        )

        if set(ids) & set(calibration_ids) or set(evaluation_ids) & (
            set(ids) | set(calibration_ids)
        ):
            raise ValueError("engine leakage in fitting/calibration/evaluation partitions")

        if set(bundle.scaler.training_engine_ids) != set(ids):
            raise ValueError("scaler fitting engines disagree with predictor fitting engines")

        taxonomy = load_taxonomy(ROOT / "configs/features.yaml").with_resolved_bounds(
            bundle.resolved_bounds,
            bundle.resolved_rate_limits,
        )

        original_coupling = SensorCouplingModel.load(coupling_path)

        if set(original_coupling.training_engine_ids) != set(ids):
            raise ValueError("coupling fitting engines disagree with predictor fitting engines")

        training = self.labeled.loc[self.labeled.engine_id.isin(ids)]

        validation = self.labeled.loc[self.labeled.engine_id.isin(calibration_ids)]

        validator = fit_mahalanobis_validator(training, bundle, ids, config)

        coupling = calibrate_coupling_thresholds(
            original_coupling,
            validation,
            calibration_ids,
            reference_distribution=config.validation.coupling_calibration_reference,
            min_rul=max(config.horizon_H, taxonomy.coupling.min_rul_cycles),
            evaluation_engine_ids=evaluation_ids,
        )

        target = OUTPUT / name / protocol

        save_mahalanobis_validator(validator, target / "mahalanobis.joblib")

        coupling.save(target / "coupling.joblib")

        if name == "base":
            save_mahalanobis_validator(validator, config.artifacts.mahalanobis)

            coupling.save(config.artifacts.coupling)

        engine = PrescriptXAIEngine(config, taxonomy, bundle, validator, coupling)

        self.engines[name, protocol] = engine

        self.provenance[f"{name}/{protocol}"] = {
            "model_path": str(model_path.relative_to(ROOT)),
            "model_sha256": digest(model_path),
            "source_coupling_sha256": digest(coupling_path),
            "validator_sha256": digest(target / "mahalanobis.joblib"),
            "calibrated_coupling_sha256": digest(target / "coupling.joblib"),
            "fitting_engine_ids": ids,
            "validation_engine_ids": calibration_ids,
            "evaluation_engine_ids": evaluation_ids,
            "partition_overlap": False,
            "predictor_and_scaler_unchanged": True,
            "bounds_and_rates_unchanged": True,
            "covariance": {
                str(regime): {
                    k: v for k, v in asdict(stats).items() if k not in {"mean", "cholesky"}
                }
                for regime, stats in validator.regime_statistics.items()
            },
            "covariance_reference": validator.reference_distribution,
            "threshold_method": validator.threshold_method,
            "coupling_calibration": coupling.calibration_report,
        }

        return engine

    def metadata(self, protocol: str, population: str, comparison: str, *, K: int = 1) -> FunnelRun:
        """Attach exact frozen configuration and protocol labels to each table."""

        path = (
            self.config_paths[protocol]
            if K == 1
            else (ROOT / f"configs/experiments/phase5-validation-v1-K{K}.yaml")
        )

        config = load_config(path)

        return FunnelRun(
            self.run_id,
            str(path.relative_to(ROOT)),
            digest(path),
            self.commit,
            protocol,
            config.recourse.k_max,
            K,
            protocol,
            config.validation.mahalanobis_max,
            population,
            comparison,
        )

    def funnel(self, observations: list[FunnelObservation], metadata: FunnelRun) -> None:
        """Keep every named population and denominator in the report."""

        config = self.configs[metadata.protocol_version]

        report = build_funnel_report(
            observations,
            metadata,
            bootstrap_replicates=config.evaluation.bootstrap_replicates,
            seed=config.seed,
        )

        self.funnels.append(report)

    def replay(
        self,
        name: str,
        protocol: str,
        rows: pd.DataFrame,
        records: Any,
        engines: dict[int, PrescriptXAIEngine] | None = None,
        *,
        K: int = 1,
    ) -> None:
        """Pair exact saved candidates with new validation, including missing solver records."""

        index = {key(record): record for record in records}

        before, after = [], []

        for row in rows.itertuples(index=False):
            identifier = key(row)

            record = index.get(identifier)

            if record is None or not record.candidate_state:
                missing = FunnelObservation(*identifier, False, False, False, False, False, False)

                before.append(missing)

                after.append(missing)

                continue

            bits = (
                record.model_valid,
                record.tier2_plausible,
                record.tier3_engineering_valid,
                record.tier4_coupling_valid,
            )

            before.append(
                FunnelObservation(
                    *identifier,
                    True,
                    record.recourse_feasible,
                    *bits,
                    evidence(bits),
                    record.final_mahalanobis_distance,
                    record.recourse_feasible,
                )
            )

            engine = engines[identifier[0]] if engines else self.engines["base", protocol]

            if K != 1:
                engine = replace(
                    engine,
                    config=load_config(
                        ROOT / f"configs/experiments/phase5-validation-v1-K{K}.yaml"
                    ),
                )

            original = state(pd.Series(row._asdict()))

            report = validate_candidate(
                original,
                record.candidate_state,
                engine.model,
                engine.taxonomy,
                engine.mahalanobis,
                engine.config,
                engine.coupling,
            )

            if abs(report.tier1_model.measurement - record.final_risk) > 1e-6:
                raise ValueError(
                    "saved-candidate risk changed: audit predictor/features/calibration leakage"
                )

            feasible = record.changed_features <= engine.config.recourse.k_max and not (
                record.frozen_feature_violations
                or record.actuator_bound_violations
                or record.rate_limit_violations
            )

            after.append(
                FunnelObservation(
                    *identifier,
                    True,
                    report.joint and feasible,
                    report.model_valid,
                    report.plausible,
                    report.tier3_engineering.valid,
                    report.tier4_coupling.valid,
                    report.evidence_level,
                    report.tier2_plausibility.measurement,
                    feasible,
                )
            )

        historical = self.source["holdout_test"][protocol]

        stage = "holdout_v1_v2"

        if name.startswith("grouped"):
            historical = self.source["grouped_cv_oof"]["by_protocol"][protocol]

            stage = "grouped_cv_oof"

        elif name.startswith("official"):
            historical = self.source["official_test"]["by_protocol"][protocol]

            stage = "official_test"

        elif name == "saved_K_sensitivity":
            historical = next(
                item
                for item in self.source["sensitivity"]
                if item["K"] == K and item["label"].startswith(("baseline-", "K"))
            )

            stage = "sensitivity"

        mirror = ROOT / (
            f"configs/experiments/phase4-historical-{protocol}"
            + (f"-K{K}" if K != 1 else "")
            + ".yaml"
        )

        before_meta = replace(
            self.metadata(protocol, name, "Phase4 saved before", K=K),
            run_id=self.source["run_id"],
            config_path=str(mirror.relative_to(ROOT)),
            config_hash=digest(mirror),
            git_hash=self.source["measurement_source_commits"][stage],
        )

        self.funnel(before, before_meta)

        self.funnels[-1]["historical_provenance"] = {
            "effective_configuration_sha256": historical["effective_configuration_sha256"],
            "per_fold_effective_configuration_sha256": historical.get(
                "per_fold_effective_configuration_sha256"
            ),
            "effective_solver_settings": historical["effective_solver_settings"],
            "mirror_note": "Committed historical mirror; not retroactive preregistration. Original source config paths and canonical effective hashes remain in the Phase 4 report.",
        }

        self.funnel(after, self.metadata(protocol, name, "Phase5 paired validation after", K=K))

        LOGGER.info("Paired replay complete: %s/%s, queries=%s", name, protocol, len(rows))

    def solve_rows(
        self,
        name: str,
        protocol: str,
        rows: pd.DataFrame,
        engines: dict[int, PrescriptXAIEngine] | None = None,
    ) -> None:
        """Run a frozen integrated solver, caching each exact query and measured timing."""

        observations = []

        for index, row in enumerate(rows.itertuples(index=False)):
            identifier = key(row)

            engine = engines[identifier[0]] if engines else self.engines["base", protocol]

            engine_name = next(
                label
                for (label, version), candidate in self.engines.items()
                if candidate is engine and version == protocol
            )

            cache = (
                self.cache_root / f"{engine_name}-{protocol}-{identifier[0]}-{identifier[1]}.json"
            )

            if cache.is_file():
                saved = json.loads(cache.read_text(encoding="utf-8"))

            else:
                result = engine.recommend(state(pd.Series(row._asdict())))

                report = result.validation

                observation = FunnelObservation(
                    *identifier,
                    bool(result.optimization.state),
                    result.outcome.success,
                    report.model_valid,
                    report.plausible,
                    report.tier3_engineering.valid,
                    report.tier4_coupling.valid,
                    report.evidence_level,
                    report.tier2_plausibility.measurement,
                    result.outcome.recourse_feasible,
                )

                saved = {
                    "observation": asdict(observation),
                    "validation": report.as_dict(),
                    "optimization": asdict(result.optimization),
                    "optimization_ms": result.optimization_ms,
                    "validation_ms": result.validation_ms,
                }

                write_json(cache, saved)

            observations.append(FunnelObservation(**saved["observation"]))

            self.integrated.append({"population": name, "protocol": protocol, **saved})

            if (index + 1) % 10 == 0:
                LOGGER.info("Integrated %s/%s: %s/%s", name, protocol, index + 1, len(rows))

        self.funnel(observations, self.metadata(protocol, name, "Phase5 integrated solver"))

    def run(self) -> dict[str, Any]:
        """Evaluate both protocols and all required populations without model selection."""

        test_ids = tuple(self.source["holdout_engine_ids"])

        for protocol in self.configs:
            self.prepare(
                "base",
                protocol,
                ROOT / "artifacts/FD001-xgboost.joblib",
                ROOT / "artifacts/FD001-coupling.joblib",
                test_ids,
            )

        base = self.engines["base", "v1"]

        test = alert_rows(base, self.labeled.loc[self.labeled.engine_id.isin(test_ids)])

        headline_keys = {
            (int(record["engine_id"]), int(record["cycle"]))
            for record in self.source["holdout_test"]["v1"]["headline_sample"]["records"]
        }

        headline = test.loc[[key(row) in headline_keys for row in test.itertuples(index=False)]]

        validation_ids = self.provenance["base/v1"]["validation_engine_ids"]

        development_all = alert_rows(
            base, self.labeled.loc[self.labeled.engine_id.isin(validation_ids)]
        )

        development = development_all.sample(
            min(len(development_all), base.config.evaluation.development_max_queries),
            random_state=base.config.seed,
        ).sort_values(["engine_id", "cycle"])

        holdout = self.checkpoints["holdout"]["records"]

        for protocol in self.configs:
            for population, rows in (
                ("internal_headline_saved_200", headline),
                ("internal_all_alerts", test),
                ("internal_first_alert_per_engine", first_alerts(test)),
            ):
                self.replay(population, protocol, rows, holdout[protocol])

            self.solve_rows("development_sample", protocol, development)

            self.solve_rows(
                "development_first_alert_per_engine", protocol, first_alerts(development_all)
            )

            self.solve_rows("internal_headline_integrated", protocol, headline)

        grouped = self.checkpoints["grouped-cv"]["grouped_cv"]

        grouped_rows = pd.DataFrame(grouped["sampled_oof_rows"])

        fold_first = []

        fold_engines: dict[str, dict[int, PrescriptXAIEngine]] = {
            version: {} for version in self.configs
        }

        for fold in grouped["folds"]:
            label = f"fold-{fold['fold']}"

            directory = ROOT / "artifacts/phase4-final/grouped-cv" / label

            ids = tuple(fold["held_out_engine_ids"])

            for protocol in self.configs:
                engine = self.prepare(
                    label, protocol, directory / "model.joblib", directory / "coupling.joblib", ids
                )

                fold_engines[protocol].update(dict.fromkeys(ids, engine))

            heldout = self.labeled.loc[self.labeled.engine_id.isin(ids)]

            fold_first.append(first_alerts(alert_rows(self.engines[label, "v1"], heldout)))

        grouped_first = pd.concat(fold_first, ignore_index=True)

        for protocol in self.configs:
            self.replay(
                "grouped_oof_saved_sample",
                protocol,
                grouped_rows,
                grouped["by_protocol"][protocol]["records"],
                fold_engines[protocol],
            )

            self.solve_rows(
                "grouped_oof_first_alert_per_engine",
                protocol,
                grouped_first,
                fold_engines[protocol],
            )

        official = to_model_frame(self.archive.test)

        terminals = official.groupby("engine_id").cycle.max()

        rul = dict(zip(self.archive.test_rul.unit_id, self.archive.test_rul.rul, strict=True))

        official["rul"] = [
            rul[int(unit)] + terminals[int(unit)] - cycle
            for unit, cycle in zip(official.engine_id, official.cycle, strict=True)
        ]

        official["engine_id"] = official.engine_id + 10000

        official_alerts = alert_rows(base, official)

        official_saved = self.checkpoints["official-test"]["official_results"]["by_protocol"]

        for protocol in self.configs:
            for population, rows in (
                ("official_all_alerts", official_alerts),
                ("official_first_alert_per_engine", first_alerts(official_alerts)),
            ):
                self.replay(population, protocol, rows, official_saved[protocol]["records"])

        for sensitivity in self.checkpoints["sensitivity"]["sensitivity"]:
            if sensitivity["label"].startswith(("baseline-", "K")):
                keys = {key(record) for record in sensitivity["records"]}

                rows = test.loc[[key(row) in keys for row in test.itertuples(index=False)]]

                self.replay(
                    "saved_K_sensitivity",
                    "v1",
                    rows,
                    sensitivity["records"],
                    K=int(sensitivity["K"]),
                )

        return {
            "run_id": self.run_id,
            "source_commit": self.commit,
            "preregistration_commit": self.preregistration_commit,
            "context_hash": self.context,
            "input_fingerprints": self.input_fingerprints,
            "configs": {
                name: {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}
                for name, path in self.config_paths.items()
            },
            "checkpoint_hashes": {name: digest(path) for name, path in self.input_paths.items()},
            "phase4_measurement_sources": self.source["measurement_source_commits"],
            "provenance": self.provenance,
            "funnels": self.funnels,
            "integrated": self.integrated,
            "development_all_alerts": len(development_all),
            "grouped_all_alerts": grouped["all_oof_alert_rows"],
            "limitations": [
                "Saved-state replay is not fresh independent generalization evidence.",
                "OOF saved sample contains 11 missing records, retained in all-query denominators.",
                "Full 2,378-alert OOF paired coverage is Partial: only the saved 200-query sample and separately named true first alerts are available/evaluated.",
                "No Phase4 before candidates exist for every true OOF first alert; integrated after is labeled unpaired.",
                "C-MAPSS sensor proxies, bounds/rates and K are assumptions; no RUL extension or E4/E5 evidence.",
            ],
        }


def format_metric(metric: dict[str, Any]) -> str:
    """Display rate/count/cluster interval and its engine denominator together."""

    if metric["ci"] is None:
        return f"unavailable (0 engines; n={metric['denominator']})"

    ci = metric["ci"]

    return (
        f"{metric['count']}/{metric['denominator']} = {metric['rate']:.3f} "
        f"[{ci['lower']:.3f}, {ci['upper']:.3f}]; {ci['engine_count']} engines"
    )


def labels(funnel: dict[str, Any]) -> str:
    """State provenance separately for historical and current measurements."""

    m = funnel["metadata"]

    return (
        f"{m['comparison']}: run `{m['run_id']}`; config `{m['config_path']}` "
        f"SHA-256 `{m['config_hash']}`; git `{m['git_hash']}`; protocol `{m['protocol_version']}`; "
        f"k_max={m['k_max']}; K={m['K']}; D_max version `{m['D_max_version']}`={m['D_max']}; "
        f"population `{m['population']}`."
    )


def render_summary(document: dict[str, Any]) -> list[str]:
    """Compare held-out, grouped OOF and official populations side by side."""

    lines = ["## Population comparison", ""]

    populations = ("internal_all_alerts", "grouped_oof_saved_sample", "official_all_alerts")

    for version in ("v1", "v2"):
        for comparison in ("Phase4 saved before", "Phase5 paired validation after"):
            items = [
                next(
                    f
                    for f in document["funnels"]
                    if f["metadata"]["population"] == p
                    and f["metadata"]["protocol_version"] == version
                    and f["metadata"]["comparison"] == comparison
                )
                for p in populations
            ]

            lines.extend([f"### {version} / {comparison}", ""])

            for item in items:
                lines.extend([labels(item), ""])

            lines += ["| Metric | " + " | ".join(populations) + " |", "|---|---:|---:|---:|"]

            for metric in (
                "tier1_all_queries",
                "tier2_all_queries",
                "tier2_returned_counterfactuals",
                "tier3_all_queries",
                "tier4_all_queries",
                "joint_tiers1_to4_all_queries",
            ):
                lines.append(
                    "| "
                    + metric
                    + " | "
                    + " | ".join(format_metric(f["independent"][metric]) for f in items)
                    + " |"
                )

            lines.append("")

    lines += [
        "## Assumed K sensitivity beside K=1",
        "",
        "![Revalidated saved-state K sensitivity](phase5_k_curve.svg)",
        "",
        "The curve uses the paired-after saved K sensitivity tables above, with engine-bootstrap intervals. "
        "Only K changes; these are assumed horizons, with no new optimization timing or physical-dynamics claim.",
        "",
    ]

    return lines


def render_latency(document: dict[str, Any]) -> list[str]:
    """Measure stage p95 with whole-engine bootstrap, never reuse old timings."""

    lines = ["## Measured integrated latency", ""]

    for funnel in document["funnels"]:
        meta = funnel["metadata"]

        if meta["comparison"] != "Phase5 integrated solver":
            continue

        rows = [
            r
            for r in document["integrated"]
            if r["population"] == meta["population"] and r["protocol"] == meta["protocol_version"]
        ]

        lines += [
            labels(funnel),
            "",
            "| Stage | p95 ms [engine-bootstrap 95% CI] | Engines | Budget ms | Result |",
            "|---|---:|---:|---:|---|",
        ]

        config = load_config(ROOT / meta["config_path"])

        for index, (stage, budget) in enumerate(
            (
                ("optimization_ms", config.latency_budget.optimization_max_ms),
                ("validation_ms", config.latency_budget.validation_max_ms),
            )
        ):
            interval = engine_bootstrap_interval(
                np.asarray([r["observation"]["engine_id"] for r in rows], dtype=np.int64),
                np.asarray([r[stage] for r in rows]),
                seed=config.seed + index,
                replicates=config.evaluation.bootstrap_replicates,
                statistic=lambda x: float(np.quantile(x, 0.95)),
            )

            lines.append(
                f"| {stage} | {interval.estimate:.2f} [{interval.lower:.2f}, {interval.upper:.2f}] | {interval.engine_count} | {budget} | {'Pass' if interval.estimate <= budget else 'Fail'} |"
            )

        lines.append("")

    return lines


def render_k_curve(document: dict[str, Any]) -> None:
    """Generate an exportable sensitivity figure directly from computed funnel data."""

    import plotly.graph_objects as go

    items = sorted(
        (
            f
            for f in document["funnels"]
            if f["metadata"]["population"] == "saved_K_sensitivity"
            and f["metadata"]["comparison"] == "Phase5 paired validation after"
        ),
        key=lambda f: f["metadata"]["K"],
    )

    counts = sorted({f["query_count"] for f in items})
    engines = sorted({f["engine_count"] for f in items})
    caption = f"n={counts}; engines={engines}; 95% whole-engine bootstrap CI"
    plot_meta = items[0]["metadata"]
    fig = go.Figure()

    for metric, label in (
        ("tier1_all_queries", "True-model validity"),
        ("tier2_all_queries", "Tier 2 plausibility"),
        ("joint_tiers1_to4_all_queries", "Joint Tiers 1–4"),
    ):
        values = [f["independent"][metric] for f in items]

        fig.add_trace(
            go.Scatter(
                x=[f["metadata"]["K"] for f in items],
                y=[v["rate"] for v in values],
                name=label,
                mode="lines+markers",
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[v["ci"]["upper"] - v["rate"] for v in values],
                    arrayminus=[v["rate"] - v["ci"]["lower"] for v in values],
                ),
            )
        )

    fig.update_layout(
        title=f"{document['run_id']}: saved-state sensitivity, {plot_meta['protocol_version']} / k={plot_meta['k_max']} / Dmax={plot_meta['D_max']}<br><sup>{caption}</sup>",
        xaxis_title="Assumed intervention horizon K",
        yaxis_title="Rate (whole-engine bootstrap CI)",
        yaxis_range=[0, 1.05],
        template="plotly_white",
    )

    fig.write_html(OUTPUT / "K-sensitivity.html", include_plotlyjs=True)

    # SVG export uses no browser dependency: labels and points come from the same data.

    from html import escape

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="520" viewBox="0 0 1000 520">',
        '<rect width="1000" height="520" fill="white"/>',
        f'<text x="50" y="30" font-size="17">{escape(document["run_id"])}: saved-state K sensitivity ({plot_meta["protocol_version"]}, k={plot_meta["k_max"]}, Dmax={plot_meta["D_max"]})</text>',
        f'<text x="70" y="53" font-size="13">{escape(caption)}</text>',
    ]

    for tick in range(6):
        y = 440 - tick * 76

        parts += [
            f'<path d="M70 {y} H930" stroke="#ddd"/>',
            f'<text x="25" y="{y + 5}">{tick / 5:.1f}</text>',
        ]

    for metric, color, label in (
        ("tier1_all_queries", "#2563eb", "True-model validity"),
        ("tier2_all_queries", "#d97706", "Tier 2 plausibility"),
        ("joint_tiers1_to4_all_queries", "#15803d", "Joint Tiers 1–4"),
    ):
        points = []

        for f in items:
            v = f["independent"][metric]
            K = f["metadata"]["K"]
            x = 70 + (K - 1) * 90
            y = 440 - v["rate"] * 380

            points.append(f"{x},{y}")

            parts += [
                f'<path d="M{x} {440 - v["ci"]["lower"] * 380} V{440 - v["ci"]["upper"] * 380}" stroke="{color}"/>',
                f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>',
            ]

        parts += [
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>'
        ]

        offset = {"#2563eb": 0, "#d97706": 260, "#15803d": 540}[color]

        parts += [f'<text x="{70 + offset}" y="495" fill="{color}">{label}</text>']

    for f in items:
        K = f["metadata"]["K"]
        parts += [f'<text x="{65 + (K - 1) * 90}" y="463">{K}</text>']

    parts += ['<text x="370" y="480">Assumed horizon K (no actuator evidence)</text>', "</svg>"]

    (ROOT / "docs/phase5_k_curve.svg").write_text("\n".join(parts), encoding="utf-8")


def render_diagnostics(document: dict[str, Any]) -> list[str]:
    """Display frozen target gaps and actual residual/covariance evidence from the saved run."""
    lines = ["## Integrated headline targets and gaps", ""]
    for version in ("v1", "v2"):
        funnel = next(
            f
            for f in document["funnels"]
            if f["metadata"]["population"] == "internal_headline_integrated"
            and f["metadata"]["protocol_version"] == version
        )
        config = load_config(ROOT / funnel["metadata"]["config_path"])
        lines += [
            labels(funnel),
            "",
            "| Metric (all queries) | Measured [95% engine CI] | Target | Gap | Result |",
            "|---|---:|---:|---:|---|",
        ]
        for metric, target in (
            ("tier1_all_queries", config.evaluation.recourse_validity_rate),
            ("tier2_all_queries", config.evaluation.physical_plausibility_rate),
        ):
            result = funnel["independent"][metric]
            lines.append(
                f"| {metric} | {format_metric(result)} | >= {target:.2f} | {result['rate'] - target:+.3f} | {'Pass' if result['rate'] >= target else 'Fail'} |"
            )
        joint = funnel["independent"]["joint_tiers1_to4_all_queries"]
        lines += [
            f"| Joint Tiers 1–4 | {format_metric(joint)} | No synopsis joint target | — | Reported separately |",
            "",
        ]
    lines += [
        "Target gaps are measured against the frozen configuration. A paired joint-count difference is descriptive, not a claim of general improvement. Returned-counterfactual plausibility is conditional on acceptance.",
        "",
        "Latency budget pass/fail is measured below. In-loop constraint checks are charged to optimization, not hidden in the final-validation stage. "
        "Residual-preserving propagation leaves absolute learned residual violations invariant, so repeated search cannot repair those violations. "
        "Any performance work must be developed and frozen on validation engines before a future test run.",
        "",
    ]
    base = document["provenance"]["base/v1"]
    calibration = base["coupling_calibration"]
    assert calibration == document["provenance"]["base/v2"]["coupling_calibration"]
    meta = dict(
        next(
            f["metadata"]
            for f in document["funnels"]
            if f["metadata"]["population"] == "internal_headline_integrated"
            and f["metadata"]["protocol_version"] == "v1"
        )
    )
    meta.update(
        population="validation calibration: healthy_to_moderate",
        comparison="Phase5 calibration diagnostic",
    )
    lines += [
        "## Coupling calibration evidence",
        "",
        labels({"metadata": meta}),
        "",
        f"Reference: {calibration['row_count']} rows from {calibration['engine_count']} validation engines; RUL > {calibration['min_rul_exclusive']}; "
        f"fixed multiplier {calibration['sigma_multiplier']}. The same residual calibration is used for v1 and v2. "
        "R² here is a calibration-reference diagnostic, not an independent test-fit score. Propagation regressors were not refitted.",
        "",
        "| Sensor | R² | Residual mean | Residual std (raw units) | Absolute limit | Share beyond limit |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for sensor, value in sorted(calibration["per_sensor"].items()):
        lines.append(
            f"| {sensor} | {value['r2']:.6f} | {value['residual_mean']:.6g} | {value['residual_std']:.6g} | {value['threshold']:.6g} | {value['share_beyond_threshold']:.6f} |"
        )
    taxonomy = load_taxonomy(ROOT / "configs/features.yaml")
    assert taxonomy.coupling is not None
    below = [
        name
        for name, value in calibration["per_sensor"].items()
        if value["r2"] < taxonomy.coupling.min_r2
    ]
    lines += [
        "",
        f"Below the configured diagnostic R² floor ({taxonomy.coupling.min_r2}): {below}. "
        "Historical engine-grouped fit-floor warnings remain in Phase 4 evidence; calibration does not replace them.",
        "",
    ]
    meta.update(
        population="fitting telemetry: all_cycles", comparison="Phase5 covariance diagnostic"
    )
    lines += [
        "## Covariance evidence",
        "",
        labels({"metadata": meta}),
        "",
        f"Fitting engines: {len(base['fitting_engine_ids'])}; method: {base['threshold_method']}; reference: {base['covariance_reference']}. "
        "The fixed quantile setting is unused for D_max=5/8. Both quantile methods and healthy-reference selection are tested; real method/reference comparisons are reserved for Phase 7.",
        "",
        "| Regime | Rows | Shrinkage | Condition number | Unregularized rank |",
        "|---|---:|---:|---:|---:|",
    ]
    for regime, value in base["covariance"].items():
        lines.append(
            f"| {regime} | {value['row_count']} | {value['shrinkage']:.6g} | {value['condition_number']:.6g} | {value['unregularized_rank']} |"
        )
    lines += [
        "",
        "Covariance factors and calibrated coupling artifacts have SHA-256 fingerprints in the JSON provenance. "
        "Mean/p50/p95 D_M distributions and per-query signed margins are also retained there. "
        "No inverse matrix is computed or persisted.",
        "",
        "## Schema and migration notes",
        "",
        "Result/report schema 1.1.0 adds independent verdicts, tier status (including skipped), signed margins, per-rule checks, surrogate warnings, evidence and assumptions. "
        "Legacy precision-only validators require a train-engine refit. Config/validator mismatches fail clearly. "
        "No validated emulator or simulator is installed; E4/E5 are unavailable.",
        "",
    ]
    return lines


def render(document: dict[str, Any]) -> str:
    """Render measured per-tier funnels with complete labels and explicit historical errata."""

    lines = [
        "# Phase 5 validation changes and measured funnels",
        "",
        f"Source commit: `{document['source_commit']}`; preregistration: `{document['preregistration_commit']}`.",
        "",
        "Mahalanobis now uses train-only Ledoit-Wolf shrinkage and Cholesky solves, with unchanged fixed D_max v1=5/v2=8. "
        "Tier 4 thresholds use held-out validation-engine residuals; propagation regressors, physical bounds and rate limits are unchanged.",
        "",
        "Plausibility means Tier 2 only. Each static tier, physical conjunction, and all-four joint is reported separately. "
        "Phase 4's `tiers2_to4_joint` summary included Tier 1 and feasibility; the paired before columns below recompute the correct definitions from saved records.",
        "",
        "Returned diagnostic candidate means a saved/generated state exists, including failed attempts. Accepted counterfactual means the historical Phase 4 return convention before, "
        "and all checks plus sparse feasibility after. Returned-counterfactual plausibility can therefore be 100% by construction after; all-query rates remain visible.",
        "",
        "All intervals resample whole engines (2000 replicates). C-MAPSS controllables, bounds, proxy rate limits, and K are assumptions. "
        "Highest possible evidence here is E3 proxy engineering, not validated control efficacy; E4/E5 are unavailable. No RUL extension is claimed.",
        "",
    ]

    lines.extend(render_diagnostics(document))
    paired: dict[tuple[str, str, int], list[dict[str, Any]]] = {}

    for funnel in document["funnels"]:
        m = funnel["metadata"]

        paired.setdefault((m["population"], m["protocol_version"], m["K"]), []).append(funnel)

    for (population, version, horizon), items in paired.items():
        lines.extend([f"## {population} / {version} / K={horizon}", ""])

        for item in items:
            lines.extend([labels(item), ""])

            if "historical_provenance" in item:
                h = item["historical_provenance"]

                lines.extend(
                    [
                        f"Historical effective configuration SHA-256 `{h['effective_configuration_sha256']}`; "
                        f"per-fold hashes: `{h['per_fold_effective_configuration_sha256']}`. "
                        + h["mirror_note"],
                        "",
                    ]
                )

        lines.extend(
            [
                "| Metric / denominator | "
                + " | ".join(item["metadata"]["comparison"] for item in items)
                + " |",
                "|---|" + "---:|" * len(items),
            ]
        )

        for metric in items[0]["independent"]:
            lines.append(
                f"| {metric} | "
                + " | ".join(format_metric(item["independent"][metric]) for item in items)
                + " |"
            )

        for stage in items[0]["funnel"]:
            lines.append(
                f"| funnel: {stage} | "
                + " | ".join(format_metric(item["funnel"][stage]) for item in items)
                + " |"
            )

        lines.append("")

    lines.extend(render_summary(document))

    lines.extend(render_latency(document))

    lines.extend(
        [
            "## Limitations and remaining evidence",
            "",
            *[f"- {item}" for item in document["limitations"]],
            "",
            "Detailed per-query checks/margins, effective solver settings, measured timings, residual calibration metrics, covariance diagnostics and artifact hashes are saved in `artifacts/phase5/funnel.json`.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Run only the committed protocol and write the Phase 5 gate evidence."""

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/experiments/phase5-validation-v1.yaml"
    )

    parser.add_argument(
        "--v2-config", type=Path, default=ROOT / "configs/experiments/phase5-validation-v2.yaml"
    )

    args = parser.parse_args()

    started = perf_counter()

    result = Experiment({"v1": args.config.resolve(), "v2": args.v2_config.resolve()}).run()

    result["measured_run_seconds"] = perf_counter() - started

    write_json(OUTPUT / "funnel.json", result)

    render_k_curve(result)

    (ROOT / "docs/phase5_changes.md").write_text(render(result), encoding="utf-8")

    LOGGER.info("Phase5 evidence written; run_id=%s", result["run_id"])


if __name__ == "__main__":
    main()
