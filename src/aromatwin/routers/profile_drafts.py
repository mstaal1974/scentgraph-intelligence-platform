from types import SimpleNamespace

from fastapi import APIRouter, HTTPException

from aromatwin.schemas.profile_draft import (
    ProfileDraftDecisionRequest,
    ProfileDraftGenerateRequest,
    ProfileDraftRead,
)
from aromatwin.services.profile_builder import (
    ProfileDraft,
    approve_profile_draft,
    build_profile_draft,
    reject_profile_draft,
)

router = APIRouter(prefix="/profile-drafts", tags=["profile drafts"])
_DRAFTS: list[ProfileDraft] = []


def _get(profile_draft_id: int) -> ProfileDraft:
    draft = next((item for item in _DRAFTS if item.id == profile_draft_id), None)
    if draft is None:
        raise HTTPException(404, "Profile draft not found")
    return draft


@router.get("", response_model=list[ProfileDraftRead])
def list_profile_drafts() -> list[ProfileDraft]:
    return _DRAFTS


@router.get("/{profile_draft_id}", response_model=ProfileDraftRead)
def get_profile_draft(profile_draft_id: int) -> ProfileDraft:
    return _get(profile_draft_id)


@router.post("/generate", response_model=ProfileDraftRead, status_code=201)
def generate_profile_draft(request: ProfileDraftGenerateRequest) -> ProfileDraft:
    supplier = SimpleNamespace(
        id=request.supplier_item_id,
        normalised_brand=request.supplier_brand,
        normalised_name=request.supplier_name,
    )
    candidate = SimpleNamespace(
        id=request.match_candidate_id,
        supplier_item_id=request.supplier_item_id,
        candidate_brand=request.candidate_brand,
        candidate_fragrance_name=request.candidate_fragrance_name,
        candidate_concentration=request.candidate_concentration,
        candidate_source_type=request.candidate_source_type,
        candidate_source_reference=request.candidate_source_reference,
        match_confidence=request.match_confidence,
    )
    draft = build_profile_draft(supplier, candidate, draft_id=len(_DRAFTS) + 1)
    _DRAFTS.append(draft)
    return draft


@router.post("/{profile_draft_id}/approve", response_model=ProfileDraftRead)
def approve_draft(
    profile_draft_id: int, decision: ProfileDraftDecisionRequest
) -> ProfileDraft:
    draft = _get(profile_draft_id)
    try:
        approved = approve_profile_draft(draft)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    _DRAFTS[_DRAFTS.index(draft)] = approved
    return approved


@router.post("/{profile_draft_id}/reject", response_model=ProfileDraftRead)
def reject_draft(
    profile_draft_id: int, decision: ProfileDraftDecisionRequest
) -> ProfileDraft:
    draft = _get(profile_draft_id)
    try:
        rejected = reject_profile_draft(draft, decision.reason or "")
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    _DRAFTS[_DRAFTS.index(draft)] = rejected
    return rejected

