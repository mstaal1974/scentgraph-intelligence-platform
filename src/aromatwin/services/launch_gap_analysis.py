"""Explain launch blockers and assign each to a responsible human role."""

from typing import Any
from uuid import NAMESPACE_URL, uuid5

GAPS = {
    "missing_profile": ("high", "A reviewed profile is unavailable.", "Create and review a sourced profile.", "fragrance_reviewer"),
    "needs_enrichment": ("medium", "Profile enrichment is incomplete.", "Complete enrichment and human review.", "fragrance_reviewer"),
    "needs_human_review": ("medium", "Human approval is outstanding.", "Complete the assigned review.", "fragrance_reviewer"),
    "missing_catalogue_record": ("high", "No catalogue record is ready.", "Prepare a catalogue record for approval.", "catalogue_admin"),
    "missing_product_record": ("high", "No product record is ready.", "Prepare a product record without creating it automatically.", "product_manager"),
    "missing_product_variants": ("high", "Product formats are not ready.", "Review and configure product variants.", "product_manager"),
    "missing_supplier_confidence": ("high", "Supplier confidence is unavailable.", "Review supplier evidence and record a confidence band.", "supplier_reviewer"),
    "missing_margin_band": ("medium", "Margin suitability has not been banded.", "Assign a protected suitability band.", "supplier_reviewer"),
    "missing_recommendations": ("medium", "Recommendation setup is incomplete.", "Build and review recommendations.", "marketing_reviewer"),
    "missing_scent_vector": ("medium", "No reviewed scent vector is available.", "Build and review the scent vector.", "data_admin"),
    "missing_consumer_signal": ("low", "No aggregated consumer signal is available.", "Collect sufficient anonymised evidence.", "data_admin"),
    "missing_seller_demand_signal": ("low", "No aggregated seller signal is available.", "Review aggregated seller demand.", "data_admin"),
    "low_source_confidence": ("critical", "Source confidence is low.", "Verify provenance with permitted sources.", "compliance_reviewer"),
    "private_data_risk": ("critical", "Private-data risk was detected.", "Remove private data and repeat the privacy audit.", "compliance_reviewer"),
    "provenance_risk": ("critical", "Required provenance is missing.", "Add traceable permitted provenance.", "compliance_reviewer"),
    "unsupported_claim_risk": ("critical", "An unsupported claim may be present.", "Remove or substantiate the claim.", "compliance_reviewer"),
}


def analyse_launch_gaps(candidate: dict[str, Any]) -> list[dict[str, str]]:
    checks = {
        "missing_profile": candidate.get("profile_status") in (None, "missing"),
        "needs_enrichment": candidate.get("enrichment_status") not in ("approved", "high", "ready"),
        "needs_human_review": candidate.get("review_status") != "approved",
        "missing_catalogue_record": candidate.get("catalogue_status") in (None, "missing"),
        "missing_product_record": candidate.get("product_status") in (None, "missing"),
        "missing_product_variants": candidate.get("format_readiness") in (None, "unknown", "none", "low"),
        "missing_supplier_confidence": candidate.get("supplier_availability_band") in (None, "unknown"),
        "missing_margin_band": candidate.get("margin_suitability_band") in (None, "unknown"),
        "missing_recommendations": candidate.get("recommendation_readiness") in (None, "unknown", "none", "low"),
        "missing_scent_vector": candidate.get("scent_vector_status") in (None, "missing"),
        "missing_consumer_signal": candidate.get("consumer_interest_band") in (None, "unknown"),
        "missing_seller_demand_signal": candidate.get("seller_demand_band") in (None, "unknown"),
        "low_source_confidence": candidate.get("source_confidence_band") == "low",
        "private_data_risk": bool(candidate.get("private_data_risk")),
        "provenance_risk": bool(candidate.get("provenance_risk")),
        "unsupported_claim_risk": bool(candidate.get("unsupported_claim_risk")),
    }
    cid = str(candidate.get("launch_candidate_id", "unknown"))
    output = []
    for gap_type, present in checks.items():
        if present:
            severity, explanation, fix, owner = GAPS[gap_type]
            output.append({"gap_id": str(uuid5(NAMESPACE_URL, f"{cid}:{gap_type}")),
                           "launch_candidate_id": cid, "gap_type": gap_type,
                           "severity": severity, "explanation": explanation,
                           "recommended_fix": fix, "owner_role": owner,
                           "review_status": "needs_human_review"})
    return output
