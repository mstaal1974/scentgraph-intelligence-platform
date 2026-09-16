from fastapi import APIRouter, HTTPException

from aromatwin.schemas.match_candidate import MatchCandidateGenerateRequest, MatchCandidateRead

router = APIRouter(prefix="/match-candidates", tags=["candidate matching"])
_CANDIDATES: list[MatchCandidateRead] = []


@router.get("", response_model=list[MatchCandidateRead])
def list_candidates() -> list[MatchCandidateRead]:
    return _CANDIDATES


@router.get("/{candidate_id}", response_model=MatchCandidateRead)
def get_candidate(candidate_id: int) -> MatchCandidateRead:
    candidate = next((item for item in _CANDIDATES if item.id == candidate_id), None)
    if candidate is None:
        raise HTTPException(404, "Match candidate not found")
    return candidate


@router.post("/generate", response_model=MatchCandidateRead, status_code=201)
def generate_candidate(request: MatchCandidateGenerateRequest) -> MatchCandidateRead:
    return MatchCandidateRead(
        id=0,
        review_status="match_candidate",
        match_notes="Unpersisted foundation preview",
        **request.model_dump(),
    )
