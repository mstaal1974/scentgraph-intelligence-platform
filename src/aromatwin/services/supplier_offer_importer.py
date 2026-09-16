"""Private multi-supplier offer ingestion with public-safe reporting."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

import pandas as pd

from aromatwin.services.normalisation import normalise_name, split_variant

FORMATS = {"auto", "existing_supplier", "fatma"}
PRIVATE_ROOT = Path("data/private")


@dataclass(frozen=True)
class SupplierOffer:
    supplier_name: str
    supplier_file_reference: str
    supplier_file_hash: str
    supplier_row_number: int
    supplier_brand_raw: str
    supplier_name_raw: str
    supplier_reference_raw: str | None
    supplier_code_private: str | None
    supplier_cn_code_private: str | None
    supplier_unit: str | None
    quantity_private: Decimal | None
    price_aed_private: Decimal | None
    price_usd_private: Decimal | None
    currency: str | None
    price_basis: str | None
    normalised_brand: str
    normalised_name: str
    normalised_reference: str | None
    candidate_brand: str | None = None
    candidate_fragrance_name: str | None = None
    linked_match_candidate_id: int | None = None
    linked_catalogue_fragrance_id: int | None = None
    offer_status: str = "active"
    confidence_score: float | None = None
    review_status: str = "supplier_offer_imported"
    private_notes: str | None = None
    is_duplicate: bool = False
    is_likely_variant: bool = False
    suspicious_price: bool = False


@dataclass(frozen=True)
class SupplierOfferImport:
    supplier_format: str
    rows: list[SupplierOffer]
    report: dict[str, object]


def _headers(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns={c: str(c).lstrip("\ufeff").strip().upper() for c in frame.columns})


def detect_supplier_format(frame: pd.DataFrame) -> str:
    columns = set(_headers(frame).columns)
    if {"BRAND", "NAME", "CODE", "USD $", "AED"} <= columns:
        return "fatma"
    if {"BRAND NAME", "ORI", "CN CODE", "QTY", "AED", "USD"} <= columns:
        return "existing_supplier"
    # Preserve compatibility with the foundation's split BRAND/NAME variant.
    if {"BRAND", "NAME", "ORI", "CN CODE", "QTY", "AED", "USD"} <= columns:
        return "existing_supplier"
    raise ValueError("Unrecognised supplier format")


def _text(value: object) -> str | None:
    if value is None or pd.isna(value) or not str(value).strip():
        return None
    return str(value).strip()


def _decimal(value: object) -> Decimal | None:
    text = _text(value)
    if text is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", text.replace(",", ""))
    try:
        return Decimal(cleaned) if cleaned else None
    except InvalidOperation:
        return None


def _section_basis(record: dict[str, object]) -> str | None:
    content = " ".join(str(value) for value in record.values() if _text(value))
    match = re.search(r"ALL\s+PRICE\s+(\d+)\s*KGS?", content, re.IGNORECASE)
    return f"{match.group(1)}kg" if match else None


def _is_repeated_header(record: dict[str, object]) -> bool:
    values = {str(value).strip().upper() for value in record.values() if _text(value)}
    return bool(values & {"BRAND", "NAME", "CODE", "USD $", "BRAND NAME", "CN CODE", "QTY"}) and (
        "BRAND" in values or "BRAND NAME" in values
    )


def prepare_supplier_offer_frame(
    frame: pd.DataFrame,
    supplier_name: str,
    source_file: str,
    supplier_format: str = "auto",
    source_hash: str | None = None,
) -> SupplierOfferImport:
    if supplier_format not in FORMATS:
        raise ValueError(f"supplier_format must be one of {sorted(FORMATS)}")
    frame = _headers(frame).dropna(how="all")
    detected = detect_supplier_format(frame) if supplier_format == "auto" else supplier_format
    digest = source_hash or sha256(frame.to_csv(index=False).encode()).hexdigest()
    rows: list[SupplierOffer] = []
    basis: str | None = None
    skipped = 0
    for index, record in zip(frame.index, frame.to_dict(orient="records"), strict=True):
        section = _section_basis(record)
        if section:
            basis = section
            skipped += 1
            continue
        if _is_repeated_header(record):
            skipped += 1
            continue
        if detected == "fatma":
            brand, name = _text(record.get("BRAND")), _text(record.get("NAME"))
            code, cn, reference, quantity = _text(record.get("CODE")), None, None, None
            usd, aed = _decimal(record.get("USD $")), _decimal(record.get("AED"))
        else:
            combined = _text(record.get("BRAND NAME"))
            brand = _text(record.get("BRAND")) or combined
            name = _text(record.get("NAME")) or combined
            code, cn = None, _text(record.get("CN CODE"))
            reference, quantity = _text(record.get("ORI")), _decimal(record.get("QTY"))
            usd, aed = _decimal(record.get("USD")), _decimal(record.get("AED"))
        if not brand or not name:
            skipped += 1
            continue
        clean_name, variant = split_variant(name)
        suspicious = any(value is not None and (value <= 0 or value > 1_000_000) for value in (usd, aed))
        rows.append(SupplierOffer(
            supplier_name=supplier_name, supplier_file_reference=source_file,
            supplier_file_hash=digest, supplier_row_number=int(index) + 2,
            supplier_brand_raw=brand, supplier_name_raw=name,
            supplier_reference_raw=reference, supplier_code_private=code,
            supplier_cn_code_private=cn, supplier_unit=None, quantity_private=quantity,
            price_aed_private=aed, price_usd_private=usd, currency=None,
            price_basis=basis, normalised_brand=normalise_name(brand),
            normalised_name=clean_name, normalised_reference=normalise_name(reference) if reference else None,
            is_likely_variant=variant is not None, suspicious_price=suspicious,
            private_notes="missing supplier code" if not (code or cn) else None,
        ))
    keys = Counter((r.supplier_name.casefold(), r.normalised_brand, r.normalised_name,
                    r.supplier_reference_raw, r.supplier_code_private, r.supplier_cn_code_private,
                    r.quantity_private, r.price_aed_private, r.price_usd_private) for r in rows)
    rows = [replace(r, is_duplicate=keys[(r.supplier_name.casefold(), r.normalised_brand,
             r.normalised_name, r.supplier_reference_raw, r.supplier_code_private,
             r.supplier_cn_code_private, r.quantity_private, r.price_aed_private,
             r.price_usd_private)] > 1,
             review_status="rejected_duplicate" if keys[(r.supplier_name.casefold(),
             r.normalised_brand, r.normalised_name, r.supplier_reference_raw,
             r.supplier_code_private, r.supplier_cn_code_private, r.quantity_private,
             r.price_aed_private, r.price_usd_private)] > 1 else "supplier_offer_imported") for r in rows]
    warnings = []
    missing = sum(not (r.supplier_code_private or r.supplier_cn_code_private) for r in rows)
    suspicious = sum(r.suspicious_price for r in rows)
    if missing:
        warnings.append(f"{missing} row(s) have no supplier code")
    if suspicious:
        warnings.append(f"{suspicious} row(s) have suspicious prices")
    report = {"supplier_name": supplier_name, "supplier_format": detected,
              "source_file": source_file, "source_sha256": digest, "rows": len(rows),
              "skipped_rows": skipped, "duplicate_rows": sum(r.is_duplicate for r in rows),
              "variant_rows": sum(r.is_likely_variant for r in rows), "missing_code_rows": missing,
              "suspicious_price_rows": suspicious, "warnings": warnings,
              "catalogue_promotion_allowed": False}
    return SupplierOfferImport(detected, rows, report)


def prepare_supplier_offer_file(path: str | Path, supplier_name: str,
                                supplier_format: str = "auto") -> SupplierOfferImport:
    source = Path(path)
    if source.suffix.casefold() != ".csv":
        raise ValueError("Supplier offer input must be CSV")
    return prepare_supplier_offer_frame(pd.read_csv(source, dtype=object), supplier_name,
                                        source.name, supplier_format, sha256(source.read_bytes()).hexdigest())


def write_private_staging(result: SupplierOfferImport, output: Path) -> None:
    resolved = output.resolve()
    if PRIVATE_ROOT.resolve() not in resolved.parents:
        raise ValueError("Private supplier offer staging must be under data/private/")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([asdict(row) for row in result.rows], default=str, indent=2) + "\n")
