"""Match commercial offers to records that already exist; never create catalogue data."""

from dataclasses import dataclass, replace
from typing import Protocol

from aromatwin.services.normalisation import normalise_name
from aromatwin.services.supplier_offer_importer import SupplierOffer


class IdentityRecord(Protocol):
    id: int
    brand: str
    name: str


@dataclass(frozen=True)
class OfferMatch:
    offer: SupplierOffer
    matched_type: str | None
    matched_id: int | None
    confidence: float
    review_status: str
    created_public_record: bool = False


def _score(offer: SupplierOffer, record: IdentityRecord) -> float:
    brand = normalise_name(record.brand) == offer.normalised_brand
    name = normalise_name(record.name) == offer.normalised_name
    if not (brand and name):
        return 0.0
    return 0.92 if offer.normalised_reference else 0.72


def match_supplier_offer(offer: SupplierOffer, candidates: list[IdentityRecord],
                         catalogue: list[IdentityRecord], threshold: float = 0.7) -> OfferMatch:
    ranked = [("catalogue", item, _score(offer, item)) for item in catalogue]
    ranked += [("candidate", item, _score(offer, item)) for item in candidates]
    kind, item, score = max(ranked, key=lambda value: value[2], default=(None, None, 0.0))
    if item is None or score < threshold:
        return OfferMatch(replace(offer, confidence_score=score, review_status="needs_human_review"),
                          None, None, score, "needs_human_review")
    status = "matched_to_catalogue" if kind == "catalogue" else "matched_to_candidate"
    linked = replace(offer, confidence_score=score, review_status=status,
                     linked_catalogue_fragrance_id=item.id if kind == "catalogue" else None,
                     linked_match_candidate_id=item.id if kind == "candidate" else None,
                     candidate_brand=item.brand, candidate_fragrance_name=item.name)
    return OfferMatch(linked, kind, item.id, score, status)


def compare_supplier_offers(offers: list[SupplierOffer]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], set[str]] = {}
    for offer in offers:
        key = (offer.candidate_brand or offer.normalised_brand,
               offer.candidate_fragrance_name or offer.normalised_name)
        groups.setdefault(key, set()).add(offer.supplier_name)
    return [{"normalised_brand": key[0], "normalised_name": key[1],
             "supplier_count": len(suppliers), "offer_count": sum(
                 (o.candidate_brand or o.normalised_brand, o.candidate_fragrance_name or o.normalised_name) == key
                 for o in offers)} for key, suppliers in sorted(groups.items())]
