from decimal import Decimal
import pandas as pd
import pytest
from aromatwin.services.supplier_importer import prepare_supplier_frame


def supplier_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "BRAND": [" Example Brand ", "example brand", "Example Brand"],
            "NAME": ["Example Scent SUPER", " example scent super ", "Example Scent LZ"],
            "ORI": ["Original Brand / Original Scent"] * 3,
            "CN CODE": ["A", "B", "C"],
            "QTY": [10, 5, 2],
            "AED": [100, 100, 120],
            "USD": [Decimal("27.23")] * 3,
        }
    )


def test_supplier_row_import_preserves_raw_fields() -> None:
    result = prepare_supplier_frame(supplier_frame(), "Supplier A", "supplier.csv")
    row = result.rows[0]
    assert row.supplier_brand_raw == "Example Brand"
    assert row.supplier_ori_raw == "Original Brand / Original Scent"
    assert row.variant_marker == "SUPER"
    assert row.status == "supplier_imported"
    assert result.report["variant_rows"] == 3


def test_duplicate_detection_includes_variant() -> None:
    result = prepare_supplier_frame(supplier_frame(), "Supplier A", "supplier.csv")
    assert [row.is_duplicate for row in result.rows] == [True, True, False]


def test_supplier_csv_header_validation() -> None:
    with pytest.raises(ValueError, match="Missing required supplier headers"):
        prepare_supplier_frame(pd.DataFrame({"BRAND": ["Example"]}), "Supplier A", "bad.csv")


def test_directory_import_uses_one_stable_batch_and_cross_file_duplicates(tmp_path) -> None:
    from aromatwin.services.supplier_importer import prepare_supplier_directory

    first = supplier_frame().iloc[[0]]
    second = supplier_frame().iloc[[1, 2]]
    first.to_csv(tmp_path / "a.csv", index=False)
    second.to_csv(tmp_path / "b.csv", index=False)
    (tmp_path / "README.md").write_text("not source data", encoding="utf-8")

    result = prepare_supplier_directory(tmp_path, "Supplier A")
    rerun = prepare_supplier_directory(tmp_path, "Supplier A")

    assert result.batch_id == rerun.batch_id
    assert result.batch_sha256 == rerun.batch_sha256
    assert {row.import_batch_id for row in result.rows} == {result.batch_id}
    assert [row.is_duplicate for row in result.rows] == [True, True, False]
    assert result.report["file_count"] == 2
    assert result.report["catalogue_promotion_allowed"] is False
    assert result.report["next_step"] == "candidate_matching"


def test_directory_import_rejects_directory_without_source_files(tmp_path) -> None:
    from aromatwin.services.supplier_importer import prepare_supplier_directory

    (tmp_path / "README.md").write_text("documentation only", encoding="utf-8")
    with pytest.raises(ValueError, match="No supplier CSV or spreadsheet files"):
        prepare_supplier_directory(tmp_path, "Supplier A")


def test_directory_validation_reports_bad_files_without_partial_staging(tmp_path) -> None:
    from aromatwin.services.supplier_importer import (
        SupplierBatchValidationError,
        prepare_supplier_directory,
    )

    supplier_frame().iloc[[0]].to_csv(tmp_path / "valid.csv", index=False)
    pd.DataFrame({"BRAND": ["Missing fields"]}).to_csv(tmp_path / "invalid.csv", index=False)

    with pytest.raises(SupplierBatchValidationError) as captured:
        prepare_supplier_directory(tmp_path, "Supplier A")

    report = captured.value.report
    assert report["status"] == "validation_failed"
    assert report["catalogue_promotion_allowed"] is False
    assert report["next_step"] is None
    assert report["errors"][0]["source_file"] == "invalid.csv"
