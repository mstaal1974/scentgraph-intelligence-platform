from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from aromatwin.services.supplier_offer_importer import (
    detect_supplier_format,
    prepare_supplier_offer_frame,
    write_private_staging,
)


def fatma_frame() -> pd.DataFrame:
    return pd.DataFrame({"BRAND": ["ALL PRICE 1 KGS", "BRAND", "Fictional House", "Fictional House"],
                         "NAME": [None, "NAME", "Night Air", "Night Air"],
                         "CODE": [None, "CODE", "INTERNAL-1", "INTERNAL-1"],
                         "USD $": [None, "USD $", "12.50", "12.50"],
                         "AED": [None, "AED", "45", "45"]})


def test_fatma_detection_cleanup_mapping_and_private_fields() -> None:
    frame = fatma_frame()
    assert detect_supplier_format(frame) == "fatma"
    result = prepare_supplier_offer_frame(frame, "Private supplier", "fatma.csv")
    assert len(result.rows) == 2
    assert result.report["skipped_rows"] == 2
    row = result.rows[0]
    assert row.price_basis == "1kg"
    assert row.supplier_code_private == "INTERNAL-1"
    assert row.price_usd_private == Decimal("12.50")
    assert row.price_aed_private == Decimal("45")
    assert result.report["duplicate_rows"] == 2


def test_existing_format_and_quality_warnings() -> None:
    frame = pd.DataFrame({"BRAND NAME": ["House Scent", "House Other"], "ORI": ["House / Scent", None],
                          "CN CODE": ["PRIVATE", None], "QTY": [1, 2], "AED": [30, -2], "USD": [8, 1]})
    result = prepare_supplier_offer_frame(frame, "Supplier", "existing.csv")
    assert result.supplier_format == "existing_supplier"
    assert result.rows[0].supplier_reference_raw == "House / Scent"
    assert result.report["missing_code_rows"] == 1
    assert result.report["suspicious_price_rows"] == 1


def test_staging_rejects_public_path(tmp_path: Path) -> None:
    result = prepare_supplier_offer_frame(fatma_frame(), "Private supplier", "fatma.csv")
    with pytest.raises(ValueError, match="data/private"):
        write_private_staging(result, tmp_path / "public.json")


def test_public_samples_have_safe_headers() -> None:
    forbidden = {"code", "cn code", "qty", "aed", "usd", "usd $", "price", "cost", "stock",
                 "quantity", "supplier code", "commercial terms"}
    for name in ("supplier_offers_sample.csv", "fatma_supplier_sample.csv"):
        headers = {header.casefold().replace("_", " ") for header in pd.read_csv(
            Path("data/samples") / name, nrows=0).columns}
        assert not headers & forbidden
