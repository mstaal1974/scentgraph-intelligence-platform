from aromatwin.services.review_readiness import build_review_readiness


def test_readiness_summarises_roles_and_bottlenecks():
    report = build_review_readiness([
        {"review_status": "supplier_review_requested", "assigned_role": "supplier_reviewer",
         "risk_band": "blocked", "priority_band": "urgent"}
    ])
    assert report["readiness_status"] == "blocked_by_supplier_review"
    assert report["owner_role_summary"] == {"supplier_reviewer": 1}
    assert report["blocked_count"] == 1
    assert "supplier" not in str(report).casefold() or "supplier_reviewer" in str(report)
