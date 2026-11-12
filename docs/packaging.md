# Packaging and local operation

## Linux verification gap (13 November 2026 IST)

Linux now passes the clean-clone two-machine API/dashboard HTTP demo, with its
own genuine fits. Its subsequent scientific/software verify fails: 787 passed,
7 failed, 4 errors and combined coverage 85.39239084655343%, below unchanged
floors. All 15,525 fresh records are preserved, but parity failed and none were
admitted to cache. Complete saved-record diagnosis finds non-borderline Tier 2
and triage changes as well as platform-specific identity hashes. See the
[measured portability status](linux_portability.md) and `PROGRESS.md` for exact
scopes and evidence. Windows verification remains passed at its original source;
Linux complete verification, Phase 18 closure and release are not claimed.


## Phase 18 Linux design-pin repair (12 November 2026 IST)

The second Linux attempt, `linux-clean-edfcc31-v1`, passed its own locked
setup, all 107 asset provisions and quality-input checks, then exited 1 at
policy preflight at 20:20:22 IST. The baseline manifest separately pins the
original 4,113-byte CRLF design, while Git supplied its 4,034-byte LF version.
This design had not been in the provisioning inventory. No demo, cache access
or scientific solve started. The container, volume, original logs and failure
receipt remain preserved; the earlier Linux attempt is also unchanged.

A read-only inspection checked all 101 direct baseline/subset hash pins in the
retained Linux clone: only the design bytes differed. Every audited dependency
version matched. A separate read-only genuine-fixture diagnostic validated all
32,116 serialized cases/observations and the fixed 15,525 IDs in 26.37 seconds,
with zero fits, solves or cache access. It did not waive the failed raw-byte
preflight or count as a regression pass. Evidence is in
`artifacts/phase18/linux-design-repair-v1` and the second attempt's preservation.

The exact historical design bytes are now committed with a file-local no-text
conversion attribute. The design and independently approved Parquet fixture are
both mandatory in the packaging provisioning inventory (109 unique registered
assets). The checkout tests require those two bindings to equal the immutable
baseline manifest and export every tracked registered input under both Git
line-ending modes. Existing fixture, subset, design values, scientific hashes,
thresholds, tolerances and known differences are unchanged. Reviewed whole-file
public-digest pins were updated for the inventory and expanded test file; no new
secret exception was added. Linux own-clone demo/verify remain pending, and the
Windows pass retains its original source and evidence.


## Phase 18 Linux taxonomy-byte repair (12 November 2026 IST)

The first Linux own-clone sequence at `3762636` passed system setup, clone
and its own locked Python 3.13 environment, then exited 1 at asset provisioning
at 18:12:40 IST. No demo, cache access or scientific solve started. Its container,
volume and 45 pinned original host files remain preserved under
`artifacts/phase18/linux-clean-3762636-v1/failure-preservation.json`.

The registered feature taxonomy and packaged duplicate contain 8,959 historical
bytes with mixed line endings. Their Git blobs contained the 8,607-byte LF
normalization. Windows could restore the registered bytes under its Git filter;
Linux correctly rejected that canonical-blob comparison with its default
`core.autocrlf` unset. Inventory inspection found exactly these two tracked
registered inputs differed from their Git blobs; normalized content is identical.

Both files now preserve their exact registered bytes at checkout using file-local
Git attributes. The CR-at-EOL whitespace attribute recognizes their retained line
endings while other whitespace checks remain active. No YAML value, taxonomy
mapping, threshold, fixture, input hash or historical result changes. The new
actual-Git checkout tests export every tracked registered input under both
`core.autocrlf=true` and `false` and require the original SHA-256 bytes. Packaging,
workspace initialization and taxonomy tests pass; Linux verification is still
pending. The passed Windows source remains `e97fbdb`, with its original receipts.
No Phase 18 closure or release is claimed.


## Latest measured packaging verification (12 November 2026 IST)

The clean Windows v5 clone at `e97fbdb` passed `make verify REUSE_ONLY=0`:
796 tests, 68 warnings, one release-only full marker deselected, and all
15,525 fixed cases freshly recomputed with exact comparison (zero reused).
`make check` took 8,805.0479676 s and complete verification 9,009.8640601 s.
Coverage was 91.1674275598621% scoped / 91.23454511902565% package lines /
88.0527867471571% combined, above unchanged floors. Security, distribution build,
fresh installed-wheel smoke and strict docs passed. See the source-bound
receipts and `closeout-verification.json` in
`artifacts/phase18/windows-verify-e97fbdb-v1` and the detailed `PROGRESS.md`.
The earlier fresh demo and authenticated two-machine container smoke remain
scoped to `4bb89a6`, with image inspect size 974,593,999 bytes. Linux own-clone
demo and complete verify are still pending; Phase 18 is not closed.

The canonical version is `prescriptxai.__version__`. Hatch reads that source
for wheel and source distributions. Optional extras are `api`, `dashboard`,
`dev` and the retained `baselines`. The repository uses the committed uv lockfile.

