"""Scan current nonignored files and optional Git blob history without printing secret values."""

import argparse
import io
import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    "openai_key_shape": rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b",
    "github_classic_token_shape": rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
    "github_fine_grained_token_shape": rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b",
    "aws_access_key_shape": rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
}


def findings(data, identity):
    """Return only pattern labels and source identity; matched bytes are never emitted."""
    return [
        {"source": identity, "pattern": name}
        for name, pattern in PATTERNS.items()
        if re.search(pattern, data)
    ]


def scan(include_history=False):
    """Inspect actual current files and every reachable historical blob when requested."""
    names = (
        subprocess.check_output(
            [
                "git",
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
            ]
        )
        .decode("utf-8")
        .split("\0")
    )
    found = []
    current_count = 0
    for name in sorted(set(names) - {""}):
        path = Path(name)
        if path.is_file():
            found.extend(findings(path.read_bytes(), name))
            current_count += 1
    historical_count = 0
    if include_history:
        objects = subprocess.check_output(["git", "rev-list", "--objects", "--all"], text=True)
        ids = "\n".join(line.split(" ", 1)[0] for line in objects.splitlines()) + "\n"
        checked = subprocess.run(
            ["git", "cat-file", "--batch-check"],
            input=ids,
            capture_output=True,
            text=True,
            check=True,
        )
        blobs = [line.split()[0] for line in checked.stdout.splitlines() if " blob " in line]
        encoded = subprocess.run(
            ["git", "cat-file", "--batch"],
            input=("\n".join(blobs) + "\n").encode(),
            capture_output=True,
            check=True,
        ).stdout
        stream = io.BytesIO(encoded)
        while header := stream.readline():
            object_id, kind, size = header.decode().split()
            if kind != "blob":
                raise ValueError("unexpected Git object in historical scan")
            data = stream.read(int(size))
            if len(data) != int(size) or stream.read(1) != b"\n":
                raise ValueError("truncated Git blob stream")
            found.extend(findings(data, f"git-blob:{object_id}"))
            historical_count += 1
    return {
        "source": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "current_files": current_count,
        "historical_blobs": historical_count,
        "patterns": sorted(PATTERNS),
        "findings": found,
        "passed": not found,
        "scope": "high-confidence byte patterns; no claim to detect every credential format",
    }


def main():
    """Write counts and non-sensitive finding locations, failing on a verified pattern match."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-history", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = scan(args.include_history)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
