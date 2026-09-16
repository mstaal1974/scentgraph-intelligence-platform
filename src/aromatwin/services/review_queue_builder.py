"""Build privacy-minimised queues from existing workflow summaries."""

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Iterable

from aromatwin.services.review_gates import build_review_gate

SOURCE_GATES = {
    "bulk_profile_drafts": "profile_draft_review", "profile_drafts": "profile_draft_review",
    "enrichment_items": "enrichment_review", "enrichment_research_queue": "enrichment_review",
    "provenance_records": "provenance_review", "supplier_sourcing_decisions": "supplier_sourcing_review",
    "seller_demand_matches": "seller_demand_match_review",
    "consumer_scent_intelligence_summaries": "consumer_signal_review",
    "consumer_signal_summaries": "consumer_signal_review", "launch_candidates": "launch_candidate_review",
    "pilot_blockers": "pilot_blocker_review", "persistent_review_items": "match_candidate_review",
    "operational_audit_events": "public_export_review",
}

_IDS = ("profile_draft_id", "enrichment_item_id", "provenance_id", "sourcing_decision_id",
        "demand_match_id", "consumer_signal_id", "launch_candidate_id", "blocker_id",
        "review_item_id", "audit_event_id", "id")


def _value(record: dict[str, Any], names: tuple[str, ...], default: str) -> str:
    return str(next((record[name] for name in names if record.get(name) is not None), default))


def _band(value: Any, allowed: set[str], default: str) -> str:
    normalised = str(value or "").casefold()
    return normalised if normalised in allowed else default


def build_review_queues(sources: dict[str, Iterable[dict[str, Any]]] | None = None,
                        **source_lists: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return allow-listed summaries only; arbitrary source text is never copied."""
    all_sources = dict(sources or {})
    all_sources.update(source_lists)
    now = datetime.now(UTC).isoformat()
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_name, records in all_sources.items():
        gate_type = SOURCE_GATES.get(source_name)
        if gate_type is None:
            continue
        for index, record in enumerate(records or []):
            entity_id = _value(record, _IDS, f"{source_name}-{index + 1}")
            gate = build_review_gate(gate_type, entity_id)
            digest = sha256(f"{gate_type}:{entity_id}".encode()).hexdigest()[:16]
            item_id = f"review-{digest}"
            if item_id in seen:
                continue
            seen.add(item_id)
            priority = _band(record.get("priority_band") or record.get("launch_priority_band"),
                             {"low", "normal", "high", "urgent"}, "normal")
            risk = _band(record.get("risk_band") or record.get("severity"),
                         {"low", "moderate", "high", "blocked"}, "moderate")
            if str(record.get("severity", "")).casefold() == "critical":
                risk, priority = "blocked", "urgent"
            summary = f"{gate_type.replace('_', ' ').title()} item awaiting human decision."
            output.append({
                "review_item_id": item_id, "gate_id": gate["gate_id"], "gate_type": gate_type,
                "linked_entity_type": gate["linked_entity_type"], "linked_entity_id": entity_id,
                "title": f"Review {gate['linked_entity_type'].replace('_', ' ')}",
                "priority_band": priority,
                "confidence_band": _band(record.get("confidence_band") or record.get("source_confidence_band"),
                                         {"low", "medium", "high", "unknown"}, "unknown"),
                "risk_band": risk, "review_status": "queued", "assigned_role": gate["reviewer_role"],
                "required_evidence": gate["required_evidence"],
                "blocking_conditions": gate["blocking_conditions"], "recommended_decision": "hold",
                "recommended_next_action": "Complete human review of the required evidence.",
                "public_safe_summary": summary, "created_at": now, "updated_at": now,
            })
    return output


build_review_queue = build_review_queues


def public_queue_summary(item: dict[str, Any]) -> dict[str, Any]:
    fields = {"review_item_id", "gate_type", "linked_entity_type", "linked_entity_id", "title",
              "priority_band", "confidence_band", "risk_band", "review_status", "assigned_role",
              "recommended_next_action", "public_safe_summary", "created_at", "updated_at"}
    return {key: item[key] for key in fields if key in item}

