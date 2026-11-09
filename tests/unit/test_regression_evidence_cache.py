"""Genuine saved-row cache admission, integrity and exact source/config/data invalidation."""

import copy
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from scripts.diagnostics.regression_tiers import (
    EvidenceCache,
    case_key,
    checkpoint_evidence,
    compare,
    digest,
    known_policy,
    python_source_hashes,
    run_tier,
    verify_resume,
)


@pytest.fixture
def saved_case() -> dict:
    """Use one genuine approved row without loading/fitting models or running a search."""
    parquet = pq.ParquetFile("tests/regression/cmapss_baseline.parquet")
    return next(parquet.iter_batches(batch_size=1)).to_pylist()[0]


def context() -> dict:
    """Construct independent identity components for cache-key boundary tests only."""
    return {
        "code_hashes": {"src/model.py": "a"},
        "input_hashes": {"weights": "b"},
        "design_sha256": "c",
        "runtime_build": {"numpy": "d", "threads": 1},
    }


def admitted(tmp_path: Path, row: dict) -> tuple[EvidenceCache, str, dict]:
    """Admit a real saved case into an explicitly test-only cache context."""
    cache = EvidenceCache(tmp_path / "cache.sqlite3")
    identity = context()
    origin = cache.add_origin({"context": identity, "kind": "unit_test_real_saved_row"})
    cache.put(row["case_id"], row["case_json"], row["observation_json"], identity, origin)
    return cache, case_key(identity, row["case_id"], row["case_json"]), identity


def test_every_execution_identity_component_invalidates_reuse(saved_case: dict) -> None:
    """New source files, changed source/config/data/runtime or case identity cannot hit old keys."""
    original = context()
    key = case_key(original, saved_case["case_id"], saved_case["case_json"])
    variants = []
    for name in original:
        changed = copy.deepcopy(original)
        changed[name] = {"changed": True}
        variants.append(changed)
    added_file = copy.deepcopy(original)
    added_file["code_hashes"]["src/new_adapter.py"] = "new"
    variants.append(added_file)
    assert all(
        case_key(value, saved_case["case_id"], saved_case["case_json"]) != key for value in variants
    )
    case = json.loads(saved_case["case_json"])
    case["config"]["seed"] += 1
    assert case_key(original, saved_case["case_id"], json.dumps(case)) != key
    assert case_key(original, "foreign-id", saved_case["case_json"]) != key


def test_cache_reuses_genuine_payload_and_preserves_original_timings(
    tmp_path: Path, saved_case: dict
) -> None:
    """A warm hit retains real old timings and another context is a miss."""
    cache, key, identity = admitted(tmp_path, saved_case)
    try:
        record, _ = cache.get(key, saved_case["case_id"], saved_case["case_json"], identity)
        expected = json.loads(saved_case["observation_json"])
        assert record["timings"] == expected["timings"]
        assert compare(saved_case["case_id"], expected, record, {}) == ([], [])
        different = {**identity, "extra": 1}
        changed_key = case_key(different, saved_case["case_id"], saved_case["case_json"])
        assert (
            cache.get(changed_key, saved_case["case_id"], saved_case["case_json"], different)
            is None
        )
    finally:
        cache.close()


@pytest.mark.parametrize("coherent_sha", [False, True])
def test_payload_poison_is_rejected_even_when_sha_is_updated(
    tmp_path: Path, saved_case: dict, coherent_sha: bool
) -> None:
    """Changing the payload and its hash together still lacks an authentic admission."""
    cache, key, identity = admitted(tmp_path, saved_case)
    try:
        value = json.loads(saved_case["observation_json"])
        value["risk_after"] += 0.01
        payload = json.dumps(value)
        if coherent_sha:
            cache.connection.execute(
                "UPDATE entries SET payload=?,payload_sha=? WHERE key=?",
                (payload, hashlib.sha256(payload.encode()).hexdigest(), key),
            )
        else:
            cache.connection.execute("UPDATE entries SET payload=? WHERE key=?", (payload, key))
        cache.connection.commit()
        with pytest.raises(ValueError, match="integrity/provenance"):
            cache.get(key, saved_case["case_id"], saved_case["case_json"], identity)
    finally:
        cache.close()


def test_missing_or_coherently_changed_admission_is_rejected(
    tmp_path: Path, saved_case: dict
) -> None:
    """A result cannot borrow missing or edited origin metadata."""
    cache, key, identity = admitted(tmp_path, saved_case)
    try:
        payload = {"context": identity, "kind": "fabricated"}
        cache.connection.execute("UPDATE origins SET payload=?", (json.dumps(payload),))
        cache.connection.commit()
        with pytest.raises(ValueError, match="origin integrity"):
            cache.get(key, saved_case["case_id"], saved_case["case_json"], identity)
        cache.connection.execute("DELETE FROM origins")
        cache.connection.commit()
        with pytest.raises(ValueError, match="origin missing"):
            cache.get(key, saved_case["case_id"], saved_case["case_json"], identity)
    finally:
        cache.close()


