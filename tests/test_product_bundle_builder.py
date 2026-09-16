import csv
from pathlib import Path

from aromatwin.services.product_bundle_builder import BUNDLE_TYPES, ProductBundleBuilder
from aromatwin.services.product_variant_builder import ProductVariantBuilder


def test_all_public_safe_bundle_types_and_samples():
    products = [
        {
            "product_id": "p1",
            "brand_name": "Fiction",
            "fragrance_name": "Orbit",
            "product_title": "Fiction Orbit",
        }
    ]
    variants = ProductVariantBuilder().build(products)
    bundles = ProductBundleBuilder().build(products, variants)
    assert {item["bundle_type"] for item in bundles} == set(BUNDLE_TYPES)
    forbidden = {
        "supplier_price",
        "supplier_cost",
        "margin",
        "supplier_code",
        "cn_code",
        "quantity",
        "stock",
        "aed",
        "usd",
        "commercial_terms",
    }
    assert all(not (forbidden & item.keys()) for item in bundles)
    for path in Path("data/samples").glob("product_*_sample.csv"):
        with path.open(encoding="utf-8") as stream:
            assert not (forbidden & set(next(csv.reader(stream))))
