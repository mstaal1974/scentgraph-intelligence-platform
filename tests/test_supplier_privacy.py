import csv
import subprocess
from pathlib import Path

import pytest

from aromatwin.services.supplier_privacy import validate_public_supplier_sample
from scripts.audit_supplier_data import audit, exposed_sample_columns

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data/samples/supplier_identity_sample.csv"
SENSITIVE_COLUMNS = {
    "AED",
    "USD",
    "QTY",
    "QUANTITY",
    "CN CODE",
    "COST",
    "PRICE",
    "SKU",
    "SUPPLIER CODE",
}


def test_public_supplier_sample_contains_no_pricing_or_supplier_codes() -> None:
    with SAMPLE.open(newline="", encoding="utf-8") as handle:
        headers = {header.strip().upper() for header in next(csv.reader(handle))}
    assert headers == {"BRAND", "NAME", "ORI"}
    assert headers.isdisjoint(SENSITIVE_COLUMNS)
    assert validate_public_supplier_sample(SAMPLE) == headers


@pytest.mark.parametrize(
    "relative_path",
    [
        "data/private/imports/supplier-2026-04-26/prices.xlsx",
        "data/private/staging/supplier-2026-04-26.json",
        "private/supplier/prices.csv",
    ],
)
def test_private_supplier_paths_are_gitignored(relative_path: str) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", relative_path],
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, f"Expected Git to ignore {relative_path}"


def test_supplier_privacy_audit_passes_for_tracked_repository() -> None:
    assert audit(ROOT) == []


def test_product_variant_sku_exception_is_narrow() -> None:
    headers = {"SKU", "SUPPLIER_CODE", "PRICE"}
    assert exposed_sample_columns("data/samples/product_variants_sample.csv", headers) == {
        "PRICE",
        "SUPPLIER CODE",
    }
    assert exposed_sample_columns("data/samples/supplier_sample.csv", headers) == {
        "PRICE",
        "SKU",
        "SUPPLIER CODE",
    }
