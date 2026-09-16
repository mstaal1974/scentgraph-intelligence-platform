"""Orchestrate private, unapproved fragrance profile drafts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from aromatwin.schemas.profile_production import (
    PrivateProfileDraftPublicSummary,
    PrivateProfileDraftRead,
    ProfileBatchPlanRead,
    ProfileProductionRunRead,
)
from aromatwin.services.profile_review_packet import build_profile_review_packet

PRIVATE_RUN_ROOT = Path("data/private/runs")
MODES = {"dry_run", "private_batch_run", "review_packet_only"}


def _get(item: object, *names: str, default=None):
    for name in names:
        value = item.get(name) if isinstance(item, Mapping) else getattr(item, name, None)
        if value is not None:
            return value
    return default


def _list(item: object, name: str) -> list[str]:
    value = _get(item, name, default=[])
    return [str(part).strip() for part in value if str(part).strip()] if isinstance(value, list) else []


def _draft(candidate_id: str, item: object, label: str, timestamp: datetime) -> PrivateProfileDraftRead:
    confidence = float(_get(item, "confidence", "match_confidence", "source_confidence", default=0) or 0)
    band = "high" if confidence >= .8 else "medium" if confidence >= .6 else "low"
    top, heart, base, accords = (_list(item, name) for name in ("top_notes", "heart_notes", "base_notes", "accords"))
    unsupported = not (top and heart and base and accords)
    brand = str(_get(item, "brand_display_name", "candidate_brand", "canonical_brand", default="Identity pending review"))
    name = str(_get(item, "fragrance_display_name", "candidate_fragrance_name", "canonical_fragrance_name", default="Fragrance identity pending review"))
    digest = sha256(candidate_id.encode()).hexdigest()[:16]
    blockers = []
    if band == "low":
        blockers.append("candidate_identity_needs_human_review")
    if unsupported:
        blockers.append("profile_evidence_needs_enrichment")
    return PrivateProfileDraftRead(
        profile_draft_id=f"ppd-{digest}", fragrance_candidate_id=candidate_id,
        supplier_public_label=label, brand_display_name=brand, fragrance_display_name=name,
        inferred_family=_get(item, "inferred_family"), top_notes=top, heart_notes=heart,
        base_notes=base, accords=accords, mood_tags=_list(item, "mood_tags"),
        occasion_tags=_list(item, "occasion_tags"), season_tags=_list(item, "season_tags"),
        strength_band=_get(item, "strength_band"), longevity_band=_get(item, "longevity_band"),
        projection_band=_get(item, "projection_band"), confidence_band=band,
        evidence_status="needs_enrichment" if unsupported else "evidence_pending_review",
        provenance_status="needs_provenance_review", enrichment_status="needs_enrichment" if unsupported else "ready_for_review",
        review_status="needs_human_review", blocking_issues=blockers,
        public_safe_summary=f"Draft profile for {brand} {name}; evidence and provenance require human review.",
        created_at=timestamp,
    )


def public_safe_draft(draft: PrivateProfileDraftRead) -> PrivateProfileDraftPublicSummary:
    return PrivateProfileDraftPublicSummary(**draft.model_dump())


def run_private_profile_production(
    plan: ProfileBatchPlanRead, match_summaries: list[object], *, mode: str = "dry_run",
    run_id: str | None = None, private_root: str | Path = PRIVATE_RUN_ROOT,
    now: datetime | None = None,
) -> tuple[ProfileProductionRunRead, list[PrivateProfileDraftRead], list[object]]:
    if mode not in MODES:
        raise ValueError(f"Unsupported production mode: {mode}")
    timestamp = now or datetime.now(UTC)
    identifier = run_id or plan.source_run_id
    by_id = {str(_get(item, "fragrance_candidate_id", "match_candidate_id", "candidate_id", "id", default="")): item for item in match_summaries}
    drafts = [_draft(candidate_id, by_id.get(candidate_id, {}), plan.supplier_public_label, timestamp) for candidate_id in plan.selected_candidate_ids]
    packets = [build_profile_review_packet(draft, identifier, now=timestamp) for draft in drafts]
    run = ProfileProductionRunRead(
        run_id=identifier, mode=mode, batch_plan_id=plan.batch_plan_id, draft_count=len(drafts),
        enrichment_queue_count=sum(d.enrichment_status == "needs_enrichment" for d in drafts),
        provenance_review_count=len(drafts), review_gate_count=len(drafts), review_packet_count=len(packets),
        drafts=[public_safe_draft(d) for d in drafts],
        status="dry_run_complete" if mode == "dry_run" else "review_packets_built" if mode == "review_packet_only" else "drafts_created_awaiting_human_review",
        created_at=timestamp,
    )
    if mode == "private_batch_run":
        root = Path(private_root).resolve()
        destination = (root / identifier / "profiles").resolve()
        expected = (Path("data/private").resolve())
        if not destination.is_relative_to(expected):
            raise ValueError("Private profile outputs must remain under data/private/runs/{run_id}/profiles")
        destination.mkdir(parents=True, exist_ok=True)
        payloads = {
            "drafts.json": [draft.model_dump(mode="json") for draft in drafts],
            "public_safe_summaries.json": [public_safe_draft(d).model_dump(mode="json") for d in drafts],
            "enrichment_queue.json": [{"profile_draft_id": d.profile_draft_id, "status": d.enrichment_status} for d in drafts],
            "provenance_review.json": [{"profile_draft_id": d.profile_draft_id, "status": d.provenance_status} for d in drafts],
            "review_gates.json": [{"profile_draft_id": d.profile_draft_id, "gate": "human_profile_review", "status": "pending"} for d in drafts],
            "review_packets.json": [packet.model_dump(mode="json") for packet in packets],
            "run.json": run.model_dump(mode="json"),
            "audit_events.json": [{"event": "private_profile_drafts_created", "run_id": identifier, "approval": "not_granted", "created_at": timestamp.isoformat()}],
        }
        for filename, payload in payloads.items():
            (destination / filename).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return run, drafts, packets
