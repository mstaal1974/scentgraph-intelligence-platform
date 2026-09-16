#!/usr/bin/env python3
"""Export an allow-listed operational audit report as CSV."""

import argparse
import csv
from pathlib import Path

from aromatwin.persistence.database import create_persistence_engine, create_session_factory
from aromatwin.persistence.repositories import AuditEventRepository, RunRepository, StageRepository

FIELDS = (
    "record_type",
    "run_id",
    "stage_name",
    "stage_status",
    "readiness_status",
    "blocker_count",
    "audit_event_type",
    "risk_level",
    "public_safe_summary",
)


def export_audit(output: Path, database_url: str | None = None) -> int:
    engine = create_persistence_engine(database_url)
    with create_session_factory(engine)() as session:
        rows = []
        for run in RunRepository(session).list_all():
            rows.append(
                {
                    "record_type": "run",
                    "run_id": run.run_id,
                    "readiness_status": run.readiness_status,
                    "public_safe_summary": "Operational run status summary.",
                }
            )
        for stage in StageRepository(session).list_all():
            rows.append(
                {
                    "record_type": "stage",
                    "run_id": stage.run_id,
                    "stage_name": stage.stage_name,
                    "stage_status": stage.stage_status,
                    "blocker_count": stage.blocked_count,
                    "public_safe_summary": stage.blocker_summary or "Stage status summary.",
                }
            )
        for event in AuditEventRepository(session).list_all():
            rows.append(
                {
                    "record_type": "audit_event",
                    "audit_event_type": event.event_type,
                    "risk_level": event.risk_level,
                    "public_safe_summary": event.event_summary,
                }
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    engine.dispose()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--database-url")
    args = parser.parse_args()
    count = export_audit(args.output, args.database_url)
    print(f"Exported {count} public-safe operational audit rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
