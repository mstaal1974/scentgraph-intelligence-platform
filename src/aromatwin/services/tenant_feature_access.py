"""Sample-context feature policy that never provisions a tenant."""

from aromatwin.schemas.commercial_packaging import TenantFeatureAccessRead
from aromatwin.services.commercial_plans import get_commercial_plan, get_commercial_plans

FEATURE_KEYS = ("product_catalogue_exports", "scentprint_quiz_contract", "recommendation_exports",
                "maison_sync_manifest", "supplier_matching", "supplier_opportunity_insights",
                "seller_demand_matching", "consumer_scentprint_insights", "review_workflow",
                "launch_readiness", "private_pilot_execution", "operational_audit",
                "white_label_exports", "api_usage_reports")
PRIVATE_FEATURES = {"maison_sync_manifest", "supplier_matching", "supplier_opportunity_insights",
                    "seller_demand_matching", "consumer_scentprint_insights", "review_workflow",
                    "launch_readiness", "private_pilot_execution", "operational_audit"}
EXPORT_FEATURES = {"product_catalogue_exports", "recommendation_exports", "white_label_exports"}


def check_tenant_feature_access(plan_id: str, feature_key: str,
                                tenant_context_id: str = "sample_context") -> TenantFeatureAccessRead:
    plan = get_commercial_plan(plan_id)
    known = feature_key in FEATURE_KEYS
    private = feature_key in PRIVATE_FEATURES
    allowed = bool(plan and known and (not private or plan.private_workflow_access))
    if feature_key == "white_label_exports":
        allowed = bool(plan and plan.white_label_allowed)
    scope = "internal_private" if allowed and private else "public_safe_only" if allowed else "disabled"
    return TenantFeatureAccessRead(
        tenant_context_id=tenant_context_id, plan_id=plan_id, tenant_label="Fictional Sample Context",
        feature_key=feature_key, allowed=allowed,
        access_level="private_operator" if allowed and private else "authenticated" if allowed else "disabled",
        data_scope=scope, export_allowed=allowed and feature_key in EXPORT_FEATURES,
        requires_review=feature_key in EXPORT_FEATURES or private,
        requires_operator_approval=private, denial_reason=None if allowed else "feature_not_available_for_plan",
        public_safe_summary=("Access is constrained to the stated scope; cross-context access is forbidden."
                             if allowed else "This feature is not available for this plan."),
    )


def build_tenant_feature_access_matrix(plan_id: str | None = None) -> list[TenantFeatureAccessRead]:
    plans = [get_commercial_plan(plan_id)] if plan_id else get_commercial_plans()
    return [check_tenant_feature_access(plan.plan_id, feature) for plan in plans if plan
            for feature in FEATURE_KEYS]
