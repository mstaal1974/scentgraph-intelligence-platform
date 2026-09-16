"""Privacy-preserving orchestration for launch decisions; never mutates source layers."""

from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from aromatwin.services.launch_gap_analysis import analyse_launch_gaps
from aromatwin.services.launch_readiness_scoring import score_launch_readiness

ALLOWED_FORMATS = {"10ml", "30ml", "50ml", "car diffuser", "body care", "kit"}


def _status(candidate: dict[str, Any], gaps: set[str], score: float) -> str:
    if "private_data_risk" in gaps:
        return "hold_private_data_risk"
    if "provenance_risk" in gaps:
        return "hold_missing_provenance"
    if "low_source_confidence" in gaps:
        return "hold_low_confidence"
    if "missing_profile" in gaps or "needs_enrichment" in gaps:
        return "launch_after_profile_enrichment"
    if "missing_supplier_confidence" in gaps or "missing_margin_band" in gaps:
        return "launch_after_supplier_review"
    if "missing_catalogue_record" in gaps:
        return "launch_after_catalogue_approval"
    if "missing_product_record" in gaps or "missing_product_variants" in gaps:
        return "launch_after_product_setup"
    if score < 40:
        return "do_not_launch_yet"
    formats = candidate.get("recommended_product_formats", [])
    if formats == ["10ml"]:
        return "sample_only_candidate"
    if candidate.get("bundle_potential_band") in {"high", "strong"}:
        return "bundle_candidate"
    return "launch_now"  # recommendation only; review_status remains human-controlled


def build_launch_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Combine already-aggregated signals into a safe, non-mutating decision record."""
    fragrance_id = candidate.get("fragrance_id")
    product_id = candidate.get("product_id")
    cid = candidate.get("launch_candidate_id") or str(uuid5(
        NAMESPACE_URL, f"launch:{fragrance_id or ''}:{product_id or ''}"))
    now = datetime.now(UTC)
    formats = [value for value in candidate.get("recommended_product_formats", [])
               if value in ALLOWED_FORMATS]
    base = {
        "launch_candidate_id": cid, "fragrance_id": fragrance_id, "product_id": product_id,
        "canonical_brand": candidate.get("canonical_brand", "Unknown"),
        "canonical_fragrance_name": candidate.get("canonical_fragrance_name", "Unknown"),
        "product_title": candidate.get("product_title"),
        "profile_status": candidate.get("profile_status", "missing"),
        "enrichment_status": candidate.get("enrichment_status", "unknown"),
        "catalogue_status": candidate.get("catalogue_status", "missing"),
        "product_status": candidate.get("product_status", "missing"),
        "supplier_availability_band": candidate.get("supplier_availability_band", "unknown"),
        "source_confidence_band": candidate.get("source_confidence_band", "unknown"),
        "margin_suitability_band": candidate.get("margin_suitability_band", "unknown"),
        "seller_demand_band": candidate.get("seller_demand_band", "unknown"),
        "consumer_interest_band": candidate.get("consumer_interest_band", "unknown"),
        "recommendation_readiness": candidate.get("recommendation_readiness", "unknown"),
        "bundle_potential_band": candidate.get("bundle_potential_band", "unknown"),
        "format_readiness": candidate.get("format_readiness", "unknown"),
        "scent_vector_status": candidate.get("scent_vector_status", "missing"),
        "recommended_product_formats": formats,
        "review_status": "needs_human_review",
        "created_at": candidate.get("created_at", now), "updated_at": now,
        "private_data_risk": bool(candidate.get("private_data_risk")),
        "provenance_risk": bool(candidate.get("provenance_risk")),
        "unsupported_claim_risk": bool(candidate.get("unsupported_claim_risk")),
    }
    score = score_launch_readiness(base)
    provisional = {**base, **score}
    gaps = analyse_launch_gaps(provisional)
    gap_types = {gap["gap_type"] for gap in gaps}
    launch_status = _status(base, gap_types, score["launch_priority_score"])
    blockers = [gap["explanation"] for gap in gaps if gap["severity"] in {"critical", "high"}]
    missing = [gap["gap_type"] for gap in gaps]
    action = gaps[0]["recommended_fix"] if gaps else "Submit candidate for human launch review."
    return {**provisional, "launch_status": launch_status,
            "launch_reasons": score["explanations"], "blocking_issues": blockers,
            "missing_requirements": missing, "recommended_next_action": action}


def build_launch_intelligence(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((build_launch_candidate(item) for item in candidates),
                  key=lambda item: (-item["launch_priority_score"], item["launch_candidate_id"]))


def public_summary(record: dict[str, Any]) -> dict[str, Any]:
    """Explicit allow-list prevents confidential source fields escaping."""
    keys = ("launch_candidate_id", "fragrance_id", "product_id", "canonical_brand",
            "canonical_fragrance_name", "product_title", "profile_status", "enrichment_status",
            "catalogue_status", "product_status", "supplier_availability_band",
            "source_confidence_band", "margin_suitability_band", "seller_demand_band",
            "consumer_interest_band", "recommendation_readiness", "bundle_potential_band",
            "format_readiness", "launch_priority_score", "launch_priority_band", "launch_status",
            "launch_reasons", "blocking_issues", "missing_requirements",
            "recommended_product_formats", "recommended_next_action", "review_status",
            "created_at", "updated_at")
    return {key: record.get(key) for key in keys}
