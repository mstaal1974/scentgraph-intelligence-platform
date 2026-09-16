"""Deterministic API entitlement policy without authentication credential issuance."""

from aromatwin.schemas.commercial_packaging import ApiEntitlementMatrixRead, ApiEntitlementRead
from aromatwin.services.commercial_plans import get_commercial_plan, get_commercial_plans

API_GROUPS = ("public_health", "scentprint_quiz", "product_catalogue_public",
              "recommendations_public", "maison_integration_internal", "private_supplier_pilot",
              "review_workflow", "operations_audit", "deployment_readiness", "staging_smoke",
              "commercial_packaging", "consumer_scent_internal", "seller_demand_internal",
              "launch_intelligence_internal")
PRIVATE_GROUPS = set(API_GROUPS) - set(API_GROUPS[:4])


def check_api_entitlement(plan_id: str, api_group: str) -> ApiEntitlementRead:
    plan = get_commercial_plan(plan_id)
    known_group = api_group in API_GROUPS
    allowed = bool(plan and known_group and api_group in plan.allowed_api_groups)
    private = api_group in PRIVATE_GROUPS
    level = ("internal" if plan and plan.private_workflow_access else "private_operator") if (
        allowed and private
    ) else ("public" if allowed else "disabled")
    return ApiEntitlementRead(
        entitlement_id=f"ent_{plan_id.removeprefix('plan_')}_{api_group}", plan_id=plan_id,
        api_group=api_group, allowed=allowed, access_level=level,
        usage_limit="contract_band" if allowed else "none",
        requires_private_api_key=allowed and private, requires_human_approval=private,
        public_safe_reason=("Included as a public-safe contract." if allowed and not private else
                            "Available only under an approved private operator contract." if allowed else
                            "This plan does not include this API group."),
        denial_reason=None if allowed else ("unknown_plan_or_api_group" if not plan or not known_group else
                                            "not_in_plan_entitlements"),
    )


def build_api_entitlement_matrix(plan_id: str | None = None) -> ApiEntitlementMatrixRead:
    plans = [get_commercial_plan(plan_id)] if plan_id else get_commercial_plans()
    plans = [plan for plan in plans if plan is not None]
    entries = [check_api_entitlement(plan.plan_id, group) for plan in plans for group in API_GROUPS]
    return ApiEntitlementMatrixRead(entitlements=entries, plan_count=len(plans),
                                    api_group_count=len(API_GROUPS), privacy_status="public_safe")
