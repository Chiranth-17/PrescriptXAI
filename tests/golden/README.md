# Fitted operator goldens

`operator-v1.json` is generated from the real seed-17 CPU MLP, train-only scaler and
covariance fit, and separate calibration engines in `fixtures/operator_artifacts.py`.
It is a synthetic software fixture, not a C-MAPSS performance result. Cases execute
RECOVERABLE, PARTIAL, ESCALATE and NO_INTERVENTION through the public library.

Discrete values, tier verdicts, keys and sequence lengths must match exactly. Numeric
fields use absolute tolerance `1e-6` plus relative tolerance `1e-5`, allowing float32
roundoff without moving the model/tier definitions. Two same-process runs and two
fresh interpreter runs must additionally match each other exactly on the same host.
Timing, run ID, config hash and model-content identity are excluded because they
describe the execution or temporary artifact paths, rather than scientific results.
All risks, states, deltas, margins, tiers, assumptions, failure diagnostics and
effective solver settings remain checked. No schema field is changed.

Normal tests never rewrite goldens. To intentionally revise one, first fit the
operator fixture into an explicitly trusted temporary directory, then run:

```powershell
$env:PYTHONPATH = 'tests'
uv run python -m fixtures.golden_operator --artifacts <trusted-directory> --golden tests/golden/operator-v1.json --update-golden
```

Review the golden diff alongside the behavior change and defect/regression log.
