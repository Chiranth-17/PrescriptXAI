# Mathematical formulation and units

Given a raw state \(x\), calibrated failure probability \(f\), and alert condition
\(f(x)\ge\tau_{danger}\), recourse searches for a sparse state \(x'=x+\Delta x\) whose
**true calibrated predictor** satisfies \(f(x')\le\tau_{safe}\). Thresholds and optimization
settings are loaded from YAML.

## Objective and constraints

The synopsis objective is

\[
\min_{x'}\; \|x-x'\|_1
 + \alpha L_{pred}(f(x'),y_{safe})
 + \beta\sum_{j\in I}|\Delta x_j|
 + \gamma P_{bounds}(x'),
\]

where \(I\) is the immutable feature set. PrescriptXAI minimizes over scaled actuator-proxy
changes \(\Delta z_A\), while it reports raw-unit changes:

\[
\min_{\Delta z_A}\;
 \lambda_1\|\Delta z_A\|_1
 + \alpha\max(0, f(x'(\Delta z_A))-\tau_{safe}+m)^q.
\]

Here \(m\) is the configured safety margin and \(q\in\{1,2\}\) selects hinge or squared
hinge. The default is squared hinge. The safety margin makes the optimization target stricter
than the final acceptance test; final model validity is always checked against the configured
\(\tau_{safe}\) without rounding.

The optimizer is SciPy L-BFGS-B with gradients from PyTorch autograd. The following implementation
choices address the nonsmooth and constrained parts of the synopsis formulation:

1. **L1 default and alternative.** The default l1_mode=smooth uses
   \(\sum_j(\sqrt{\Delta z_j^2+\epsilon^2}-\epsilon)\), whose gradient is finite at zero.
   l1_mode=split is the exact alternative: \(\Delta z=p-n\), \(p,n\ge0\), and the L1
   term is \(\sum_j(p_j+n_j)\). The tests compare both objective values and check the smooth
   gradient against centered finite differences. Both are valid L-BFGS-B parameterizations.
2. **Immutable features.** They are hard-frozen: no immutable coordinate is in the optimization
   vector, which is equivalent to lower and upper bounds both being zero change. beta is retained
   in logged objective terms but multiplies zero because no immutable variable exists.
3. **Physical and rate bounds.** Each control's raw physical interval is intersected with its
   per-step rate interval around the current state. The default rate mode is a configurable
   training-delta quantile: for each control, compute absolute adjacent-cycle changes within each
   training engine, then take the configured quantile (0.99 by default). It never differences the
   end of one engine against the start of another. The fitted raw-unit rate values are persisted in
   the model artifact. A configured absolute rate or fraction of the fitted range remains available
   as an alternative. The intersection is converted to scaled-change bounds and passed to
   L-BFGS-B. The configured scaled movement radius is an additional per-feature trust bound. The
   bounds penalty term is zero on feasible solver iterates; it remains explicit in the term report
   for correspondence with the synopsis.
4. **Dependent sensors.** They are not free variables. The Phase 3 differentiable coupling model
   propagates them from the proposed controls and fixed operating context before computing risk.
5. **Nondifferentiable XGBoost.** A trained differentiable surrogate is used to obtain gradients.
   After every optimization and support-restricted solve, the candidate is rescored with the actual
   calibrated predictor. Only this true predictor determines model_valid; surrogate validity is
   never accepted as a result.
6. **Alpha and sparsity.** Alpha is increased through the configured schedule until a dense
   candidate reaches the safe target or the schedule is exhausted. L1 weight is escalated through
   its configured schedule; candidates are then pruned to top-k scaled-change supports and those
   supports are re-optimized. A deterministic bounded search over the top-m candidates handles
   cases where simple pruning loses validity. The true-model grid fallback below expands the
   search if no physically valid sparse candidate is found. When the bounded searches cannot find
   a model-valid sparse action, the result reports failure and the lowest-risk bounded candidate
   found. When the starting state
   is outside an actuator range but the one-step rate box can reach it, the failure candidate first
   projects to the nearest point in the physical/rate intersection. If those intervals are empty,
   the result sets actuator_constraints_feasible=false and echoes the input only as a diagnostic;
   it is not an actionable counterfactual.

7. **True-model grid fallback.** When the gradient/support path finds no candidate that passes the
   configured physical checks, a deterministic grid enumerates one-, two-, and up-to-
   \(k_{max}\)-feature supports. Each changed control is sampled at the configured number of
   equally spaced points inside the same physical, per-step-rate, and scaled-trust intersection.
   The batched candidates are scored by the true calibrated predictor, and the least-cost
   candidate passing Tier 2–4 is preferred when one is found. Immutable coordinates never enter
   the grid; dependent sensors are recomputed with the fitted coupling estimators. The grid does
   not change the objective or the model-validity threshold, and it is not a proof of continuous
   or global optimality: a finite grid can miss a safe interval between sample points. Enablement
   and resolution are set by `recourse.true_model_grid_enabled` and
   `recourse.true_model_grid_points` in YAML.
8. **FAST versus THOROUGH grid search.** THOROUGH scores every bounded sparse-grid point in one
   batch and selects the minimum common objective among points that pass Tier 2–4, with an
   engineering-only fallback explicitly flagged if no Tier 2 point exists. FAST groups points by
   support, vector-scores each visited support, and orders supports by a lower bound on their L1
   cost. It can stop only after a Tier 2–4-valid point reaches the configured risk margin and the
   next unvisited support's L1 lower bound is greater than the best physical candidate's full
   objective. The prediction penalty is nonnegative, so that lower bound cannot hide a better
   finite-grid candidate. FAST and THOROUGH therefore have the same optimum on the configured
   finite grid when the bound is applied; this does not certify a continuous-space optimum. The
   evaluation also compares their returned true-model states and risks on the same saved queries.
9. **Intervention horizon sensitivity.** `rate_horizon_steps=K` multiplies the training-derived
   one-step rate limit by K around the current state, while retaining physical and scaled trust
   bounds. K greater than one assumes the movement can be spread over K steps. It is reported as a
   sensitivity assumption because static C-MAPSS data cannot validate actuator response or the
   chosen horizon.
10. **Historical `d_max=6.0` setting.** The expanded experimental profile used
    `recourse.max_scaled_distance=6.0`, a per-feature scaled-space movement trust radius. Its
    Mahalanobis plausibility threshold remained `D_max=5.0`. The two quantities have different
    units and roles and must not be conflated.

Train-derived rates describe observed telemetry movement and are proxy envelopes because C-MAPSS
has no actuator commands. They must not be presented as real actuator slew limits. The grid uses
the same bounds as the objective and does not relax those limits.

Tier 2–4 results are used to prefer a physically valid candidate when available, but remain
reported separately from Tier 1. A physically valid candidate is not accepted as model-valid
without the independent true-predictor score.

The candidate is accepted as model-valid only when the final calibrated predictor returns
\(f(x')\le\tau_{safe}\). Tier 2 is statistical plausibility; Tiers 3–4 are separate proxy
engineering/coupling constraints and can still reject a model-valid candidate.

The reported true-risk check is kept separate from optimizer feasibility. A diagnostic closest
candidate can happen to score below \(\tau_{safe}\) even when the sparse-support search failed or
the diagnostic action exceeds \(k_{max}\). In that case `model_valid` remains true for the
measured risk, `recourse_feasible` is false, and joint `success` is false. The legacy Phase 4 sparsity headline uses joint successes. Phase 7 reports all-query,
returned-candidate and joint-success support sizes separately, and its design-target/gap table
uses `sparsity_all`. The short reproduction additionally reports successful-query sparsity.
Failure diagnostics are counted separately.

## Unit mapping

- Input state, OptimizationResult.state, and DeltaMapping.raw_delta use raw feature units.
- DeltaMapping.scaled_delta is the change in the fitted train-only standardized coordinate:
  \(\Delta z_j=\Delta x_j/s_j\).
- Optimization distance and the per-feature movement trust bound use scaled units.
- Physical actuator bounds, direction restrictions, and rate limits use raw units.
- Ordinary coupling estimators receive and return raw units. The differentiable scaled wrapper
  unscales inputs, propagates in raw units, then rescales for the predictor.
- Tier 2 Mahalanobis distance uses standardized model features and covariance fitted on training
  engines only.

Counterfactual direction diagnostics compare signed control changes only for pairs of evaluated
states within the configured Euclidean radius in scaled feature space. They are descriptive
consistency measurements, not evidence of causal effect.

The high-risk evaluation reports all held-out alerts, counts alerts whose configured physical/rate
intervals are infeasible, and samples the requested recourse benchmark size from the remaining
actionable states. The excluded count is explicit in the JSON, Markdown, and CLI outputs; it is not
folded into the model-validity rate. The real FD001 Phase 4 benchmark and its exact search
configuration are saved in the generated JSON/Markdown artifacts. True model validity, physical
plausibility, recourse feasibility, risk reduction, and latency are reported separately; a
surrogate prediction or risk reduction alone never counts as a safe result.


## Phase 5 shared validation and search feedback

Tier 2 fits a Ledoit–Wolf covariance on declared fitting engines only, adds the fixed configured
diagonal floor, and stores its Cholesky factor L. Distance is `||solve_triangular(L, x-mu)||_2`;
no precision matrix or explicit inverse is formed, including inside the shrinkage estimator.
A separate factor is fitted for each training-derived operating regime. Original frozen settings
select the factor during scoring and optimization. Fixed, empirical-training-quantile and
`sqrt(chi2.ppf(q,d))` cutoffs have explicit recorded methods; only the fixed pre-registered v1/v2
cutoffs are used for Phase 5 reports. The reference-cycle filter is a separate config choice.

The search adds normalized squared positive excess for Tier 2 distance and Tier 4 learned
residual/YAML relation limits to the differentiable objective. Dependents still follow the
residual-preserving propagation equation; they never become free variables. The exact same
validator computes final acceptance. A nonlinear differentiable coupling approximation can
supply a search gradient, but the original regressors and true calibrated predictor decide the
final tiers. Bound/rate intersections and immutable coordinates remain hard constraints.

When no fully plausible candidate is found, at most the configured number of feedback
refinements increase the feasibility penalty on the existing sparse support. D_max and all
physical/rate bounds stay fixed. Exhaustion returns a structured diagnostic failure, even if
Tier 1 passes. Runtime metadata records the actual refinement count, effective settings and
per-stage timing. Collect-all mode exposes each tier independently; fail-fast mode marks every
unrun tier skipped, with no fabricated pass. Model validity, Tier 2 plausibility, Tiers 3–4
constraints and all-four joint are separate boolean verdicts.


Tier 3 domain checks apply cycle bounds as well as physical control bounds. Engine identifiers
are frozen nominal labels, not physical quantities; official-test namespaces must not be rejected
against an arbitrary identifier display range. This changes no actuator or cycle bound.

## Complete action-space formulation

Write raw telemetry as controls c, dependents d, and frozen context s. The learned coupling g is
fitted on training engines. It preserves the original residual rather than resetting d to a mean:

\[
d' = d + g(c',s)-g(c,s),\qquad s'=s,\qquad z_j=(x_j-\mu_j)/\sigma_j.
\]

For a fixed original operating regime r(s), an ideal feasible recourse problem is

\[
\begin{aligned}
\min_{\Delta z_A}\quad&\lambda_1\|\Delta z_A\|_1\\
\text{s.t.}\quad& f_{\mathrm{cal}}(x')\le\tau_{\mathrm{safe}},\quad
D_{M,r(s)}(z')\le D_{\max,r(s)},\\
&\ell_j\le c'_j\le u_j,\quad |c'_j-c_j|\le K v_j,\quad
|\Delta z_j|\le R,\quad\|\Delta z_A\|_0\le k_{\max},\\
&s'=s,\quad d'=d+g(c',s)-g(c,s),\quad h_q(x')\le0.
\end{aligned}
\]

Bounds intersect any configured directional restriction. R is a per-coordinate scaled trust
radius; v is a raw-unit one-step proxy rate. K, v and the control map are assumptions. The actual
finite search approximates this problem with the L1 and risk penalties above, plus normalized
squared positive Tier2/Tier4 excesses and bounded feedback. If a gradient surrogate is used,
replace f in the *search loss* only; final validity always uses f_cal. Neither L-BFGS-B nor the
finite sparse grid is a certificate of global feasibility/optimality. Gamma/beta synopsis terms
are zero where hard bounds/frozen coordinates already enforce their associated constraints.

## Mahalanobis distance and threshold methods

For regime r, training-only standardized reference rows determine mean m_r and shrinkage
covariance S_r. With fixed configured diagonal floor lambda and Cholesky factor L_r:

\[
\Sigma_r=\widehat\Sigma_{\mathrm{Ledoit-Wolf},r}+\lambda I=L_rL_r^T,
\qquad D_{M,r}(z)=\sqrt{(z-m_r)^T\Sigma_r^{-1}(z-m_r)}
=\|L_r^{-1}(z-m_r)\|_2.
\]

The implementation solves the triangular system; it does not explicitly invert covariance.
The original immutable operating settings select r throughout optimization and validation.
Available cutoff methods are

\[
D_{\max,r}=d_{\mathrm{fixed}},\qquad
D_{\max,r}=Q_q\{D_{M,r}(z_i):i\in\mathcal T_r\},\qquad
D_{\max,r}=\sqrt{F^{-1}_{\chi^2_p}(q)}.
\]

The empirical quantile uses the declared training reference, never evaluation states. The
chi-square cutoff assumes an appropriate multivariate distribution; it is not a universal
coverage guarantee. v1 uses fixed5 and v2 fixed8; sensitivity results state their own method,
reference distribution and quantile. The fixed thresholds are not fitted after seeing outcomes.

## Calibration and coupling residual checks

Let p be the uncalibrated predictor probability and a clipped logit
l=log(clip(p)/clip(1-p)). Sigmoid and temperature maps are

\[
f_{\mathrm{sigmoid}}(x)=\sigma(a l+b),\ a\ge0,\qquad
f_{\mathrm{temperature}}(x)=\sigma(l/T),\ T>0.
\]

Parameters minimize binary log loss on validation-engine predictions. Isotonic calibration
fits a monotone piecewise-linear map with clipped endpoints. Runtime logit clipping uses
10^-12; NumPy and differentiable paths share that rule and float64 calibration arithmetic.
Calibration is applied once. It does not change the label definition y=1[RUL<=H]. Training
RUL is final_cycle-current_cycle; official-test RUL adds the provided remaining-life offset.

For a dependent channel j, the Tier4 residual threshold is calibrated separately:

\[
e_{ij}=d_{ij}-g_j(c_i,s_i),\quad
b_j=k_\sigma\operatorname{std}_{i\in\mathcal V}(e_{ij}),\quad
|d'_j-g_j(c',s)|\le b_j.
\]

The configured validation reference filter is explicit. Residual mean, standard deviation,
R2 and share beyond threshold are reported; a large bias is not hidden by claiming that a
large sensor movement proves consistency. Propagation and its gradient approximation are
separate from exact residual/YAML checks used for final acceptance.

## Metric denominators, uncertainty and triage

For N declared queries, V_i=1[f_cal(x'_i)<=.20], P_i=1[D_M(x'_i)<=D_max], T3_i and T4_i are
independent tier flags; R_i indicates a returned nonzero feasible candidate, and A_i a feasible
bounded sparse action. The key rates are

\[
\mathrm{Validity}=\frac{\sum_i V_i}{N},\qquad
\mathrm{Plausibility}_{all}=\frac{\sum_i P_i}{N},\qquad
\mathrm{Plausibility}_{returned}=\frac{\sum_i P_iR_i}{\sum_iR_i},
\]
\[
\mathrm{Tier3}=\frac{\sum_i T3_i}{N},\quad
\mathrm{Tier4}=\frac{\sum_i T4_i}{N},\quad
\mathrm{Joint}=\frac{\sum_i V_iP_iT3_iT4_iA_i}{N}.
\]

An empty conditional denominator is unmeasured, not zero or100%. Failed queries remain in
all-query denominators. The legacy sample runner reports infeasible-interval pre-screen
exclusions explicitly; its sampled rates are not all-alert rates. The full Phase7 framework
retains all declared alert states. Risk drop is mean(f(x)-f(x')); success sparsity averages
proxy support only over joint successes, with all/returned support reported separately.

Bootstrap draws sample **whole engines with replacement**, carrying every state and solver
seed of each selected engine together. Ratios are recomputed from summed numerators and
denominators in each draw; report the engine count, observations, seed, replicate count and
zero-denominator draws. These intervals describe these sampled engines and fitted models,
not intervention uncertainty or a new predictor-training ensemble.

Below tau_danger: NO_INTERVENTION. At/above the gate, joint accepted action: RECOVERABLE.
A proxy/statistically acceptable feasible action with risk drop>=delta_min and final risk
**above** tau_safe: PARTIAL. Otherwise: ESCALATE with diagnostics. A low-risk but Tier2-failing
candidate can be E1/ESCALATE; PARTIAL cannot report risk<=.20. Stage latency passes when p95
is at or below the upper budget; a lower displayed band endpoint is never a minimum.