def test_missing_local_authentication_key_does_not_replace_existing_cache(
    tmp_path: Path, saved_case: dict
) -> None:
    """Loss of the separate key fails closed instead of blessing existing rows with a new key."""
    cache, _, _ = admitted(tmp_path, saved_case)
    cache.close()
    database = tmp_path / "cache.sqlite3"
    before = database.read_bytes()
    database.with_suffix(".key").unlink()
    with pytest.raises(ValueError, match="authentication key missing"):
        EvidenceCache(database)
    assert database.read_bytes() == before


def test_unlisted_or_stale_known_difference_is_not_silently_accepted(saved_case: dict) -> None:
    """Unexpected changes fail and an obsolete accepted exception cannot silently persist."""
    original = json.loads(saved_case["observation_json"])
    changed = copy.deepcopy(original)
    changed["risk_after"] += 0.01
    with pytest.raises(ValueError, match="Unlisted"):
        compare(saved_case["case_id"], original, changed, {})
    entry = {
        "case_id": saved_case["case_id"],
        "field": "/risk_after",
        "saved_value": original["risk_after"],
        "accepted_value": changed["risk_after"],
        "reason": "Constructed policy boundary test; no real baseline exception",
    }
    document = {
        "schema_version": 1,
        "absolute_tolerance": 1e-6,
        "relative_tolerance": 0,
        "entries": [entry],
    }
    expected = {saved_case["case_id"]: saved_case["observation_json"]}
    policy = known_policy(document, expected)
    assert compare(saved_case["case_id"], original, changed, policy)[0] == ["/risk_after"]
    with pytest.raises(ValueError, match="Stale"):
        compare(saved_case["case_id"], original, original, policy)
    document["entries"].append(entry)
    with pytest.raises(ValueError, match="Duplicate"):
        known_policy(document, expected)
    assert digest(original) != digest(changed)


@pytest.mark.parametrize("field", ["context", "tier", "ids", "policy_hashes"])
def test_resume_refuses_changed_execution_or_comparison_policy(field: str) -> None:
    """A resume cannot adopt old results after any execution or acceptance policy change."""
    previous = {
        "context": context(),
        "tier": "subset",
        "ids": ["case"],
        "policy_hashes": {"known": "a"},
    }
    changed = {**previous, field: "changed"}
    with pytest.raises(ValueError, match="Resume"):
        verify_resume(previous, changed)
    verify_resume(previous, dict(previous))


def test_missing_fixture_fails_before_creating_or_opening_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An absent genuine fixture cannot be hidden by a cache, skip or substitute."""
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / "must-not-exist/cache.sqlite3"
    with pytest.raises(FileNotFoundError, match="Required audited regression manifest missing"):
        run_tier("subset", tmp_path / "preserved-failure", cache, reuse_only=True)
    assert not cache.parent.exists()


def test_failed_admission_rolls_back_entries_and_origin(tmp_path: Path, saved_case: dict) -> None:
    """Reject the whole batch when validation fails after the first insert."""
    cache = EvidenceCache(tmp_path / "cache.sqlite3")
    identity = context()
    with pytest.raises(ValueError, match="later row"), cache.transaction():
        origin = cache.add_origin({"context": identity})
        cache.put(
            saved_case["case_id"],
            saved_case["case_json"],
            saved_case["observation_json"],
            identity,
            origin,
        )
        raise ValueError("later row")
    assert cache.connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 0
    assert cache.connection.execute("SELECT COUNT(*) FROM origins").fetchone()[0] == 0
    cache.close()


def test_checkpoint_refuses_foreign_execution_manifest(tmp_path: Path) -> None:
    """A matching outer descriptor cannot authorize a foreign inner execution."""
    descriptor = {
        "source": "source",
        "context": context(),
        "ids": ["case"],
        "policy_hashes": {"policy": "sha"},
    }
    replay = tmp_path / "recomputed"
    replay.mkdir()
    for path, value in (
        (tmp_path / "cache-accounting.json", {"missing_ids": ["case"], "pending_recompute": 1}),
        (replay / "manifest.json", {"requested_ids": ["foreign"]}),
        (replay / "segments.json", []),
    ):
        path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="Checkpoint execution manifest"):
        checkpoint_evidence(tmp_path, descriptor)


def test_python_newline_equivalence_still_requires_raw_origin_pin(tmp_path: Path) -> None:
    """Accept Python newline equivalence only after checking the original bytes."""
    path = tmp_path / "worker.py"
    original = b"value = 2\r\n"
    lf = b"value = 2\n"
    path.write_bytes(original)
    pinned = {"worker.py": hashlib.sha256(original).hexdigest()}
    assert python_source_hashes(tmp_path, pinned) == {"worker.py": hashlib.sha256(lf).hexdigest()}
    path.write_bytes(lf)
    with pytest.raises(ValueError, match="pinned bytes"):
        python_source_hashes(tmp_path, pinned)
