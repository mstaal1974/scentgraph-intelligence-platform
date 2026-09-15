from pathlib import Path
import pandas as pd
import pytest
from scripts.validate_data import validate
from scentgraph.services.importer import duplicate_mask, prepare_supplier_csv


def supplier_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "brand_name": [" Example Brand ", "example brand", "Example Brand"],
            "fragrance_name": ["Example Scent", " example  scent ", "Example Scent"],
            "concentration": ["EDP", "eau de parfum", "EDT"],
            "product_type": ["spray"] * 3,
            "size_ml": [50] * 3,
            "sku": ["1", "2", "3"],
            "price": [10] * 3,
            "currency": ["GBP"] * 3,
            "source_reference": ["a", "b", "c"],
        }
    )


def test_duplicate_detection_respects_variants() -> None:
    assert duplicate_mask(supplier_frame()).tolist() == [True, True, False]


def test_supplier_header_validation(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    pd.DataFrame({"brand_name": ["Example"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing required headers"):
        prepare_supplier_csv(path, "test")


def test_repository_csv_headers_are_valid() -> None:
    assert validate(Path("data")) == []