## Local demo

From the checkout run `uv sync --all-groups --locked`, followed by
`mingw32-make demo` on Windows or `make demo` on Linux. The command prepares
an isolated workspace, downloads and verifies the NASA archive, runs the
registered FD001 reproduction and fits a separately labeled synthetic CSV
sample. Both are visible in one dashboard and the named API. This sample
illustrates adding a spec through the tabular adapter. It represents no real
second machine. See [adding a machine](adding_a_machine.md).

The first preparation can take 10–20 minutes after installation. Later starts
check saved files before using them. `DEMO_WORKSPACE=artifacts/my-demo`
selects a new destination. `DEMO_ARCHIVE=C:/trusted/CMAPSSData.zip` can supply
the exact registered archive locally. Its hash is checked against
`configs/experiments/phase18-packaging-v1.yaml` before use.
`DEMO_SMOKE=1` starts both services, scores an observation for each machine,
checks HTTP dashboard readiness, records the output and stops both listeners.
Browser rendering is verified separately from this HTTP smoke test.

Preparation refuses an existing incomplete workspace. Keep it and its logs
and use a new destination after diagnosing the failure. A completed workspace
records input, config, artifact and source provenance in `demo.json`.
Changed files prevent warm reuse. Demo observations and computation timings
provide no population efficacy estimate or controlled serial-latency result.

## Environment settings

| Variable | Meaning and default |
| --- | --- |
| `PSX_DEMO_API_PORT` | Local demo API port, 8000 |
| `PSX_DEMO_DASHBOARD_PORT` | Local demo dashboard port, 8501 |
| `PRESCRIPTXAI_API__HOST`, `PRESCRIPTXAI_API__PORT` | API bind address and port from typed config. `--local-demo` requires loopback. |
| `PRESCRIPTXAI_AUTH_ORIGIN` | Exact HTTPS origin for one authenticated listener |
| `PRESCRIPTXAI_OPERATOR_PASSWORD_HASH`, `PRESCRIPTXAI_ADMIN_PASSWORD_HASH` | Distinct salted verifiers generated by `prescriptxai hash-password` |
| `PRESCRIPTXAI_TLS_CERTFILE`, `PRESCRIPTXAI_TLS_KEYFILE` | Direct-listener certificate and private key, both required together |
| `PRESCRIPTXAI_ARTIFACT_MANIFEST` | Independently verified artifact digest trust anchor |
| `PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS` | Optional trusted artifact roots, as documented in artifact security |
| `PRESCRIPTXAI_API_TOKEN` | Optional short-lived dashboard token for a separate API |
| `PSX_WORKSPACE` | Compose bind source, `./artifacts/demo` |
| `PSX_TLS_DIR`, `PSX_MANIFEST` | Compose host certificate directory and independent manifest file |
| `PSX_API_ORIGIN`, `PSX_DASHBOARD_ORIGIN` | Public HTTPS origins for the two Compose listeners |
| `PSX_IMAGE` | Compose image tag, `prescriptxai:local` |
| `PSX_ENV_FILE` | Compose credentials and settings file, `.env` |

The typed config loader also supports `PRESCRIPTXAI_SECTION__FIELD`
overrides. Unknown config variables and invalid values fail startup. Keep
secrets in process environment or the ignored `.env`, outside scientific YAML.
The local demo runs its child services with its recorded config and explicit
loopback mode. Authenticated serving remains the default for the CLI.

## Authenticated Docker

`make image` builds the wheel and the shared API/dashboard image. Compose
uses the same image for both roles. Copy `.env.example` to ignored `.env`.
The builder constrains transitive runtime dependencies with
`runtime-requirements.txt`, exported from `uv.lock` for the API/dashboard
extras. A test checks that this export matches the lockfile. The explicit
CPU Torch wheel retains its actual local version in runtime provenance.
Supply distinct password verifiers, the exact origins, a certificate directory
containing `tls.crt` and `tls.key`, and an independently reviewed artifact
manifest. The certificate must cover `localhost` for the local HTTPS health
probe. Generate a certificate through your deployment's trusted procedure.
Do not use the demonstration config as approval for a plant.

Start with `docker compose up -d`, inspect `docker compose ps` and stop with
`docker compose down`. The image runs as UID/GID 10001. Give that account
read access to configs, data, models, TLS files and the manifest, and write
access to `artifacts/machines` for the scoped feedback log. That directory
also contains the sample fit. Its model hashes remain checked before decode.
Protect it with host permissions and keep the independent trust anchor outside it.

Compose uses a read-only root and read-only configs/data/artifacts mounts,
with a writable machine-log mount and temporary filesystem. It drops Linux
capabilities, prevents privilege escalation and restarts failed listeners.
Docker captures stdout with log rotation. The HTTPS health probe validates
the supplied certificate and accepts the authentication boundary's 401
response or a successful response. Functional scoring is checked separately.
The host ports bind to loopback in the shipped Compose file.

