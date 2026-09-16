from aromatwin.services.pilot_run_manifest import build_manifest, public_manifest_summary


def test_manifest_tracks_stage_outcomes_and_public_projection_is_minimal():
    result = {"run_id": "safe-run", "run_mode": "dry_run", "output_locations": [],
              "privacy_audit_status": "passed", "stage_results": [
                  {"stage": "one", "status": "completed", "blockers": []},
                  {"stage": "two", "status": "skipped", "blockers": []},
                  {"stage": "three", "status": "failed", "blockers": []}]}
    manifest = build_manifest(result=result, request={"input_locations": []})
    assert manifest["stages_completed"] == ["one"]
    assert manifest["stages_skipped"] == ["two"]
    assert manifest["stages_failed"] == ["three"]
    summary = public_manifest_summary(manifest, "blocked_low_confidence")
    assert set(summary) == {"run_id", "run_mode", "completed_count", "skipped_count",
                            "failed_count", "blocker_count", "privacy_audit_status",
                            "readiness_status"}
