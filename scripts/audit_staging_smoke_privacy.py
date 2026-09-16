#!/usr/bin/env python3
"""Reject likely sensitive values in public staging-smoke artifacts."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.staging_smoke import StagingSmokeAuditReport  # noqa: E402

DEFAULT_PATHS = [
    Path("data/samples/staging_smoke_report_sample.csv"),
    Path("data/samples/staging_operator_handoff_sample.csv"),
    Path("docs/staging-smoke-test-operator-handoff.md"),
    Path(".github/workflows/staging-smoke-template.yml"),
]
VALUE_PATTERNS = (
    re.compile(r"(?i)(?:api[_-]?key|password|token|secret)\s*[:=]\s*[\"']?(?!\$\{\{|<|placeholder|from-environment|not-a-value)[^\s\"'#}]+"),
    re.compile(r"(?i)(?:postgres(?:ql)?|mysql)://[^\s:/]+:[^\s@]+@"),
    re.compile(r"\b(?:sk|rk|ghp|github_pat)_[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?<!\w)(?:\+?\d[\d .()-]{7,}\d)(?!\w)"),
)
FORBIDDEN_PUBLIC_FIELD = re.compile(
    r"(?i)\b(supplier[_ -]?(?:price|cost|code|commercial terms?)|cn[_ -]?code|aed[_ -]?price|"
    r"usd[_ -]?price|raw[_ -]?margin|stock|quantity|seller[_ -]?private notes?|"
    r"consumer[_ -]?private notes?|street[_ -]?address)\b"
)


def audit_paths(paths: list[Path]) -> StagingSmokeAuditReport:
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else [path])
    violations: list[str] = []
    for path in files:
        if not path.is_file():
            violations.append(f"{path}: missing audit target")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(text) for pattern in VALUE_PATTERNS):
            violations.append(f"{path}: likely credential or personal value")
        # The operator guide must name prohibited categories; structured public artifacts must not.
        if path.suffix in {".csv", ".yml", ".yaml"} and FORBIDDEN_PUBLIC_FIELD.search(text):
            violations.append(f"{path}: private or commercial field marker")
    return StagingSmokeAuditReport(
        passed=not violations, audited_file_count=len(files), violation_count=len(violations),
        violations=violations, summary="No sensitive public values detected." if not violations else "Sensitive public artifact markers require review.",
    )


def main(argv: list[str] | None = None) -> int:
    paths = [Path(value) for value in (argv if argv is not None else sys.argv[1:])] or DEFAULT_PATHS
    report = audit_paths(paths)
    for violation in report.violations:
        print(f"FAIL: {violation}")
    print(("PASS" if report.passed else "FAIL") + f": audited {report.audited_file_count} staging smoke artifacts.")
    return int(not report.passed)


if __name__ == "__main__":
    raise SystemExit(main())
