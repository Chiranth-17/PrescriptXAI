# Add a machine

Create `configs/machines/<machine_id>/machine.yaml` from the example in
`templates/new_machine`. The directory name and the machine ID must match.
Provision the telemetry locally. Keep the source data and fitted files outside Git.
Use `synthetic: true` for synthetic or simulated data and identify the source in the spec.

The local tabular adapter maps CSV or Parquet columns to a canonical table with
`unit_id`, `time_index`, and the declared measurement names. Each unit/time
pair must be unique. The time index and failure horizon use the same units.
Map uncapped remaining life, map an event flag with one terminal failure per
unit, or explicitly declare complete run-to-failure trajectories. A terminal
event policy rejects censored units. It never assumes their final observation
was a failure.

An engineer must decide which settings can change, the raw-unit operating
bounds and step limits, what counts as failure, the prediction horizon, and
which sensor relationships constrain a candidate. Record the name, role and
date only after confirmation. An empty block permits risk alerts and withholds
prescriptions and applied-control previews. The FD001 spec is unconfirmed.
Its controls and fitted limits describe benchmark proxies.

Use positive disjoint split fractions. The adapter splits entire units and
audits the partition. The runtime fits the scaler, predictor and covariance on
training units, fits the probability calibration on validation units, and
evaluates on the held-out partition. It records the machine ID and spec hash.
Keep protocol versions separate. The named runtime loads fitted files only for
the selected spec and protocol, from a trusted local artifact root.

```console
prescriptxai --machine my_machine data prepare
prescriptxai --machine my_machine --protocol v1 train --model xgb
prescriptxai --machine my_machine check observed.json
prescriptxai --machine my_machine assess observed.json
prescriptxai --machine my_machine recommend observed.json --mode fast
```

An observed JSON window is a chronological array of canonical rows with the
declared feature fields and `time_index`. A single JSON object is accepted
for snapshot scoring. Sequence models require their saved history length.
If any row includes `unit_id`, all rows in the window must refer to the same
unit. A quality failure reports its reason and field before prediction or
search. Training-derived intervals are action bounds. Declared raw-unit
intervals also serve as quality checks.

The HTTP service lists specs with `GET /machines` and accepts named window
requests under `/machines/{id}/assess`, `/recommend`, `/validate-controls`
and `/feedback`. Each request includes `rows` and may include
`protocol_version` and `mode`. The version 3 decision carries machine identity,
spec hash, protocol and the synthetic label. Feedback re-scores applied
controls, records per-action adherence and writes an advisory SQLite row.
The compatibility CLI commands and unprefixed v2 HTTP routes remain available
to reproduce historical benchmark results.

The Phase 13 contract constructs a toy spec and a synthetic CSV in its test
directory. It fits and scores with the shared numerical runtime and runs
actual bounded FAST and THOROUGH searches offline. Its public named routes
withhold recommendations without an engineer confirmation.
