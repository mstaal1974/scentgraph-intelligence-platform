from dataclasses import dataclass

from aromatwin.services.normalisation import parse_original_hint
from aromatwin.services.supplier_importer import SupplierRow


@dataclass(frozen=True)
class CandidateMatch:
    supplier_item_id: int | None
    candidate_brand: str
    candidate_fragrance_name: str
    candidate_source_type: str
    candidate_source_reference: str | None
    match_method: str
    match_confidence: float
    review_status: str = "match_candidate"
    candidate_concentration: str | None = None
    match_notes: str | None = None


def candidate_from_supplier(
    row: SupplierRow, supplier_item_id: int | None = None
) -> CandidateMatch:
    hint_brand, hint_name = parse_original_hint(row.supplier_ori_raw)
    brand = hint_brand or row.normalised_brand
    name = hint_name or row.normalised_name
    confidence = 0.75 if hint_brand and hint_name else 0.45
    return CandidateMatch(
        supplier_item_id,
        brand,
        name,
        "supplier_source",
        f"{row.source_file}:{row.source_row_number}",
        "supplier_original_hint" if row.supplier_ori_raw else "normalised_supplier_name",
        confidence,
        match_notes="Hypothesis only; independent verification required",
    )


def candidate_from_reference(
    *, supplier_item_id: int, candidate_brand: str, candidate_name: str, source_reference: str
) -> CandidateMatch:
    return CandidateMatch(
        supplier_item_id,
        candidate_brand,
        candidate_name,
        "reference_only",
        source_reference,
        "reference_identifier_match",
        0.6,
        match_notes="Reference-only identifier; content may not be promoted",
    )
