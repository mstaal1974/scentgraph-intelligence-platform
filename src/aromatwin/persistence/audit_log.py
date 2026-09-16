"""Privacy-safe construction of operational audit events."""

import re
from typing import Any
from uuid import uuid4

from aromatwin.persistence.repositories import AuditEventRepository

EVENT_TYPES = frozenset(
    {
        "workflow_run_created",
        "workflow_stage_completed",
        "profile_draft_created",
        "enrichment_queue_item_created",
        "review_item_created",
        "review_status_changed",
        "launch_candidate_created",
        "blocker_added",
        "public_safe_export_generated",
        "privacy_audit_passed",
        "privacy_audit_failed",
    }
)
_SENSITIVE = re.compile(
    r"(?i)\b(?:supplier[ _-]?(?:price|cost|code|terms)|cn[ _-]?code|(?:aed|usd)[ _-]?price|"
    r"stock|quantit(?:y|ies)|raw[ _-]?margin|commercial[ _-]?terms|email|phone|address|"
    r"private[ _-]?notes?|raw[ _-]?feedback)\b"
)


def safe_event_summary(summary: str) -> str:
    if _SENSITIVE.search(summary):
        return "Sensitive detail redacted; consult the authorised private source."
    return summary[:500]


class AuditLog:
    def __init__(self, repository: AuditEventRepository):
        self.repository = repository

    def record(
        self,
        *,
        event_type: str,
        actor_type: str,
        linked_entity_type: str,
        linked_entity_id: str,
        event_summary: str,
        risk_level: str = "low",
        privacy_boundary: str = "internal_public_safe",
        **_: Any,
    ):
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unsupported operational event type: {event_type}")
        return self.repository.append_audit_event(
            audit_event_id=f"audit-{uuid4().hex}",
            event_type=event_type,
            actor_type=actor_type,
            linked_entity_type=linked_entity_type,
            linked_entity_id=linked_entity_id,
            event_summary=safe_event_summary(event_summary),
            risk_level=risk_level,
            privacy_boundary=privacy_boundary,
        )
