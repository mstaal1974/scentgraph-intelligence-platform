from pathlib import Path

from aromatwin.services.private_supplier_intake import PrivateSupplierIntakeService


def test_intake_accepts_supported_private_files_and_rejects_public(tmp_path: Path):
    data = tmp_path / "data"
    private = data / "private/imports/suppliers/demo"
    private.mkdir(parents=True)
    for suffix in ("csv", "xlsx", "xls"):
        path = private / f"offer.{suffix}"
        if suffix == "csv":
            path.write_text("brand,product_name\nFictional,Example\n")
        else:
            # Inspection of an empty workbook-shaped file safely blocks but recognises its type.
            path.write_bytes(b"not a workbook")
    service = PrivateSupplierIntakeService(data)
    results = service.scan()
    assert {item.file_type for item in results} == {"csv", "xls", "xlsx"}
    assert next(item for item in results if item.file_type == "csv").readiness_status == "ready_for_import"
    public = data / "samples/example.csv"
    public.parent.mkdir()
    public.write_text("brand,product_name\nFictional,Example\n")
    assert service.inspect(public).readiness_status == "blocked_outside_private_path"


def test_unknown_and_unsupported_are_blocked(tmp_path: Path):
    root = tmp_path / "data/private/imports"
    root.mkdir(parents=True)
    (root / "unknown.csv").write_text("unmapped,value\na,b\n")
    (root / "offer.pdf").write_bytes(b"fictional")
    statuses = {item.file_type: item.readiness_status
                for item in PrivateSupplierIntakeService(tmp_path / "data").scan()}
    assert statuses["csv"] == "needs_format_mapping"
    assert statuses["pdf"] == "blocked_unsupported_file_type"
