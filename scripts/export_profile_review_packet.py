#!/usr/bin/env python3
"""Export review guidance from private draft output."""

import argparse
import json
from pathlib import Path

from aromatwin.schemas.profile_production import PrivateProfileDraftRead
from aromatwin.services.profile_review_packet import build_profile_review_packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--public-safe", action="store_true")
    args = parser.parse_args()
    root = Path("data/private/runs") / args.run_id / "profiles"
    drafts = [PrivateProfileDraftRead.model_validate(item) for item in json.loads((root / "drafts.json").read_text())]
    packets = [build_profile_review_packet(draft, args.run_id).model_dump(mode="json") for draft in drafts]
    target = root / ("review_packet_public_safe.json" if args.public_safe else "review_packets_export.json")
    target.write_text(json.dumps(packets, indent=2) + "\n", encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
