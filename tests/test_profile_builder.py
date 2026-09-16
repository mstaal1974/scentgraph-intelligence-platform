import csv
from datetime import UTC, datetime
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from aromatwin.main import app
from aromatwin.repositories.profile_drafts import GenerationSource
from aromatwin.routers.profile_drafts import get_profile_draft_repository
from aromatwin.schemas.profile_draft import (
    ProfileDraftDecisionRequest,
    ProfileDraftGenerateRequest,
    ProfileDraftRead,
    ProfileDraftStatus,
)
from aromatwin.services.profile_builder import (
    RESTRICTED_INPUT_FIELDS,
    approve_profile_draft,
    generate_profile_draft,
    reject_profile_draft,
)

ROOT = Path(__file__).resolve().parents[1]


def supplier() -> dict[str, object]:
    return {
        "id": 1,
        "normalised_brand": "Supplier Brand",
        "normalised_name": "Supplier Scent",
        "aed_price": "100",
        "supplier_cn_code": "SECRET",
    }


def candidate() -> dict[str, object]:
    return {
        "id": 2,
        "supplier_item_id": 1,
        "candidate_brand": "Candidate Brand",
        "candidate_fragrance_name": "Candidate Scent",
        "candidate_source_type": "reference_only",
        "match_confidence": "0.9",
        "description": "restricted prose",
        "reviews": "restricted review",
        "images": "restricted.jpg",
        "ratings": "5",
    }


def read_draft(identifier: int = 1) -> ProfileDraftRead:
    created = generate_profile_draft(supplier(), candidate())
    now = datetime.now(UTC)
    return ProfileDraftRead(id=identifier, created_at=now, updated_at=now, **created.model_dump())


def restricted_evidence() -> list[dict[str, object]]:
    return [
        {
            "source_name": "Reference DB",
            "source_type": "reference_only",
            "source_reference": "row-1",
            "source_url": None,
            "licence_status": "restricted_non_commercial",
            "commercial_use_allowed": False,
            "confidence": 0.9,
        }
    ]


def official_evidence() -> list[dict[str, object]]:
    return [
        {
            "source_name": "Official brand",
            "source_type": "official_source",
            "source_reference": "product-1",
            "source_url": "https://brand.example/product-1",
            "licence_status": "official_source",
            "commercial_use_allowed": True,
            "confidence": 0.9,
        }
    ]


class FakeRepository:
    def __init__(self):
        self.records: dict[int, ProfileDraftRead] = {}
        self.evidence = restricted_evidence()

    def list(self):
        return list(self.records.values())

    def get(self, draft_id):
        return self.records.get(draft_id)

    def existing_keys(self):
        return {(item.supplier_item_id, item.match_candidate_id) for item in self.records.values()}

    def generation_sources(self, request: ProfileDraftGenerateRequest):
        return [GenerationSource(supplier(), candidate(), restricted_evidence())]

    def add(self, draft):
        record = read_draft(max(self.records, default=0) + 1).model_copy(update=draft.model_dump())
        self.records[record.id] = record
        return record

    def commit_created(self, drafts):
        return drafts

    def approval_provenance(self, draft):
        return self.evidence

    def save(self, draft):
        self.records[draft.id] = draft
        return draft


@pytest.fixture
def api_client():
    repository = FakeRepository()
    app.dependency_overrides[get_profile_draft_repository] = lambda: repository
    try:
        yield TestClient(app), repository
    finally:
        app.dependency_overrides.clear()


def test_draft_generation_from_supplier_and_match_candidate() -> None:
    draft = generate_profile_draft(supplier(), candidate())
    assert draft.supplier_item_id == 1 and draft.match_candidate_id == 2
    assert draft.profile_title == "Candidate Brand Candidate Scent"
    assert draft.confidence_score <= 0.35


def test_generated_drafts_always_need_human_review() -> None:
    assert (
        generate_profile_draft(supplier(), candidate()).review_status
        == ProfileDraftStatus.needs_human_review
    )


def test_reference_only_source_cannot_be_approved() -> None:
    decision = ProfileDraftDecisionRequest(reviewer="Reviewer", reason="Attempt")
    with pytest.raises(ValueError, match="lacks trusted"):
        approve_profile_draft(read_draft(), decision, restricted_evidence())


