import csv
from datetime import UTC, datetime
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from aromatwin.main import app
from aromatwin.routers.enrichment import get_enrichment_repository
from aromatwin.schemas.enrichment import (
    EnrichmentDecisionRequest,
    EnrichmentGenerateRequest,
    EnrichmentReviewRead,
    EnrichmentReviewStatus,
)
from aromatwin.schemas.profile_draft import ProfileDraftRead, ProfileDraftStatus
from aromatwin.services.enrichment import (
    approve_enrichment_review,
    generate_enrichment_review,
    mark_ready,
    reject_enrichment,
)

ROOT = Path(__file__).resolve().parents[1]


def profile() -> ProfileDraftRead:
    now = datetime.now(UTC)
    return ProfileDraftRead(
        id=1,
        supplier_item_id=1,
        match_candidate_id=1,
        candidate_brand="Example Brand",
        candidate_fragrance_name="Example Scent",
        likely_original_brand="Example Brand",
        likely_original_name="Example Scent",
        profile_title="Example Brand Example Scent",
        description_original="Original profile draft",
        description_generation_method="deterministic",
        confidence_score=0.7,
        source_confidence=0.7,
        provenance_notes="Identifiers only",
        review_status=ProfileDraftStatus.needs_human_review,
        created_at=now,
        updated_at=now,
    )


def source(**overrides):
    payload = {
        "id": 1,
        "source_name": "Official source",
        "source_type": "official_source",
        "source_url": "https://example.com/product",
        "commercial_use_allowed": True,
        "can_copy_text": False,
        "can_use_for_factual_reference": True,
        "source_confidence": 0.85,
        "notes": "RESTRICTED SOURCE TEXT MUST NOT COPY",
    }
    payload.update(overrides)
    return payload


def review(sources=None) -> EnrichmentReviewRead:
    created = generate_enrichment_review(profile(), sources or [source()])
    now = datetime.now(UTC)
    return EnrichmentReviewRead(id=1, created_at=now, updated_at=now, **created.model_dump())


def test_enrichment_generated_from_profile_draft() -> None:
    result = generate_enrichment_review(profile(), [source()])
    assert result.profile_draft_id == 1
    assert result.approved_brand == "Example Brand"
    assert result.enrichment_confidence == 0.85


def test_enrichment_defaults_to_human_review() -> None:
    assert (
        generate_enrichment_review(profile(), [source()]).review_status
        == EnrichmentReviewStatus.needs_human_review
    )


def test_restricted_source_cannot_be_promoted_directly() -> None:
    restricted = source(
        source_type="reference_only",
        commercial_use_allowed=False,
        can_use_for_factual_reference=False,
        source_confidence=0.99,
    )
    result = generate_enrichment_review(profile(), [restricted])
    assert result.licensing_risk == "high"
    assert result.review_status == EnrichmentReviewStatus.needs_human_review
    with pytest.raises(ValueError):
        mark_ready(review([restricted]), [restricted], "Reviewer")


def test_approval_fails_with_insufficient_provenance() -> None:
    low = source(source_confidence=0.4)
    draft = review([low])
    draft = draft.model_copy(update={"review_status": "ready_for_approval"})
    with pytest.raises(ValueError, match="confidence"):
        approve_enrichment_review(
            draft, [low], EnrichmentDecisionRequest(reviewer="Reviewer", reason="Attempt")
        )


def test_approval_fails_with_high_licensing_risk() -> None:
    draft = review().model_copy(
        update={"review_status": "ready_for_approval", "licensing_risk": "high"}
    )
    with pytest.raises(ValueError, match="Licensing risk"):
        approve_enrichment_review(
            draft, [source()], EnrichmentDecisionRequest(reviewer="Reviewer", reason="Attempt")
        )


