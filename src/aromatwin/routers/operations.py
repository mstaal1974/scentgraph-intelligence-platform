"""Authenticated, public-safe operational persistence views."""

from collections.abc import Generator
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from aromatwin.persistence.database import (
    create_persistence_engine,
    create_session_factory,
    initialise_persistence,
)
from aromatwin.persistence.models import PersistentProvenanceRecord
from aromatwin.persistence.repositories import (
    ArtifactRepository,
    AuditEventRepository,
    LaunchCandidateRepository,
    ReviewItemRepository,
    RunRepository,
    StageRepository,
)
from aromatwin.schemas.persistence import (
    OperationalAuditReport,
    PersistenceHealthRead,
    PersistentArtifactRead,
    PersistentAuditEventRead,
    PersistentLaunchCandidateRead,
    PersistentProvenanceRecordRead,
    PersistentReviewItemRead,
    PersistentRunPublicSummary,
    PersistentRunStageRead,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.operational_audit import build_operational_audit

router = APIRouter(
    prefix="/operations",
    tags=["internal operations"],
    dependencies=[Depends(require_private_api_key)],
)


@lru_cache
def _engine() -> Engine:
    engine = create_persistence_engine()
    initialise_persistence(engine)
    return engine


def get_persistence_session() -> Generator[Session, None, None]:
    with create_session_factory(_engine())() as session:
        yield session


@router.get("/health", response_model=PersistenceHealthRead)
def health(session: Session = Depends(get_persistence_session)) -> dict[str, object]:
    session.execute(select(1))
    return {
        "status": "ok",
        "database_type": session.bind.dialect.name,
        "destructive_initialisation": False,
    }


@router.get("/runs", response_model=list[PersistentRunPublicSummary])
def runs(session: Session = Depends(get_persistence_session)) -> list[dict[str, object]]:
    repo = RunRepository(session)
    return [repo.public_safe_projection(item) for item in repo.list_all()]


@router.get("/runs/{run_id}", response_model=PersistentRunPublicSummary)
def run(run_id: str, session: Session = Depends(get_persistence_session)) -> dict[str, object]:
    repo = RunRepository(session)
    item = repo.get_by_id(run_id)
    if item is None:
        raise HTTPException(404, "Operational run not found")
    return repo.public_safe_projection(item)


@router.get("/runs/{run_id}/stages", response_model=list[PersistentRunStageRead])
def stages(
    run_id: str, session: Session = Depends(get_persistence_session)
) -> list[dict[str, object]]:
    repo = StageRepository(session)
    return [repo.public_safe_projection(item) for item in repo.list_by_run_id(run_id)]


@router.get("/runs/{run_id}/artifacts", response_model=list[PersistentArtifactRead])
def artifacts(
    run_id: str, session: Session = Depends(get_persistence_session)
) -> list[dict[str, object]]:
    repo = ArtifactRepository(session)
    return [repo.public_safe_projection(item) for item in repo.list_by_run_id(run_id)]


@router.get("/review-items", response_model=list[PersistentReviewItemRead])
def review_items(
    review_status: str | None = Query(None), session: Session = Depends(get_persistence_session)
) -> list[dict[str, object]]:
    repo = ReviewItemRepository(session)
    items = repo.list_by_review_status(review_status) if review_status else repo.list_all()
    return [repo.public_safe_projection(item) for item in items]


@router.get("/launch-candidates", response_model=list[PersistentLaunchCandidateRead])
def launch_candidates(
    review_status: str | None = Query(None), session: Session = Depends(get_persistence_session)
) -> list[dict[str, object]]:
    repo = LaunchCandidateRepository(session)
    items = repo.list_by_review_status(review_status) if review_status else repo.list_all()
    return [repo.public_safe_projection(item) for item in items]


@router.get("/provenance", response_model=list[PersistentProvenanceRecordRead])
def provenance(
    session: Session = Depends(get_persistence_session),
) -> list[PersistentProvenanceRecord]:
    return list(
        session.scalars(
            select(PersistentProvenanceRecord).order_by(
                PersistentProvenanceRecord.created_at.desc()
            )
        )
    )


@router.get("/audit-events", response_model=list[PersistentAuditEventRead])
def audit_events(session: Session = Depends(get_persistence_session)) -> list[dict[str, object]]:
    repo = AuditEventRepository(session)
    return [repo.public_safe_projection(item) for item in repo.list_all()]


@router.get("/audit", response_model=OperationalAuditReport)
def audit(session: Session = Depends(get_persistence_session)) -> dict[str, object]:
    return build_operational_audit(session)


@router.post("/audit/export", response_model=OperationalAuditReport)
def export_audit(session: Session = Depends(get_persistence_session)) -> dict[str, object]:
    """Return an allow-listed report; filesystem export remains an explicit CLI action."""
    return build_operational_audit(session)