## Packaging verification

`make verify` runs `make check`, the security gate, builds both distributions,
installs the wheel in a temporary environment outside the checkout, exercises
its CLI and resources, and builds strict docs. Each stage records command,
native exit and wall time. The wheel smoke installs runtime and API/dashboard
dependencies into a fresh environment, constrained by the committed uv lockfile,
and checks that the package imports from that installation. Each subprocess
retains stdout, stderr and its native exit. The environment is retained for diagnosis.

The full regression is reserved for the release gate. `make verify` runs
the fixed 15,525-case subset with the existing exact-key policy. To verify
from a fresh clone, provision the required scientific fitted files, genuine
inputs and registered evidence referenced by the regression fixture manifest,
plus the quality input manifests. The Phase 18 verification inventory also
requires the genuine legacy validators and complete saved Phase 7 records,
summary and serial-latency evidence used by dashboard tests. These remain
outside Git, pinned in `configs/experiments/phase18-verification-inputs-v1.yaml`. The preflight
checks their hashes and missing assets fail. `make demo` instead prepares its
own demonstration fits and does not replace those scientific assets.

From the fresh clone, provision those bytes from a trusted workspace using
`uv run python scripts/packaging/provision.py --source C:/path/to/trusted-workspace`.
Use a Linux path on Linux. The source must have the same registered asset
inventory. Every file is checked against the committed hashes before copying.
Existing differing untracked files cause failure. A tracked file with normalized
checkout line endings can be restored only when its canonical Git blob equals
HEAD, and its original bytes are preserved. The resulting tree must stay clean.

Optionally append `--reuse-cache` to copy a local authenticated cache snapshot.
The gate still checks each original signature, full execution context and
scientific output and reports reused versus recomputed counts. A different
platform or numerical build requires fresh solves. Cache copying grants no
compatibility by itself. Both provisioning and verification preserve receipts.

## Current verification status

The clean Windows clone at `56ded65` passed the two-machine demo and HTTP
smoke in 335.22 seconds. It downloaded the pinned real archive and fitted its
own models. Its distribution build passed in 11.83 seconds. The first wheel
smoke failed because inherited system packages lacked XGBoost. A diagnostic
reproduced that cause. The corrected helper passed on the same wheel after
installing the locked runtime and API/dashboard dependencies in a fresh
environment, with imports, resources, provenance and CLI verified. Receipts
are under `artifacts/phase18/packaging-preflight-56ded65-v1` and
`artifacts/phase18/wheel-smoke-fixed-20261111-v1`.

At `8cc7ba7`, the main `make verify` passed in 782.08 seconds, including
786 tests and all 15,525 fixed cases reused with exact comparison. Both
coverage gates and security passed. The image built at 964,648,175 bytes.
Its authenticated Compose smoke passed FD001 scoring but failed loading the
Windows-created sample because version-1 path serialization produced a
different spec hash on Linux. The failed run is preserved in
`artifacts/phase18/container-smoke-20261112-v1`.

Machine-spec version 2 gives new relative-path specs a portable identity.
Version 1 keeps its original identity. The sample template now uses version 2,
with a separate new fit required. See [schema history](schema_changelog.md).
Nineteen local packaging and portability tests pass. Real scoring of the new
sample in the container, Linux demo and complete clean-clone Windows/Linux
verification remain pending. Phase 18 closure and release are pending.

The subsequent clean Windows clone at `9482823` stopped before demo or
regression because its software diagnostic lacked those five historical assets
and retained a test rejecting newly supported schema 2. The failed clone and
all outputs are preserved under `artifacts/phase18/windows-portable-9482823-v1`.
The exact archived inputs are now mandatory and the test uses unsupported
version 999. All eight previously failed/erroring tests pass in 43.80 seconds.
This focused pass does not establish clean-clone or scientific verification.

The `f481190` clone passed provisioning but one of 795 selected software tests
failed because Git converted the registered scenario-selection YAML from LF
to CRLF. Its exact original bytes are now required by the Phase 18 inventory
and preserved by a file-specific Git attribute. Scenario IDs and saved results
were unchanged. The failed clone and outputs remain preserved. No scientific
subset was started by either failed clean-clone diagnostic.

Recovery of the user-paused `4bb89a6` clone passed 795 software-only tests,
both coverage gates, the fresh two-machine demo and authenticated HTTPS scoring
inside the Linux image. The actual `make verify` then stopped at the subset
policy hash before cache access or solves. The immutable subset manifest binds
the original CRLF policy bytes, while its committed LF blob gave a different
clean-checkout hash. Those original CRLF bytes are now committed explicitly
and required by provisioning. The manifest, subset, values and tolerances are
unchanged. Preserve the recovery receipt and failed gate; complete Windows/Linux
verification and Phase 18 closure remain pending.
