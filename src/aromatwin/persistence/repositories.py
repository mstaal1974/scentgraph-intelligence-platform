"""Small SQLAlchemy repositories for operational records."""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from aromatwin.persistence import models, projections

Model = TypeVar("Model")


class Repository(Generic[Model]):
    model: type[Model]
    identity_field: str
    projection: Any

    def __init__(self, session: Session):
        self.session = session

    def create(self, **values: Any) -> Model:
        item = self.model(**values)
        self.session.add(item)
        self.session.flush()
        return item

    def get_by_id(self, value: str | int) -> Model | None:
        if isinstance(value, int):
            return self.session.get(self.model, value)
        return self.session.scalar(
            select(self.model).where(getattr(self.model, self.identity_field) == value)
        )

    def upsert(self, **values: Any) -> Model:
        item = self.get_by_id(values[self.identity_field])
        if item is None:
            return self.create(**values)
        for key, value in values.items():
            setattr(item, key, value)
        self.session.flush()
        return item

    def list_by_run_id(self, run_id: str) -> list[Model]:
        if not hasattr(self.model, "run_id"):
            return []
        return list(self.session.scalars(select(self.model).where(self.model.run_id == run_id)))

    def list_by_review_status(self, status: str) -> list[Model]:
        if not hasattr(self.model, "review_status"):
            return []
        return list(
            self.session.scalars(select(self.model).where(self.model.review_status == status))
        )

    def update_status(self, value: str, status: str) -> Model | None:
        item = self.get_by_id(value)
        if item is not None:
            field = "review_status" if hasattr(item, "review_status") else "status"
            setattr(item, field, status)
            self.session.flush()
        return item

    def list_all(self) -> list[Model]:
        return list(self.session.scalars(select(self.model).order_by(self.model.created_at.desc())))

    def public_safe_projection(self, item: Model) -> dict[str, Any]:
        return self.projection(item)


class RunRepository(Repository[models.PersistentRun]):
    model, identity_field, projection = (
        models.PersistentRun,
        "run_id",
        projections.run_public_summary,
    )


class StageRepository(Repository[models.PersistentRunStage]):
    model, identity_field, projection = (
        models.PersistentRunStage,
        "id",
        projections.stage_public_summary,
    )

    def append(self, **values: Any) -> models.PersistentRunStage:
        existing = self.session.scalar(
            select(self.model).where(
                self.model.run_id == values["run_id"], self.model.stage_name == values["stage_name"]
            )
        )
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            self.session.flush()
            return existing
        return self.create(**values)


class ArtifactRepository(Repository[models.PersistentArtifact]):
    model, identity_field, projection = (
        models.PersistentArtifact,
        "id",
        projections.artifact_public_summary,
    )


class ProfileDraftRepository(Repository[models.PersistentProfileDraft]):
    model, identity_field, projection = (
        models.PersistentProfileDraft,
        "profile_draft_id",
        projections.profile_draft_public_summary,
    )


class ReviewItemRepository(Repository[models.PersistentReviewItem]):
    model, identity_field, projection = (
        models.PersistentReviewItem,
        "review_item_id",
        projections.review_item_public_summary,
    )


class LaunchCandidateRepository(Repository[models.PersistentLaunchCandidate]):
    model, identity_field, projection = (
        models.PersistentLaunchCandidate,
        "launch_candidate_id",
        projections.launch_candidate_public_summary,
    )


class SellerDemandRepository(Repository[models.PersistentSellerDemandBrief]):
    model, identity_field, projection = (
        models.PersistentSellerDemandBrief,
        "demand_brief_id",
        projections.seller_demand_public_summary,
    )


class ConsumerScentprintRepository(Repository[models.PersistentConsumerScentprint]):
    model, identity_field, projection = (
        models.PersistentConsumerScentprint,
        "scentprint_id",
        projections.consumer_scentprint_public_summary,
    )


class ProvenanceRepository(Repository[models.PersistentProvenanceRecord]):
    model, identity_field, projection = (
        models.PersistentProvenanceRecord,
        "provenance_id",
        projections.provenance_public_summary,
    )


class AuditEventRepository(Repository[models.PersistentAuditEvent]):
    model, identity_field, projection = (
        models.PersistentAuditEvent,
        "audit_event_id",
        projections.audit_event_public_summary,
    )

    def append_audit_event(self, **values: Any) -> models.PersistentAuditEvent:
        return self.upsert(**values)
