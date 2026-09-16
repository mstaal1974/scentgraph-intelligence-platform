#!/usr/bin/env python3
"""Generate private product margin scenarios from private JSON assumptions."""

import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from aromatwin.services.margin_intelligence import CostInput, calculate_margin


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Private JSON list of cost assumptions")
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/margin-scenarios.json"))
    args = parser.parse_args()
    private = Path("data/private").resolve()
    if private not in args.input.resolve().parents:
        raise ValueError("Cost assumptions must be read from data/private/")
    reports = Path("data/private/reports").resolve()
    if reports != args.output.resolve().parent and reports not in args.output.resolve().parents:
        raise ValueError("Margin reports must be written under data/private/reports/")
    raw = json.loads(args.input.read_text())
    accepted, rejected = [], []
    for row in raw:
        try:
            values = {key: Decimal(str(value)) if key != "product_format" and value is not None else value
                      for key, value in row.items() if key != "scenario_name"}
            accepted.append(calculate_margin(CostInput(**values), row.get("scenario_name", "target")))
        except (TypeError, ValueError, ArithmeticError) as error:
            rejected.append(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"accepted_count": len(accepted),
        "rejected_count": len(rejected), "scenarios": [asdict(item) for item in accepted],
        "rejections": rejected}, default=str, indent=2) + "\n")
    print(f"accepted={len(accepted)} rejected={len(rejected)} report={args.output}")


if __name__ == "__main__":
    main()
