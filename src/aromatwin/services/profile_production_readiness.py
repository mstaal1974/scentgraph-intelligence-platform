"""Preflight checks for safe private profile production."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aromatwin.schemas.profile_production import ProfileProductionReadinessReport
from aromatwin.services.private_supplier_intake import PrivateSupplierIntakeService


def _safe_output(path: Path, data_root: Path) -> bool:
    resolved = path.resolve()
    private = (data_root.resolve() / "private").resolve()
    return resolved == private or resolved.is_relative_to(private)


def assess_profile_production_readiness(
    *, data_root: str | Path = "data", output_path: str | Path = "data/private/runs",
    intake_manifests: list[object] | None = None, match_candidate_count: int | None = None,
    review_configured: bool = True, generation_available: bool = True,
    enrichment_available: bool = True, privacy_audit_available: bool | None = None,
    persistence_available: bool = False, now: datetime | None = None,
) -> ProfileProductionReadinessReport:
    root = Path(data_root)
    intakes = intake_manifests if intake_manifests is not None else PrivateSupplierIntakeService(root).scan()
    ready_intakes = [item for item in intakes if getattr(item, "readiness_status", None) == "ready_for_import" or (isinstance(item, dict) and item.get("readiness_status") == "ready_for_import")]
    matches = match_candidate_count if match_candidate_count is not None else _count_match_files(root)
    audit_available = privacy_audit_available if privacy_audit_available is not None else Path("scripts/audit_profile_production_privacy.py").is_file()
    safe = _safe_output(Path(output_path), root)
    blockers: list[str] = []
    actions: list[str] = []
    if not intakes:
        blockers.append("private_supplier_files_not_detected")
        actions.append("Place supplier files in data/private/imports and run private intake.")
    elif not ready_intakes:
        blockers.append("supplier_intake_not_ready")
        actions.append("Resolve supplier format or intake blockers.")
    if matches <= 0:
        blockers.append("match_candidates_not_available")
        actions.append("Run supplier matching and review candidate identities.")
    if not generation_available:
        blockers.append("profile_generation_unavailable")
    if not review_configured:
        blockers.append("review_gates_not_configured")
    if not audit_available:
        blockers.append("privacy_audit_unavailable")
    if not safe:
        blockers.append("unsafe_output_path")
        actions.append("Use data/private/runs/{run_id}/profiles for operational outputs.")
    if not generation_available:
        overall = "blocked_generation_unavailable"
    elif not safe:
        overall = "blocked_output_path_risk"
    elif not audit_available:
        overall = "blocked_privacy_risk"
    elif not intakes:
        overall = "blocked_missing_private_supplier_files"
    elif not ready_intakes:
        overall = "ready_after_supplier_files_added"
    elif matches <= 0:
        overall = "blocked_missing_match_candidates"
    elif not review_configured:
        overall = "ready_after_review_configured"
    else:
        overall = "ready_for_private_profile_batch"
    return ProfileProductionReadinessReport(
        readiness_id=f"ppr-{(now or datetime.now(UTC)):%Y%m%d%H%M%S%f}", overall_status=overall,
        supplier_intake_status="ready" if ready_intakes else "missing" if not intakes else "blocked",
        matching_status="ready" if matches > 0 else "missing", profile_generation_status="available" if generation_available else "unavailable",
        enrichment_status="available" if enrichment_available else "unavailable",
        review_status="configured" if review_configured else "not_configured",
        persistence_status="available" if persistence_available else "private_local_output_available",
        privacy_status="available" if audit_available else "blocked",
        output_path_status="safe_private_path" if safe else "unsafe_public_path",
        blocking_issues=blockers,
        warnings=[] if persistence_available else ["persistence_not_configured_using_private_local_output"],
        required_operator_actions=actions,
        recommended_next_step="Build a bounded private profile batch plan." if not blockers else actions[0] if actions else "Resolve blocking issues.",
        created_at=now or datetime.now(UTC),
    )


def _count_match_files(root: Path) -> int:
    locations = (root / "private/matches", root / "private/staging/match_candidates")
    return sum(1 for location in locations if location.exists() for path in location.rglob("*") if path.suffix.lower() in {".csv", ".json"})
