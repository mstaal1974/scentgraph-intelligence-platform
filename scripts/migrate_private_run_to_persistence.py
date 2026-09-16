#!/usr/bin/env python3
"""Persist allow-listed summaries from a private pilot run directory."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from aromatwin.persistence.database import (
    create_persistence_engine,
    create_session_factory,
    initialise_persistence,
    transaction,
)
from aromatwin.services.persistence_service import PersistenceService


def _date(value: Any) -> datetime | None:
    return datetime.fromisoformat(value) if isinstance(value, str) and value else None


def migrate_run(run_dir: Path, database_url: str | None = None) -> str:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    readiness_path = run_dir / "readiness.json"
    readiness = (
        json.loads(readiness_path.read_text(encoding="utf-8")) if readiness_path.exists() else {}
    )
    engine = create_persistence_engine(database_url)
    initialise_persistence(engine)
    factory = create_session_factory(engine)
    run_id = str(manifest["run_id"])
    with transaction(factory) as session:
        service = PersistenceService(session)
        service.persist_pilot_run_summary(
            {
                "run_id": run_id,
                "run_mode": str(manifest.get("run_mode", "private_run")),
                "workflow_type": "private_pilot",
                "status": "completed",
                "started_at": _date(manifest.get("created_at")),
                "completed_at": _date(manifest.get("updated_at")),
                "readiness_status": str(readiness.get("readiness_status", "pending")),
                "private_output_root": str(run_dir),
            }
        )
        statuses = (
            ("completed", manifest.get("stages_completed", [])),
            ("skipped", manifest.get("stages_skipped", [])),
            ("failed", manifest.get("stages_failed", [])),
        )
        for status, stages in statuses:
            for stage_name in stages:
                service.persist_run_stage_result(
                    {
                        "run_id": run_id,
                        "stage_name": str(stage_name),
                        "stage_status": status,
                        "accepted_count": 0,
                        "skipped_count": 0,
                        "blocked_count": 1 if status == "failed" else 0,
                        "warning_count": 0,
                    }
                )
        service.record_audit_event(
            event_type="workflow_stage_completed",
            actor_type="migration_script",
            linked_entity_type="run",
            linked_entity_id=run_id,
            event_summary="Private pilot manifest summaries migrated through the allow-list boundary.",
        )
    engine.dispose()
    return run_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--runs-root", type=Path, default=Path("data/private/runs"))
    parser.add_argument("--database-url")
    args = parser.parse_args()
    run_id = migrate_run(args.runs_root / args.run_id, args.database_url)
    print(f"Persisted safe operational summaries for run {run_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
