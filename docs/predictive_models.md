# Predictive models

## Inputs and labels

Training starts from the C-MAPSS run-to-failure training file. It derives each row's remaining
life from the final observed cycle and sets the failure target to one when remaining life is no
greater than configured `horizon_H`. The optional RUL cap affects reported RUL only; binary labels
use uncapped RUL. C-MAPSS's official truncated test file is not used as the internal holdout.

Whole engines are assigned to train, validation, and internal test partitions before feature
filtering or scaling. Variance filtering and the standard scaler fit on train-engine rows only.
Threshold selection and calibration fit on validation engines. The held-out test engines are
scored once for AUROC, AUPRC, F1 at `tau_danger`, Brier score, ECE, confusion matrix, high-risk
recall, reliability data, and optional surrogate fidelity.

## Predictors

- `xgb` is the CPU XGBoost snapshot classifier. Its positive-class weight is computed from the
  training labels, and validation engines provide early-stopping feedback.
- `mlp` is the differentiable snapshot model used by gradient-based recourse. It uses configured
  hidden widths, deterministic seeds, validation early stopping, gradient clipping, and optional
  CUDA execution.
- `lstm` consumes fixed-size cycle windows assembled separately within each engine. Short windows
  repeat the engine's first row on the left. During a recourse forward pass, callers perturb only
  the latest timestep and preserve the observed earlier timesteps.
- `xgb` also trains an MLP on XGBoost's training-engine probabilities. The validation and test
  reports compare calibrated surrogate and calibrated teacher probabilities using MAE, rank
  correlation, and decision agreement at `tau_safe` and `tau_danger`.

Calibration supports isotonic regression, monotone Platt sigmoid scaling, and temperature scaling.
The selected calibrator is fit on validation predictions only. Reports keep pre-calibration and
post-calibration Brier score, equal-width expected calibration error, and reliability-curve bins
separate. Model-risk thresholds are applied to calibrated probabilities.

## Training

```powershell
uv run prescriptxai train --subset FD001 --model xgb
uv run prescriptxai train --subset FD001 --model mlp
uv run prescriptxai train --subset FD001 --model lstm
```

Each run writes a versioned model bundle, training-engine-fitted Mahalanobis artifact, measured
metrics JSON, and held-out reliability PNG and HTML to the configured artifact directory. The
registry verifies artifact version and feature order when loading. Metrics are results of the
actual configured data, seed, model, and split; synopsis example values are not inserted into
reports.

The LSTM bundle requires a history window through `predict_risk_sequence`. The current snapshot
recommendation request does not carry that history and therefore cannot run LSTM recourse. This
interface limitation is reported instead of fabricating repeated history at inference time.
