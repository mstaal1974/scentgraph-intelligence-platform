"""Operational audit reporting over persisted public-safe projections."""

from sqlalchemy.orm import Session

from aromatwin.persistence.repositories import (
    AuditEventRepository,
    LaunchCandidateRepository,
    ReviewItemRepository,
    RunRepository,
    StageRepository,
)


def build_operational_audit(session: Session) -> dict[str, object]:
    runs = RunRepository(session).list_all()
    stages = StageRepository(session).list_all()
    reviews = ReviewItemRepository(session).list_all()
    launches = LaunchCandidateRepository(session).list_all()
    events = AuditEventRepository(session).list_all()
    return {
        "run_count": len(runs),
        "stage_count": len(stages),
        "review_item_count": len(reviews),
        "launch_candidate_count": len(launches),
        "blocker_count": sum(stage.blocked_count for stage in stages),
        "audit_event_count": len(events),
        "run_statuses": [RunRepository(session).public_safe_projection(item) for item in runs],
        "audit_events": [
            AuditEventRepository(session).public_safe_projection(item) for item in events
        ],
    }
