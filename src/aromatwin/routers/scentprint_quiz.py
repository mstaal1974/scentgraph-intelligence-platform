"""Stateless public-safe Scentprint quiz endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.scentprint_quiz import (
    ScentprintQuizAuditReport,
    ScentprintQuizContractRead,
    ScentprintQuizQuestionRead,
    ScentprintQuizResponseCreate,
    ScentprintQuizResultRead,
    ScentprintQuizVectorRead,
)
from aromatwin.security import require_public_api_key
from aromatwin.services.scentprint_quiz_contracts import (
    QUIZ_CONTRACT_VERSION,
    get_quiz_contract,
    validate_quiz_contract,
)
from aromatwin.services.scentprint_quiz_results import build_quiz_result
from aromatwin.services.scentprint_quiz_scoring import score_quiz_responses

router = APIRouter(prefix="/scentprint-quiz", tags=["public scentprint quiz"], dependencies=[Depends(require_public_api_key)])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "storage": "none", "privacy_status": "public_safe_anonymous"}


@router.get("/contract", response_model=ScentprintQuizContractRead)
def contract() -> dict[str, object]:
    return get_quiz_contract()


@router.get("/questions", response_model=list[ScentprintQuizQuestionRead])
def questions() -> list[dict[str, object]]:
    return get_quiz_contract()["questions"]


@router.post("/score", response_model=ScentprintQuizVectorRead)
def score(payload: ScentprintQuizResponseCreate) -> dict[str, object]:
    try:
        return score_quiz_responses(payload.scentprint_public_alias,
                                    [item.model_dump() for item in payload.responses])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/results/demo", response_model=ScentprintQuizResultRead)
def demo_result(payload: ScentprintQuizResponseCreate) -> dict[str, object]:
    try:
        scored = score_quiz_responses(payload.scentprint_public_alias,
                                      [item.model_dump() for item in payload.responses])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return build_quiz_result(scored, demo_mode=True)


@router.get("/audit", response_model=ScentprintQuizAuditReport)
def audit() -> dict[str, object]:
    errors = validate_quiz_contract()
    return {"passed": not errors, "quiz_contract_version": QUIZ_CONTRACT_VERSION,
            "question_count": len(get_quiz_contract()["questions"]), "violations": errors,
            "privacy_status": "public_safe_anonymous"}
