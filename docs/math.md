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
\(f(x')\le\tau_{safe}\). Tiers 2–4 are a separate physical-plausibility pipeline and can still
reject a model-valid candidate.

The reported true-risk check is kept separate from optimizer feasibility. A diagnostic closest
candidate can happen to score below \(\tau_{safe}\) even when the sparse-support search failed or
the diagnostic action exceeds \(k_{max}\). In that case `model_valid` remains true for the
measured risk, `recourse_feasible` is false, and joint `success` is false. The sparsity target is
computed only over joint successes; failure diagnostics are counted separately.

## Unit mapping

- Input state, OptimizationResult.state, and DeltaMapping.raw_delta use raw feature units.
- DeltaMapping.scaled_delta is the change in the fitted train-only standardized coordinate:
  \(\Delta z_j=\Delta x_j/s_j\).
- Optimization distance and the per-feature movement trust bound use scaled units.
- Physical actuator bounds, direction restrictions, and rate limits use raw units.
- The coupling model receives scaled features and writes its propagated dependent outputs in the
  same scaled feature space used by the predictor.
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
