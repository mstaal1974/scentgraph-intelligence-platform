#!/usr/bin/env python3
"""Export a private run's count/status-only acceptance projection."""

import argparse
import json
from pathlib import Path

from aromatwin.schemas.private_supplier_pilot import PilotAcceptancePublicSummary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--output")
    args = parser.parse_args()
    source = Path("data/private/runs") / args.run_id / "acceptance.json"
    report = PilotAcceptancePublicSummary.model_validate_json(source.read_text())
    rendered = json.dumps(report.model_dump(mode="json"), indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
