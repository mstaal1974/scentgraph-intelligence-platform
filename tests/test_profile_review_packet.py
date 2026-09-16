from datetime import UTC, datetime

from aromatwin.schemas.profile_production import PrivateProfileDraftRead
from aromatwin.services.profile_review_packet import build_profile_review_packet


def test_review_packet_has_questions_and_no_commercial_fields():
    draft = PrivateProfileDraftRead(profile_draft_id="draft-1", fragrance_candidate_id="candidate-1", supplier_public_label="fictional", brand_display_name="Fictional Atelier", fragrance_display_name="Cloud Archive", confidence_band="medium", evidence_status="needs_enrichment", provenance_status="needs_provenance_review", enrichment_status="needs_enrichment", review_status="needs_human_review", blocking_issues=[], public_safe_summary="Fictional draft", created_at=datetime.now(UTC))
    packet = build_profile_review_packet(draft, "run-1")
    assert len(packet.reviewer_questions) >= 7
    serialized = packet.model_dump_json().casefold()
    assert "supplier_price" not in serialized and "supplier_code" not in serialized
    assert packet.recommended_review_gate == "enrichment_review"
