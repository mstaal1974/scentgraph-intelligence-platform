#!/usr/bin/env python3
"""Build empty/local public-safe export templates; never performs a network operation."""
import argparse
import csv
import json
from pathlib import Path

from aromatwin.services.maison_export_contracts import contract_fields
from aromatwin.services.maison_sync_manifest import build_sync_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--public-safe-sample", action="store_true")
    parser.add_argument("--output-dir", type=Path,
                        default=Path("data/private/reports/maison"))
    args = parser.parse_args()
    output = Path("data/samples") if args.public_safe_sample else args.output_dir
    names = {"products": "maison_product_export.csv",
             "recommendations": "maison_recommendation_export.csv",
             "scentprint_matches": "maison_scentprint_match.csv", "bundles": "maison_bundle_export.csv"}
    planned = [str(output / name) for name in names.values()]
    if not args.dry_run:
        output.mkdir(parents=True, exist_ok=True)
        for kind, filename in names.items():
            with (output / filename).open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerow(contract_fields()[kind])
        manifest = build_sync_manifest(export_files=planned)
        (output / "maison_sync_manifest.json").write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n")
    print(json.dumps({"mode": "dry_run" if args.dry_run else "local_export_only", "files": planned}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
