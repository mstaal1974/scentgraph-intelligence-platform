from aromatwin.services.commercial_readiness import check_commercial_readiness


def test_readiness_is_not_paid_launch_and_requires_manual_review():
    report = check_commercial_readiness()
    assert report.billing_status == "intentionally_not_connected"
    assert "paid launch" in report.warnings[0]
    assert any("legal" in action.lower() for action in report.required_operator_actions)
    assert "payments" in report.recommended_next_step
