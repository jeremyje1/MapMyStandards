#!/usr/bin/env python3
"""Pre-commit hook to detect hardcoded secrets in staged code files."""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Iterable, Iterator

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "API key assignment",
        re.compile(r"(api_key|apikey|apiKey)\s*=\s*['\"]{1}[^'\"]{12,}"),
    ),
    (
        "Password assignment",
        re.compile(r"(password|passwd|pwd)\s*=\s*['\"]{1}[^'\"]{8,}"),
    ),
    (
        "Secret key assignment",
        re.compile(r"(secret_key|secretKey)\s*=\s*['\"]{1}[^'\"]{12,}"),
    ),
    (
        "Access token assignment",
        re.compile(r"(access_token|token)\s*=\s*['\"]{1}[^'\"]{20,}"),
    ),
]

ALLOWED_EXTENSIONS = (
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".sh",
    ".env",
    ".yaml",
    ".yml",
    ".json",
)


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


def iter_relevant_additions(diff: str) -> Iterator[tuple[str, str]]:
    current_file: str | None = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current_file = line[6:] if line.startswith("+++ b/") else None
            continue

        if not current_file or current_file == "/dev/null":
            continue

        if not current_file.endswith(ALLOWED_EXTENSIONS):
            continue

        if line.startswith("+") and not line.startswith("+++"):
            yield current_file, line[1:]


def find_violations(diff: str) -> Iterable[str]:
    for filename, line in iter_relevant_additions(diff):
        for pattern_name, pattern in PATTERNS:
            if pattern.search(line):
                yield f"{pattern_name} in {filename}: {line.strip()}"


def main() -> int:
    diff = get_staged_diff()
    if not diff:
        return 0

    violations = list(find_violations(diff))
    if violations:
        print("❌ Potential hardcoded secrets detected in staged changes:")
        for violation in violations:
            print(f"   - {violation}")
        print(
            "\nℹ️  Use environment variables (os.environ / getenv) instead of hardcoding secrets."
        )
        return 1

    print("✅ No hardcoded secrets detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
