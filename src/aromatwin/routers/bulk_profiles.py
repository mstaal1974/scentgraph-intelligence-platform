"""Internal workflow endpoints with public-safe response models."""

from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.bulk_profile_generation import (
    BulkProfileDraftPublicSummary,
    BulkProfileGenerationRequest,
    BulkProfileGenerationResult,
    EnrichmentResearchQueueItem,
    EnrichmentResearchQueueResult,
    ProfileCoverageRead,
    ProfileCoverageReport,
    ProfileGenerationAuditReport,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.bulk_profile_generation import (
    BulkProfileDraft,
    generate_bulk_profile_drafts,
    load_records,
    public_safe_draft,
)
from aromatwin.services.enrichment_research_queue import (
    ResearchQueueItem,
    build_enrichment_research_queue,
)
from aromatwin.services.profile_coverage import (
    ProfileCoverage,
    build_profile_coverage,
    coverage_summary,
)

router = APIRouter(prefix="/bulk-profiles", tags=["internal bulk profiles"],
                   dependencies=[Depends(require_private_api_key)])
_OFFERS: list[dict[str, object]] = []
_MATCHES: list[dict[str, object]] = []
_DRAFTS: list[BulkProfileDraft] = []
_COVERAGE: list[ProfileCoverage] = []
_QUEUE: list[ResearchQueueItem] = []


def _private_records(path: str | None) -> list[dict[str, object]]:
    if not path:
        return []
    source = Path(path)
    if Path("data/private").resolve() not in source.resolve().parents:
        raise ValueError("Workflow inputs must be under data/private/")
    return load_records(source)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal", "response_policy": "public_safe"}


@router.post("/generate", response_model=BulkProfileGenerationResult)
def generate(request: BulkProfileGenerationRequest) -> dict[str, object]:
    try:
        offers = _private_records(request.private_offer_path)
        matches = _private_records(request.private_match_candidate_path)
        existing = _private_records(request.private_existing_draft_path)
    except (OSError, ValueError) as error:
        raise HTTPException(422, str(error)) from error
    outcome = generate_bulk_profile_drafts(offers, matches, [*existing, *_DRAFTS])
    _OFFERS[:] = offers
    _MATCHES[:] = matches
    _DRAFTS.extend(outcome.drafts)
    _refresh_coverage()
    return {"accepted_count": outcome.accepted_count, "rejected_count": outcome.rejected_count,
            "unique_candidate_count": outcome.unique_candidate_count,
            "skipped_duplicate_count": outcome.skipped_duplicate_count,
            "drafts": [public_safe_draft(item) for item in outcome.drafts]}


@router.get("/drafts", response_model=list[BulkProfileDraftPublicSummary])
def drafts() -> list[dict[str, object]]:
    return [public_safe_draft(item) for item in _DRAFTS]


@router.get("/drafts/{profile_draft_id}", response_model=BulkProfileDraftPublicSummary)
def draft(profile_draft_id: str) -> dict[str, object]:
    found = next((item for item in _DRAFTS if item.profile_draft_id == profile_draft_id), None)
    if found is None:
        raise HTTPException(404, "Bulk profile draft not found")
    return public_safe_draft(found)


def _refresh_coverage() -> None:
    _COVERAGE[:] = build_profile_coverage(_OFFERS, match_candidates=_MATCHES,
                                          profile_drafts=_DRAFTS)


@router.get("/coverage", response_model=list[ProfileCoverageRead])
def coverage() -> list[ProfileCoverage]:
    _refresh_coverage()
    return _COVERAGE


@router.get("/coverage/summary", response_model=ProfileCoverageReport)
def coverage_report() -> dict[str, object]:
    _refresh_coverage()
    return {**coverage_summary(_COVERAGE), "records": _COVERAGE}


@router.post("/research-queue/build", response_model=EnrichmentResearchQueueResult)
def research_queue_build() -> dict[str, object]:
    _refresh_coverage()
    _QUEUE[:] = build_enrichment_research_queue(_COVERAGE, _DRAFTS)
    return {"item_count": len(_QUEUE), "items": _QUEUE}


@router.get("/research-queue", response_model=list[EnrichmentResearchQueueItem])
def research_queue() -> list[ResearchQueueItem]:
    return _QUEUE


@router.get("/audit", response_model=ProfileGenerationAuditReport)
def audit() -> dict[str, object]:
    return {"draft_count": len(_DRAFTS), "coverage_count": len(_COVERAGE),
            "research_queue_count": len(_QUEUE),
            "all_require_human_review": all(item.review_status == "needs_human_review"
                                             for item in [*_DRAFTS, *_QUEUE]),
            "catalogue_records_generated": 0, "private_commercial_fields_exposed": False,
            "copied_third_party_content_stored": False,
            "details": {"policy": "review_only", "queue_preview": [asdict(x) for x in _QUEUE[:0]]}}
