import pytest

from aromatwin.persistence.database import (
    create_persistence_engine,
    create_session_factory,
    initialise_persistence,
)
from aromatwin.persistence.repositories import (
    ArtifactRepository,
    AuditEventRepository,
    ConsumerScentprintRepository,
    LaunchCandidateRepository,
    ProfileDraftRepository,
    ProvenanceRepository,
    ReviewItemRepository,
    RunRepository,
    SellerDemandRepository,
    StageRepository,
)


@pytest.fixture
def session():
    engine = create_persistence_engine("sqlite:///:memory:")
    initialise_persistence(engine)
    with create_session_factory(engine)() as value:
        yield value


def test_run_stage_and_artifact_repositories(session):
    run = RunRepository(session).create(
        run_id="run-1",
        run_mode="test",
        workflow_type="pilot",
        status="created",
        readiness_status="pending",
    )
    assert RunRepository(session).get_by_id("run-1") is run
    stage = StageRepository(session).append(
        run_id="run-1", stage_name="safe-stage", stage_status="completed"
    )
    assert StageRepository(session).list_by_run_id("run-1") == [stage]
    artifact = ArtifactRepository(session).create(
        run_id="run-1",
        artifact_type="report",
        artifact_label="private evidence",
        storage_location="data/private/evidence.json",
        storage_visibility="private",
        public_safe=False,
    )
    projection = ArtifactRepository(session).public_safe_projection(artifact)
    assert "storage_location" not in projection


def test_summary_and_review_repositories(session):
    profile = ProfileDraftRepository(session).create(
        profile_draft_id="draft-1",
        run_id="run-1",
        canonical_brand="Fictional Brand",
        canonical_fragrance_name="Fictional Scent",
        profile_status="draft",
        source_confidence_band="medium",
    )
    assert profile.review_status == "pending"
    review = ReviewItemRepository(session).create(
        review_item_id="review-1",
        linked_entity_type="profile",
        linked_entity_id="draft-1",
        review_type="quality",
        priority_band="normal",
    )
    ReviewItemRepository(session).update_status("review-1", "in_review")
    assert review.review_status == "in_review"
    launch = LaunchCandidateRepository(session).create(
        launch_candidate_id="launch-1",
        canonical_brand="Fictional Brand",
        canonical_fragrance_name="Fictional Scent",
        launch_priority_band="medium",
        margin_suitability_band="review",
        supplier_availability_band="unknown",
        seller_demand_band="unknown",
        consumer_interest_band="unknown",
    )
    assert launch.launch_status == "candidate"


def test_redacted_subject_provenance_and_audit_repositories(session):
    seller = SellerDemandRepository(session).create(
        demand_brief_id="demand-1",
        seller_public_label="Seller cohort A",
        seller_segment="pilot",
        demand_theme="format request",
    )
    consumer = ConsumerScentprintRepository(session).create(
        scentprint_id="scent-1", consumer_public_alias="Participant A"
    )
    assert seller.private_data_redacted and consumer.private_data_redacted
    assert "notes" not in SellerDemandRepository(session).public_safe_projection(seller)
    assert "email" not in ConsumerScentprintRepository(session).public_safe_projection(consumer)
    provenance = ProvenanceRepository(session).create(
        provenance_id="prov-1",
        linked_entity_type="profile",
        linked_entity_id="draft-1",
        source_type="authorised_internal",
        source_confidence_band="medium",
        permitted_use_status="reviewed",
        provenance_summary="Summary-only evidence.",
    )
    assert provenance.permitted_use_status == "reviewed"
    event = AuditEventRepository(session).append_audit_event(
        audit_event_id="audit-1",
        event_type="review_item_created",
        actor_type="system",
        linked_entity_type="review",
        linked_entity_id="review-1",
        event_summary="Review item created.",
        risk_level="low",
        privacy_boundary="internal_public_safe",
    )
    assert event.event_summary == "Review item created."
