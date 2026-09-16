from aromatwin.services.pilot_acceptance_report import build_acceptance_report


def test_acceptance_aggregates_and_never_recommends_public_launch():
    report = build_acceptance_report("run-1", [{"stage": "supplier_import", "status": "completed",
        "accepted_count": 2, "blocked_count": 1, "review_required_count": 3,
        "enrichment_required_count": 4}])
    assert (report.accepted_count, report.blocked_count, report.review_required_count,
            report.enrichment_required_count) == (2, 1, 3, 4)
    assert "public launch" not in report.recommended_next_step.lower()
