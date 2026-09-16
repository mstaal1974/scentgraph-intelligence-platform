"""Private supplier ranking and deliberately non-commercial summaries."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from aromatwin.services.supplier_offer_importer import SupplierOffer

PRIVATE_ROOT = Path("data/private")


@dataclass(frozen=True)
class SourcingDecision:
    id: str
    catalogue_fragrance_id: int | None
    match_candidate_id: int | None
    fragrance_title: str
    supplier_name: str
    supplier_offer_id: str
    supplier_match_confidence: float
    supplier_price_confidence: float
    availability_status: str
    price_basis: str | None
    internal_rank: int
    sourcing_recommendation: str
    sourcing_reason: str
    risk_flags: list[str]
    review_status: str
    created_at: datetime
    updated_at: datetime
    # These fields are never emitted by public_safe_decision.
    supplier_price_private: Decimal | None = None
    supplier_code_private: str | None = None
    supplier_cn_code_private: str | None = None
    quantity_private: Decimal | None = None


def load_private_supplier_offers(path: str | Path) -> list[SupplierOffer]:
    """Load importer JSON, rejecting paths outside the private data tree."""
    source = Path(path).resolve()
    if PRIVATE_ROOT.resolve() not in source.parents:
        raise ValueError("Supplier offers must be read from data/private/")
    payload = json.loads(source.read_text())
    return [SupplierOffer(**{**row, **{
        field: Decimal(str(row[field])) if row.get(field) is not None else None
        for field in ("quantity_private", "price_aed_private", "price_usd_private")
    }}) for row in payload]


def grouping_key(offer: SupplierOffer) -> tuple[str, int | str]:
    if offer.linked_catalogue_fragrance_id is not None:
        return ("catalogue", offer.linked_catalogue_fragrance_id)
    if offer.linked_match_candidate_id is not None:
        return ("candidate", offer.linked_match_candidate_id)
    return ("unlinked", f"{offer.normalised_brand}|{offer.normalised_name}")


def group_supplier_offers(offers: list[SupplierOffer]) -> dict[tuple[str, int | str], list[SupplierOffer]]:
    grouped: dict[tuple[str, int | str], list[SupplierOffer]] = defaultdict(list)
    for offer in offers:
        grouped[grouping_key(offer)].append(offer)
    return dict(grouped)


def _price(offer: SupplierOffer) -> Decimal | None:
    return offer.price_usd_private if offer.price_usd_private is not None else offer.price_aed_private


def _duplicate_keys(offers: list[SupplierOffer]) -> set[tuple[object, ...]]:
    keys = [(o.supplier_name.casefold(), grouping_key(o), o.supplier_code_private,
             o.supplier_cn_code_private, _price(o), o.quantity_private) for o in offers]
    counts = Counter(keys)
    return {key for key, count in counts.items() if count > 1}


def _risk_flags(offer: SupplierOffer, duplicates: set[tuple[object, ...]]) -> list[str]:
    flags: list[str] = []
    key = (offer.supplier_name.casefold(), grouping_key(offer), offer.supplier_code_private,
           offer.supplier_cn_code_private, _price(offer), offer.quantity_private)
    if offer.is_duplicate or key in duplicates:
        flags.append("duplicate_offer")
    if not (offer.supplier_code_private or offer.supplier_cn_code_private):
        flags.append("missing_supplier_code")
    price = _price(offer)
    if offer.suspicious_price or price is not None and (price <= 0 or price > Decimal("1000000")):
        flags.append("suspicious_price")
    if (offer.confidence_score or 0) < 0.7:
        flags.append("low_match_confidence")
    return flags


def build_sourcing_decisions(offers: list[SupplierOffer]) -> list[SourcingDecision]:
    """Rank each identity group; price affects rank but remains private."""
    now = datetime.now(UTC)
    duplicates = _duplicate_keys(offers)
    decisions: list[SourcingDecision] = []
    for grouped in group_supplier_offers(offers).values():
        def score(item: SupplierOffer) -> tuple[object, ...]:
            price = _price(item)
            available = item.offer_status.casefold() in {"active", "available", "in_stock"}
            return (not available, -float(item.confidence_score or 0),
                    price is None, price or Decimal("Infinity"), item.supplier_name.casefold())

        ranked = sorted(grouped, key=score)
        for rank, offer in enumerate(ranked, 1):
            flags = _risk_flags(offer, duplicates)
            recommended = rank == 1 and not {"duplicate_offer", "suspicious_price"} & set(flags)
            title = offer.candidate_fragrance_name or offer.supplier_name_raw
            decisions.append(SourcingDecision(
                id=str(uuid4()), catalogue_fragrance_id=offer.linked_catalogue_fragrance_id,
                match_candidate_id=offer.linked_match_candidate_id, fragrance_title=title,
                supplier_name=offer.supplier_name,
                supplier_offer_id=f"{offer.supplier_file_hash[:12]}:{offer.supplier_row_number}",
                supplier_match_confidence=float(offer.confidence_score or 0),
                supplier_price_confidence=0.9 if _price(offer) is not None and "suspicious_price" not in flags else 0.2,
                availability_status=offer.offer_status, price_basis=offer.price_basis,
                internal_rank=rank, sourcing_recommendation="preferred_candidate" if recommended else "review",
                sourcing_reason="Highest eligible internal ranking" if recommended else "Risk or lower-ranked offer requires review",
                risk_flags=flags, review_status="pending_review", created_at=now, updated_at=now,
                supplier_price_private=_price(offer),
                supplier_code_private=offer.supplier_code_private,
                supplier_cn_code_private=offer.supplier_cn_code_private,
                quantity_private=offer.quantity_private,
            ))
    return decisions


def public_safe_decision(decision: SourcingDecision) -> dict[str, object]:
    """Return an allowlisted summary with no supplier identity or commercial values."""
    return {
        "id": decision.id,
        "catalogue_fragrance_id": decision.catalogue_fragrance_id,
        "match_candidate_id": decision.match_candidate_id,
        "fragrance_title": decision.fragrance_title,
        "availability_status": "available" if decision.availability_status.casefold() in {"active", "available", "in_stock"} else "review",
        "sourcing_recommendation": decision.sourcing_recommendation,
        "risk_flags": decision.risk_flags,
        "review_status": decision.review_status,
        "confidence_score": decision.supplier_match_confidence,
        "public_safe_summary": "An internal supplier candidate is available for review.",
        "created_at": decision.created_at,
        "updated_at": decision.updated_at,
    }


def private_decision_dict(decision: SourcingDecision) -> dict[str, object]:
    return asdict(decision)


def audit_offers(offers: list[SupplierOffer]) -> dict[str, int | bool]:
    decisions = build_sourcing_decisions(offers)
    counts = Counter(flag for decision in decisions for flag in decision.risk_flags)
    return {"passed": not counts, "checked_offer_count": len(offers),
            "duplicate_offer_count": counts["duplicate_offer"],
            "missing_code_count": counts["missing_supplier_code"],
            "suspicious_price_count": counts["suspicious_price"],
            "low_confidence_count": counts["low_match_confidence"]}
