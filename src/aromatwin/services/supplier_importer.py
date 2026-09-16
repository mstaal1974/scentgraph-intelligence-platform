from collections import Counter
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid5

import pandas as pd

from aromatwin.services.normalisation import normalise_name, split_variant
from aromatwin.services.validation import validate_supplier_headers

SUPPORTED_SUFFIXES = {".csv", ".xls", ".xlsx"}
BATCH_NAMESPACE = UUID("b90482c8-d532-4c08-91ac-178960599b04")


@dataclass(frozen=True)
class SupplierRow:
    supplier_name: str
    supplier_brand_raw: str
    supplier_name_raw: str
    supplier_ori_raw: str | None
    supplier_cn_code: str | None
    quantity: Decimal | None
    aed_price: Decimal | None
    usd_price: Decimal | None
    source_file: str
    source_row_number: int
    import_batch_id: UUID
    normalised_brand: str
    normalised_name: str
    variant_marker: str | None
    status: str = "supplier_imported"
    is_duplicate: bool = False


@dataclass(frozen=True)
class SupplierImportResult:
    batch_id: UUID
    source_sha256: str
    rows: list[SupplierRow]
    report: dict[str, object]


@dataclass(frozen=True)
class SupplierBatchResult:
    batch_id: UUID
    batch_sha256: str
    rows: list[SupplierRow]
    report: dict[str, object]


class SupplierBatchValidationError(ValueError):
    def __init__(self, report: dict[str, object]):
        self.report = report
        super().__init__("Supplier batch validation failed")


def _is_missing(value: object) -> bool:
    missing = pd.isna(value)
    return bool(missing) if not hasattr(missing, "all") else bool(missing.all())


def _optional_text(value: object) -> str | None:
    if value is None or _is_missing(value) or not str(value).strip():
        return None
    return str(value).strip()


def _decimal(value: object) -> Decimal | None:
    if value is None or _is_missing(value) or not str(value).strip():
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except InvalidOperation as error:
        raise ValueError(f"Invalid numeric value: {value}") from error


def _normalise_headers(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {column: str(column).lstrip("\ufeff").strip().upper() for column in frame.columns}
    return frame.rename(columns=renamed)


def load_supplier_file(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    suffix = source.suffix.casefold()
    if suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(source, dtype=object)
    elif suffix == ".csv":
        frame = pd.read_csv(source, dtype=object)
    else:
        raise ValueError("Supplier input must be CSV, XLSX, or XLS")
    return _normalise_headers(frame).dropna(how="all")


def discover_supplier_files(directory: str | Path) -> list[Path]:
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f"Supplier import directory does not exist: {root}")
    files = sorted(
        path
        for path in root.iterdir()
        if path.is_file()
        and not path.name.startswith(".")
        and path.suffix.casefold() in SUPPORTED_SUFFIXES
    )
    if not files:
        raise ValueError(f"No supplier CSV or spreadsheet files found in: {root}")
    return files


def _row_key(row: SupplierRow) -> tuple[str, str, str | None]:
    return (row.normalised_brand.casefold(), row.normalised_name.casefold(), row.variant_marker)


def prepare_supplier_frame(
    frame: pd.DataFrame,
    supplier_name: str,
    source_file: str,
    batch_id: UUID | None = None,
    source_sha256: str | None = None,
) -> SupplierImportResult:
    frame = _normalise_headers(frame).dropna(how="all")
    validate_supplier_headers(frame.columns)
    digest = source_sha256 or sha256(frame.to_csv(index=False).encode()).hexdigest()
    current_batch_id = batch_id or uuid5(BATCH_NAMESPACE, f"{supplier_name}:{digest}")
    rows: list[SupplierRow] = []
    for row_number, record in zip(
        frame.index.to_list(), frame.to_dict(orient="records"), strict=True
    ):
        raw_brand = _optional_text(record["BRAND"])
        raw_name = _optional_text(record["NAME"])
        if not raw_brand or not raw_name:
            raise ValueError(f"{source_file}:{int(row_number) + 2}: BRAND and NAME are required")
        clean_name, variant = split_variant(raw_name)
        rows.append(
            SupplierRow(
                supplier_name=supplier_name,
                supplier_brand_raw=raw_brand,
                supplier_name_raw=raw_name,
                supplier_ori_raw=_optional_text(record["ORI"]),
                supplier_cn_code=_optional_text(record["CN CODE"]),
                quantity=_decimal(record["QTY"]),
                aed_price=_decimal(record["AED"]),
                usd_price=_decimal(record["USD"]),
                source_file=source_file,
                source_row_number=int(row_number) + 2,
                import_batch_id=current_batch_id,
                normalised_brand=normalise_name(raw_brand),
                normalised_name=clean_name,
                variant_marker=variant,
            )
        )
    counts = Counter(_row_key(row) for row in rows)
    rows = [replace(row, is_duplicate=counts[_row_key(row)] > 1) for row in rows]
    report = {
        "source_file": source_file,
        "source_sha256": digest,
        "rows": len(rows),
        "duplicate_rows": sum(row.is_duplicate for row in rows),
        "variant_rows": sum(row.variant_marker is not None for row in rows),
        "status": "supplier_imported",
        "catalogue_promotion_allowed": False,
        "warnings": [],
    }
    return SupplierImportResult(current_batch_id, digest, rows, report)


def prepare_supplier_file(
    path: str | Path, supplier_name: str, batch_id: UUID | None = None
) -> SupplierImportResult:
    source = Path(path)
    digest = sha256(source.read_bytes()).hexdigest()
    stable_batch_id = batch_id or uuid5(BATCH_NAMESPACE, f"{supplier_name}:{digest}")
    return prepare_supplier_frame(
        load_supplier_file(source), supplier_name, source.name, stable_batch_id, digest
    )


def prepare_supplier_directory(directory: str | Path, supplier_name: str) -> SupplierBatchResult:
    root = Path(directory)
    files = discover_supplier_files(root)
    fingerprints = [(path, sha256(path.read_bytes()).hexdigest()) for path in files]
    manifest = "\n".join(f"{path.name}:{digest}" for path, digest in fingerprints)
    batch_digest = sha256(manifest.encode()).hexdigest()
    batch_id = uuid5(BATCH_NAMESPACE, f"{supplier_name}:{root.name}:{batch_digest}")
    results: list[SupplierImportResult] = []
    errors: list[dict[str, str]] = []
    for path, _ in fingerprints:
        try:
            results.append(prepare_supplier_file(path, supplier_name, batch_id))
        except (ValueError, OSError) as error:
            errors.append({"source_file": path.name, "message": str(error)})

    rows = [row for result in results for row in result.rows]
    counts = Counter(_row_key(row) for row in rows)
    rows = [replace(row, is_duplicate=counts[_row_key(row)] > 1) for row in rows]
    report: dict[str, object] = {
        "supplier_name": supplier_name,
        "source_directory": root.as_posix(),
        "batch_id": str(batch_id),
        "batch_sha256": batch_digest,
        "files": [result.report for result in results],
        "file_count": len(files),
        "validated_file_count": len(results),
        "rows": len(rows),
        "duplicate_rows": sum(row.is_duplicate for row in rows),
        "variant_rows": sum(row.variant_marker is not None for row in rows),
        "status": "validation_failed" if errors else "supplier_imported",
        "catalogue_promotion_allowed": False,
        "next_step": None if errors else "candidate_matching",
        "errors": errors,
    }
    if errors:
        raise SupplierBatchValidationError(report)
    return SupplierBatchResult(batch_id, batch_digest, rows, report)
