from fastapi import APIRouter, Depends, HTTPException

from aromatwin.routers.catalogue import _CATALOGUE
from aromatwin.schemas.scent_vector import (
    ScentVectorGenerateRequest,
    ScentVectorRead,
    ScentVectorReviewDecision,
    ScentVectorSimilarityRequest,
    ScentVectorSimilarityResult,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.scent_vector_engine import (
    ScentVector,
    approve_scent_vector,
    generate_scent_vector,
    public_vector,
    reject_scent_vector,
    similarity,
)

router = APIRouter(
    tags=["scent vectors"], dependencies=[Depends(require_private_api_key)]
)
_VECTORS: list[ScentVector] = []


def _read(vector: ScentVector) -> ScentVectorRead:
    payload = public_vector(vector)
    payload.pop("restricted_content_detected")
    payload.pop("private_fields_detected")
    return ScentVectorRead.model_validate(payload)


def _find(vector_id: int) -> ScentVector:
    vector = next((item for item in _VECTORS if item.id == vector_id), None)
    if vector is None:
        raise HTTPException(404, "Scent vector not found")
    return vector


@router.get("/scent-vectors", response_model=list[ScentVectorRead])
def list_vectors() -> list[ScentVectorRead]:
    return [_read(vector) for vector in _VECTORS]


@router.get("/scent-vectors/{scent_vector_id}", response_model=ScentVectorRead)
def get_vector(scent_vector_id: int) -> ScentVectorRead:
    return _read(_find(scent_vector_id))


@router.get("/catalogue/fragrances/{fragrance_id}/scent-vector", response_model=ScentVectorRead)
def get_fragrance_vector(fragrance_id: int) -> ScentVectorRead:
    vector = next((item for item in _VECTORS if item.fragrance_id == fragrance_id), None)
    if vector is None:
        raise HTTPException(404, "Scent vector not found")
    return _read(vector)


@router.post("/scent-vectors/generate", response_model=ScentVectorRead, status_code=201)
def generate_vector(request: ScentVectorGenerateRequest) -> ScentVectorRead:
    fragrance = next((item for item in _CATALOGUE if item.id == request.fragrance_id), None)
    if fragrance is None:
        raise HTTPException(422, "Only approved catalogue fragrances can receive scent vectors")
    try:
        vector = generate_scent_vector(fragrance, _VECTORS)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    prior = next((item for item in _VECTORS if item.fragrance_id == vector.fragrance_id), None)
    if prior is None:
        _VECTORS.append(vector)
    elif prior != vector:
        _VECTORS[_VECTORS.index(prior)] = vector
    return _read(vector)


@router.post("/scent-vectors/{scent_vector_id}/approve", response_model=ScentVectorRead)
def approve_vector(scent_vector_id: int) -> ScentVectorRead:
    current = _find(scent_vector_id)
    try:
        updated = approve_scent_vector(current)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    _VECTORS[_VECTORS.index(current)] = updated
    return _read(updated)


@router.post("/scent-vectors/{scent_vector_id}/reject", response_model=ScentVectorRead)
def reject_vector(scent_vector_id: int, decision: ScentVectorReviewDecision) -> ScentVectorRead:
    current = _find(scent_vector_id)
    try:
        updated = reject_scent_vector(current, decision.reason or "")
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    _VECTORS[_VECTORS.index(current)] = updated
    return _read(updated)


@router.post("/scent-vectors/similarity", response_model=list[ScentVectorSimilarityResult])
def compare_vectors(request: ScentVectorSimilarityRequest) -> list[ScentVectorSimilarityResult]:
    source = _find(request.scent_vector_id)
    candidates = [item for item in _VECTORS if item.id != source.id]
    if request.candidate_vector_ids:
        candidates = [item for item in candidates if item.id in request.candidate_vector_ids]
    try:
        results = [
            ScentVectorSimilarityResult(
                scent_vector_id=source.id,
                candidate_vector_id=item.id,
                fragrance_id=item.fragrance_id,
                similarity_score=similarity(source, item),
            )
            for item in candidates
        ]
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return sorted(results, key=lambda item: (-item.similarity_score, item.candidate_vector_id))
