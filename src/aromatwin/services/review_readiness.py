"""Aggregate review progress without exposing underlying records."""

from collections import Counter
from typing import Any


def build_review_readiness(items: list[dict[str, Any]], queue_id: str = "review-workflow") -> dict[str, Any]:
    statuses = Counter(str(item.get("review_status", "queued")) for item in items)
    roles = Counter(str(item.get("assigned_role", "unassigned")) for item in items)
    risks = Counter(str(item.get("risk_band", "moderate")) for item in items)
    priorities = Counter(str(item.get("priority_band", "normal")) for item in items)
    if not items:
        readiness = "review_not_started"
    elif statuses["compliance_review_requested"]:
        readiness = "blocked_by_compliance"
    elif statuses["provenance_review_requested"]:
        readiness = "blocked_by_provenance"
    elif statuses["supplier_review_requested"]:
        readiness = "blocked_by_supplier_review"
    elif risks["blocked"]:
        readiness = "blocked_by_missing_data"
    elif statuses["product_setup_requested"]:
        readiness = "ready_for_product_setup"
    elif any(item.get("next_status") == "approved_for_launch_planning" for item in items):
        readiness = "ready_for_launch_planning"
    elif statuses["enrichment_requested"]:
        readiness = "ready_for_enrichment"
    elif statuses["approved"]:
        readiness = "ready_for_catalogue_approval"
    else:
        readiness = "review_in_progress"
    bottlenecks = [f"{name}: {count}" for name, count in (statuses + Counter({"blocked": risks["blocked"]})).most_common(5)
                   if name not in {"approved", "queued"} and count]
    actions = ["Resolve blocked and escalated reviews before internal progression."] if bottlenecks else [
        "Continue assigned human reviews; approval does not authorize publication."
    ]
    return {
        "queue_id": queue_id, "total_items": len(items), "queued_count": statuses["queued"],
        "in_review_count": statuses["in_review"], "approved_count": statuses["approved"],
        "rejected_count": statuses["rejected"],
        "enrichment_requested_count": statuses["enrichment_requested"],
        "supplier_review_requested_count": statuses["supplier_review_requested"],
        "provenance_review_requested_count": statuses["provenance_review_requested"],
        "product_setup_requested_count": statuses["product_setup_requested"],
        "compliance_review_requested_count": statuses["compliance_review_requested"],
        "held_count": statuses["held"], "escalated_count": statuses["escalated"],
        "blocked_count": risks["blocked"], "high_priority_count": priorities["high"],
        "urgent_count": priorities["urgent"], "top_bottlenecks": bottlenecks,
        "owner_role_summary": dict(roles), "next_actions": actions, "readiness_status": readiness,
    }


build_readiness_report = build_review_readiness
