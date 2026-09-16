"""Apply explicit, idempotent internal-stage review decisions."""

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Callable

from aromatwin.services.review_gates import ALLOWED_DECISIONS

STATUS_BY_DECISION = {
    "reject": "rejected", "request_enrichment": "enrichment_requested",
    "request_supplier_review": "supplier_review_requested",
    "request_provenance_review": "provenance_review_requested",
    "request_product_setup": "product_setup_requested",
    "request_compliance_review": "compliance_review_requested", "hold": "held",
    "mark_duplicate": "duplicate", "mark_out_of_scope": "out_of_scope", "escalate": "escalated",
}
APPROVAL_STATUS = {
    "profile_draft_review": "approved_for_catalogue_review",
    "launch_candidate_review": "approved_for_launch_planning",
    "catalogue_approval_review": "approved_for_product_setup",
}


def apply_review_decision(review_item: dict[str, Any], decision: str, reviewer_role: str,
                          decision_reason: str | None = None, evidence_summary: str = "Evidence reviewed.",
                          reviewer_alias: str | None = None,
                          audit_recorder: Callable[..., Any] | None = None) -> dict[str, Any]:
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported decision: {decision}")
    gate_type = str(review_item["gate_type"])
    next_status = (APPROVAL_STATUS.get(gate_type, "approved_for_next_internal_stage")
                   if decision == "approve" else STATUS_BY_DECISION[decision])
    seed = f"{review_item['review_item_id']}:{decision}:{reviewer_role}"
    decision_id = f"decision-{sha256(seed.encode()).hexdigest()[:16]}"
    result = {
        "decision_id": decision_id, "review_item_id": review_item["review_item_id"],
        "gate_id": review_item["gate_id"], "decision": decision,
        "decision_reason": decision_reason, "reviewer_role": reviewer_role,
        "reviewer_alias": reviewer_alias or f"{reviewer_role}:reviewer",
        "evidence_summary": evidence_summary, "next_status": next_status,
        "next_action": f"Proceed to {next_status.replace('_', ' ')}; no publication is authorised.",
        "creates_audit_event": True, "created_at": datetime.now(UTC).isoformat(),
    }
    if audit_recorder is not None:
        audit_recorder(event_type="review_decision_applied", actor_type="human_reviewer",
                       linked_entity_type="review_item",
                       linked_entity_id=str(review_item["review_item_id"]),
                       event_summary=f"{decision} recorded for internal workflow progression.")
    return result


def public_decision_summary(decision: dict[str, Any]) -> dict[str, Any]:
    fields = {"decision_id", "review_item_id", "gate_id", "decision", "reviewer_role",
              "reviewer_alias", "evidence_summary", "next_status", "next_action",
              "creates_audit_event", "created_at"}
    return {key: decision[key] for key in fields if key in decision}

