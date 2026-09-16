"""Build local manifests describing—not performing—a potential Maison transfer."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aromatwin.schemas.maison_integration import MaisonSyncManifestRead, SyncMode


def build_sync_manifest(*, products: list[object] | None = None,
                        recommendations: list[object] | None = None,
                        scentprint_matches: list[object] | None = None,
                        bundles: list[object] | None = None, variant_count: int | None = None,
                        sync_mode: SyncMode = "dry_run", source_environment: str = "local",
                        export_files: list[str] | None = None, skipped_count: int = 0,
                        blocked_count: int = 0, review_status: str = "human_review_required",
                        privacy_status: str = "passed") -> MaisonSyncManifestRead:
    products, recommendations = products or [], recommendations or []
    scentprint_matches, bundles, export_files = scentprint_matches or [], bundles or [], export_files or []
    checksums = {}
    for name in export_files:
        path = Path(name)
        if path.is_file():
            checksums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    issues = [] if not blocked_count else ["One or more records were blocked from export."]
    next_action = ("Obtain human review before any staging contract test."
                   if review_status != "approved" else "Review this manifest for staging use only.")
    return MaisonSyncManifestRead(
        sync_manifest_id=f"maison-sync-{uuid4().hex[:12]}", sync_mode=sync_mode,
        source_environment=source_environment, generated_at=datetime.now(UTC),
        product_count=len(products), variant_count=variant_count if variant_count is not None else len(products),
        recommendation_count=len(recommendations), scentprint_match_count=len(scentprint_matches),
        bundle_count=len(bundles), skipped_count=skipped_count, blocked_count=blocked_count,
        export_files=[Path(name).name for name in export_files], checksums=checksums,
        review_status=review_status, privacy_status=privacy_status, blocking_issues=issues,
        recommended_next_action=next_action,
    )


class MaisonSyncManifestService:
    build = staticmethod(build_sync_manifest)
