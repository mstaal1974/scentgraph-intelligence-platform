from aromatwin.services.profile_production_readiness import assess_profile_production_readiness


def test_readiness_reports_missing_inputs_and_matches(tmp_path):
    report = assess_profile_production_readiness(data_root=tmp_path, output_path=tmp_path / "private/runs", intake_manifests=[], match_candidate_count=0, privacy_audit_available=True)
    assert report.overall_status == "blocked_missing_private_supplier_files"
    assert "private_supplier_files_not_detected" in report.blocking_issues
    assert "match_candidates_not_available" in report.blocking_issues


def test_readiness_blocks_public_output(tmp_path):
    report = assess_profile_production_readiness(data_root=tmp_path, output_path=tmp_path / "samples", intake_manifests=[{"readiness_status": "ready_for_import"}], match_candidate_count=1, privacy_audit_available=True)
    assert report.overall_status == "blocked_output_path_risk"
