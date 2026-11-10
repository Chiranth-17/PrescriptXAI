"""The scan policy fails closed on expired and unlisted findings."""

import hashlib
from datetime import date
from pathlib import Path

import pytest
from scripts.quality.security import active_exceptions, finding_ids, public_digest_ids


def test_exception_scope_and_expiry(tmp_path: Path) -> None:
    """An explicit dated finding expires after its documented deadline."""
    policy = tmp_path / "exceptions.yaml"
    policy.write_text(
        "- finding: fixture-id\n  reason: synthetic test fixture\n  expires: 2026-11-10\n"
    )
    assert active_exceptions(policy, date(2026, 11, 10)) == {"fixture-id"}
    assert active_exceptions(policy, date(2026, 11, 11)) == set()
    policy.write_text("- finding: fixture-id\n  reason: ''\n  expires: 2026-11-10\n")
    with pytest.raises(ValueError, match="justified"):
        active_exceptions(policy, date(2026, 11, 10))


def test_high_findings_are_bound_to_source_location_and_version() -> None:
    """Block high source findings, credential detections and dependency advisories."""
    bandit = {
        "results": [
            {
                "issue_severity": "HIGH",
                "test_id": "B001",
                "filename": r"src\fixture.py",
                "line_number": 3,
            },
            {
                "issue_severity": "LOW",
                "test_id": "B002",
                "filename": "src/fixture.py",
                "line_number": 8,
            },
        ]
    }
    fingerprint = hashlib.sha1(b"fixture-digest", usedforsecurity=False).hexdigest()
    secrets = {"results": {"config.ini": [{"line_number": 4, "hashed_secret": fingerprint}]}}
    audit = {
        "dependencies": [{"name": "example", "version": "0.1", "vulns": [{"id": "fixture-id"}]}]
    }
    assert finding_ids(bandit, secrets, audit) == {
        "bandit:B001:src/fixture.py:3",
        f"secret:config.ini:4:{fingerprint}",
        "pip-audit:example:0.1:fixture-id",
    }


def test_public_digest_review_is_content_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changing the reviewed file invalidates its public-checksum exception."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/security_exceptions.yaml").write_text("[]")
    public = "01ab" * 16
    fingerprint = hashlib.sha1(public.encode(), usedforsecurity=False).hexdigest()
    reviewed = Path("public.json")
    reviewed.write_text(f'["{public}"]\n', encoding="utf-8")
    digest = hashlib.sha256(reviewed.read_text(encoding="utf-8").encode()).hexdigest()
    policy = Path("configs/security_public_digests.yaml")
    policy.write_text(
        f"reason: Public fixture\nexpires: 2027-02-28\nfiles:\n  public.json: {digest}\n"
    )
    scan = {
        "results": {
            "public.json": [
                {"type": "Hex High Entropy String", "line_number": 1, "hashed_secret": fingerprint}
            ]
        }
    }
    today = date(2026, 11, 10)
    assert public_digest_ids(scan, policy, today) == {f"secret:public.json:1:{fingerprint}"}
    with reviewed.open("a", encoding="utf-8") as stream:
        stream.write("\n")
    assert public_digest_ids(scan, policy, today) == set()
