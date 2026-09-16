from aromatwin.services.commercial_plans import PLAN_TYPES, get_commercial_plans


def test_catalogue_has_every_required_plan_and_no_prices():
    plans = get_commercial_plans()
    assert {p.plan_type for p in plans} == set(PLAN_TYPES)
    assert all(p.billing_integration_status == "not_connected" for p in plans)
    assert not any("price" in key.lower() for p in plans for key in p.monthly_usage_limits)
