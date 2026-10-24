"""Explicit trust boundary for retained local Python-object research artifacts.

Pickle/joblib can execute code. Only operator-controlled artifact roots are accepted; hashes
detect replacement and do not make an untrusted artifact safe. No request/upload grants trust.
"""

from __future__ import annotations

import hashlib
import io
import os
import pickle
from pathlib import Path

import joblib


class ArtifactLoadError(ValueError):
    """A trusted local artifact cannot be decoded or violates its declared identity."""


def trusted_artifact_bytes(path: Path, expected_sha256: str | None = None) -> bytes:
    """Read a regular file beneath a resolved operator-trusted root.

    The default root is ``artifacts/`` in the operator's working directory. Additional roots
    require the process environment ``PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS`` (os.pathsep list).
    Symlinks/junctions are resolved before the containment check. External models must be
    independently verified by their owner before their directory is explicitly trusted.
    """
    resolved = path.expanduser().resolve()
    roots = [Path("artifacts").resolve()]
    roots.extend(
        Path(value).expanduser().resolve()
        for value in os.environ.get("PRESCRIPTXAI_TRUSTED_ARTIFACT_ROOTS", "").split(os.pathsep)
        if value.strip()
    )
    if not any(resolved.is_relative_to(root) for root in roots):
        raise ArtifactLoadError("artifact path is outside operator-trusted artifact roots")
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    if not resolved.is_file():
        raise ArtifactLoadError("artifact path must be a regular file")
    data = resolved.read_bytes()
    if expected_sha256 is not None and hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ArtifactLoadError("artifact changed after fingerprinting; reload the complete bundle")
    return data


def load_trusted_joblib(path: Path, expected_sha256: str | None = None) -> object:
    """Decode only verified bytes from a trusted local joblib artifact."""
    data = trusted_artifact_bytes(path, expected_sha256)
    try:
        loaded: object = joblib.load(io.BytesIO(data))
        return loaded
    except Exception as error:
        raise ArtifactLoadError(
            f"cannot decode trusted artifact {path.name}: {type(error).__name__}"
        ) from error


def load_trusted_pickle(path: Path) -> object:
    """Decode a legacy preprocessor only inside the same explicit trust boundary."""
    data = trusted_artifact_bytes(path)
    try:
        loaded: object = pickle.loads(data)
        return loaded
    except Exception as error:
        raise ArtifactLoadError(
            f"cannot decode trusted artifact {path.name}: {type(error).__name__}"
        ) from error
