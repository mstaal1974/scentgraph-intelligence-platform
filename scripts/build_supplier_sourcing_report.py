#!/usr/bin/env python3
"""Build a private sourcing report from staged private supplier offers."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from aromatwin.services.supplier_sourcing import (
    audit_offers,
    build_sourcing_decisions,
    load_private_supplier_offers,
    public_safe_decision,
)


def _private_output(path: Path) -> Path:
    resolved = path.resolve()
    root = Path("data/private/reports").resolve()
    if root != resolved.parent and root not in resolved.parents:
        raise ValueError("Private reports must be written under data/private/reports/")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/supplier-sourcing-report.json"))
    parser.add_argument("--public-safe-summary", type=Path)
    args = parser.parse_args()
    offers = load_private_supplier_offers(args.input)
    decisions = build_sourcing_decisions(offers)
    accepted = sum(item.sourcing_recommendation == "preferred_candidate" for item in decisions)
    payload = {"accepted_count": accepted, "rejected_count": len(decisions) - accepted,
               "audit": audit_offers(offers), "decisions": [asdict(item) for item in decisions]}
    output = _private_output(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, default=str, indent=2) + "\n")
    if args.public_safe_summary:
        safe = {"accepted_count": accepted, "rejected_count": len(decisions) - accepted,
                "decisions": [public_safe_decision(item) for item in decisions]}
        args.public_safe_summary.parent.mkdir(parents=True, exist_ok=True)
        args.public_safe_summary.write_text(json.dumps(safe, default=str, indent=2) + "\n")
    print(f"accepted={accepted} rejected={len(decisions) - accepted} report={output}")


if __name__ == "__main__":
    main()
