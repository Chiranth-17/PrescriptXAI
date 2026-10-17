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
   per-step rate interval around the current state. The intersection is converted to scaled-change
   bounds and passed to L-BFGS-B. The configured scaled movement radius is an additional
   per-feature trust bound. The bounds penalty term is zero on feasible solver iterates; it remains
   explicit in the term report for correspondence with the synopsis.
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
   cases where simple pruning loses validity. If no sparse candidate passes the true-model target,
   the result reports failure and the lowest-risk bounded candidate found. When the starting state
   is outside an actuator range but the one-step rate box can reach it, the failure candidate first
   projects to the nearest point in the physical/rate intersection. If those intervals are empty,
   the result sets actuator_constraints_feasible=false and echoes the input only as a diagnostic;
   it is not an actionable counterfactual.

The candidate is accepted as model-valid only when the final calibrated predictor returns
\(f(x')\le\tau_{safe}\). Tiers 2–4 are a separate physical-plausibility pipeline and can still
reject a model-valid candidate.

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
folded into the model-validity rate. The Phase 4 FD001 200-state report was run with the search
limits recorded in its JSON/Markdown artifact because the full default search was computationally
impractical in this environment. Its measured true-model validity rate was zero; the lower search
budget does not change the definition of validity, and no target is treated as satisfied by a
surrogate prediction or a risk reduction alone.
