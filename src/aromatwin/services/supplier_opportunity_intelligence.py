"""Aggregated and anonymised reverse-demand intelligence."""

from collections import Counter, defaultdict
from uuid import uuid4

from aromatwin.services.seller_supplier_matching import SellerSupplierMatch


def _top(values: list[str], limit: int = 3) -> list[str]:
    return [value for value, _ in Counter(values).most_common(limit)]


def build_supplier_opportunities(matches: list[SellerSupplierMatch]) -> list[dict[str, object]]:
    groups: dict[str, list[SellerSupplierMatch]] = defaultdict(list)
    for match in matches:
        groups[match.supplier_internal_key].append(match)
    output = []
    for grouped in groups.values():
        demand_ids = {item.demand_brief_id for item in grouped}
        formats = [value for item in grouped for value in item.product_formats_internal]
        gaps = Counter(value for item in grouped for value in item.missing_requirements)
        score = sum(item.overall_match_score for item in grouped) / len(grouped)
        ready = sum(item.launch_readiness_score >= 0.7 for item in grouped)
        action = "provide format-specific suitability data"
        if gaps.get("profile_enrichment"):
            action = "provide permitted note pyramids"
        elif gaps.get("catalogue_review"):
            action = "improve catalogue naming consistency"
        output.append({
            "supplier_opportunity_id": str(uuid4()),
            "supplier_name_public_label": grouped[0].supplier_name_public_label,
            "opportunity_theme": "aggregated seller demand alignment",
            "matched_demand_count": len(demand_ids), "matched_format_count": len(set(formats)),
            "strongest_product_formats": _top(formats),
            "strongest_fragrance_families": _top([v for m in grouped for v in m.fragrance_families_internal]),
            "strongest_moods": _top([v for m in grouped for v in m.moods_internal]),
            "strongest_occasions": _top([v for m in grouped for v in m.occasions_internal]),
            "strongest_seasons": _top([v for m in grouped for v in m.seasons_internal]),
            "catalogue_readiness_summary": f"{ready} of {len(grouped)} candidates meet the readiness threshold",
            "profile_gap_summary": ", ".join(gaps) if gaps else "no material aggregate gap",
            "opportunity_score": round(score, 3),
            "opportunity_reason": "Multiple anonymised demand signals align with this supplier catalogue.",
            "recommended_supplier_action": action, "review_status": "needs_human_review"})
    return sorted(output, key=lambda item: float(item["opportunity_score"]), reverse=True)
