#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from aromatwin.services.provenance import PermittedUse, SourcePolicy, validate_commercial_promotion


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reject unsafe source policies before catalogue promotion"
    )
    parser.add_argument("policy", type=Path)
    parser.add_argument("--for-promotion", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.policy.read_text())
    payload["permitted_use"] = PermittedUse(payload["permitted_use"])
    policy = SourcePolicy(**payload)
    if args.for_promotion:
        validate_commercial_promotion(policy)
    print("Source policy is valid for the requested use")


if __name__ == "__main__":
    main()
