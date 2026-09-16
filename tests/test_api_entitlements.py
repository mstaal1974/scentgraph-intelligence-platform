from aromatwin.services.api_entitlements import PRIVATE_GROUPS, check_api_entitlement


def test_public_group_allowed_and_private_supplier_denied_for_customer():
    assert check_api_entitlement("plan_retailer_starter", "public_health").allowed
    denied = check_api_entitlement("plan_retailer_starter", "private_supplier_pilot")
    assert not denied.allowed and denied.access_level == "disabled"


def test_any_allowed_private_group_requires_private_control():
    for group in PRIVATE_GROUPS:
        item = check_api_entitlement("plan_internal_maison", group)
        if item.allowed:
            assert item.requires_private_api_key and item.requires_human_approval
            assert item.access_level in {"internal", "private_operator"}
