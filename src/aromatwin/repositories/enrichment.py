from sqlalchemy import select
from sqlalchemy.orm import Session
from aromatwin.models.enrichment_review import EnrichmentReview
from aromatwin.models.enrichment_source import EnrichmentSource
from aromatwin.models.profile_draft import ProfileDraft
from aromatwin.models.profile_enrichment_event import ProfileEnrichmentEvent
from aromatwin.models.profile_source_link import ProfileSourceLink
from aromatwin.schemas.enrichment import (
    EnrichmentGenerateRequest,
    EnrichmentReviewCreate,
    EnrichmentSourceCreate,
    ProfileSourceLinkCreate,
)
from aromatwin.services.enrichment import EnrichmentEventData


class EnrichmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_sources(self) -> list[EnrichmentSource]:
        return list(self.session.scalars(select(EnrichmentSource).order_by(EnrichmentSource.id)))

    def add_source(self, payload: EnrichmentSourceCreate) -> EnrichmentSource:
        source = EnrichmentSource(**payload.model_dump(mode="python"))
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def list_reviews(self) -> list[EnrichmentReview]:
        return list(
            self.session.scalars(
                select(EnrichmentReview)
                .where(EnrichmentReview.profile_draft_id.is_not(None))
                .order_by(EnrichmentReview.id)
            )
        )

    def get_review(self, review_id: int) -> EnrichmentReview | None:
        return self.session.get(EnrichmentReview, review_id)

    def profiles_for_generation(self, request: EnrichmentGenerateRequest) -> list[ProfileDraft]:
        statement = select(ProfileDraft).where(
            ProfileDraft.review_status.in_(
                ("needs_human_review", "requires_more_sources", "approved_for_catalogue")
            )
        )
        if request.profile_draft_ids:
            statement = statement.where(ProfileDraft.id.in_(request.profile_draft_ids))
        existing = select(EnrichmentReview.profile_draft_id).where(
            EnrichmentReview.profile_draft_id.is_not(None)
        )
        statement = statement.where(ProfileDraft.id.not_in(existing))
        return list(self.session.scalars(statement.order_by(ProfileDraft.id)))

    def linked_sources(self, profile_draft_id: int) -> list[EnrichmentSource]:
        return list(
            self.session.scalars(
                select(EnrichmentSource)
                .join(
                    ProfileSourceLink, ProfileSourceLink.enrichment_source_id == EnrichmentSource.id
                )
                .where(ProfileSourceLink.profile_draft_id == profile_draft_id)
            )
        )

    def add_review(self, payload: EnrichmentReviewCreate) -> EnrichmentReview:
        values = payload.model_dump(mode="python")
        values.update(
            {
                "match_candidate_id": None,
                "official_source_url": str(payload.official_source_url)
                if payload.official_source_url
                else None,
                "description_ai_generated": False,
                "description_reviewed": False,
                "top_notes": payload.note_pyramid_json.get("top", []),
                "heart_notes": payload.note_pyramid_json.get("heart", []),
                "base_notes": payload.note_pyramid_json.get("base", []),
                "accords": payload.accords_json,
                "fragrance_family": payload.family,
                "season": payload.season_json,
                "occasion": payload.occasion_json,
                "mood": payload.mood_json,
                "scent_vector_status": "draft",
                "source_confidence": payload.enrichment_confidence,
                "review_status": payload.review_status.value,
            }
        )
        for key in ("accords_json", "family", "season_json", "occasion_json", "mood_json"):
            values.pop(key, None)
        record = EnrichmentReview(**values)
        self.session.add(record)
        self.session.flush()
        return record

    def attach_source(
        self, review: EnrichmentReview, payload: ProfileSourceLinkCreate, actor: str
    ) -> ProfileSourceLink:
        source = self.session.get(EnrichmentSource, payload.enrichment_source_id)
        if source is None:
            raise ValueError("Enrichment source not found")
        link = ProfileSourceLink(
            profile_draft_id=review.profile_draft_id,
            enrichment_source_id=source.id,
            usage_type=payload.usage_type,
            confidence=payload.confidence,
            notes=payload.notes,
        )
        self.session.add(link)
        self.add_event(
            EnrichmentEventData(
                review.profile_draft_id,
                "source_attached",
                f"Source {source.id} attached for {payload.usage_type}.",
                actor,
            )
        )
        self.session.commit()
        self.session.refresh(link)
        return link

    def add_event(self, event: EnrichmentEventData) -> ProfileEnrichmentEvent:
        record = ProfileEnrichmentEvent(**event.__dict__)
        self.session.add(record)
        return record

    def save_with_event(
        self, review: EnrichmentReview, event: EnrichmentEventData
    ) -> EnrichmentReview:
        self.session.add(review)
        self.add_event(event)
        self.session.commit()
        self.session.refresh(review)
        return review

    def commit_generated(
        self, reviews: list[EnrichmentReview], events: list[EnrichmentEventData]
    ) -> list[EnrichmentReview]:
        for event in events:
            self.add_event(event)
        self.session.commit()
        for review in reviews:
            self.session.refresh(review)
        return reviews
