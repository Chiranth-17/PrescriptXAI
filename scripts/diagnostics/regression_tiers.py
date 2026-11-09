"""Exact-key regression evidence reuse, explicit fresh misses and immutable execution segments."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import inspect
import json
import logging
import math
import os
import secrets
import sqlite3
import subprocess
import time
from collections import Counter, defaultdict
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

import yaml
from filelock import FileLock
from scripts.diagnostics.phase12_baseline import (
    atomic_json,
    differences,
    idle_sleep_guard,
    portable,
    run_cases,
    validate_record,
)
from scripts.diagnostics.phase12_regression import (
    FIXTURE,
    MANIFEST,
    comparison_record,
    native_margins,
    preflight,
    verify_files,
    verify_unchanged,
)

import prescriptxai
from prescriptxai.evaluation.experiments import QueryCase, file_hash

CONFIG = Path("configs/experiments/phase12-test-tiers-v1.yaml")
SUBSET = Path("tests/regression/subset_ids.json")
SUBSET_MANIFEST = SUBSET.with_name("subset_manifest.json")
KNOWN = Path("tests/regression/known_diffs.json")
CACHE = Path("artifacts/regression-cache/records.sqlite3")
ORIGIN = Path("configs/experiments/phase12-test-cache-origin-v1.json")


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def runtime_build() -> dict:
    """Fingerprint installed numerical binaries/builds; paths are relative to each environment."""
    import hashlib
    import importlib.metadata
    import platform
    from pathlib import Path

    import numpy as np
    import torch
    from threadpoolctl import threadpool_info

    # Load the same numerical backends in both isolated environments before inspecting pools.
    __import__("scipy.linalg")
    __import__("sklearn")
    __import__("xgboost")
    packages, binaries = {}, {}
    numerical = {"numpy", "scipy", "scikit-learn", "torch", "xgboost"}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata["Name"].lower().replace("_", "-")
        if name == "prescriptxai":
            continue
        if name in packages:
            raise ValueError(f"Duplicate installed dependency: {name}")
        packages[name] = distribution.version
        if name in numerical:
            for item in distribution.files or ():
                if item.suffix.lower() in {".dll", ".pyd", ".so", ".dylib"}:
                    path = Path(distribution.locate_file(item))
                    with path.open("rb") as stream:
                        binaries[f"{name}/{item.as_posix()}"] = hashlib.file_digest(
                            stream, "sha256"
                        ).hexdigest()
    if not binaries:
        raise ValueError("Numerical build fingerprints unavailable")
    pools = [
        {key: value for key, value in pool.items() if key not in {"filepath", "num_threads"}}
        for pool in threadpool_info()
    ]
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "packages": dict(sorted(packages.items())),
        "native_binaries": dict(sorted(binaries.items())),
        "torch_build": torch.__config__.show(),
        "numpy_build": np.__config__.CONFIG,
        "numeric_pools": sorted(pools, key=lambda value: str(sorted(value.items()))),
        "execution_policy": {"workers": 4, "cpu_threads": 1, "device": "cpu"},
    }


def execution_context(manifest: dict, build: dict) -> dict:
    return {
        "schema_version": 1,
        "code_hashes": manifest["code_hashes"],
        "input_hashes": manifest["reference"]["input_hashes"],
        "design_sha256": manifest["reference"]["design_sha256"],
        "runtime_build": build,
    }


def checked_preflight() -> tuple[dict, dict, dict]:
    if not MANIFEST.is_file():
        raise FileNotFoundError(f"Required audited regression manifest missing: {MANIFEST}")
    root = Path.cwd().resolve()
    if Path(prescriptxai.__file__).resolve() != root / "src/prescriptxai/__init__.py":
        raise ValueError("The installed package must resolve to the current checkout")
    for function, name in ((preflight, "phase12_regression"), (run_cases, "phase12_baseline")):
        if Path(inspect.getfile(function)).resolve() != root / f"scripts/diagnostics/{name}.py":
            raise ValueError(f"The loaded {name} helper is outside the current checkout")
    return preflight()


def case_key(context: dict, case_id: str, case_json: str) -> str:
    return keyed_case(digest(context), case_id, case_json)


def keyed_case(context_sha: str, case_id: str, case_json: str) -> str:
    return digest(
        {"context": context_sha, "case_id": case_id, "case": portable(json.loads(case_json))}
    )


def pointer(value: object, path: str) -> object:
    for part in path.removeprefix("/").split("/"):
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise ValueError(f"Known difference is not a leaf field: {path}")
    return value


def known_policy(document: dict, expected: dict[str, str]) -> dict[tuple[str, str], dict]:
    if (
        document.get("schema_version") != 1
        or document.get("absolute_tolerance") != 1e-6
        or document.get("relative_tolerance") != 0
    ):
        raise ValueError("Known-difference policy changed its registered numeric envelope")
    policy = {}
    for entry in document["entries"]:
        key = entry["case_id"], entry["field"]
        if key in policy or key[0] not in expected or not entry.get("reason", "").strip():
            raise ValueError("Duplicate, unknown or unexplained known difference")
        reference = pointer(comparison_record(json.loads(expected[key[0]])), key[1])
        if isinstance(reference, (dict, list)) or differences(
            reference, entry["saved_value"], atol=0
        ):
            raise ValueError("Known difference does not bind the exact saved scalar")
        if ("accepted_value" in entry) == ("accepted_range" in entry):
            raise ValueError("Known difference requires exactly one acceptance rule")
        if "accepted_range" in entry:
            low, high = entry["accepted_range"]
            if (
                not isinstance(reference, float)
                or any(
                    isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                    for v in (low, high)
                )
                or low > high
            ):
                raise ValueError("Invalid known numerical range")
        policy[key] = entry
    return policy


def compare(
    case_id: str, expected: dict, actual: dict, policy: dict
) -> tuple[list[str], list[str]]:
    reference, measured = comparison_record(expected), comparison_record(actual)
    changed = differences(reference, measured, atol=0)
    used = []
    for path in changed:
        entry = policy.get((case_id, path))
        if entry is None:
            raise ValueError(f"Unlisted regression difference: {case_id}{path}")
        value = pointer(measured, path)
        if "accepted_value" in entry:
            accepted = not differences(entry["accepted_value"], value, atol=0)
        else:
            low, high = entry["accepted_range"]
            accepted = isinstance(value, float) and math.isfinite(value) and low <= value <= high
        if not accepted:
            raise ValueError(f"Known regression difference exceeded acceptance: {case_id}{path}")
        used.append(path)
    if {path for key, path in policy if key == case_id} != set(used):
        raise ValueError(f"Stale known difference: {case_id}")
    return used, changed


class EvidenceCache:
    """Append-only local cache; a separate local authentication key detects coherent row edits."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        auth = path.with_suffix(".key")
        if not auth.exists():
            if path.exists():
                raise ValueError("Cache authentication key missing; preserve the cache")
            descriptor = os.open(auth, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(secrets.token_bytes(32))
        self.auth = auth.read_bytes()
        self.checked_origins = {}
        if len(self.auth) != 32:
            raise ValueError("Cache authentication key is invalid")
        self.connection = sqlite3.connect(path, isolation_level=None)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS origins (id TEXT PRIMARY KEY, payload TEXT, signature TEXT)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS entries (key TEXT PRIMARY KEY, case_id TEXT, payload TEXT, "
            "payload_sha TEXT, case_sha TEXT, origin TEXT, signature TEXT)"
        )
        self.connection.commit()

    @contextmanager
    def transaction(self):
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            yield

    def sign(self, value: object) -> str:
        return hmac.new(self.auth, digest(value).encode(), hashlib.sha256).hexdigest()

    def add_origin(self, value: dict) -> str:
        key = digest(value)
        payload = json.dumps(value, sort_keys=True, allow_nan=False)
        signature = self.sign(value)
        previous = self.connection.execute(
            "SELECT payload,signature FROM origins WHERE id=?", (key,)
        ).fetchone()
        if previous and (previous[0] != payload or not hmac.compare_digest(previous[1], signature)):
            raise ValueError("Existing origin integrity failure")
        self.connection.execute(
            "INSERT OR IGNORE INTO origins VALUES (?,?,?)", (key, payload, signature)
        )
        return key

    def get(self, key: str, case_id: str, case_json: str, context: dict) -> tuple[dict, str] | None:
        row = self.connection.execute(
            "SELECT case_id,payload,payload_sha,case_sha,origin,signature FROM entries WHERE key=?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        found_id, payload, payload_sha, case_sha, origin, signature = row
        descriptor = [key, found_id, payload_sha, case_sha, origin]
        if (
            found_id != case_id
            or case_sha != digest(portable(json.loads(case_json)))
            or hashlib.sha256(payload.encode()).hexdigest() != payload_sha
            or not hmac.compare_digest(self.sign(descriptor), signature)
        ):
            raise ValueError("Cache record integrity/provenance failure; preserve and investigate")
        source = self.connection.execute(
            "SELECT payload,signature FROM origins WHERE id=?", (origin,)
        ).fetchone()
        if source is None:
            raise ValueError("Cache admission origin missing")
        checked = self.checked_origins.get(origin)
        if checked is None or checked[0] != source or checked[1] is not context:
            source_value = json.loads(source[0])
            if (
                digest(source_value) != origin
                or source_value["context"] != context
                or not hmac.compare_digest(self.sign(source_value), source[1])
            ):
                raise ValueError("Cache origin integrity/context failure")
            self.checked_origins[origin] = (source, context)
        case = QueryCase.model_validate(portable(json.loads(case_json)))
        value = validate_record(case, case_id, payload).model_dump(mode="json")
        return value, origin

    def put(
        self,
        case_id: str,
        case_json: str,
        payload: str,
        context: dict,
        origin: str,
        *,
        context_sha: str | None = None,
    ) -> None:
        key = keyed_case(context_sha or digest(context), case_id, case_json)
        old = self.get(key, case_id, case_json, context)
        if old is not None:
            if differences(
                comparison_record(old[0]), comparison_record(json.loads(payload)), atol=0
            ):
                raise ValueError("An existing exact-key scientific result cannot be replaced")
            return
        payload_sha = hashlib.sha256(payload.encode()).hexdigest()
        case_sha = digest(portable(json.loads(case_json)))
        descriptor = [key, case_id, payload_sha, case_sha, origin]
        self.connection.execute(
            "INSERT INTO entries VALUES (?,?,?,?,?,?,?)",
            (key, case_id, payload, payload_sha, case_sha, origin, self.sign(descriptor)),
        )

    def close(self) -> None:
        self.connection.close()


def select_ids(cases: dict, expected: dict, config: dict) -> tuple[list[str], dict]:
    rules = config["selection"]
    diagnostic_path = Path(rules["mandatory_diagnostic_ids"])
    if SUBSET_MANIFEST.is_file():
        frozen = json.loads(SUBSET_MANIFEST.read_text(encoding="utf-8"))["selection"]
        diagnostic = set(frozen["mandatory_diagnostic_ids"])
        diagnostic_sha = frozen["diagnostic_source_sha256"]
    else:
        diagnostic = {
            row["case_id"]
            for row in json.loads(diagnostic_path.read_text(encoding="utf-8"))["mismatches"]
        }
        diagnostic_sha = file_hash(diagnostic_path)
    if len(diagnostic) != rules["mandatory_count"] or not diagnostic <= cases.keys():
        raise ValueError("Mandatory historical diagnostic population differs")
    borderline, strata = set(), defaultdict(list)
    for key, encoded in expected.items():
        record = json.loads(encoded)
        case = json.loads(cases[key])
        if any(
            abs(margin) <= config["borderline_absolute_margin"]
            for _, margin, _, _ in native_margins(
                record, delta_min=case["config"]["pipeline"]["delta_min"]
            )
        ):
            borderline.add(key)
        band = sum(record["risk_before"] >= edge for edge in rules["risk_band_edges"])
        stratum = "/".join(
            str(v) for v in (record["mode"], record["population"], record["status"], band)
        )
        strata[stratum].append(key)
    sampled = set()
    counts = {}
    for name, values in sorted(strata.items()):
        selected = sorted(values, key=lambda key: digest([rules["seed"], name, key]))[
            : rules["per_stratum"]
        ]
        sampled.update(selected)
        counts[name] = {"population": len(values), "selected": selected}
    ids = sorted(diagnostic | borderline | sampled)
    return ids, {
        "mandatory_diagnostic_count": len(diagnostic),
        "mandatory_diagnostic_ids_sha256": digest(sorted(diagnostic)),
        "diagnostic_source_sha256": diagnostic_sha,
        "mandatory_diagnostic_ids": sorted(diagnostic),
        "borderline_count": len(borderline),
        "borderline_ids_sha256": digest(sorted(borderline)),
        "strata": counts,
    }


def read_policy(cases: dict, expected: dict, tier: str) -> tuple[list[str], dict, dict]:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    policy = known_policy(json.loads(KNOWN.read_text(encoding="utf-8")), expected)
    generated, selection = select_ids(cases, expected, config)
    registered = json.loads(SUBSET.read_text(encoding="utf-8"))
    manifest = json.loads(SUBSET_MANIFEST.read_text(encoding="utf-8"))
    if (
        registered != generated
        or len(set(registered)) != len(registered)
        or manifest["subset_sha256"] != file_hash(SUBSET)
        or manifest["config_sha256"] != file_hash(CONFIG)
        or manifest["fixture_sha256"] != file_hash(FIXTURE)
        or manifest["selection"] != selection
    ):
        raise ValueError("Fixed subset or its mandatory coverage/provenance changed")
    hashes = {path.as_posix(): file_hash(path) for path in (CONFIG, KNOWN, SUBSET, SUBSET_MANIFEST)}
    return sorted(cases) if tier == "full" else registered, policy, hashes


def require_closed_database(path: Path) -> None:
    wal = path.with_name(path.name + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise ValueError(f"Database has pending WAL data: {path}")


def database_rows(path: Path):
    require_closed_database(path)
    with closing(
        sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as connection:
        yield from connection.execute(
            "SELECT c.case_id,c.payload,r.payload FROM cases c JOIN records r USING(case_id) ORDER BY c.case_id"
        )


def verify_resume(previous: dict, current: dict) -> None:
    """Require the execution and comparison policy before admitting a preserved partial."""
    if any(previous[key] != current[key] for key in ("context", "tier", "ids", "policy_hashes")):
        raise ValueError("Resume source/config/data/runtime/selection/policy key differs")


def checkpoint_evidence(output: Path, descriptor: dict) -> tuple[dict, set[str]]:
    """Bind a closed execution segment to the actual prior cache misses and preserved rows."""
    replay = output / "recomputed"
    paths = [
        output / "manifest.json",
        output / "cache-accounting.json",
        replay / "manifest.json",
        replay / "segments.json",
        replay / "records.sqlite3",
    ]
    before = json.loads(paths[1].read_text(encoding="utf-8"))
    inner = json.loads(paths[2].read_text(encoding="utf-8"))
    segments = json.loads(paths[3].read_text(encoding="utf-8"))
    requested = set(before["missing_ids"])
    if (
        not requested
        or not requested <= set(descriptor["ids"])
        or len(requested) != before["pending_recompute"]
        or inner["requested_ids"] != sorted(requested)
        or inner["source"] != descriptor["source"]
        or inner["tier_context"] != descriptor["context"]
        or inner["code_hashes"] != descriptor["context"]["code_hashes"]
        or inner["reference"]["input_hashes"] != descriptor["context"]["input_hashes"]
        or inner["reference"]["design_sha256"] != descriptor["context"]["design_sha256"]
        or inner["policy_hashes"] != descriptor["policy_hashes"]
    ):
        raise ValueError("Checkpoint execution manifest differs from prior misses and context")
    if (
        len(segments) != 1
        or not segments[0].get("ended_utc")
        or segments[0]["completed_before"] != 0
    ):
        raise ValueError("Checkpoint requires one closed execution segment")
    database = paths[-1]
    require_closed_database(database)
    with closing(
        sqlite3.connect(database.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as conn:
        cases = {row[0] for row in conn.execute("SELECT case_id FROM cases")}
        records = {row[0] for row in conn.execute("SELECT case_id FROM records")}
    segment = segments[0]
    if not records <= cases <= requested or (
        segment.get("actual_success") is True
        and (
            records != requested
            or segment["completed_after"] != len(records)
            or segment["new_records"] != len(records)
        )
    ):
        raise ValueError("Checkpoint rows differ from its registered cases or segment counts")
    return {
        "file_hashes": {path.relative_to(output).as_posix(): file_hash(path) for path in paths},
        "records": len(records),
        "registered_cases": len(cases),
    }, requested


def import_rows(
    cache: EvidenceCache,
    rows,
    cases: dict,
    expected: dict,
    context: dict,
    admission: dict,
    policy: dict,
    *,
    complete: bool,
) -> int:
    origin, seen = cache.add_origin(admission), set()
    context_sha = digest(context)
    for key, case_json, payload in rows:
        if (
            key in seen
            or key not in cases
            or portable(json.loads(case_json)) != portable(json.loads(cases[key]))
        ):
            raise ValueError("Foreign, duplicate or changed origin case")
        case = QueryCase.model_validate(portable(json.loads(case_json)))
        record = validate_record(case, key, payload).model_dump(mode="json")
        compare(key, json.loads(expected[key]), record, policy)
        cache.put(key, cases[key], payload, context, origin, context_sha=context_sha)
        seen.add(key)
    if complete and seen != cases.keys():
        raise ValueError("Origin did not genuinely execute all32116 required cases")
    return len(seen)


def import_gate(run: Path, cache_path: Path) -> dict:
    registration = json.loads(ORIGIN.read_text(encoding="utf-8"))
    audit = Path(registration["audit_path"])
    verify_files({audit.as_posix(): registration["audit_sha256"]})
    approval = json.loads(audit.read_text(encoding="utf-8"))
    if not all(
        approval.get(key) is True
        for key in ("saved_audit_passed", "science_replay_go", "full_gate_go")
    ):
        raise ValueError("Independent completed-gate/scientific audit GO is absent")
    run = run.resolve()
    clone = run.parents[2]
    anchors = {
        "run": run,
        "run_parent": run.parent,
        "checkout": Path.cwd(),
        "origin_checkout": clone,
    }
    paths = {
        name: anchors[item["base"]] / item["relative_path"]
        for name, item in registration["files"].items()
    }
    verify_files({str(paths[name]): item["sha256"] for name, item in registration["files"].items()})
    require_closed_database(paths["database"])
    complete = json.loads(paths["complete"].read_text(encoding="utf-8"))
    comparison = json.loads(paths["comparison"].read_text(encoding="utf-8"))
    origin_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    if (
        complete["actual_success"] is not True
        or complete["queries"] != 32116
        or len(complete["groups"]) != 24
        or sum(complete["groups"].values()) != 32116
        or complete["source"] != registration["source"]
        or paths["native_exit"].read_text(encoding="utf-8-sig").strip() != "0"
        or paths["gate_native_exit"].read_text(encoding="utf-8-sig").strip() != "0"
        or comparison["mismatches"]
        or comparison["float_exact_different_cases"]
    ):
        raise ValueError("Origin full completion/native/comparison proof differs")
    manifest, cases, expected = checked_preflight()
    build = runtime_build()
    origin_code = inspect.getsource(runtime_build)
    probe = origin_code + (
        "\nimport json,prescriptxai\nfrom pathlib import Path\n"
        "assert Path(prescriptxai.__file__).resolve() == Path.cwd() / 'src/prescriptxai/__init__.py'\n"
        "from scripts.diagnostics.phase12_regression import runtime_manifest\n"
        "print(json.dumps([runtime_manifest(), runtime_build()],sort_keys=True))\n"
    )
    recorded_runtime, origin_build = json.loads(
        subprocess.check_output(
            [
                str(clone / ".venv/Scripts/python.exe")
                if os.name == "nt"
                else str(clone / ".venv/bin/python"),
                "-c",
                probe,
            ],
            cwd=clone,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
        )
    )
    if origin_manifest["runtime"] != recorded_runtime:
        raise ValueError("Origin runtime differs from its saved run manifest")
    for name, sha in origin_manifest["code_hashes"].items():
        verify_files({str(clone / name): sha})
    verify_files(
        {
            str(clone / name): sha
            for name, sha in origin_manifest["reference"]["input_hashes"].items()
        }
    )
    origin_context = execution_context(origin_manifest, origin_build)
    context = execution_context(manifest, build)
    if origin_context != context:
        raise ValueError("Origin execution/build context differs; never restamp saved results")
    policy_sha = file_hash(KNOWN)
    policy = known_policy(json.loads(KNOWN.read_text(encoding="utf-8")), expected)
    admission = {
        "kind": "independently_audited_full_gate",
        "context": context,
        "registration": registration,
        "registration_sha256": file_hash(ORIGIN),
        "original_run": str(run),
        "original_source": complete["source"],
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(cache_path.with_suffix(".lock")), timeout=0):
        cache = EvidenceCache(cache_path)
        try:
            with cache.transaction():
                imported = import_rows(
                    cache,
                    database_rows(paths["database"]),
                    cases,
                    expected,
                    context,
                    admission,
                    policy,
                    complete=True,
                )
                verify_unchanged(manifest)
                require_closed_database(paths["database"])
                verify_files(
                    {
                        str(paths[name]): item["sha256"]
                        for name, item in registration["files"].items()
                    }
                )
                verify_files(
                    {
                        KNOWN.as_posix(): policy_sha,
                        audit.as_posix(): registration["audit_sha256"],
                        ORIGIN.as_posix(): admission["registration_sha256"],
                    }
                )
                if runtime_build() != build:
                    raise ValueError("Runtime build changed during cache admission")
        finally:
            cache.close()
    return {
        "imported": imported,
        "recomputed": 0,
        "queries_executed": 0,
        "origin_context_equals_current": True,
        "context_sha256": digest(context),
        "original_source": complete["source"],
        "current_source": manifest["source"],
    }


def run_tier(
    tier: str,
    output: Path,
    cache_path: Path,
    resume: Path | None = None,
    *,
    reuse_only: bool = False,
) -> dict:
    start = time.perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    manifest, cases, expected = checked_preflight()  # Missing assets fail before cache access.
    ids, policy, policy_hashes = read_policy(cases, expected, tier)
    context = execution_context(manifest, runtime_build())
    context_sha = digest(context)
    descriptor = {
        "schema_version": 1,
        "source": manifest["source"],
        "context": context,
        "tier": tier,
        "ids": ids,
        "policy_hashes": policy_hashes,
        "started_utc": datetime.now(UTC).isoformat(),
        "resumed_from": str(resume) if resume else None,
    }
    atomic_json(output / "manifest.json", descriptor)
    reused, origins, missing = 0, Counter(), {}
    accepted, exact_changes = [], []
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(cache_path.with_suffix(".lock")), timeout=0):
        cache = EvidenceCache(cache_path)
        try:
            with cache.transaction():
                if resume:
                    previous = json.loads((resume / "manifest.json").read_text(encoding="utf-8"))
                    verify_resume(previous, descriptor)
                    sealed = json.loads((resume / "checkpoint.json").read_text(encoding="utf-8"))
                    checkpoint, prior_misses = checkpoint_evidence(resume, previous)
                    if checkpoint != sealed["evidence"] or not hmac.compare_digest(
                        cache.sign(checkpoint), sealed["signature"]
                    ):
                        raise ValueError("Checkpoint authentication failed")
                    admission = {
                        "kind": "explicit_preserved_partial_segment",
                        "context": context,
                        "run": str(resume),
                        "checkpoint": checkpoint,
                    }
                    count = import_rows(
                        cache,
                        database_rows(resume / "recomputed/records.sqlite3"),
                        {key: cases[key] for key in prior_misses},
                        expected,
                        context,
                        admission,
                        policy,
                        complete=False,
                    )
                    if (
                        count != checkpoint["records"]
                        or checkpoint_evidence(resume, previous)[0] != checkpoint
                    ):
                        raise ValueError("Checkpoint changed during admission")
                for key in ids:
                    hit = cache.get(
                        keyed_case(context_sha, key, cases[key]), key, cases[key], context
                    )
                    if hit is None:
                        missing[key] = cases[key]
                        continue
                    record, origin = hit
                    known, exact = compare(key, json.loads(expected[key]), record, policy)
                    accepted.extend((key, path) for path in known)
                    if exact:
                        exact_changes.append(key)
                    reused += 1
                    origins[origin] += 1
                atomic_json(
                    output / "cache-accounting.json",
                    {
                        "stage": "before_compute",
                        "requested": len(ids),
                        "reused": reused,
                        "recomputed": 0,
                        "pending_recompute": len(missing),
                        "missing_ids": sorted(missing),
                        "origins": dict(origins),
                    },
                )
                if missing and reuse_only:
                    raise ValueError(
                        "Exact-key evidence missing; reuse-only verification cannot launch solves"
                    )
                recomputed = 0
                if missing:
                    execution = {
                        **manifest,
                        "run_id": output.name,
                        "tier_context": context,
                        "requested_ids": sorted(missing),
                        "policy_hashes": policy_hashes,
                    }
                    with FileLock("artifacts/phase12-headline.lock", timeout=0), idle_sleep_guard():
                        try:
                            measured = run_cases(
                                missing, execution, output / "recomputed", resume=False
                            )
                        except BaseException as error:
                            try:
                                verify_unchanged(manifest)
                                verify_files(policy_hashes)
                                if runtime_build() != context["runtime_build"]:
                                    raise ValueError("Runtime changed during interrupted execution")
                                checkpoint, _ = checkpoint_evidence(output, descriptor)
                                atomic_json(
                                    output / "checkpoint.json",
                                    {"evidence": checkpoint, "signature": cache.sign(checkpoint)},
                                )
                            except (
                                OSError,
                                ValueError,
                                KeyError,
                                sqlite3.Error,
                            ) as checkpoint_error:
                                error.add_note(f"Partial remains unsealed: {checkpoint_error}")
                            raise
                    checkpoint, _ = checkpoint_evidence(output, descriptor)
                    admission = {
                        "kind": "fresh_actual_execution_segment",
                        "context": context,
                        "run": str(output / "recomputed"),
                        "checkpoint": checkpoint,
                    }
                    recomputed = import_rows(
                        cache,
                        database_rows(output / "recomputed/records.sqlite3"),
                        missing,
                        expected,
                        context,
                        admission,
                        policy,
                        complete=True,
                    )
                    for record in measured:
                        key = record["case_id"]
                        known, exact = compare(key, json.loads(expected[key]), record, policy)
                        accepted.extend((key, path) for path in known)
                        if exact:
                            exact_changes.append(key)
                    if checkpoint_evidence(output, descriptor)[0] != checkpoint:
                        raise ValueError("New checkpoint changed during admission")
                verify_unchanged(manifest)
                verify_files(policy_hashes)
                if (missing or resume) and runtime_build() != context["runtime_build"]:
                    raise ValueError("Runtime build changed during cache admission")
                if reused + recomputed != len(ids):
                    raise ValueError("Incomplete regression accounting")
        except BaseException as error:
            atomic_json(
                output / "failure.json",
                {
                    "actual_success": False,
                    "error": str(error),
                    "reused_before_error": reused,
                    "partials_retained": True,
                    "automatic_retry": False,
                },
            )
            raise
        finally:
            cache.close()
    result = {
        "actual_success": True,
        "tier": tier,
        "requested": len(ids),
        "reused": reused,
        "recomputed": recomputed,
        "reuse_only": reuse_only,
        "origin_counts": dict(origins),
        "complete_groups": dict(Counter(json.loads(expected[key])["group"] for key in ids)),
        "source": manifest["source"],
        "context_sha256": context_sha,
        "accepted_known_differences": accepted,
        "float_exact_different_cases": exact_changes,
        "elapsed_seconds": time.perf_counter() - start,
        "evidence_scope": "Exact-key saved evidence revalidation plus disclosed genuine cache misses; no cached timing is a new solve or serial latency claim",
        "completed_utc": datetime.now(UTC).isoformat(),
    }
    atomic_json(output / "complete.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=("subset", "full"), default="subset")
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--generate-subset", action="store_true")
    parser.add_argument("--import-run", type=Path)
    parser.add_argument("--reuse-only", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.generate_subset:
        _, cases, expected = checked_preflight()
        ids, selection = select_ids(
            cases, expected, yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        )
        if SUBSET.exists() or SUBSET_MANIFEST.exists():
            raise FileExistsError("Fixed subset is already registered; preserve it")
        atomic_json(SUBSET, ids)
        atomic_json(
            SUBSET_MANIFEST,
            {
                "subset_sha256": file_hash(SUBSET),
                "config_sha256": file_hash(CONFIG),
                "fixture_sha256": file_hash(FIXTURE),
                "selection": selection,
            },
        )
        print(json.dumps({"selected": len(ids), **selection}, sort_keys=True))
    elif args.import_run:
        print(json.dumps(import_gate(args.import_run, args.cache), sort_keys=True))
    else:
        output = args.output or Path("artifacts/regression-tiers") / (
            args.tier + "-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + f"-{os.getpid()}"
        )
        print(
            json.dumps(
                run_tier(args.tier, output, args.cache, args.resume, reuse_only=args.reuse_only),
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
