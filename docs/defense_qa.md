# Defense questions and answers

Population results below refer to the frozen Phase 7 run and its [generated results tables](results.md).
Individual manual-preview examples in question 16 come from the separately recorded Phase 8
walkthrough. These are measured examples, not synopsis illustrations. All depend on proxy assumptions.

## 1. How do you know a recommendation lowers failure risk on a real machine? (synopsis)

We do not establish that causal claim. Tier1 tests the fitted calibrated predictor. Tier2 checks
statistical distance; Tiers3/4 check proxy limits and learned/configured relationships. Field
interventions or a validated dynamic simulator are absent. The current ceiling is E3.

## 2. Can you claim extra RUL cycles from C-MAPSS? (synopsis)

No. These are static run-to-failure trajectories without observed interventions. RUL labels define
the classification target; moving a feature vector does not produce a new life trajectory.

## 3. What distinguishes predictive, diagnostic, unconstrained and prescriptive methods?

Prediction produces an alert probability. Diagnostic attribution describes model influence.
Unconstrained recourse seeks a model-changing feature vector. This system adds an explicit proxy
action space, bounded sparse search, independent tiers, failure triage and evidence/provenance.
The constraints improve the question being asked; they do not turn correlation into causation.

## 4. Why L1 instead of L0?

L0 counts nonzero actions but is combinatorial. Scaled L1 provides a useful continuous search cost;
the implementation supports smooth L1 or exact variable splitting. L1 alone does not enforce
k_max: support pruning/reoptimization and bounded grid checks enforce the explicit support cap.

## 5. Why Mahalanobis distance?

It accounts for train-observed feature covariance instead of treating correlated sensor axes as
independent. Shrinkage plus a diagonal floor improves numerical stability. Regime-specific
Cholesky distances remain a coarse ellipsoidal plausibility test, not a physical law.

## 6. Why calibrate probabilities?

The .80 alert and .20 safe gates act on probabilities. Calibration is fitted on validation engines
and checked on held-out data with Brier score, ECE and reliability bins. It does not guarantee
calibration under distribution shift or establish causal response to a changed sensor.

## 7. How were immutable features chosen?

The YAML taxonomy freezes operating settings and context identifiers/cycle for an individual
recommendation. Seven measured channels are configured as controllable proxies. This mapping is
a documented assumption, not actuator telemetry; a real deployment needs domain-approved controls.

## 8. What if the gradient surrogate is wrong?

Search can miss feasible candidates or waste effort. Every final candidate is rescored by the true
calibrated predictor and exact validators. Reports expose probability disagreement and surrogate
fidelity; model selection is never tuned to make recourse look successful. This controls false
surrogate acceptance, not completeness of search.

## 9. Why not reinforcement learning?

The dataset supplies no interactive actuator environment or reliable transition/reward model.
Training a control policy here would require unverified dynamics assumptions. Static recourse
makes a narrower, inspectable recommendation with explicit limitations and an optional future
validated dynamics interface.

## 10. What is novel relative to DiCE and other recourse libraries?

