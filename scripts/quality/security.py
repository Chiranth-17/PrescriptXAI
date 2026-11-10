"""Record Phase 16 scans and fail on unresolved high findings or missing evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import distributions
from pathlib import Path

import yaml

EXCEPTIONS = Path("configs/security_exceptions.yaml")
PUBLIC_DIGESTS = Path("configs/security_public_digests.yaml")


def active_exceptions(path, today):
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, list):
        raise ValueError("security exceptions must be a list")
    active, seen = set(), set()
    for item in document:
        if set(item) != {"finding", "reason", "expires"}:
            raise ValueError("each exception needs a finding, reason and expiry")
        finding = item["finding"]
        if not finding or finding in seen or not item["reason"].strip():
            raise ValueError("exception findings must be unique and justified")
        seen.add(finding)
        expiry = datetime.strptime(str(item["expires"]), "%Y-%m-%d").date()
        if expiry >= today:
            active.add(finding)
    return active


def native(directory, stage, args, *, stdout_name=None):
    with (
        (directory / (stdout_name or f"{stage}.stdout.log")).open("x", encoding="utf-8") as stdout,
        (directory / f"{stage}.stderr.log").open("x", encoding="utf-8") as stderr,
    ):
        result = subprocess.run(args, stdout=stdout, stderr=stderr, check=False)
    (directory / f"{stage}.exit").write_text(f"{result.returncode}\n", encoding="utf-8")
    print(f"{stage}: native {result.returncode}", flush=True)
    return result.returncode


def source_path(value):
    return value.replace("\\", "/")


def finding_ids(bandit, secrets, audit):
    high = set()
    for item in bandit["results"]:
        if item["issue_severity"] in {"HIGH", "CRITICAL"}:
            high.add(
                f"bandit:{item['test_id']}:{source_path(item['filename'])}:{item['line_number']}"
            )
    for filename, matches in secrets["results"].items():
        for item in matches:
            high.add(
                f"secret:{source_path(filename)}:{item['line_number']}:{item['hashed_secret']}"
            )
    for item in audit["dependencies"]:
        for vulnerability in item["vulns"]:
            high.add(f"pip-audit:{item['name']}:{item['version']}:{vulnerability['id']}")
    return high


def public_digest_ids(secrets, path, today):
    policy = yaml.safe_load(path.read_text(encoding="utf-8"))
    if set(policy) != {"reason", "expires", "files"} or not policy["reason"].strip():
        raise ValueError("public digest evidence requires a reason, expiry and pinned files")
    if datetime.strptime(str(policy["expires"]), "%Y-%m-%d").date() < today:
        return set()
    pins = policy["files"]
    # Policy metadata itself contains public digests and hashed scanner references.
    metadata = {
        path.as_posix(): set(pins.values()),
        EXCEPTIONS.as_posix(): {
            item["finding"].rsplit(":", 1)[-1]
            for item in yaml.safe_load(EXCEPTIONS.read_text(encoding="utf-8"))
            if item["finding"].startswith("secret:")
        },
    }
    result = set()
    for name, matches in secrets["results"].items():
        filename = source_path(name)
        if filename not in pins and filename not in metadata:
            continue
        content = Path(filename).read_text(encoding="utf-8")
        fixed_snapshot = (
            filename in pins and hashlib.sha256(content.encode()).hexdigest() == pins[filename]
        )
        if not fixed_snapshot and filename not in metadata:
            continue
        lines = content.splitlines()
        for item in matches:
            if item["type"] != "Hex High Entropy String":
                continue
            line = item["line_number"]
            if not 1 <= line <= len(lines):
                continue
            words = re.findall(r"\b(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\b", lines[line - 1])
            if any(
                (fixed_snapshot or word in metadata.get(filename, ()))
                and hashlib.sha1(word.encode(), usedforsecurity=False).hexdigest()
                == item["hashed_secret"]
                for word in words
            ):
                result.add(f"secret:{filename}:{line}:{item['hashed_secret']}")
    return result


def exact_environment_pins(path):
    pins = {
        f"{dist.metadata['Name']}=={dist.version}"
        for dist in distributions()
        if dist.metadata["Name"].lower().replace("_", "-") != "prescriptxai"
    }
    if not pins:
        raise ValueError("the auditable dependency environment is empty")
    path.write_text("\n".join(sorted(pins, key=str.casefold)) + "\n", encoding="utf-8")
    return len(pins)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    started = datetime.now(UTC)
    root = args.output or Path("artifacts/phase16") / started.strftime("security-%Y%m%dT%H%M%S%fZ")
    root.mkdir(parents=True, exist_ok=False)
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    (root / "launch.json").write_text(
        json.dumps(
            {
                "source": source,
                "started_utc": started.isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    expected = exact_environment_pins(root / "installed-pins.txt")
    codes = {}
    commands = {
        "pip-audit": [
            sys.executable,
            "-m",
            "pip_audit",
            "--strict",
            "--no-deps",
            "--disable-pip",
            "--progress-spinner",
            "off",
            "--format",
            "json",
            "-r",
            str(root / "installed-pins.txt"),
            "--output",
            str(root / "pip-audit.json"),
        ],
        "bandit": [
            "uv",
            "tool",
            "run",
            "--from",
            "bandit==1.9.4",
            "bandit",
            "-r",
            "src",
            "scripts",
            "-f",
            "json",
            "-o",
            str(root / "bandit.json"),
        ],
        "secrets": [
            "uv",
            "tool",
            "run",
            "--from",
            "detect-secrets==1.5.0",
            "detect-secrets",
            "scan",
            "--no-verify",
        ],
        "sbom": [
            "uv",
            "export",
            "--locked",
            "--all-groups",
            "--all-extras",
            "--format",
            "cyclonedx1.5",
        ],
        "tests": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *[str(p) for p in sorted(Path("tests").rglob("test_phase16_*.py"))],
        ],
    }
    for stage, command in commands.items():
        codes[stage] = native(
            root,
            stage,
            command,
            stdout_name={"secrets": "secrets.json", "sbom": "sbom.cdx.json"}.get(stage),
        )

    high, excepted, public = set(), set(), set()
    errors = []
    for stage, code in codes.items():
        allowed = {0, 1} if stage in {"bandit", "pip-audit"} else {0}
        if code not in allowed:
            errors.append(f"{stage} did not complete successfully")
    bandit_counts, secret_count, audited, components = {}, 0, 0, 0
    try:
        bandit = json.loads((root / "bandit.json").read_text(encoding="utf-8"))
        secrets = json.loads((root / "secrets.json").read_text(encoding="utf-8"))
        audit = json.loads((root / "pip-audit.json").read_text(encoding="utf-8"))
        sbom = json.loads((root / "sbom.cdx.json").read_text(encoding="utf-8"))
        bandit_counts = bandit["metrics"]["_totals"]
        secret_count = sum(len(items) for items in secrets["results"].values())
        audited = len(audit["dependencies"])
        components = len(sbom["components"])
        if bandit["errors"] or (codes["bandit"] == 1 and not bandit["results"]):
            errors.append("Bandit did not produce a complete scan")
        if (
            audited != expected
            or any("skip_reason" in item for item in audit["dependencies"])
            or (
                codes["pip-audit"] == 1 and not any(item["vulns"] for item in audit["dependencies"])
            )
        ):
            errors.append("dependency audit did not cover the installed pins")
        if sbom["bomFormat"] != "CycloneDX" or sbom["specVersion"] != "1.5" or not components:
            errors.append("SBOM is incomplete")
        high = finding_ids(bandit, secrets, audit)
        excepted = high & active_exceptions(EXCEPTIONS, started.date())
        public = high & public_digest_ids(secrets, PUBLIC_DIGESTS, started.date())
    except (OSError, ValueError, TypeError, KeyError) as error:
        errors.append(
            f"incomplete scan or invalid exception configuration ({type(error).__name__})"
        )
    blocked = high - excepted - public
    result = {
        "source": source,
        "started_utc": started.isoformat(),
        "ended_utc": datetime.now(UTC).isoformat(),
        "passed": not blocked and not errors,
        "native_exit": codes,
        "audited_dependencies": audited,
        "sbom_components": components,
        "bandit_totals": bandit_counts,
        "secret_findings": secret_count,
        "verified_public_digest_findings": len(public),
        "blocking_findings": sorted(blocked),
        "excepted_findings": sorted(excepted),
        "errors": errors,
    }
    (root / "complete.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{root / 'complete.json'}: {'passed' if result['passed'] else 'failed'}")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
