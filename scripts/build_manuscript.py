"""Build a complete research draft and evidence appendix from immutable saved results."""

import argparse
import hashlib
import json
import re
import subprocess
from functools import partial
from pathlib import Path
from xml.sax.saxutils import escape


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value, digits=3):
    return "undefined" if value is None else f"{value:.{digits}f}"


def interval(group, metric, percent=False):
    ci = group["metrics"][metric]["ci"]
    factor = 100 if percent else 1
    if ci["estimate"] is None:
        return "undefined"
    digits = 6 if metric == "risk_reduction" else 2
    return (f"{ci['estimate'] * factor:.{digits}f} "
            f"[{ci['lower'] * factor:.{digits}f}, {ci['upper'] * factor:.{digits}f}]")


def target_gap(gap, digits=2):
    return f"{gap:+.{digits}f} {'miss' if gap > 0 else 'pass'}"


def table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        + ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    ) + "\n\n"


def evidence_appendix(summary, metadata, assets):
    manifest = summary["manifest"]
    study = manifest["configuration"]
    text = "# Appendix A. Complete measured results\n\n"
    text += (
        f"Run {manifest['run_id']}. Measured source {manifest['git_hash']}. "
        f"Study {manifest['study_path']} (SHA256 {manifest['study_file_sha256']}). "
        f"All following headline tables are FAST/full, assumed K=1, k_max=3; "
        f"v1 D_max={study['d_max_versions']['v1']} and v2 D_max={study['d_max_versions']['v2']}. "
        f"Solver seeds {study['solver_seeds']}; fixed predictor fits. "
        f"Intervals are {100 * study['bootstrap_confidence']:g}% whole-engine bootstrap intervals, "
        f"{study['bootstrap_replicates']} requested draws, bootstrap seed1729. "
        "Engine counts apply to every interval in the row. E3 is the maximum available proxy "
        "evidence, not a universal attained level. Failed queries remain in all-query denominators.\n\n"
    )
    selected = {}
    for dataset, model in [("FD001", "xgb"), ("FD001", "mlp"), ("FD001", "lstm"), ("FD002", "xgb")]:
        text += f"## {dataset} / {model.upper()}\n\n"
        rows, constraints, targets, diagnostics = [], [], [], []
        for protocol in ("v1", "v2"):
            for population, short in [("internal_heldout_all_alerts", "held-out"),
                                      ("grouped_oof_all_alerts", "OOF"),
                                      ("official_test_all_alerts", "official")]:
                key = f"{dataset}/{model}/{protocol}/{population}/fast/full"
                group = summary["groups"][key]
                selected[key] = group
                label = f"{protocol}/{short}"
                count = f"{group['unique_engine_cycle_queries']}/{group['query_seed_observations']}/{group['engines']}"
                rows.append([label, count, interval(group, "validity", True),
                             interval(group, "plausibility_all", True),
                             interval(group, "plausibility_returned", True)])
                constraints.append([f"{label} (N={group['engines']})", interval(group, "tier3", True),
                                    interval(group, "tier4", True), interval(group, "joint", True)])
                conditional = group["metrics"]["plausibility_returned"]["ci"]["denominator"]
                targets.append([f"{label} (N={group['engines']})", f"{group['query_seed_observations']}/{conditional:g}",
                                interval(group, "sparsity_all"), interval(group, "risk_reduction")])
                dm = group["D_M_quantiles"]
                diagnostics.append([label, number(dm.get("p50")), number(dm.get("p95")),
                                    number(dm.get("p99")), number(group["coupling_margin_min"])])
        text += "Rates (%) and query / seed-observation / engine counts:\n\n"
        text += table(["Population", "Q / observations / N", "Validity", "T2 all", "T2 returned"], rows)
        text += table(["Population", "Tier 3 (%)", "Tier 4 (%)", "Joint (%)"], constraints)
        text += table(["Population", "All / returned denominator", "Mean support (all)", "Mean risk drop (all)"], targets)
        text += "Distribution and coupling point diagnostics (no bootstrap CI saved for these summaries):\n\n"
        text += table(["Population", "D_M p50", "D_M p95", "D_M p99", "Minimum coupling margin"], diagnostics)
        text += (
            f"Config paths and all five effective runtime hashes for each row are retained "
            f"in paper/evidence.json under the full group key. Registered profile configs: "
            f"configs/experiments/phase7-{dataset}-{model}-v1.yaml and "
            f"configs/experiments/phase7-{dataset}-{model}-v2.yaml. "
            "Returned denominators are explicit and may differ from all queries.\n\n"
        )
    text += "# Appendix B. Design targets and measured gaps\n\n"
    text += (
        "The following gaps are signed shortfalls: positive means the target is missed; "
        "negative means the estimate is beyond the target in the favorable direction. "
        "A point-estimate pass does not imply its entire CI passes. Rate gaps are percentage points. "
        "All intervals and engine counts are in Appendix A. Simulated trajectory health is unmeasured.\n\n"
    )
    gap_rows = []
    for key, group in selected.items():
        dataset, model, protocol, population, _, _ = key.split("/")
        short = population.replace("internal_heldout_all_alerts", "held-out").replace("grouped_oof_all_alerts", "OOF").replace("official_test_all_alerts", "official")
        m = group["metrics"]
        gap_rows.append([f"{dataset}/{model}/{protocol}/{short}",
                         target_gap((0.95-m['validity']['ci']['estimate'])*100),
                         target_gap((0.90-m['plausibility_all']['ci']['estimate'])*100),
                         target_gap((0.90-m['plausibility_returned']['ci']['estimate'])*100)
                         if m['plausibility_returned']['ci']['estimate'] is not None else "undefined",
                         target_gap(m['sparsity_all']['ci']['estimate']-3),
                         target_gap(0.60-m['risk_reduction']['ci']['estimate'], 6)])
    text += table(["Population", "Validity 95%", "T2 all 90%", "T2 returned 90%", "Support <=3", "Risk drop >=0.60"], gap_rows)
    latency = summary["latency"]
    text += "## Historical warm serial backend latency\n\n"
    text += f"Same run/source as Appendix A. Exact latency labels: {json.dumps(latency['labels'], sort_keys=True)}. "
    text += "Startup, network, attribution and browser paint are excluded. Faster than a band's lower endpoint passes.\n\n"
    latency_rows = []
    for mode, stages in latency["modes"].items():
        for stage, item in stages.items():
            if item["p95_ms"] is None:
                continue
            ci = item["p95_engine_ci"]
            latency_rows.append([f"{mode}/{stage.removesuffix('_ms')}",
                                 f"{item['count']}/{item['engine_count']}",
                                 f"{item['p95_ms']:.2f} [{ci['lower']:.2f}, {ci['upper']:.2f}]",
                                 number(item['upper_budget_ms'], 0),
                                 number(item['p95_ms']-item['upper_budget_ms'], 2), str(item['passed'])])
    text += table(["Mode / stage", "Calls / N", "p95 ms [engine CI]", "Upper budget", "Signed gap ms", "Pass"], latency_rows)
    text += (
        "UI <250ms and full UI/network total <=2200ms remain unmeasured at browser-interaction scope. "
        "The separately saved server-construction timing must not be relabeled as browser paint. "
        "Historical latency is not a measurement of the post-audit implementation.\n\n"
    )
    text += "# Appendix C. Predictor, calibration and coupling evidence\n\n"
    text += "Predictive and calibration entries below are saved point diagnostics without engine CIs. No interval is invented.\n\n"
    model_rows = []
    for key in ("FD001/xgb/base", "FD001/mlp/base", "FD001/lstm/base", "FD002/xgb/base"):
        meta = metadata[key]
        metrics = meta["metrics"]
        holdout = metrics["test_holdout"]
        before, after = metrics["calibration"]["test_before"], metrics["calibration"]["test_after"]
        model_rows.append([key.removesuffix("/base"), holdout["sample_count"],
                           number(holdout["auroc"], 4), number(holdout["auprc"], 4),
                           f"{number(before['brier_score'],5)} -> {number(after['brier_score'],5)}",
                           f"{number(before['ece'],5)} -> {number(after['ece'],5)}"])
    text += table(["Profile", "Rows", "AUROC", "AUPRC", "Brier before -> after", "ECE before -> after"], model_rows)
    text += "Calibration is not uniformly better. Training provenance and fit/calibration/test engine identities:\n\n"
    for key in ("FD001/xgb/base", "FD001/mlp/base", "FD001/lstm/base", "FD002/xgb/base"):
        meta = metadata[key]
        metrics = meta["metrics"]
        text += f"## {key}\n\nTraining source {meta['training_git_hash']}; training config SHA256 {meta['training_config_hash']}; actual training seed {meta['actual_training_seed']}. "
        split = metrics['split_engines']
        counts = {name: len(ids) for name, ids in split.items() if isinstance(ids, list)}
        text += f"Engine counts by split: {json.dumps(counts, sort_keys=True)}. "
        text += f"Calibration-fit engines: {len(metrics['calibration']['fit_engine_ids'])}. "
        text += "All engine identities, overlap checks, metadata and committed experiment config paths "
        text += "are copied unchanged to paper/evidence.json.\n\n"
        fidelity = metrics.get("surrogate_fidelity")
        if fidelity:
            text += f"Surrogate on observed held-out states: {json.dumps(fidelity, sort_keys=True)}. "
            text += "These states differ from optimized counterfactual candidates.\n\n"
        else:
            text += "No distillation surrogate is used for this differentiable predictor; surrogate fidelity is not applicable.\n\n"
        for population in ("internal_heldout_all_alerts", "grouped_oof_all_alerts", "official_test_all_alerts"):
            group = selected[f"{key.removesuffix('/base')}/v1/{population}/fast/full"]
            text += f"v1/{population}, {group['engines']} engines: candidate surrogate MAE {interval(group,'surrogate_MAE')}; false-safe share over all queries (%) {interval(group,'surrogate_false_safe_share_all',True)}. "
        text += "\n\n"
        cc = assets["models"][key]["coupling_calibration"]
        text += (f"Learned coupling residual calibration: {cc['row_count']} rows / {cc['engine_count']} engines, "
                 f"reference distribution {cc['reference_distribution']}, RUL > {cc['min_rul_exclusive']}, "
                 f"sigma multiplier {cc['sigma_multiplier']}. These validation engines are disjoint from "
                 "coupling training but also determine residual thresholds; they are not untouched coupling test units.\n\n")
        text += table(["Sensor", "R2", "Residual mean", "Residual std", "Threshold", "Share beyond"],
                       [[sensor, *[format(row[k], '.6g') for k in
                                  ("r2", "residual_mean", "residual_std", "threshold", "share_beyond_threshold")]]
                       for sensor, row in cc["per_sensor"].items()])
    text += "# Appendix D. Diagnostics, reproducibility and provenance\n\n"
    text += "## Paired K sensitivity beside the K=1 headline assumption\n\n"
    prefix = 'FD001/xgb/v1/paired_internal_diagnostic/fast/'
    text += ("This is the preregistered paired FD001/XGB/v1 diagnostic population, not the all-alert "
             "headline cohort. K changes assumed cumulative rate allowance only. It is not a dynamic "
             "trajectory or a physical response measurement. Each row retains its exact config path/hash "
             "and effective labels in paper/evidence.json, diagnostic_groups.\n\n")
    k_rows = []
    for horizon in (1, 2, 3, 5, 10):
        group = summary['groups'][prefix + f'sensitivity-horizon-K-{horizon}']
        k_rows.append([horizon, f"{group['query_seed_observations']}/{group['engines']}",
                       interval(group, 'validity', True), interval(group, 'plausibility_all', True),
                       interval(group, 'joint', True)])
    text += table(['K', 'Observations / engines', 'Validity (%)', 'T2 all (%)', 'Joint (%)'], k_rows)
    text += "## Paired constraint ladder and baseline comparisons\n\n"
    ladder_rows = []
    for name in ('L0_all_free', 'L1_immutable', 'L2_bounds', 'L3_rates', 'L4_propagation',
                 'L5_sparsity', 'L6_mahalanobis', 'L7_coupling', 'unconstrained',
                 'bounded_without_plausibility', 'dice', 'full'):
        group = summary['groups'][prefix+name]
        ladder_rows.append([name.replace('_', ' '), f"{group['query_seed_observations']}/{group['engines']}",
                            interval(group, 'validity', True), interval(group, 'plausibility_all', True),
                            interval(group, 'joint', True)])
    text += table(['Variant', 'Observations / engines', 'Validity (%)', 'T2 all (%)', 'Joint (%)'], ladder_rows)
    text += ("Ladder variants progressively activate constraints; baselines use the saved configured "
             "implementations. Their permitted spaces differ. This is not evidence that every DiCE "
             "configuration is unconstrained or that a finite baseline failed to find a globally feasible action.\n\n")
    text += "## Headline acceptance funnel\n\n"
    funnel_group = selected['FD001/xgb/v1/internal_heldout_all_alerts/fast/full']
    funnel_rows = []
    for stage, item in funnel_group['funnel'].items():
        ci = item['ci']
        funnel_rows.append([stage.replace('_', ' '), item['count'], ci['engine_count'],
                            f"{100*ci['estimate']:.2f} [{100*ci['lower']:.2f}, {100*ci['upper']:.2f}]"])
    text += table(['Sequential stage', 'Count', 'Engines', 'All-query share (%) [engine CI]'], funnel_rows)
    text += ("Funnel stages are cumulative acceptance steps, whereas Appendix A tier pass rates are "
             "independent checks. Do not substitute a cumulative funnel numerator for an independent tier metric.\n\n")
    text += "## LSTM scorable-history accounting\n\n"
    history_rows = []
    for key, cohort in manifest['cohorts'].items():
        if key.startswith('FD001/lstm/v1/') and key.endswith('_all_alerts') and 'development' not in key:
            a = cohort['accounting']
            history_rows.append([key.removeprefix('FD001/lstm/v1/').removesuffix('_all_alerts'),
                                 a['total_rows'], a['insufficient_history_rows'], a['scorable_rows'],
                                 a['selected_alerts']])
    text += table(['Cohort', 'Input rows', 'Insufficient history', 'Scorable', 'Selected alerts'], history_rows)
    text += ("Early rows without the required real-history prefix are excluded before alert scoring, "
             "with counts disclosed above. This makes LSTM populations differ from snapshot models. "
             "Queries that enter the registered scorable-alert cohort remain in its result denominators.\n\n")
    text += ("The full paired constraint ladder, K curves, ablations, baselines and first-alert strata remain "
             f"in docs/phase7_changes.md and all {summary.get('total_saved_group_count', len(summary['groups']))} saved summary groups. They are separate diagnostic or "
             f"sensitivity populations, not replacements for the {len(selected)} headline rows. Exact selected-group funnel "
             "counts, failure reasons and D_M distributions are preserved in paper/evidence.json.\n\n")
    text += "Reference classifications remain unresolved finite searches, not certified infeasibility:\n\n"
    oracle_rows = []
    for key, items in summary['oracle_summary'].items():
        ci = items['unresolved_finite_search']
        oracle_rows.append([key.split('/paired_')[0], ci['observation_count'], ci['engine_count'],
                            f"{100*ci['estimate']:.1f} [{100*ci['lower']:.1f}, {100*ci['upper']:.1f}]"])
    text += table(["Profile / protocol", "Failed cases", "Engines", "Unresolved (%) [engine CI]"], oracle_rows)
    text += ("The frozen second-seed replay is documented in docs/final_verification.md under run "
             "phase11-seed1730-20261028T030707Z and source63c2ed445fba16c73a2771e184f635abf76b4405. "
             "It completed 34,298 records / 64 groups. Comparisons against historical 1730 and 1729 each found "
             "zero mismatches at absolute tolerance 1e-6 / relative tolerance 1e-5, with discrete verdicts exact. "
             "All 576 whole-engine CI objects passed independent checks. This reused-engine replay is "
             "reproducibility evidence, not an independent generalization sample. Execution segments and "
             "host interruptions are disclosed in that verification record.\n\n")
    return text, selected