def test_copied_text_fails_when_source_disallows_copying() -> None:
    draft = review().model_copy(
        update={"review_status": "ready_for_approval", "copied_text_detected": True}
    )
    with pytest.raises(ValueError, match="Copied text"):
        approve_enrichment_review(
            draft,
            [source(can_copy_text=False)],
            EnrichmentDecisionRequest(reviewer="Reviewer", reason="Attempt"),
        )


def test_rejection_stores_reason_and_creates_event() -> None:
    rejected, event = reject_enrichment(
        review(),
        EnrichmentDecisionRequest(
            reviewer="Reviewer",
            reason="Duplicate",
            rejection_status=EnrichmentReviewStatus.rejected_duplicate,
        ),
    )
    assert rejected.review_notes == "Duplicate"
    assert event.event_type == "rejected" and "Duplicate" in event.event_summary


def test_approval_creates_event_after_ready() -> None:
    ready, _ = mark_ready(review(), [source()], "Reviewer")
    approved, event = approve_enrichment_review(
        ready, [source()], EnrichmentDecisionRequest(reviewer="Approver", reason="Verified")
    )
    assert approved.review_status == "approved_for_catalogue"
    assert event.event_type == "approved"


def test_generated_description_does_not_copy_restricted_text() -> None:
    result = generate_enrichment_review(profile(), [source()])
    assert "RESTRICTED SOURCE TEXT" not in result.description_original
    assert "ratings" not in result.description_original.casefold()


def test_enrichment_csv_templates_have_expected_headers() -> None:
    expected = {
        "enrichment_sources.csv": {
            "source_name",
            "commercial_use_allowed",
            "can_copy_text",
            "source_confidence",
        },
        "enrichment_reviews.csv": {
            "profile_draft_id",
            "description_original",
            "licensing_risk",
            "review_status",
        },
        "profile_source_links.csv": {"profile_draft_id", "enrichment_source_id", "usage_type"},
        "enrichment_validation_report.csv": {"profile_draft_id", "status", "error"},
    }
    for filename, required in expected.items():
        with (ROOT / "data" / filename).open(newline="", encoding="utf-8") as handle:
            headers = set(next(csv.reader(handle)))
        assert required <= headers
        assert headers.isdisjoint(
            {"AED", "USD", "QTY", "CN CODE", "SUPPLIER CODE", "PRICE", "COST"}
        )


class FakeEnrichmentRepository:
    def __init__(self):
        self.reviews = {}
        self.events = []
        self.sources = [source()]

    def list_sources(self):
        return self.sources

    def add_source(self, payload):
        return payload

    def list_reviews(self):
        return list(self.reviews.values())

    def get_review(self, review_id):
        return self.reviews.get(review_id)

    def profiles_for_generation(self, request: EnrichmentGenerateRequest):
        return [profile()] if not self.reviews else []

    def linked_sources(self, profile_draft_id):
        return self.sources

    def add_review(self, payload):
        now = datetime.now(UTC)
        record = EnrichmentReviewRead(id=1, created_at=now, updated_at=now, **payload.model_dump())
        self.reviews[1] = record
        return record

    def commit_generated(self, reviews, events):
        self.events.extend(events)
        return reviews

    def save_with_event(self, review, event):
        self.reviews[review.id] = review
        self.events.append(event)
        return review


@pytest.fixture
def api_client():
    repository = FakeEnrichmentRepository()
    app.dependency_overrides[get_enrichment_repository] = lambda: repository
    try:
        yield TestClient(app), repository
    finally:
        app.dependency_overrides.clear()


def test_api_rejection_persists_event(api_client) -> None:
    client, repository = api_client
    review_id = client.post("/enrichment-reviews/generate", json={}).json()[0]["id"]
    response = client.post(
        f"/enrichment-reviews/{review_id}/reject",
        json={
            "reviewer": "Reviewer",
            "reason": "More sources needed",
            "rejection_status": "requires_more_sources",
        },
    )
    assert response.status_code == 200
    assert repository.events[-1].event_type == "rejected"
