from aromatwin.services.profile_pipeline_gap_report import build_profile_pipeline_gap_report


def test_gap_report_keeps_operator_tasks_open_and_separate():
    report = build_profile_pipeline_gap_report("fictional-rehearsal-001")
    assert report.operator_task_count
    assert report.code_gap_count == sum(not g.operator_action_required for g in report.gaps)
    assert any(g.category == "manual_operator_step" for g in report.gaps)
    assert all(not g.can_fix_automatically for g in report.gaps)
