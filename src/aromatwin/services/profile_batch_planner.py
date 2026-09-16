"""Plan bounded profile batches without carrying supplier-commercial values."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from hashlib import sha256

from aromatwin.schemas.profile_production import ProfileBatchControls, ProfileBatchPlanRead


def _get(record: object, *names: str, default=None):
    for name in names:
        value = record.get(name) if isinstance(record, Mapping) else getattr(record, name, None)
        if value is not None:
            return value
    return default


def _band(confidence: float) -> str:
    return "high" if confidence >= 0.8 else "medium" if confidence >= 0.6 else "low"


def build_profile_batch_plan(
    intake_manifests: Iterable[object], match_summaries: Iterable[object],
    controls: ProfileBatchControls | None = None, *, source_run_id: str | None = None,
    now: datetime | None = None,
) -> ProfileBatchPlanRead:
    controls = controls or ProfileBatchControls()
    intakes, matches = list(intake_manifests), list(match_summaries)
    timestamp = now or datetime.now(UTC)
    run_id = source_run_id or f"profile-{timestamp:%Y%m%d%H%M%S}"
    ready = [item for item in intakes if _get(item, "readiness_status") == "ready_for_import"]
    blockers: list[str] = []
    warnings: list[str] = []
    if not intakes:
        blockers.append("no_private_supplier_intake")
    elif controls.require_supplier_intake_ready and not ready:
        blockers.append("supplier_intake_not_ready")
    label = controls.supplier_public_label or str(_get((ready or intakes or [{}])[0], "supplier_public_label", default="private-supplier"))
    seen: set[str] = set()
    selected: list[str] = []
    bands = {"high": 0, "medium": 0, "low": 0}
    skipped = blocked = duplicates = 0
    for index, item in enumerate(matches, 1):
        candidate_id = str(_get(item, "fragrance_candidate_id", "match_candidate_id", "candidate_id", "id", default="")).strip()
        if not candidate_id:
            blocked += 1
            continue
        if candidate_id in seen:
            duplicates += 1
            if not controls.include_duplicates:
                skipped += 1
                continue
        seen.add(candidate_id)
        confidence = float(_get(item, "confidence", "match_confidence", "source_confidence", default=0) or 0)
        status = str(_get(item, "status", "match_status", default="candidate"))
        is_blocked = status.startswith("blocked") or confidence < controls.confidence_threshold
        if is_blocked and not controls.include_low_confidence:
            blocked += 1
            continue
        if len(selected) >= controls.max_profiles:
            skipped += 1
            continue
        selected.append(candidate_id)
        bands[_band(confidence)] += 1
    if controls.require_match_candidate and not matches:
        blockers.append("no_match_candidates")
    if not selected and matches:
        blockers.append("no_eligible_match_candidates")
    if bands["low"]:
        warnings.append("low_confidence_candidates_require_human_identity_review")
    action = ("Resolve blocking issues before profile generation." if blockers else
              "Run a dry run and inspect the human-review queue." if controls.dry_run else
              "Run the private batch; drafts remain unapproved.")
    digest = sha256(f"{run_id}|{label}|{'|'.join(selected)}".encode()).hexdigest()[:12]
    return ProfileBatchPlanRead(
        batch_plan_id=f"pbp-{digest}", source_run_id=run_id, supplier_public_label=label,
        planned_profile_count=len(selected), skipped_count=skipped, blocked_count=blocked,
        duplicate_count=duplicates, confidence_band_summary=bands,
        selected_candidate_ids=selected,
        required_review_gates=["identity_review", "evidence_review", "provenance_review", "catalogue_review"],
        required_enrichment_steps=["note_pyramid", "accords", "context_tags", "performance_bands"],
        privacy_checks_required=["private_output_path", "commercial_field_exclusion", "original_copy"],
        blocking_issues=blockers, warnings=warnings, recommended_next_action=action,
        created_at=timestamp,
    )
