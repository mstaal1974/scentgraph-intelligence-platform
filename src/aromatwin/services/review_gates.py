"""Formal, non-automating human review gates."""

from copy import deepcopy
from typing import Any

ALLOWED_DECISIONS = (
    "approve", "reject", "request_enrichment", "request_supplier_review",
    "request_provenance_review", "request_product_setup", "request_compliance_review",
    "hold", "mark_duplicate", "mark_out_of_scope", "escalate",
)

_GATE_CONFIG = {
    "supplier_offer_review": ("supplier_offer", "supplier_reviewer", ["offer summary"]),
    "match_candidate_review": ("match_candidate", "matching_reviewer", ["match evidence"]),
    "profile_draft_review": ("profile_draft", "catalogue_reviewer", ["profile completeness"]),
    "enrichment_review": ("enrichment_item", "enrichment_reviewer", ["research summary"]),
    "provenance_review": ("provenance_record", "provenance_reviewer", ["source summary"]),
    "catalogue_approval_review": ("catalogue_candidate", "catalogue_reviewer", ["approved profile"]),
    "product_readiness_review": ("product_candidate", "product_reviewer", ["readiness summary"]),
    "supplier_sourcing_review": ("sourcing_decision", "supplier_reviewer", ["sourcing bands"]),
    "margin_band_review": ("margin_assessment", "commercial_reviewer", ["margin band"]),
    "seller_demand_match_review": ("seller_demand_match", "demand_reviewer", ["demand bands"]),
    "consumer_signal_review": ("consumer_signal_summary", "consumer_insights_reviewer", ["aggregate signal summary"]),
    "launch_candidate_review": ("launch_candidate", "launch_reviewer", ["launch readiness summary"]),
    "pilot_blocker_review": ("pilot_blocker", "pilot_operator", ["blocker summary"]),
    "public_export_review": ("public_export", "privacy_reviewer", ["privacy audit result"]),
}


def build_review_gate(gate_type: str, linked_entity_id: str = "unassigned") -> dict[str, Any]:
    """Create an explicit gate; construction never implies approval or publication."""
    if gate_type not in _GATE_CONFIG:
        raise ValueError(f"Unknown review gate: {gate_type}")
    entity_type, role, evidence = _GATE_CONFIG[gate_type]
    return {
        "gate_id": f"gate:{gate_type}:{linked_entity_id}", "gate_type": gate_type,
        "linked_entity_type": entity_type, "linked_entity_id": linked_entity_id,
        "required_evidence": deepcopy(evidence), "allowed_decisions": list(ALLOWED_DECISIONS),
        "blocking_conditions": ["required evidence missing", "privacy review unresolved"],
        "next_allowed_statuses": [
            "approved", "rejected", "enrichment_requested", "supplier_review_requested",
            "provenance_review_requested", "product_setup_requested",
            "compliance_review_requested", "held", "duplicate", "out_of_scope", "escalated",
        ],
        "reviewer_role": role, "audit_required": True,
        "public_safe_summary": f"Human review required for {gate_type.replace('_', ' ')}.",
    }


def list_review_gates() -> list[dict[str, Any]]:
    return [build_review_gate(gate_type) for gate_type in _GATE_CONFIG]


def get_review_gate(gate_id: str) -> dict[str, Any] | None:
    return next((gate for gate in list_review_gates() if gate["gate_id"] == gate_id), None)

