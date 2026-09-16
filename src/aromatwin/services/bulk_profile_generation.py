"""Review-only bulk profile drafting from private supplier identity data."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from aromatwin.services.normalisation import normalise_name
from aromatwin.services.profile_builder import draft_description

PRIVATE_ROOT = Path("data/private")
MISSING_PROFILE_FIELDS = (
    "notes",
    "accords",
    "moods",
    "seasons",
    "occasions",
    "projection",
    "longevity",
)


def _value(record: object, *names: str, default: Any = None) -> Any:
    for name in names:
        value = record.get(name) if isinstance(record, Mapping) else getattr(record, name, None)
        if value is not None and str(value).strip():
            return value
    return default


def _clean(value: object | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _identity(record: object) -> tuple[str, str, str]:
    brand = _clean(_value(record, "candidate_brand", "canonical_brand", "normalised_brand",
                          "supplier_brand_raw", "brand"))
    name = _clean(_value(record, "candidate_fragrance_name", "canonical_fragrance_name",
                         "normalised_name", "supplier_name_raw", "fragrance_name", "name"))
    reference = _clean(_value(record, "candidate_reference", "normalised_reference",
                              "supplier_reference_raw", "reference"))
    return normalise_name(brand), normalise_name(name), normalise_name(reference)


def _record_id(record: object, prefix: str, ordinal: int) -> str:
    value = _value(record, "id", f"{prefix}_id", "supplier_offer_id", "match_candidate_id")
    if value is not None:
        return str(value)
    digest = sha256("|".join(_identity(record)).encode()).hexdigest()[:12]
    return f"{prefix}-{digest}-{ordinal}"


@dataclass(frozen=True)
class BulkProfileDraft:
    profile_draft_id: str
    supplier_offer_ids: list[str]
    match_candidate_ids: list[str]
    canonical_brand: str
    canonical_fragrance_name: str
    concentration: str | None
    candidate_reference: str | None
    draft_description: str
    provenance_notes: str
    source_confidence: float
    confidence_reason: str
    missing_profile_fields: list[str]
    enrichment_needed: bool
    review_status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class BulkGenerationOutcome:
    drafts: list[BulkProfileDraft]
    accepted_count: int
    rejected_count: int
    unique_candidate_count: int
    skipped_duplicate_count: int


def _key(record: object) -> tuple[str, str, str]:
    """Use reference when present without allowing its absence to split an identity."""
    return _identity(record)


def generate_bulk_profile_drafts(
    supplier_offers: Iterable[object],
    match_candidates: Iterable[object] = (),
    existing_drafts: Iterable[object] = (),
    *,
    now: datetime | None = None,
) -> BulkGenerationOutcome:
    """Collapse offer rows into unique identities and create safe, unapproved drafts."""
    offers = list(supplier_offers)
    matches = list(match_candidates)
    groups: dict[tuple[str, str, str], list[tuple[int, object]]] = {}
    rejected = 0
    for index, offer in enumerate(offers, 1):
        key = _key(offer)
        if not key[0] or not key[1]:
            rejected += 1
            continue
        # Reference-less Fatma offers join an already-known brand/name group.
        compatible = next((candidate for candidate in groups
                           if candidate[:2] == key[:2] and (not key[2] or not candidate[2])), None)
        groups.setdefault(compatible or key, []).append((index, offer))

    existing_keys = {_key(item) for item in existing_drafts}
    timestamp = now or datetime.now(UTC)
    drafts: list[BulkProfileDraft] = []
    duplicate_rows = sum(max(0, len(group) - 1) for group in groups.values())
    for key, group in groups.items():
        if key in existing_keys or any(old[:2] == key[:2] for old in existing_keys):
            duplicate_rows += len(group)
            continue
        related_matches = [item for item in matches if _key(item)[:2] == key[:2]]
        first = group[0][1]
        brand = _clean(_value(first, "candidate_brand", "canonical_brand", "supplier_brand_raw",
                              "normalised_brand", "brand"))
        name = _clean(_value(first, "candidate_fragrance_name", "canonical_fragrance_name",
                             "supplier_name_raw", "normalised_name", "fragrance_name", "name"))
        reference = _clean(_value(first, "candidate_reference", "supplier_reference_raw",
                                  "normalised_reference", "reference")) or None
        concentrations = {_clean(_value(item, "candidate_concentration", "concentration"))
                          for item in related_matches}
        concentration = next(iter(concentrations - {""}), None)
        offer_ids = [_record_id(item, "offer", ordinal) for ordinal, item in group]
        match_ids = [_record_id(item, "match", i) for i, item in enumerate(related_matches, 1)]
        match_confidences = [float(_value(item, "match_confidence", "source_confidence", default=0))
                             for item in related_matches]
        if reference and match_confidences:
            confidence = min(0.95, max(match_confidences))
            reason = "Reference and match-candidate identity are available; human verification remains required."
        elif reference:
            confidence = 0.65
            reason = "Supplier reference supports identity, but no reviewed match candidate is available."
        else:
            confidence = min(0.55, max(match_confidences, default=0.5))
            reason = "ORI/reference is missing (including Fatma-format offers); confidence is reduced."
        digest = sha256("|".join(key).encode()).hexdigest()[:16]
        drafts.append(BulkProfileDraft(
            profile_draft_id=f"bpd-{digest}", supplier_offer_ids=offer_ids,
            match_candidate_ids=match_ids, canonical_brand=brand,
            canonical_fragrance_name=name, concentration=concentration,
            candidate_reference=reference, draft_description=draft_description(brand, name),
            provenance_notes=("Generated only from supplier identity fields and safe match metadata; "
                              "no supplier commercial data or third-party descriptive content was used."),
            source_confidence=round(confidence, 2), confidence_reason=reason,
            missing_profile_fields=list(MISSING_PROFILE_FIELDS), enrichment_needed=True,
            review_status="needs_human_review", created_at=timestamp, updated_at=timestamp,
        ))
    return BulkGenerationOutcome(drafts, len(drafts), rejected, len(groups), duplicate_rows)


def public_safe_draft(draft: BulkProfileDraft) -> dict[str, object]:
    """Return the default API representation, deliberately omitting private link IDs."""
    data = asdict(draft)
    data.pop("supplier_offer_ids", None)
    data.pop("match_candidate_ids", None)
    data.pop("candidate_reference", None)
    return data


def load_records(path: str | Path) -> list[dict[str, object]]:
    source = Path(path)
    if source.suffix.casefold() == ".json":
        value = json.loads(source.read_text())
        return value if isinstance(value, list) else value.get(
            "items", value.get("drafts", value.get("records", []))
        )
    if source.suffix.casefold() == ".csv":
        import csv
        with source.open(newline="") as handle:
            return list(csv.DictReader(handle))
    raise ValueError("Bulk profile inputs must be JSON or CSV")


def write_private_drafts(drafts: Iterable[BulkProfileDraft], output: str | Path) -> None:
    destination = Path(output)
    if PRIVATE_ROOT.resolve() not in destination.resolve().parents:
        raise ValueError("Operational profile drafts must be written under data/private/")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps([asdict(item) for item in drafts], default=str, indent=2) + "\n")
