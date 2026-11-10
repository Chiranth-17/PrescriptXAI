# Trusted local artifacts

The historical research bundles use Python pickle/joblib for fitted sklearn, PyTorch, scaler,
coupling and covariance objects. These formats can execute arbitrary code while loading.
A hash detects replacement; it does not establish that an artifact is safe or authentic.
The current work preserves these historical files and does not silently rewrite measurements.

All readers use `prescriptxai.artifacts`. By default, only the resolved `artifacts/` directory
under the operator's working directory is trusted. For an independently verified external
artifact directory, the operator must explicitly configure the process environment:

```powershell
$env:PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS = 'C:/verified/prescriptxai-artifacts'
```

On Windows separate additional roots with `;`; on Unix use `:`. The application resolves
symlinks/junctions before checking containment, requires regular files and validates the
decoded object and scientific metadata. The facade also checks the bytes actually loaded
against its model/validator/coupling fingerprints. Decode failures are typed and production
facades require fitted calibration; there is no uncalibrated-production fallback.

The same boundary covers archival diagnostic checkpoint readers. A source-tree regression
forbids direct pickle/joblib decoding elsewhere. The current review-bundle command only copies
saved JSON/Markdown/CSV/HTML bytes and writes hashes; it does not load models, fit anything or
recompute a result. Raw query databases remain at their original location and are explicitly
referenced rather than silently described as included.

Only administrators may populate these directories. Do not approve Downloads, upload folders,
shared writable folders or a broad home/filesystem root. Never place untrusted downloaded
models inside a trusted directory. The API accepts telemetry/context/control data, not artifact
paths or serialized Python objects. The dashboard telemetry upload is JSON data and grants no
artifact trust. Tests explicitly trust only their own managed temporary outputs; child-process
tests inherit that scoped environment.

This restriction is an operator trust boundary, not a pickle sandbox or a claim that malicious
code becomes safe. JSON metadata, NPZ numerical arrays, native XGBoost and safe tensor formats
are preferred for future exchange formats. Migrating a historical fitted bundle requires
separate versioning and output-parity verification; retained pickle exceptions and their
administrative requirement remain explicit here. Keep credentials in the process environment,
never in scientific YAML or recommendation exports.

## Authenticated serving

The API and dashboard CLI commands require HTTPS authentication by default.
Provision separate long passwords for the operator and administrator. Run
`prescriptxai hash-password` once for each account and put its output in the
appropriate environment variable. The command prompts without echoing the
password. Verifiers use PBKDF2-HMAC-SHA256 with 600,000 iterations and distinct
random salts. See [OWASP password storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

| Environment variable | Purpose |
| --- | --- |
| `PRESCRIPTXAI_AUTH_ORIGIN` | Exact HTTPS origin, including any non-default port, for this listener |
| `PRESCRIPTXAI_OPERATOR_PASSWORD_HASH` | Salted verifier for the `operator` account |
| `PRESCRIPTXAI_ADMIN_PASSWORD_HASH` | Salted verifier for the `admin` account |
| `PRESCRIPTXAI_TLS_CERTFILE` and `PRESCRIPTXAI_TLS_KEYFILE` | Certificate and key for direct HTTPS. Set both when terminating TLS in the service. |
| `PRESCRIPTXAI_ARTIFACT_MANIFEST` | Administrator-controlled JSON file containing independently established model checksums |
| `PRESCRIPTXAI_API_TOKEN` | Optional short-lived bearer token when the dashboard calls a separate HTTPS API |

Use a single worker per listener. Authentication sessions expire after five
minutes of request inactivity or fifteen minutes total. Restarting the
process discards all sessions. Login is limited to six attempts per client
and 64 total in a rolling minute. Cookie-authenticated API writes require the
configured Origin and `X-CSRF-Token` from login. The dashboard checks the
WebSocket origin and session and retains Streamlit's native HTTP XSRF
protection. Browser logout is at `/auth/session`. Cookies are Secure,
HttpOnly and SameSite=Strict.
[OWASP session management guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

For API automation, POST a JSON object with `username` and `password` to
`/auth/login` using the configured Origin header. Keep the returned
`access_token` in memory and pass it as an Authorization bearer token. The
operator can read views and record feedback. The administrator can also inspect
the account inventory at `/auth/admin`. Account rotation and model deployment
are host administration operations. The network service has no upload or
account-edit endpoint. Run behind a controlled TLS ingress if the certificate
is provisioned at the proxy. Forward scheme and client address only from
trusted proxy peers and preserve the public Host header.

The manifest has `schema_version: 1` and a `files` object mapping
workspace-relative or absolute fitted-artifact paths to lowercase SHA-256
digests. Establish those hashes from an independently verified model bundle.
Store the manifest under an administrator-controlled path separate from writable
model storage. During loads, serialized files absent from the manifest or
different from their registered bytes are refused before decoding. Rotate the
manifest and model bundle together, then restart the listener.

For local research and usability sessions, the `--local-demo` flag on
`prescriptxai dashboard` or `prescriptxai serve` explicitly selects loopback-only
operation. Use the recorded demonstration limits and keep the session on the
operator's device.

## Dependency audit checkpoint

The installed environment was audited with pip-audit2.10.1 using its public PyPI advisory
source. The initial scan found51advisories affecting6distributions. The patched lockfile
upgrades Pillow to13.0.0 and Streamlit to1.66.1 (whose Pillow requirement supports13), plus
patched certifi, filelock, opentelemetry-api, setuptools and virtualenv. Package metadata was
verified against the official PyPI JSON API; scanner documentation is the
[PyPA pip-audit project](https://github.com/pypa/pip-audit).

The second scan found0known advisories among109audited distributions. The local project itself
(prescriptxai0.1.0) is the sole exclusion because it is unavailable on public PyPI; its source
is tested and audited separately. This is a dated advisory-database snapshot, not proof of
absence of unknown vulnerabilities. Raw before/after JSON, logs and status files remain in
artifacts/phase9/dependency-audit*. Historical experiment dependency fingerprints are retained.

```powershell
uv run pip-audit --path .venv/Lib/site-packages --format json --output artifacts/phase9/dependency-audit-after.json
```

Use the corresponding site-packages path on other platforms. Scientific results from the old
measurement source must not be relabeled as measurements of the patched environment.
