#!/usr/bin/env python3
"""Reject credential-like values and private/commercial fields in public deploy artifacts."""

import re
import sys
from pathlib import Path

DEFAULT_PATHS = [Path("deployment"), Path("data/samples/deployment_readiness_sample.csv"),
                 Path("data/samples/environment_readiness_sample.csv")]
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*(?!<|\$\{|\[|set-in-host|placeholder|null)([^\s#]+)"),
    re.compile(r"(?i)(postgres(?:ql)?|mysql)://[^\s:/]+:[^\s@]+@"),
    re.compile(r"\b(?:sk|rk|ghp|github_pat)_[A-Za-z0-9_-]{16,}\b"),
)
PRIVATE_FIELD = re.compile(
    r"(?i)\b(supplier[_ -]?(?:price|cost|code|terms?)|cn[_ -]?code|aed[_ -]?price|"
    r"usd[_ -]?price|raw[_ -]?margin|stock|quantity|seller[_ -]?private|consumer[_ -]?private|"
    r"email|phone|street[_ -]?address)\b"
)
ALLOWED_DOCS = {"README.md", "staging.env.example"}


def audit_paths(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else [path])
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                violations.append(f"{path}: credential-like value")
        # Documentation and env key names may describe forbidden data without containing records.
        if path.name not in ALLOWED_DOCS and PRIVATE_FIELD.search(text):
            violations.append(f"{path}: private or commercial field marker")
    return violations


def main(argv: list[str] | None = None) -> int:
    paths = [Path(value) for value in (argv if argv is not None else sys.argv[1:])] or DEFAULT_PATHS
    violations = audit_paths(paths)
    for violation in violations:
        print(f"FAIL: {violation}")
    if violations:
        return 1
    print(f"PASS: audited {len(paths)} deployment/public-sample targets; no sensitive values found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
