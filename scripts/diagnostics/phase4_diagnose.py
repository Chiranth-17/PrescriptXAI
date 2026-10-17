#!/usr/bin/env python3
"""Phase 4 post-run diagnostics: D1-D7 funnel, constraint ladder, failure classification.

Usage
-----
    uv run python scripts/diagnostics/phase4_diagnose.py \\
        --report artifacts/FD001-evaluation-grid-final.json \\
        --config data/processed/phase4-grid-final.yaml \\
        --out docs/phase4_diagnosis.md

All numbers are computed from the saved JSON records.  No hand tallies.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct(n: int, d: int) -> str:
    if d == 0:
        return "N/A (0 denominator)"
    return f"{n}/{d} = {n / d:.1%}"


def _percentile(values: list[float], p: float) -> float:
    return float(np.percentile(values, p)) if values else float("nan")


def _load_report(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# D1 - Recourse funnel (all queries are the denominator)
# ---------------------------------------------------------------------------

def d1_funnel(records: list[dict], tau_safe: float, d_max: float) -> dict:
    """Compute D1 metrics exactly as defined in the synopsis.

    - Recourse Validity Rate  : f(x') <= tau_safe, over ALL queries.
    - Distributional Plausibility (Tier 2): D_M(x') <= D_max, over ALL queries.
    - Tier 3 engineering pass rate, over ALL queries.
    - Tier 4 coupling pass rate, over ALL queries.
    - Joint success (Tier 1 AND Tiers 2-4), over ALL queries.
    - Plausibility among model-valid candidates only (extra row, not the 90% target).
    """
    n = len(records)
    if n == 0:
        return {"error": "no records"}

    model_valid      = [r for r in records if r["model_valid"]]
    tier2_pass       = [r for r in records if r["tier2_plausible"]]
    tier3_pass       = [r for r in records if r["tier3_engineering_valid"]]
    tier4_pass       = [r for r in records if r["tier4_coupling_valid"]]
    joint_success    = [
        r for r in records
        if r["model_valid"]
        and r["tier2_plausible"]
        and r["tier3_engineering_valid"]
        and r["tier4_coupling_valid"]
    ]
    # Plausibility among model-valid only (additional diagnostic row)
    mv_tier2_pass    = [r for r in model_valid if r["tier2_plausible"]]

    return {
        "total_queries":               n,
        "recourse_validity_rate":      {"n": len(model_valid), "d": n,
                                        "rate": len(model_valid) / n,
                                        "target": ">=0.95",
                                        "passes": len(model_valid) / n >= 0.95},
        "tier2_distributional_rate":   {"n": len(tier2_pass), "d": n,
                                        "rate": len(tier2_pass) / n,
                                        "target": ">=0.90",
                                        "passes": len(tier2_pass) / n >= 0.90},
        "tier3_engineering_rate":      {"n": len(tier3_pass), "d": n,
                                        "rate": len(tier3_pass) / n,
                                        "target": "no synopsis target"},
        "tier4_coupling_rate":         {"n": len(tier4_pass), "d": n,
                                        "rate": len(tier4_pass) / n,
                                        "target": "no synopsis target"},
        "joint_success_rate":          {"n": len(joint_success), "d": n,
                                        "rate": len(joint_success) / n,
                                        "target": "strictly separate; NOT the 90% plausibility target"},
        "tier2_among_model_valid":     {"n": len(mv_tier2_pass), "d": len(model_valid),
                                        "rate": (len(mv_tier2_pass) / len(model_valid)
                                                 if model_valid else None),
                                        "note": "extra diagnostic; not a synopsis target denominator"},
    }


# ---------------------------------------------------------------------------
# D2 - Constraint ladder (per-failure breakdown)
# ---------------------------------------------------------------------------

def d2_constraint_ladder(records: list[dict]) -> dict:
    """Classify each failure by which constraint it fails first (funnel order)."""
    n = len(records)
    fail_tier1       = [r for r in records if not r["model_valid"]]
    fail_tier2_only  = [r for r in records if r["model_valid"] and not r["tier2_plausible"]]
    fail_tier3_only  = [r for r in records
                        if r["model_valid"] and r["tier2_plausible"]
                        and not r["tier3_engineering_valid"]]
    fail_tier4_only  = [r for r in records
                        if r["model_valid"] and r["tier2_plausible"]
                        and r["tier3_engineering_valid"]
                        and not r["tier4_coupling_valid"]]
    all_pass         = [r for r in records
                        if r["model_valid"] and r["tier2_plausible"]
                        and r["tier3_engineering_valid"] and r["tier4_coupling_valid"]]

    return {
        "total_queries":         n,
        "fail_tier1_model":      {"n": len(fail_tier1),      "pct": _pct(len(fail_tier1),     n)},
        "fail_tier2_only":       {"n": len(fail_tier2_only), "pct": _pct(len(fail_tier2_only), n)},
        "fail_tier3_only":       {"n": len(fail_tier3_only), "pct": _pct(len(fail_tier3_only), n)},
        "fail_tier4_only":       {"n": len(fail_tier4_only), "pct": _pct(len(fail_tier4_only), n)},
        "all_pass":              {"n": len(all_pass),         "pct": _pct(len(all_pass),        n)},
    }


# ---------------------------------------------------------------------------
# D3 - Failure classification: search failure vs. true infeasible
#       (exhaustive reference search not yet implemented -> all marked unclassified)
# ---------------------------------------------------------------------------

def d3_failure_classification(records: list[dict]) -> dict:
    """Placeholder: mark remaining failures as 'not yet classified' per protocol."""
    failures = [r for r in records if not (
        r["model_valid"] and r["tier2_plausible"]
        and r["tier3_engineering_valid"] and r["tier4_coupling_valid"]
    )]
    return {
        "total_failures": len(failures),
        "classified_as_search_failure": 0,
        "classified_as_true_infeasible": 0,
        "remaining_failures_not_yet_classified": len(failures),
        "note": (
            "Exhaustive reference search (D3 protocol) has not yet been run. "
            "All failures remain unclassified.  Do not claim 'fundamental limitation' "
            "until this step is complete."
        ),
    }


# ---------------------------------------------------------------------------
# D4 - Latency (THOROUGH mode = this run; FAST mode = not yet measured)
# ---------------------------------------------------------------------------

def d4_latency(records: list[dict]) -> dict:
    opt_ms   = [r["optimization_ms"] for r in records if r.get("optimization_ms") is not None]
    val_ms   = [r["validation_ms"]   for r in records if r.get("validation_ms")   is not None]
    pipe_ms  = [
        (r["backend_pipeline_ms"] if r.get("backend_pipeline_ms") is not None
         else r["optimization_ms"] + r["validation_ms"])
        for r in records
        if r.get("optimization_ms") is not None and r.get("validation_ms") is not None
    ]

    def stats(vals: list[float]) -> dict:
        if not vals:
            return {"p50_ms": None, "p95_ms": None, "p99_ms": None, "mean_ms": None}
        return {
            "p50_ms":  round(_percentile(vals, 50),  1),
            "p95_ms":  round(_percentile(vals, 95),  1),
            "p99_ms":  round(_percentile(vals, 99),  1),
            "mean_ms": round(float(np.mean(vals)),    1),
        }

    opt_stats = stats(opt_ms)
    budget_passed = (
        opt_stats["p95_ms"] <= 1800 if opt_stats["p95_ms"] is not None else None
    )
    return {
        "mode":   "THOROUGH (expanded grid; offline only)",
        "note":   (
            "FAST (production) mode not yet measured. "
            "p95 optimization budget is <=1800 ms. "
            "This run is expected to be well above budget."
        ),
        "optimization_budget_p95_ms": 1800,
        "optimization": opt_stats,
        "validation":   stats(val_ms),
        "pipeline":     stats(pipe_ms),
        "budget_passed": budget_passed,
    }


# ---------------------------------------------------------------------------
# D5 - Sparsity and risk reduction
# ---------------------------------------------------------------------------

def d5_sparsity_and_risk(records: list[dict]) -> dict:
    joint = [
        r for r in records
        if r["model_valid"] and r["tier2_plausible"]
        and r["tier3_engineering_valid"] and r["tier4_coupling_valid"]
    ]
    all_changed = [r["changed_features"] for r in records]
    joint_changed = [r["changed_features"] for r in joint]
    risk_drops = [r["initial_risk"] - r["final_risk"] for r in records]
    return {
        "mean_changed_features_all_queries":   round(float(np.mean(all_changed)), 4) if all_changed else None,
        "mean_changed_features_joint_success": round(float(np.mean(joint_changed)), 4) if joint_changed else None,
        "mean_risk_drop_all_queries":          round(float(np.mean(risk_drops)), 4) if risk_drops else None,
        "average_sparsity_target":             "<=3 (over joint successes)",
        "average_sparsity_passes":             (float(np.mean(joint_changed)) <= 3) if joint_changed else None,
    }


# ---------------------------------------------------------------------------
# D6 - Constraint violation counts
# ---------------------------------------------------------------------------

def d6_violations(records: list[dict]) -> dict:
    return {
        "frozen_feature_violations": sum(r.get("frozen_feature_violations", 0) for r in records),
        "actuator_bound_violations": sum(r.get("actuator_bound_violations",  0) for r in records),
        "rate_limit_violations":     sum(r.get("rate_limit_violations",       0) for r in records),
    }


# ---------------------------------------------------------------------------
# D7 - Provenance
# ---------------------------------------------------------------------------

def d7_provenance(report: dict, config_path: str) -> dict:
    prov = report.get("provenance", {})
    records = report.get("records", [])
    query_ids = [(r["engine_id"], r["cycle"]) for r in records]
    return {
        "config_path":           config_path,
        "evaluation_git_commit": prov.get("evaluation_git_commit"),
        "source_dirty":          prov.get("evaluation_tracked_source_dirty"),
        "total_queries":         len(records),
        "query_engine_ids":      sorted({r["engine_id"] for r in records}),
        "query_ids":             query_ids,
        "holdout_engine_ids":    prov.get("holdout_engine_ids"),
        "sampling_policy":       prov.get("sampling_policy"),
        "population_note": (
            "Queries are sampled from high-risk test-split states with feasible actuator "
            "intervals (all alert states from held-out test engines, seeded uniform sample "
            "when count exceeds max_queries).  This is NOT 'first alert per engine'."
        ),
        "config_sha256":         prov.get("effective_configuration_sha256"),
        "model_git_commit":      prov.get("model_training_git_commit"),
        "tuning_note": (
            "WARNING: expanded solver settings (k_max=5, max_scaled_distance=6.0, "
            "restarts=3, max_iter=100, true_model_grid_points=10) were applied while "
            "observing results from these same test states.  Per tuning protocol (item 5), "
            "these settings must be frozen under configs/experiments/, tuned on validation "
            "engines, and a fresh run on test states must be done before quoting a headline number."
        ),
    }


# ---------------------------------------------------------------------------
# Decision table (per Prompt 4R-A)
# ---------------------------------------------------------------------------

def decision_table(d1: dict, d4: dict) -> list[str]:
    lines = ["## Decision table (Prompt 4R-A)"]
    validity_rate = d1["recourse_validity_rate"]["rate"]
    tier2_rate    = d1["tier2_distributional_rate"]["rate"]
    opt_p95       = d4["optimization"]["p95_ms"]

    lines.append(f"- Recourse validity rate  : {validity_rate:.1%}  (target >=95%)")
    lines.append(f"- Tier 2 plausibility rate: {tier2_rate:.1%}  (target >=90%)")
    lines.append(f"- Optimization p95 latency: {opt_p95} ms  (budget <=1800 ms)")
    lines.append("")

    if validity_rate >= 0.95 and tier2_rate >= 0.90:
        lines.append("OUTCOME: Both synopsis targets met -> proceed to close Phase 4.")
    elif validity_rate >= 0.95:
        lines.append("OUTCOME: Validity target met; plausibility gap remains -> one round of 4R-B allowed (Tier 2 fixes only).")
    elif tier2_rate >= 0.90:
        lines.append("OUTCOME: Plausibility target met; validity gap remains -> one round of 4R-B allowed (optimizer fixes only).")
    else:
        lines.append("OUTCOME: Both targets missed -> one round of 4R-B allowed. After that, close Phase 4 with honest numbers.")

    if opt_p95 is not None and opt_p95 > 1800:
        lines.append(
            f"LATENCY: THOROUGH mode exceeds budget ({opt_p95} ms p95 vs 1800 ms). "
            "FAST mode must be designed and measured before claiming production readiness."
        )
    else:
        lines.append("LATENCY: p95 within budget (or unmeasured).")

    return lines


# ---------------------------------------------------------------------------
# Render Markdown
# ---------------------------------------------------------------------------

def render_markdown(
    config_path: str,
    d1: dict, d2: dict, d3: dict, d4: dict, d5: dict, d6: dict, d7: dict,
    decision: list[str],
) -> str:
    lines = [
        "# Phase 4 Diagnosis Report",
        "",
        f"**Config**: `{config_path}`",
        f"**Evaluation git commit**: `{d7['evaluation_git_commit']}`",
        f"**Source dirty at eval time**: `{d7['source_dirty']}`",
        f"**Total queries**: {d7['total_queries']}",
        f"**Sampling policy**: {d7['sampling_policy']}",
        f"**Population**: {d7['population_note']}",
        "",
        "> [!WARNING]",
        f"> {d7['tuning_note']}",
        "",
        "---",
        "",
        "## D1 - Recourse funnel (all queries = denominator)",
        "",
        "| Metric | N | D | Rate | Target | Status |",
        "|--------|---|---|------|--------|--------|",
    ]

    rv  = d1["recourse_validity_rate"]
    t2  = d1["tier2_distributional_rate"]
    t3  = d1["tier3_engineering_rate"]
    t4  = d1["tier4_coupling_rate"]
    js  = d1["joint_success_rate"]
    mv2 = d1["tier2_among_model_valid"]

    def row(label: str, m: dict) -> str:
        rate_str = f"{m['rate']:.1%}" if m.get("rate") is not None else "N/A"
        passes = m.get("passes")
        status = ("PASS" if passes else "FAIL") if isinstance(passes, bool) else m.get("target", "-")
        return f"| {label} | {m['n']} | {m['d']} | {rate_str} | {m['target']} | {status} |"

    lines.append(row("Recourse Validity (Tier 1: f(x') <= tau_safe)", rv))
    lines.append(row("Distributional Plausibility (Tier 2: D_M <= D_max)", t2))
    lines.append(row("Engineering validity (Tier 3)", t3))
    lines.append(row("Sensor coupling validity (Tier 4)", t4))
    lines.append(
        f"| Joint success (Tiers 1-4) | {js['n']} | {js['d']} | "
        f"{js['rate']:.1%} | {js['target']} | - |"
    )
    mv2_rate = f"{mv2['rate']:.1%}" if mv2.get("rate") is not None else "N/A"
    lines.append(
        f"| Tier 2 plausibility among model-valid (extra diagnostic) | "
        f"{mv2['n']} | {mv2['d']} | {mv2_rate} | {mv2['note']} | - |"
    )

    lines += [
        "",
        "---",
        "",
        "## D2 - Constraint ladder (first failing constraint per query)",
        "",
        "| Failure type | N | % of all queries |",
        "|---|---|---|",
        f"| Fail Tier 1 (model invalid) | {d2['fail_tier1_model']['n']} | {d2['fail_tier1_model']['pct']} |",
        f"| Fail Tier 2 only (model valid, not plausible) | {d2['fail_tier2_only']['n']} | {d2['fail_tier2_only']['pct']} |",
        f"| Fail Tier 3 only | {d2['fail_tier3_only']['n']} | {d2['fail_tier3_only']['pct']} |",
        f"| Fail Tier 4 only | {d2['fail_tier4_only']['n']} | {d2['fail_tier4_only']['pct']} |",
        f"| All pass (joint success) | {d2['all_pass']['n']} | {d2['all_pass']['pct']} |",
        "",
        "---",
        "",
        "## D3 - Failure classification",
        "",
        f"Total failures: {d3['total_failures']}",
        f"- Search failures (solver missed valid candidate): {d3['classified_as_search_failure']}",
        f"- True infeasible (exhaustive search confirmed): {d3['classified_as_true_infeasible']}",
        f"- Remaining failures not yet classified: {d3['remaining_failures_not_yet_classified']}",
        "",
        f"> {d3['note']}",
        "",
        "---",
        "",
        "## D4 - Latency",
        "",
        f"**Mode**: {d4['mode']}",
        "",
        f"> {d4['note']}",
        "",
        "| Stage | Mean ms | P50 ms | P95 ms | P99 ms | Budget (p95) |",
        "|-------|---------|--------|--------|--------|--------------|",
    ]

    def lat_row(label: str, s: dict, budget: float | None = None) -> str:
        bp = "-"
        if budget is not None and s["p95_ms"] is not None:
            bp = f"<={budget:.0f} ms -> {'PASS' if s['p95_ms'] <= budget else 'FAIL'}"
        return (
            f"| {label} | {s['mean_ms']} | {s['p50_ms']} | {s['p95_ms']} "
            f"| {s['p99_ms']} | {bp} |"
        )

    lines.append(lat_row("Optimization", d4["optimization"], d4["optimization_budget_p95_ms"]))
    lines.append(lat_row("Validation",   d4["validation"]))
    lines.append(lat_row("Pipeline",     d4["pipeline"]))

    lines += [
        "",
        "**FAST (production) mode**: not yet measured.  "
        "Speedups to explore: early stopping on first margin-passing candidate, "
        "vectorized batch true-model scoring, pruning dominated supports before grid search.",
        "",
        "---",
        "",
        "## D5 - Sparsity and risk reduction",
        "",
        f"- Mean changed features (all queries): {d5['mean_changed_features_all_queries']}",
        f"- Mean changed features (joint successes): {d5['mean_changed_features_joint_success']}",
        f"- Mean risk drop (all queries): {d5['mean_risk_drop_all_queries']}",
        f"- Average sparsity target: {d5['average_sparsity_target']}",
        f"- Average sparsity passes: {d5['average_sparsity_passes']}",
        "",
        "---",
        "",
        "## D6 - Constraint violation counts",
        "",
        f"- Frozen-feature violations: {d6['frozen_feature_violations']}",
        f"- Actuator-bound violations: {d6['actuator_bound_violations']}",
        f"- Rate-limit violations: {d6['rate_limit_violations']}",
        "",
        "---",
        "",
        "## D7 - Provenance",
        "",
        f"- Config path: `{d7['config_path']}`",
        f"- Evaluation git commit: `{d7['evaluation_git_commit']}`",
        f"- Config SHA-256: `{d7['config_sha256']}`",
        f"- Model training commit: `{d7['model_git_commit']}`",
        f"- Total queries: {d7['total_queries']}",
        f"- Held-out test engine IDs: {d7['holdout_engine_ids']}",
        f"- Query engine IDs in this run: {d7['query_engine_ids']}",
        "",
        "---",
        "",
    ] + decision + [
        "",
        "---",
        "",
        "_Generated by `scripts/diagnostics/phase4_diagnose.py`. "
        "All numbers computed from saved JSON records._",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4 post-run diagnostics")
    parser.add_argument("--report",   required=True, type=Path, help="Path to evaluation JSON report")
    parser.add_argument("--config",   required=True, type=str,  help="Config path used for the run")
    parser.add_argument("--out",      required=True, type=Path, help="Output Markdown path")
    parser.add_argument("--json-out", type=Path, default=None,  help="Optional JSON output path")
    parser.add_argument("--tau-safe", type=float, default=0.20)
    parser.add_argument("--d-max",    type=float, default=5.0)
    args = parser.parse_args(argv)

    if not args.report.exists():
        print(f"ERROR: report file not found: {args.report}", file=sys.stderr)
        return 1

    print(f"Loading report: {args.report}")
    report  = _load_report(args.report)
    records = report.get("records", [])
    print(f"  {len(records)} records loaded.")

    if not records:
        print("ERROR: no records in report.", file=sys.stderr)
        return 1

    d1 = d1_funnel(records, args.tau_safe, args.d_max)
    d2 = d2_constraint_ladder(records)
    d3 = d3_failure_classification(records)
    d4 = d4_latency(records)
    d5 = d5_sparsity_and_risk(records)
    d6 = d6_violations(records)
    d7 = d7_provenance(report, args.config)
    decision = decision_table(d1, d4)

    md = render_markdown(args.config, d1, d2, d3, d4, d5, d6, d7, decision)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    print(f"Markdown report written: {args.out}")

    if args.json_out:
        payload = {
            "d1_funnel": d1, "d2_constraint_ladder": d2,
            "d3_classification": d3, "d4_latency": d4,
            "d5_sparsity": d5, "d6_violations": d6,
            "d7_provenance": d7,
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON report written: {args.json_out}")

    # Print summary to stdout
    print()
    print("=== D1 SUMMARY ===")
    rv = d1["recourse_validity_rate"]
    t2 = d1["tier2_distributional_rate"]
    js = d1["joint_success_rate"]
    print(f"  Recourse validity   : {rv['rate']:.1%}  {rv['n']}/{rv['d']}  target {rv['target']} -> {'PASS' if rv['passes'] else 'FAIL'}")
    print(f"  Tier 2 plausibility : {t2['rate']:.1%}  {t2['n']}/{t2['d']}  target {t2['target']} -> {'PASS' if t2['passes'] else 'FAIL'}")
    print(f"  Joint success       : {js['rate']:.1%}  {js['n']}/{js['d']}  (separate metric)")
    print()
    print("=== D4 LATENCY (THOROUGH mode) ===")
    print(
        f"  Optimization p50/p95/p99 ms: "
        f"{d4['optimization']['p50_ms']} / {d4['optimization']['p95_ms']} / {d4['optimization']['p99_ms']}"
    )
    passed_str = "PASS" if d4["budget_passed"] else "FAIL"
    print(f"  Budget (p95 <=1800 ms): {passed_str}")
    print()
    for line in decision:
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
