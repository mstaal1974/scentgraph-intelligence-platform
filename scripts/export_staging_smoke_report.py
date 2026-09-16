#!/usr/bin/env python3
"""Export an allowlisted public summary from a private sanitized smoke result."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.staging_smoke import StagingSmokeRunResult  # noqa: E402
from aromatwin.services.staging_smoke_tests import public_summary  # noqa: E402

PRIVATE_ROOT = Path("data/private/reports").resolve()


def _inside(path: Path, root: Path) -> bool:
    resolved = path.resolve()
    return resolved == root or root in resolved.parents


def export_report(source: Path, output: Path) -> None:
    if not _inside(source, PRIVATE_ROOT):
        raise ValueError("input must be under data/private/reports/")
    result = StagingSmokeRunResult.model_validate_json(source.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(public_summary(result).model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    export_report(args.input, args.output)
    print(f"Wrote allowlisted public summary to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
