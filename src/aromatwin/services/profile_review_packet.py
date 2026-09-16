"""Build public-safe guidance packets for human profile review."""

from datetime import UTC, datetime
from hashlib import sha256

from aromatwin.schemas.profile_production import PrivateProfileDraftRead, ProfileReviewPacketRead

QUESTIONS = [
    "Is the fragrance identity correct?",
    "Are the note pyramid fields supported?",
    "Are accords supported?",
    "Is the profile copy original?",
    "Are mood, occasion and season tags reasonable?",
    "Is provenance sufficient?",
    "Should this profile be approved for catalogue review, returned for enrichment or rejected?",
]


def build_profile_review_packet(draft: PrivateProfileDraftRead, run_id: str, *, now: datetime | None = None) -> ProfileReviewPacketRead:
    missing = []
    for field in ("inferred_family", "top_notes", "heart_notes", "base_notes", "accords", "mood_tags", "occasion_tags", "season_tags", "strength_band", "longevity_band", "projection_band"):
        if not getattr(draft, field):
            missing.append(field)
    digest = sha256(f"{run_id}|{draft.profile_draft_id}".encode()).hexdigest()[:12]
    gate = "identity_review" if draft.confidence_band == "low" else "enrichment_review" if missing else "provenance_review"
    return ProfileReviewPacketRead(
        review_packet_id=f"prp-{digest}", run_id=run_id,
        profile_draft_id=draft.profile_draft_id,
        fragrance_display_name=draft.fragrance_display_name,
        brand_display_name=draft.brand_display_name, confidence_band=draft.confidence_band,
        evidence_status=draft.evidence_status, provenance_status=draft.provenance_status,
        enrichment_status=draft.enrichment_status, missing_fields=missing,
        reviewer_questions=list(QUESTIONS), recommended_review_gate=gate,
        recommended_decision_options=["approve_for_catalogue_review", "return_for_enrichment", "reject"],
        public_safe_summary=draft.public_safe_summary, created_at=now or datetime.now(UTC),
    )