The contribution is the integrated maintenance-proxy workflow: engine-disjoint provenance,
raw/scaled action mappings, learned coupling, separate tiers, failure triage, and audited reporting.
It is not a claim to have invented sparse recourse. DiCE already supports diverse counterfactuals
and feature/range constraints ([official documentation](https://interpret.ml/DiCE/)); our comparison
must use the same cohorts and report its settings and failures, not describe it as inherently
unconstrained or assert universal superiority.

## 11. Why not 95% validity?

The design target is not a guaranteed deliverable. For FD001 XGBoost v1 grouped OOF all-alert
states, the measured validity is52.52% and joint success39.91% (100engines; intervals in results).
The retained funnel is11890query/seed observations ->11245returned ->6245T1 ->4775T2 ->4775T3
->4745T4/joint. Triage is4745RECOVERABLE,610PARTIAL,6535ESCALATE. These counts include five
solver seeds on fixed predictors, not11890independent engines.

The paired12-query/10-engine diagnostic ladder illustrates the trade-off: all-free L0 validity75%
with T2plausibility8.33%, versus full/L7 validity33.33% with T2plausibility50%. It is a different
population from the headline. All40failed reference-search observations remain
unresolved_finite_search; none establishes true continuous infeasibility. Feasibility limits,
model/coupling constraints and search incompleteness must remain separate explanations.

## 12. Is 90% plausibility just a constraint you imposed?

D_max is a declared constraint, but returned states can fail it and queries can return no usable
counterfactual. Report both denominators: v1 groupedOOF Tier2 is48.70% over11890observations and
51.04% over11245returned candidates. The separately registered v2 gives98.07% all-query and
98.98% returned, while validity stays52.52%. That trade-off is visible rather than replacing v1;
a relaxed ellipsoid does not demonstrate better physics. See both-protocol tables and CIs.

## 13. What evidence level did you reach?

At most E3 for qualifying results: model safety, statistical plausibility and proxy engineering/
coupling checks. Failed tiers remain visible, skipped dynamic checks do not pass, and a PARTIAL
result failing Tier1 is not model-safe. No E4 transition emulator or E5 physics evidence exists.

## 14. How do you prevent leakage?

Split complete engines before fitting. Fit scaling/covariance/coupling/predictor on training
engines; calibration and solver development use validation engines. Freeze solver/configuration
before held-out evaluation. Grouped OOF predictions use only their fold's held-out engines.
Repeated public-engine evaluations are labeled reused evidence, not fresh confirmation.

## 15. What does PARTIAL mean?

The candidate meets the proxy/statistical constraints and configured minimum risk drop, but its
true calibrated risk remains above .20. It requires review and is not a safe recommendation.
A state at or below .20 can never be PARTIAL; it may still ESCALATE because another tier fails.

## 16. Why can a low-risk candidate be rejected?

True risk is only Tier1. The historical manual preview at20/c179 reached .05420930 but failed
Tier2 and a rate constraint, so it correctly ESCALATEd with E1 only. The separate accepted
historical case reached .12086279 with E3. These individual examples are not population rates.
See the [Phase 8 walkthrough and provenance](phase8_changes.md).

## 17. Is latency within budget?

Not uniformly. The frozen serial study retains1000calls/mode across16engines. Optimization p95
is2339.075ms FAST and2080.227ms THOROUGH, both above1800ms. THOROUGH backend total2089.845ms
meets2200ms; FAST2348.233ms misses. Faster than a band's lower figure is a pass. Warm backend
measurements exclude startup/network/browser; Phase9's fixture optimization is not a revised
C-MAPSS timing claim. See the generated budget table and engine intervals.

## 18. What is the deployment path?

Use a validated actual-control map, secure artifact supply chain, prospective temporal/engine
validation and qualified domain review. Then test transition/physical behavior with independent
safety controls, monitor drift/calibration and operate in shadow mode before any intervention.
The packaged API/container are engineering delivery mechanisms, not deployment certification.

## 19. How does this relate to SDG9?

Reliable maintenance decision support is a research connection to Target9.1 infrastructure
reliability; resource-aware industrial maintenance could connect to9.4 efficiency. This repository
does not measure downtime, fuel, emissions, production value or SDG indicators. See the
[source-linked SDG discussion](sdg9.md).

## 20. Can someone reproduce the numbers from the demo command?

The short command reconstructs a separately registered FD001 demonstration and manifest from raw
data. It does not recreate the multi-day Phase7 study. Historical tables retain their original
run/source/config identities and saved records; reproducing that study requires its full declared
populations and hardware/runtime context. Never present the short demo as the full experiment.

## 21. What happens when artifacts or inputs are broken?

Typed boundary checks reject malformed fields, nonfinite values, incompatible feature lists,
missing calibration/coupling and untrusted artifact paths. Operator interfaces give structured
errors. Reproduction refuses existing output directories and retains selected queries/completed
records on a later failure. Error handling does not substitute a synthetic successful result.
