#!/usr/bin/env python3
"""Export allowlisted Maison storefront product data; never copies arbitrary input fields."""

import csv
import json
from pathlib import Path

from aromatwin.schemas.product_catalogue import (
    ProductBundlePublicRead,
    ProductCataloguePublicRead,
    ProductVariantPublicRead,
)
from aromatwin.services.product_bundle_builder import ProductBundleBuilder
from aromatwin.services.product_catalogue import ProductCatalogueService
from aromatwin.services.product_variant_builder import ProductVariantBuilder


def write(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
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
    products = ProductCatalogueService().build()
    variants = ProductVariantBuilder().build(products)
    bundles = ProductBundleBuilder().build(products, variants)
    exports = (
        (
            Path("data/maison_product_catalogue_export.csv"),
            [
                ProductCataloguePublicRead.model_validate(x).model_dump(mode="json")
                for x in products
            ],
        ),
        (
            Path("data/maison_product_variants_export.csv"),
            [ProductVariantPublicRead.model_validate(x).model_dump(mode="json") for x in variants],
        ),
        (
            Path("data/maison_product_bundles_export.csv"),
            [ProductBundlePublicRead.model_validate(x).model_dump(mode="json") for x in bundles],
        ),
    )
    for path, rows in exports:
        write(path, rows)
    print(" ".join(f"{path}={len(rows)}" for path, rows in exports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
