"""Execute the committed Phase 7 study with exact resumable stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prescriptxai.config import load_config
from prescriptxai.evaluation.assets import dataset_frames, prepare_study_assets
from prescriptxai.evaluation.experiments import load_study
from prescriptxai.evaluation.latency import benchmark_serial_checkpointed
from prescriptxai.evaluation.report import write_study_report
from prescriptxai.evaluation.runner import _worker_threads, observed_alert_cohort
from prescriptxai.evaluation.study import (
    effective_asset_config,
    run_quality_stage,
    run_reference_stage,
    verify_asset_index,
)
from prescriptxai.logging_utils import configure_logging
from prescriptxai.pipeline import PrescriptXAI


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("configs/experiments/phase7-study.yaml"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--stage",
        choices=["assets", "quality", "diagnostics", "reference", "latency", "report", "all"],
        default="all",
    )
    args = parser.parse_args()
    study = load_study(args.study)
    _worker_threads(study.cpu_threads_per_worker)
    configure_logging(run_id=args.run_id)
    stages = (
        ["assets", "diagnostics", "quality", "reference", "latency", "report"]
        if args.stage == "all"
        else [args.stage]
    )
    directory = study.output_root / args.run_id
    for stage in stages:
        if stage == "assets":
            prepare_study_assets(study)
        elif stage in {"quality", "diagnostics"}:
            run_quality_stage(study, args.study, args.run_id, stage)
        elif stage == "reference":
            run_reference_stage(study, directory)
        elif stage == "latency":
            index = json.loads((study.artifact_root / "index.json").read_text(encoding="utf-8"))
            verify_asset_index(study, index)
            subset, model = study.diagnostic_models[0].split("/")
            protocol = next(iter(study.d_max_versions))
            asset = index["models"][f"{subset}/{model}/base"]
            config = effective_asset_config(
                load_config(Path(f"configs/experiments/phase7-{subset}-{model}-{protocol}.yaml")),
                asset,
                protocol,
            )
            pipeline = PrescriptXAI.from_config(config)
            frame, _ = dataset_frames(config)
            validation = frame.loc[frame.engine_id.isin(asset["validation_ids"])]
            alerts, _, _ = observed_alert_cohort(pipeline, validation)
            benchmark_serial_checkpointed(pipeline, alerts, study, directory)
        else:
            write_study_report(
                directory, study, safe_threshold=load_config(study.frozen_solver_config).tau_safe
            )


if __name__ == "__main__":
    main()
