"""Build and persist value-free operational evidence for pilot runs."""

import json
from datetime import UTC, datetime
from pathlib import Path

PRIVACY_NOTES = [
    "Commercial source values remain inside approved private source systems.",
    "Seller and consumer records are not copied into workflow artifacts.",
    "Public projections contain only counts, statuses, bands, and remediation summaries.",
]


def build_manifest(*, result: dict[str, object], request: dict[str, object]) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    stages = list(result["stage_results"])
    blockers = [blocker for stage in stages for blocker in stage.get("blockers", [])]
    return {
        "run_id": result["run_id"], "run_mode": result["run_mode"],
        "source_input_type": request.get("source_input_type", "private_files"),
        "source_input_label": request.get("source_input_label", "private pilot input"),
        "private_input_paths": list(request.get("input_locations", [])),
        "private_output_paths": list(result["output_locations"]),
        "public_sample_output_paths": [],
        "stages_requested": [stage["stage"] for stage in stages],
        "stages_completed": [stage["stage"] for stage in stages if stage["status"] == "completed"],
        "stages_skipped": [stage["stage"] for stage in stages if stage["status"] == "skipped"],
        "stages_failed": [stage["stage"] for stage in stages if stage["status"] == "failed"],
        "audit_results": {"privacy": str(result["privacy_audit_status"])},
        "privacy_boundary_notes": PRIVACY_NOTES, "blocking_issues": blockers,
        "generated_artifacts": list(result["output_locations"]), "created_at": now,
        "updated_at": now,
    }


def public_manifest_summary(manifest: dict[str, object], readiness_status: str) -> dict[str, object]:
    return {
        "run_id": manifest["run_id"], "run_mode": manifest["run_mode"],
        "completed_count": len(manifest["stages_completed"]),
        "skipped_count": len(manifest["stages_skipped"]),
        "failed_count": len(manifest["stages_failed"]),
        "blocker_count": len(manifest["blocking_issues"]),
        "privacy_audit_status": manifest["audit_results"]["privacy"],
        "readiness_status": readiness_status,
    }


def write_manifest(manifest: dict[str, object], run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    target = run_dir / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return target
