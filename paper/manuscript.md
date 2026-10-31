# PrescriptXAI: sparse recourse with separate model, distribution and proxy engineering checks

PrescriptXAI Contributors | Research draft | 30 October 2026

## Abstract

Predictive maintenance scores do not specify a permissible intervention. PrescriptXAI integrates sparse bounded recourse with four separately reported checks: calibrated model validity, distributional plausibility, proxy engineering limits and learned sensor relationships. The application searches a configured control space and rescores every candidate with the true predictor before acceptance. Experiments on C-MAPSS include XGBoost, multilayer perceptron and history-aware LSTM profiles, two registered Mahalanobis thresholds, and internal held-out, grouped out-of-fold and official-test populations. All failures remain in all-query denominators. Confidence intervals resample complete engines rather than treating cycles or solver seeds as independent units. The saved results show that model validity alone can coexist with poor plausibility or coupling. They do not establish uniformly satisfactory recourse. A frozen second-seed replay reproduced every registered query within the stated numerical tolerance, while historical latency measurements miss some design budgets. The system reaches at most E3 evidence under documented sensor-proxy assumptions. It does not demonstrate actual actuator response, physical safety, field resource savings or remaining-useful-life extension. This manuscript reports an auditable research implementation and its limitations, not a submitted or peer-reviewed article.

Keywords: algorithmic recourse, predictive maintenance, C-MAPSS, calibration, sparse optimization, grouped uncertainty, reproducibility.

## 1. Introduction

A high predicted failure score can justify inspection without identifying a change that an operator can safely apply. Feature attribution explains a prediction, whereas recourse asks which allowed changes would reach a specified model target. These questions remain distinct from whether an intervention would improve the machine. A maintenance interface that merges them risks presenting a statistical counterfactual as an operating instruction.

The research question is whether constrained recourse can generate sparse, actionable and plausible candidates while avoiding unsupported operating states. We operationalize this question in an explicitly assumed proxy action space because public C-MAPSS trajectories contain sensor observations rather than commanded interventions. The contribution is an integrated, inspectable workflow: grouped preprocessing and calibration, bounded sparse search, independent final validation, explicit escalation, an operator dashboard, and result-level provenance. We make no claim of a globally optimal nonlinear solver or a new causal model.

The original synopsis contains a turbofan illustration with specific risk and control percentages. Those values are examples, not measurements from this work. The appendix is generated from the completed study rather than copied from that case. Design targets remain visible even when the observations miss them.

## 2. Related work

C-MAPSS damage-propagation modeling provides a foundation for prognostic benchmarks [1]. The fact that benchmark trajectories originated in simulation does not supply this project with an interactive, independently validated simulator. Wachter and colleagues describe counterfactual explanations as changes that would alter a decision [2]. Ustun and colleagues examine actionable recourse for linear classification [3]. Their optimization certificates do not transfer to our bounded finite nonlinear search.

DiCE generates diverse counterfactual explanations and explicitly considers feasibility and user constraints [4]. It would therefore be inaccurate to characterize all other recourse methods as unconstrained. Our comparison concerns the exact configured baseline implementations saved in this study, rather than a claim about every possible use of those methods. Karimi and colleagues distinguish counterfactual feature changes from causal interventions [5], a distinction central to interpreting maintenance candidates.

Calibration concerns the relationship between predicted scores and observed frequencies [6]. It does not establish that moving a sensor feature changes failure probability under intervention. We use calibration diagnostics to select and assess predictors independently of their recourse outcomes. Covariance shrinkage [7] supports regularized statistical distance estimation. XGBoost [8] supplies a tree-based prediction option, whose differentiable surrogate is used only during search. UN Sustainable Development Goal 9 [9] motivates infrastructure reliability and resource efficiency; no official SDG indicator is measured here.

## 3. Method

### 3.1 State, units and admissible action space

