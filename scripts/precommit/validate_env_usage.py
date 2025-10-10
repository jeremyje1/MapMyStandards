#!/usr/bin/env python3
"""Pre-commit hook to ensure API secrets reference environment variables."""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Iterable

# Patterns representing sensitive assignments that should not be hardcoded
SENSITIVE_ASSIGNMENT = re.compile(
    r"^\+.*=\s*['\"](?:sk-|rk_|pk_|AKIA|SG\.|mlsn\.|whsec|ghp_)[^'\"]{4,}",
    re.IGNORECASE,
)

# Allowed environment access patterns
ALLOWED_ENV_USAGE = re.compile(r"os\.(environ|getenv)|settings?\.get", re.IGNORECASE)


def get_staged_diff() -> str:
    try:
        completed = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        sys.stderr.write(exc.stderr)
        return ""
    return completed.stdout


def detect_issues(diff: str) -> Iterable[str]:
    for block in diff.split("\n\n"):
        lines = block.splitlines()
        if not any(line.startswith("+++") for line in lines):
            continue
        additions = [
            line
            for line in lines
            if line.startswith("+") and not line.startswith("+++")
        ]
        for line in additions:
            if SENSITIVE_ASSIGNMENT.search(line) and not ALLOWED_ENV_USAGE.search(
                block
            ):
                yield line.strip()


def main() -> int:
    diff = get_staged_diff()
    if not diff:
        return 0

    issues = list(detect_issues(diff))
    if issues:
        print("❌ Sensitive assignments should come from environment variables:")
        for issue in issues:
            print(f"   - {issue}")
        print(
            "\nℹ️  Use os.environ[...] or os.getenv(...) to load secrets from environment variables."
        )
        return 1

    print("✅ Environment usage validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
