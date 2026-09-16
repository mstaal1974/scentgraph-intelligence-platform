from aromatwin.services.tenant_feature_access import check_tenant_feature_access


def test_public_plan_has_safe_scope_and_no_private_workflows():
    public = check_tenant_feature_access("plan_retailer_starter", "product_catalogue_exports")
    private = check_tenant_feature_access("plan_retailer_starter", "supplier_matching")
    assert public.data_scope == "public_safe_only"
    assert not private.allowed and private.data_scope == "disabled"
    assert "cross-context" in public.public_safe_summary


def test_white_label_export_is_public_safe():
    access = check_tenant_feature_access("plan_white_label_partner", "white_label_exports")
    assert access.allowed and access.export_allowed and access.data_scope == "public_safe_only"