Let x be a raw state, z=(x-mu)/s its training-fitted standardized representation, and f the calibrated failure predictor for the configured label 1[RUL <= H]. Engine identity and cycle count are context, never mutable decision variables. A danger gate starts recourse only when the true calibrated score reaches tau_danger. The final model target is f(x') <= tau_safe. Exact settings and per-run hashes appear in the generated appendix.

The taxonomy partitions channels into control proxies, immutable context and dependent sensors. The optimization variable delta contains scaled changes to active controls only. For each control, the raw physical interval intersects the assumed K-step rate interval and the configured scaled trust radius. The resulting interval is transformed into scaled-change bounds. The default rate envelope is derived from within-engine adjacent-cycle training changes, without differencing across engine boundaries. It is a proxy assumption, not a measured actuator slew limit.

Raw changes satisfy delta_x_j = s_j * delta_z_j and are displayed alongside scaled changes. All frozen bounds, masks, rates, sparsity limits, thresholds and horizons come from YAML and fitted training artifacts. The literal synopsis taxonomy is not available in full: public channels are not fuel or bleed-valve commands, environmental measurements are absent, and physical core speed is configured as a proxy control while corrected core speed is dependent. These choices are disclosed rather than relabeled as direct actuator telemetry.

### 3.2 Objective and search

The synopsis objective combines full-state L1 movement, prediction-flip loss, an immutable penalty and a bound penalty. The implemented adaptation minimizes a scaled control-space movement cost with a prediction penalty and configured feasibility feedback. In compact form:

J(delta) = lambda_1 * sum_j(sqrt(delta_j^2 + epsilon^2)-epsilon) + alpha * max(0, f_search(x'(delta))-tau_safe+m)^q + gamma*P_bounds(delta) + w_feas*P_feas(x'(delta)).

Here q selects hinge or squared hinge, m is the configured search margin, and P_feas penalizes normalized distribution and coupling excess. An exact positive/negative L1 parameterization is also supported. Immutable coordinates are absent from delta, so their reported penalty is identically zero. Hard box constraints remain active even when the soft bound penalty is zero. This is not literal raw full-state L1 minimization.

SciPy L-BFGS-B uses autograd derivatives. The configured weight schedules, restarts and support search are frozen for evaluation. Dense candidates are pruned and reoptimized on sparse supports. A deterministic bounded grid over the same admissible intervals provides a true-predictor fallback. XGBoost search uses a learned differentiable surrogate, but all candidate selection and final validity decisions use the actual calibrated tree predictor. A surrogate-safe result is never accepted on that basis alone. FAST and THOROUGH are distinct configured search modes, not guarantees of a runtime ordering.

### 3.3 Dependent channels and four checks

The learned relationship g(c) propagates a dependent observation as d'=d+g(c')-g(c). A zero action retains the observed residual; that residual need not represent degradation. The scaled implementation keeps the explicit scaled-to-raw and raw-to-scaled operations. Scalar propagation updates all fitted dependent targets. Batched and torch propagation update only targets represented in the predictor/scaler feature order; grid materialization retains original values for omitted targets. The residual formula therefore does not apply to every target on every path, and no global Tier 4 margin invariance is claimed. Relationship residuals, threshold exceedance and surrogate error diagnostics accompany recourse outcomes.

Tier 1 independently evaluates true calibrated model risk. Tier 2 computes the square root Mahalanobis distance using train-fitted regularized covariance and, when configured, a regime fixed by the original operating context. Tier 3 checks immutable fields, proxy bounds, rates and operating context. Support/action feasibility is checked separately when computing joint success. Tier 4 checks configured relationships and learned residual envelopes. Joint success requires all four checks and solver feasibility. None of these checks is a certificate of physical safety.

Evidence E1 denotes model validity, E2 statistical plausibility, and E3 the proxy engineering/coupling checks available here. E4 would require a validated response emulator on held-out units and operating regions. E5 would require validated physics simulation. The optional simulator contract is disabled by default. A learned coupling regressor is not a simulator. The dashboard exposes the attained evidence and assumptions for each result.

### 3.4 Operator delivery and failure handling

The pipeline ingests a state, evaluates risk, applies the gate, searches if eligible, validates independently and returns an operator-facing result. An unavailable admissible action produces escalation and diagnostics. An input projected into a bound intersection is not automatically an actionable recommendation. A true-model-safe diagnostic can still fail sparsity or another tier. The dashboard shows original and candidate risk, raw changes, validation evidence and impact attribution; its sliders remain decision-support controls, not a connection to hardware.

## 4. Experimental protocol

### 4.1 Populations and fitting isolation

The committed evaluation protocol defines development states on validation engines, reporting on internal held-out engines, grouped out-of-fold predictions and official test engines when cycle-level RUL is derivable. The full study includes FD001 XGBoost, MLP and history-aware LSTM, and FD002 XGBoost. Preprocessors, covariance and coupling models use only declared training engines. Calibrators use their registered calibration engines. Predictor selection uses predictive and calibration metrics, never recourse feasibility. The predictive table separately reports original training source/config hashes and evaluation source/config paths. Later Phase 7 evaluation configs are not reconstructed original fitting configs; where the original fit file is unavailable, its saved hash/source is retained without claiming full file reconstruction.

Both registered D_max versions are retained: v1 uses its original cutoff and v2 uses its separately documented larger cutoff. The latter never replaces v1. Version 2 was separately registered before its own run and remains a distinct result alongside v1. This versioning does not erase earlier diagnostic exposure: the historical record cannot certify that every public test engine was never previously inspected, or that every v2 engine was fresh at first diagnosis. This limits strict once-ever generalization claims even though fit isolation and run provenance can be checked.

The headline intervention horizon is K=1. Saved K sensitivities expand assumed cumulative rate allowance without supplying a dynamic response model. LSTM recourse retains real history and changes only the permitted final state; no candidate is copied into the past. Model-fit seeds are fixed. Repeated solver seeds do not constitute new engines or independent training repetitions.

### 4.2 Metrics and uncertainty

Validity is the fraction of all queries meeting the true calibrated safe threshold. Tier 2 plausibility is reported both over all queries and over returned counterfactuals, with both denominators shown. Returned means a nonzero action-feasible candidate regardless of its tier outcomes. T2_all = count(T2 passes)/count(all queries), using the Tier 2 check on every resulting state, including unchanged or action-infeasible diagnostics. T2_returned = count(returned and T2 passes)/count(returned). The all-query definition is independent of the returned-action gate; an empty returned denominator is undefined. Tier 3 and Tier 4 pass fractions are separate. Joint success is an additional stricter metric and is never substituted for the plausibility design target. Support size and model-score reduction are reported over all queries. Returned-only and successful-only support summaries remain separate diagnostics. Missing or failed queries are not silently dropped.

The five synopsis metrics comprise validity, action sparsity, Tier 2 plausibility, score reduction and conditional simulated trajectory health. The last is unmeasured. Every interval in the generated result tables resamples complete engines with all their cycles and solver observations. It is not a binomial interval over states. The appendix gives the engine count, observation count, conditional denominator, requested bootstrap draws and seed. Undefined conditional estimates remain undefined.

Latency budgets use the p95 upper endpoint rule: faster than the lower end of a design band passes. Warm serial backend measurements include all timed calls. Server-side dashboard construction excludes browser paint, network and end-to-end interaction. Independently measured stage percentiles cannot be added to manufacture a total percentile. Post-audit development profiling is a separate study with a different source and population; it does not replace the historical serial gate.

### 4.3 Reproducibility and reference search

Saved records retain effective runtime solver settings, config paths and hashes, source revision, query identities, model/validator hashes and execution segments. A frozen second-seed replay is compared against the historical seeds with exact discrete checks and the documented absolute/relative numerical tolerance. Reused public engines establish execution repeatability, not fresh generalization. The package reproduce workflow is a smaller installation check and is not substituted for the complete experiment.

A reference search can certify a failed production state as infeasible only if it is a verified superset that reproduces the production candidate. The saved finite reference cases remain unresolved finite searches. Failure to find a better action does not establish an infeasibility certificate or a feasibility ceiling.

## 5. Results

The following generated appendices report every headline model/protocol/population combination, not only a favorable XGBoost subset. They include confidence intervals, engine counts, conditional denominators, target gaps and exact provenance. Predictive/calibration and fidelity diagnostics are also generated from the saved study. No experiment is rerun by the publication build.

The results demonstrate why evidence tiers must remain separate. Model validity can be high while the operating-distribution and relationship checks fail. Conversely, a candidate can remain plausible without meeting the model target. The predictor and population affect these trade-offs. Calibration is not uniformly improved by fitting a calibrator, and a favorable discriminative metric does not by itself imply accessible safe recourse. LSTM history constraints further restrict what a snapshot change can achieve.

Sparsity is enforced structurally but does not establish small physical effort or useful hardware response. Measured risk reductions are changes in calibrated model scores. Coupling residuals and surrogate errors describe statistical fidelity under their data support, not first-principles thermodynamics. The complete study report retains the paired constraint ladder, K curves, ablations and baseline results so that a reduced headline table is not mistaken for the whole experiment.

Historical warm serial optimization misses the upper budget in both modes, and FAST backend total also misses its budget. The dashboard server-construction measurement covers a narrower scope than a browser interaction. New development profiling retained laptop-standby outliers and therefore cannot certify a steady-state speedup. These limitations are distinct from the scientific target misses.

## 6. Limitations and discussion

Static C-MAPSS data provide no ground truth for commanded interventions. The sensor-proxy mapping, bounds, rate limits and K are documented assumptions. No physical failure reduction, ongoing-production recovery, lifespan gain, avoided disposal, downtime saving or RUL extension is established. Evidence stops at E3. Optional simulation remains absent rather than being represented by an emulator with a stronger name.

Finite nonlinear search is incomplete. A failed query might reflect search limitations, model geometry, statistical support, coupling conflict or their combination. Even a successful model counterfactual can exploit model error. Independent validation rejects specified inconsistencies but does not guarantee that every surrogate artifact or unsupported physical state is detected. Prospective evaluation requires a validated response model and operational safety procedures.

The benchmark is publicly available and has been reused during development. Engine-disjoint fitting reduces leakage, but it cannot undo earlier test exposure. Solver seed repeatability does not quantify predictor-training uncertainty. Engine-bootstrap intervals capture variation within the registered sampled populations, not every operating domain. The separate D_max and K studies must be interpreted with their protocol labels.

SDG 9.1 and 9.4 provide motivation for reliability and resource efficiency. A contribution to those outcomes requires a field or lifecycle study with an operational baseline. A lower model score cannot establish either official target. The software is an installable research package, not certified industrial control or evidence of production deployment. This draft has not been submitted or peer reviewed.

## 7. Defense answers and future work

Does the recommended change reduce real-machine failure probability? Tier 1 establishes that the calibrated model target is met. A score can also decrease without reaching that target. Distribution, proxy engineering and coupling checks add evidence about the candidate but do not validate the causal response. Establishing physical benefit requires independently validated response data, simulator evidence or a prospective intervention study.

Can PrescriptXAI extend Remaining Useful Life by a specific number of cycles on C-MAPSS? No. Static run-to-failure data are non-interactive. This work establishes no dynamic RUL extension. Such a claim would require independently validated transition/simulator evidence or prospective intervention data, with an appropriate baseline and uncertainty assessment.

Why not simply alter any high-attribution sensor until the predictor changes? Immutable coordinates are excluded, control proxies obey configured envelopes, dependent observations are propagated and independently checked, and failures remain visible. These restrictions reduce specified forms of model exploitation without turning a statistical proxy into an actuator. The true-model rescore prevents accepting a surrogate-only flip.

Prioritized future work is real simulator integration with held-out response validation, extension to N-CMAPSS operating domains, first-principles coupling constraints, and richer actuator telemetry. A prospective preregistration should reserve genuinely untouched engines or an external dataset, quantify emulator uncertainty and define a deployment decision threshold independently of reported recourse outcomes. Runtime work should preserve the search and validation semantics and measure browser interaction separately from backend stages.

## 8. Conclusion

PrescriptXAI supplies a runnable and auditable integration of sparse recourse, explicit proxy constraints and separately measured evidence tiers. The completed benchmark supports reproducibility and exposes target gaps rather than establishing universal feasible recourse or physical maintenance benefit. A candidate that changes a prediction remains a model result until stronger intervention evidence is obtained.

## References

[1] A. Saxena, K. Goebel, D. Simon and N. Eklund. Damage Propagation Modeling for Aircraft Engine Prognostics. PHM, 2008. NASA NTRS 20090029214. https://ntrs.nasa.gov/citations/20090029214

[2] S. Wachter, B. Mittelstadt and C. Russell. Counterfactual Explanations without Opening the Black Box: Automated Decisions and the GDPR. Harvard Journal of Law & Technology, 2018. https://arxiv.org/abs/1711.00399

[3] B. Ustun, A. Spangher and Y. Liu. Actionable Recourse in Linear Classification. FAccT, 2019. DOI:10.1145/3287560.3287566. https://www.berkustun.com/papers/actionable-recourse/

[4] R. K. Mothilal, A. Sharma and C. Tan. Explaining Machine Learning Classifiers through Diverse Counterfactual Explanations. FAT*, 2020. DOI:10.1145/3351095.3372850. https://arxiv.org/abs/1905.07697

[5] A.-H. Karimi, B. Scholkopf and I. Valera. Algorithmic Recourse: from Counterfactual Explanations to Interventions. arXiv:2002.06278, 2020. https://arxiv.org/abs/2002.06278

[6] C. Guo, G. Pleiss, Y. Sun and K. Q. Weinberger. On Calibration of Modern Neural Networks. PMLR 70:1321-1330, 2017. https://proceedings.mlr.press/v70/guo17a.html

[7] O. Ledoit and M. Wolf. A well-conditioned estimator for large-dimensional covariance matrices. Journal of Multivariate Analysis 88(2):365-411, 2004. DOI:10.1016/S0047-259X(03)00096-4. https://ledoit.net/research.htm

[8] T. Chen and C. Guestrin. XGBoost: A Scalable Tree Boosting System. KDD, 2016. DOI:10.1145/2939672.2939785. https://arxiv.org/abs/1603.02754

[9] United Nations DESA. Sustainable Development Goal 9: Industry, Innovation and Infrastructure, targets 9.1 and 9.4. Accessed 30 October 2026. https://sdgs.un.org/goals/goal9