def test_official_source_still_requires_explicit_human_approval() -> None:
    decision = ProfileDraftDecisionRequest(reviewer="Reviewer", reason="Official source verified")
    approved = approve_profile_draft(
        read_draft().model_copy(update={"source_confidence": 0.8}), decision, official_evidence()
    )
    assert approved.review_status == ProfileDraftStatus.approved_for_catalogue
    assert approved.reviewer == "Reviewer"


def test_approval_rejects_low_draft_source_confidence() -> None:
    decision = ProfileDraftDecisionRequest(reviewer="Reviewer", reason="Official source verified")
    with pytest.raises(ValueError, match="source confidence"):
        approve_profile_draft(read_draft(), decision, official_evidence())


def test_approval_rejects_restricted_content_flag() -> None:
    decision = ProfileDraftDecisionRequest(reviewer="Reviewer", reason="Official source verified")
    flagged = read_draft().model_copy(
        update={"source_confidence": 0.8, "restricted_content_detected": True}
    )
    with pytest.raises(ValueError, match="restricted or copied content"):
        approve_profile_draft(flagged, decision, official_evidence())


def test_rejection_records_reason() -> None:
    decision = ProfileDraftDecisionRequest(
        reviewer="Reviewer",
        reason="Licensing risk",
        rejection_status=ProfileDraftStatus.rejected_licensing_risk,
    )
    rejected = reject_profile_draft(read_draft(), decision)
    assert rejected.rejection_reason == "Licensing risk" and rejected.rejected_at is not None


def test_profile_builder_does_not_copy_restricted_or_commercial_fields() -> None:
    payload = generate_profile_draft(supplier(), candidate()).model_dump()
    rendered = " ".join(str(value) for value in payload.values())
    assert all(
        value not in rendered
        for value in ("restricted prose", "restricted review", "SECRET", "100")
    )
    assert RESTRICTED_INPUT_FIELDS.isdisjoint(payload)


def test_profile_drafts_csv_headers() -> None:
    expected = {
        "id",
        "supplier_item_id",
        "match_candidate_id",
        "profile_title",
        "description_original",
        "description_generation_method",
        "confidence_score",
        "source_confidence",
        "provenance_notes",
        "restricted_content_detected",
        "top_notes_json",
        "heart_notes_json",
        "base_notes_json",
        "accords_json",
        "season_json",
        "occasion_json",
        "mood_json",
        "review_status",
        "reviewer",
        "rejection_reason",
        "approved_at",
        "rejected_at",
        "created_at",
        "updated_at",
    }
    with (ROOT / "data/profile_drafts.csv").open(newline="", encoding="utf-8") as handle:
        headers = set(next(csv.reader(handle)))
    assert expected <= headers
    assert headers.isdisjoint({"AED", "USD", "QTY", "CN CODE", "PRICE", "COST", "SUPPLIER CODE"})
    with (ROOT / "data/profile_drafts.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows and {row["review_status"] for row in rows} == {"needs_human_review"}


def test_approve_endpoint_rejects_insufficient_stored_provenance(api_client) -> None:
    client, repository = api_client
    identifier = client.post("/profile-drafts/generate", json={}).json()[0]["id"]
    response = client.post(
        f"/profile-drafts/{identifier}/approve",
        json={"reviewer": "Reviewer", "reason": "No independent source"},
    )
    assert response.status_code == 409
    assert repository.get(identifier).review_status == ProfileDraftStatus.needs_human_review


def test_reject_endpoint_stores_reason(api_client) -> None:
    client, _ = api_client
    identifier = client.post("/profile-drafts/generate", json={}).json()[0]["id"]
    response = client.post(
        f"/profile-drafts/{identifier}/reject",
        json={
            "reviewer": "Reviewer",
            "reason": "Duplicate candidate",
            "rejection_status": "rejected_duplicate",
        },
    )
    assert (
        response.status_code == 200 and response.json()["rejection_reason"] == "Duplicate candidate"
    )


def test_generate_endpoint_is_idempotent_for_active_drafts(api_client) -> None:
    client, _ = api_client
    assert len(client.post("/profile-drafts/generate", json={}).json()) == 1
    assert client.post("/profile-drafts/generate", json={}).json() == []
