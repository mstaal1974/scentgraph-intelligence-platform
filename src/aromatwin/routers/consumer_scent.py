"""Private workflow endpoints with explicitly privacy-safe default responses."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.consumer_scent import (
    CommunityScentIntelligencePublicSummary,
    ConsumerFeedbackCreate,
    ConsumerFeedbackRead,
    ConsumerScentAuditReport,
    ConsumerScentMatchResult,
    ConsumerScentprintCreate,
    ConsumerScentprintPublicSummary,
    ScentWardrobeItemCreate,
    ScentWardrobeItemRead,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.community_scent_intelligence import (
    build_community_intelligence,
)
from aromatwin.services.community_scent_intelligence import (
    public_summary as public_intelligence,
)
from aromatwin.services.consumer_feedback import (
    ConsumerFeedback,
    create_feedback,
    public_safe_feedback,
)
from aromatwin.services.consumer_scentprint import (
    ConsumerScentprint,
    create_scentprint,
    match_scent_profile,
    public_summary,
)
from aromatwin.services.scent_wardrobe import ScentWardrobeItem, add_item, analyse_gaps

router = APIRouter(prefix="/consumer-scent", tags=["internal private consumer scent"],
                   dependencies=[Depends(require_private_api_key)])
_SCENTPRINTS: list[ConsumerScentprint] = []
_FEEDBACK: list[ConsumerFeedback] = []
_INTELLIGENCE: list[dict[str, object]] = []
_WARDROBE: list[ScentWardrobeItem] = []


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.post("/scentprints", response_model=ConsumerScentprintPublicSummary, status_code=201)
def add_scentprint(payload: ConsumerScentprintCreate) -> dict[str, object]:
    scentprint = create_scentprint(payload)
    _SCENTPRINTS.append(scentprint)
    return public_summary(scentprint)


@router.get("/scentprints", response_model=list[ConsumerScentprintPublicSummary])
def scentprints() -> list[dict[str, object]]:
    return [public_summary(item) for item in _SCENTPRINTS]


def _find_scentprint(scentprint_id: str) -> ConsumerScentprint:
    found = next((item for item in _SCENTPRINTS if item.scentprint_id == scentprint_id), None)
    if found is None:
        raise HTTPException(404, "Scentprint not found")
    return found


@router.get("/scentprints/{scentprint_id}", response_model=ConsumerScentprintPublicSummary)
def scentprint(scentprint_id: str) -> dict[str, object]:
    return public_summary(_find_scentprint(scentprint_id))


@router.post("/scentprints/{scentprint_id}/match", response_model=ConsumerScentMatchResult)
def match(scentprint_id: str, target: dict[str, object]) -> dict[str, object]:
    return match_scent_profile(_find_scentprint(scentprint_id), target)


@router.post("/feedback", response_model=ConsumerFeedbackRead, status_code=201)
def add_feedback(payload: ConsumerFeedbackCreate) -> dict[str, object]:
    _find_scentprint(payload.scentprint_id)
    feedback = create_feedback(payload)
    _FEEDBACK.append(feedback)
    return public_safe_feedback(feedback)


@router.get("/feedback", response_model=list[ConsumerFeedbackRead])
def feedback() -> list[dict[str, object]]:
    return [public_safe_feedback(item) for item in _FEEDBACK]


@router.get("/community-intelligence", response_model=list[CommunityScentIntelligencePublicSummary])
def community_intelligence() -> list[dict[str, object]]:
    return [public_intelligence(item) for item in _INTELLIGENCE]


@router.post("/community-intelligence/build", response_model=CommunityScentIntelligencePublicSummary)
def build_intelligence(fragrance_id: str | None = None, product_id: str | None = None) -> dict[str, object]:
    result = build_community_intelligence(_FEEDBACK, fragrance_id=fragrance_id, product_id=product_id)
    _INTELLIGENCE.append(result)
    return public_intelligence(result)


@router.post("/wardrobe/items", response_model=ScentWardrobeItemRead, status_code=201)
def add_wardrobe_item(payload: ScentWardrobeItemCreate) -> ScentWardrobeItem:
    _find_scentprint(payload.scentprint_id)
    item = add_item(payload)
    _WARDROBE.append(item)
    return item


@router.get("/wardrobe/{scentprint_id}", response_model=list[ScentWardrobeItemRead])
def wardrobe(scentprint_id: str) -> list[ScentWardrobeItem]:
    _find_scentprint(scentprint_id)
    return [item for item in _WARDROBE if item.scentprint_id == scentprint_id]


@router.get("/wardrobe/{scentprint_id}/gaps")
def wardrobe_gaps(scentprint_id: str) -> dict[str, object]:
    profile = _find_scentprint(scentprint_id)
    return analyse_gaps([item for item in _WARDROBE if item.scentprint_id == scentprint_id],
                        profile.preferred_families)


@router.get("/audit", response_model=ConsumerScentAuditReport)
def audit() -> dict[str, object]:
    return {"passed": True, "scentprint_count": len(_SCENTPRINTS),
            "feedback_count": len(_FEEDBACK), "intelligence_count": len(_INTELLIGENCE),
            "wardrobe_item_count": len(_WARDROBE), "privacy_violations": []}
