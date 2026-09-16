from aromatwin.persistence.audit_log import AuditLog
from aromatwin.persistence.database import (
    create_persistence_engine,
    create_session_factory,
    initialise_persistence,
)
from aromatwin.persistence.repositories import AuditEventRepository, RunRepository
from aromatwin.services.operational_audit import build_operational_audit


def test_audit_redacts_commercial_summary():
    engine = create_persistence_engine("sqlite:///:memory:")
    initialise_persistence(engine)
    with create_session_factory(engine)() as session:
        RunRepository(session).create(
            run_id="run-audit",
            run_mode="test",
            workflow_type="pilot",
            status="complete",
            readiness_status="ready",
        )
        event = AuditLog(AuditEventRepository(session)).record(
            event_type="privacy_audit_failed",
            actor_type="system",
            linked_entity_type="run",
            linked_entity_id="run-audit",
            event_summary="supplier price appeared in unsafe input",
            risk_level="high",
        )
        assert "price" not in event.event_summary.casefold()
        report = build_operational_audit(session)
        assert report["run_count"] == 1
        assert report["audit_event_count"] == 1
