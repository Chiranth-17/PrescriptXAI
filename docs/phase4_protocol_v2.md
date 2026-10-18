# Phase 4 evaluation protocol v2: degraded-state plausibility

**Protocol status:** frozen before protocol-v2 evaluation.  
**Version:** 2.0.0  
**Freeze commit:** recorded in the evaluation provenance after this document is committed.  
**Evaluation date:** 2026-10-18 (Asia/Kolkata).  
**Dataset:** FD001 only; no operational actuator data or validated turbofan simulator is available.

## Purpose

Protocol v2 is a secondary sensitivity protocol for Tier 2 distributional
plausibility. It does not replace, relabel, or retroactively alter the v1
threshold. Model validity (`f(x') <= tau_safe`) remains separate from Tiers 2–4.

## Frozen definitions

| Item | Frozen definition |
|---|---|
| Tier 2 distance | The Phase 3 training-engine Mahalanobis validator and feature mapping, unchanged between v1 and v2. |
| Protocol v1 | `D_max = 5.0`, the existing primary/historical evaluation. |
| Protocol v2 | `D_max = 8.0`, a secondary sensitivity threshold selected from the nearest-rank 95th percentile of Mahalanobis distances of **validation-engine alert states** under the already-fitted v1 model and validator. |
| Alert | The true calibrated predictor returns risk `>= 0.80`. |
| Target | The true calibrated predictor returns risk `<= 0.20`; this is independent of Tier 2. |
| Sparsity and action limits | Use the frozen headline configuration; no bounds, rate limits, masks, thresholds, or sparsity rules are changed. |
| Headline population | Seeded sample of up to 200 actionable high-risk states, sampled uniformly without replacement from all high-risk states on the 15-engine held-out test split whose configured actuator/rate/trust intervals are nonempty. The test split is engine-disjoint from model, scaler, coupling, calibrator, and covariance fitting. |
| All-alert population | Every high-risk state on the named engine population, including states whose action intervals are infeasible; these remain in the denominator and are triaged as escalation where no action can be returned. |
| First-alert population | For each engine in the named population, the lowest-cycle state with calibrated risk `>= 0.80`; engines with no alert are excluded and counted. |
| Bootstrap | Percentile 95% confidence interval using engine-cluster resampling, with the configured deterministic seed and 2,000 replicates. Resampled engines carry all of their selected states. |

The headline population above was committed in the pre-existing evaluation
protocol at commit `f531682b09096abbd3abc69b633580e926ac49c8` on 2026-10-18.
Protocol v2 preserves that population. For protocol-v2 fresh-engine reporting,
use engine-grouped out-of-fold predictions and the official FD001 test engines;
all learned preprocessing and validators for a fold must be fit without its
held-out engines. A frozen holdout result alone must not be described as grouped
cross-validation.

## Secondary low-risk-tail diagnostic

Compute the nearest-rank 95th percentile of Mahalanobis distance among real
validation states with calibrated risk `< 0.80`. Report candidate distances,
real alert-state distances, and real low-risk distances. Also report the share
of returned candidates above that low-risk-tail cutoff. This is a secondary
diagnostic, not a replacement for either v1 or v2 plausibility.

## Reporting and provenance

Every result table must state: run ID, effective configuration hash, protocol
version, effective `k_max`, intervention horizon `K`, `D_max` version, and
population. Distinguish record-level from all-query denominators, and show the
number of engines used for every engine-bootstrap interval. Report target gaps
without changing their definitions. If a grouped-fold run cannot be completed,
label it unavailable and do not substitute in-sample or holdout statistics.

`K=1` means the configured single-step rate limit. `K>1` is an explicit
multi-step cumulative-action assumption: rate allowance is multiplied by `K`
while the action is assumed to be distributed over `K` steps. C-MAPSS does not
identify this horizon or validate the associated actuator dynamics. Such
results are sensitivity analyses only, not evidence that an operational
intervention is safe.
