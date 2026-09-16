#!/usr/bin/env python3
"""Build public-safe Maison products, variants and optional default bundles."""

import argparse
import csv
import json
from pathlib import Path

from aromatwin.services.product_bundle_builder import ProductBundleBuilder
from aromatwin.services.product_catalogue import ProductCatalogueService
from aromatwin.services.product_variant_builder import ProductVariantBuilder


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(
            {
                key: json.dumps(value) if isinstance(value, list) else value
                for key, value in row.items()
            }
            for row in rows
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/generated/products"))
    parser.add_argument("--bundles", action="store_true")
    args = parser.parse_args()
    service = ProductCatalogueService(data_dir=args.data_dir)
    products = service.build()
    variants = ProductVariantBuilder().build(products)
    bundles = ProductBundleBuilder().build(products, variants) if args.bundles else []
    write_csv(args.output_dir / "products.csv", products)
    write_csv(args.output_dir / "variants.csv", variants)
    if args.bundles:
        write_csv(args.output_dir / "bundles.csv", bundles)
    print(
        f"accepted={len(products)} rejected={service.rejected_count} variants={len(variants)} bundles={len(bundles)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
