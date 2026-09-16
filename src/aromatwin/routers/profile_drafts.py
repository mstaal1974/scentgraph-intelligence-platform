from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from aromatwin.database import get_db
from aromatwin.repositories.profile_drafts import ProfileDraftRepository
from aromatwin.schemas.profile_draft import (
    ProfileDraftDecisionRequest,
    ProfileDraftGenerateRequest,
    ProfileDraftRead,
)
from aromatwin.services.profile_builder import (
    approve_profile_draft,
    generate_profile_draft,
    reject_profile_draft,
)

router = APIRouter(prefix="/profile-drafts", tags=["profile drafts"])


def get_profile_draft_repository(db: Session = Depends(get_db)) -> ProfileDraftRepository:
    return ProfileDraftRepository(db)


@router.get("", response_model=list[ProfileDraftRead])
def list_profile_drafts(
    repository: ProfileDraftRepository = Depends(get_profile_draft_repository),
) -> list[object]:
    return repository.list()


@router.get("/{profile_draft_id}", response_model=ProfileDraftRead)
def get_profile_draft(
    profile_draft_id: int,
    repository: ProfileDraftRepository = Depends(get_profile_draft_repository),
) -> object:
    draft = repository.get(profile_draft_id)
    if draft is None:
        raise HTTPException(404, "Profile draft not found")
    return draft


@router.post("/generate", response_model=list[ProfileDraftRead], status_code=201)
def generate_profile_drafts(
    request: ProfileDraftGenerateRequest,
    repository: ProfileDraftRepository = Depends(get_profile_draft_repository),
) -> list[object]:
    existing = repository.existing_keys()
    created = []
    for source in repository.generation_sources(request):
        generated = generate_profile_draft(source.supplier, source.candidate)
        key = (generated.supplier_item_id, generated.match_candidate_id)
        if key in existing:
            continue
        created.append(repository.add(generated))
        existing.add(key)
    try:
        return repository.commit_created(created)
    except IntegrityError as error:
        raise HTTPException(409, "An active profile draft already exists") from error


@router.post("/{profile_draft_id}/approve", response_model=ProfileDraftRead)
def approve(
    profile_draft_id: int,
    decision: ProfileDraftDecisionRequest,
    repository: ProfileDraftRepository = Depends(get_profile_draft_repository),
) -> object:
    draft = repository.get(profile_draft_id)
    if draft is None:
        raise HTTPException(404, "Profile draft not found")
    try:
        approve_profile_draft(draft, decision, repository.approval_provenance(draft))
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    return repository.save(draft)


@router.post("/{profile_draft_id}/reject", response_model=ProfileDraftRead)
def reject(
    profile_draft_id: int,
    decision: ProfileDraftDecisionRequest,
    repository: ProfileDraftRepository = Depends(get_profile_draft_repository),
) -> object:
    draft = repository.get(profile_draft_id)
    if draft is None:
        raise HTTPException(404, "Profile draft not found")
    try:
        reject_profile_draft(draft, decision)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return repository.save(draft)