def pdf_from_markdown(markdown, output):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import (
        LongTable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        TableStyle,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyResearch", fontName="Helvetica", fontSize=9.5,
                              leading=13.5, spaceAfter=8, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="CellResearch", fontName="Helvetica", fontSize=7.4,
                              leading=9.8, wordWrap="CJK"))
    styles["Title"].fontSize = 22
    styles["Title"].leading = 27
    styles["Title"].textColor = colors.HexColor("#153649")
    for style in ("Heading1", "Heading2", "Heading3"):
        styles[style].textColor = colors.HexColor("#153649")
    story = []
    lines = markdown.splitlines()
    idx = 0
    first = True
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        if line.startswith("|"):
            rows = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                row = [cell.strip() for cell in lines[idx].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in row):
                    rows.append([Paragraph(escape(cell), styles["CellResearch"]) for cell in row])
                idx += 1
            width = A4[0] - 84
            weights = [1.3] + [1] * (len(rows[0]) - 1)
            tab = LongTable(rows, colWidths=[width*w/sum(weights) for w in weights],
                            repeatRows=1, hAlign="LEFT")
            tab.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5edf0")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#426979")),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#cbd5da")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend((tab, Spacer(1, 10)))
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if level == 1 and title.startswith("Appendix"):
                story.append(PageBreak())
            style = "Title" if first else ("Heading1" if level == 1 else "Heading2")
            story.append(Paragraph(escape(title), styles[style]))
            first = False
            idx += 1
            continue
        paragraph = [line]
        idx += 1
        while idx < len(lines) and lines[idx].strip() and not lines[idx].startswith(("#", "|")):
            paragraph.append(lines[idx].strip())
            idx += 1
        story.append(Paragraph(escape(" ".join(paragraph)), styles["BodyResearch"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526772"))
        canvas.drawString(42, 25, "PrescriptXAI | Research draft | At most E3 proxy evidence")
        canvas.drawRightString(A4[0]-42, 25, str(doc.page))
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=42, rightMargin=42,
                            topMargin=42, bottomMargin=43,
                            invariant=1,
                            title="PrescriptXAI: sparse recourse with separate evidence checks",
                            author="PrescriptXAI Contributors")
    doc.build(story, onFirstPage=footer, onLaterPages=footer,
              canvasmaker=partial(Canvas, invariant=1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, default=Path("artifacts/experiments/phase7-20261020T102540Z"))
    parser.add_argument("--output", type=Path, default=Path("output/pdf/prescriptxai-research-draft.pdf"))
    parser.add_argument("--publication-data", type=Path,
                        help="build from the reviewed report-data snapshot without raw/fitted assets")
    args = parser.parse_args()
    inputs = [args.study/"summary.json", args.study/"model_metadata.json",
              Path("artifacts/phase7-models/index.json"), Path("paper/manuscript.md")]
    if args.publication_data:
        saved = json.loads(args.publication_data.read_text(encoding="utf-8"))
        summary = {"manifest": saved['study_manifest'], "groups": saved['headline_groups'],
                   "latency": saved['latency'], "oracle_summary": saved['oracle_summary'],
                   "total_saved_group_count": saved['total_saved_group_count'], "complete": True}
        summary['groups'].update(saved['diagnostic_groups'])
        metadata, assets = saved['model_metadata'], saved['coupling_asset_index']
        input_hashes = {**saved['input_hashes'], str(inputs[-1]): digest(inputs[-1])}
    else:
        summary, metadata, assets = [json.loads(path.read_text(encoding="utf-8")) for path in inputs[:3]]
        input_hashes = {str(path): digest(path) for path in inputs}
    if summary.get("complete") is not True:
        raise ValueError("a complete saved study is required")
    appendix, selected = evidence_appendix(summary, metadata, assets)
    if len(selected) != 24:
        raise ValueError("all24headline strata are required")
    Path("paper/appendix.md").write_text(appendix, encoding="utf-8")
    base_keys = ("FD001/xgb/base", "FD001/mlp/base", "FD001/lstm/base", "FD002/xgb/base")
    try:
        builder_git = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        builder_git = None  # Source archives need no Git installation to typeset saved evidence.
    evidence = {"study_manifest": summary["manifest"], "headline_groups": selected,
                "latency": summary['latency'], "oracle_summary": summary['oracle_summary'],
                "diagnostic_groups": {key: group for key, group in summary['groups'].items()
                                      if key.startswith('FD001/xgb/v1/paired_internal_diagnostic/fast/')},
                "total_saved_group_count": summary.get('total_saved_group_count', len(summary['groups'])),
                "model_metadata": {key: metadata[key] for key in base_keys},
                "coupling_asset_index": {"models": {key: {
                    "coupling_calibration": assets['models'][key]['coupling_calibration']}
                    for key in base_keys}},
                "input_hashes": input_hashes,
                "publication_builder_git": builder_git,
                "builder_sha256": digest(Path(__file__)),
                "note": "Publication build only; saved measurements and original source identities retained."}
    Path("paper/evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    manuscript = inputs[-1].read_text(encoding="utf-8")
    pdf_from_markdown(manuscript + "\n\n" + appendix, args.output)
    print(json.dumps({"pdf": str(args.output), "pdf_sha256": digest(args.output),
                      "headline_groups": len(selected), "input_hashes": evidence["input_hashes"]}, indent=2))


if __name__ == "__main__":
    main()
