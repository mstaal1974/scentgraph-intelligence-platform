"""Static, public-safe plan definitions; no customers, prices, or billing side effects."""

from aromatwin.schemas.commercial_packaging import CommercialPlanRead

PLAN_TYPES = (
    "internal_maison", "retailer_starter", "retailer_growth", "retailer_enterprise",
    "supplier_insights", "marketplace_operator", "white_label_partner", "api_partner",
    "sandbox_developer",
)

_PUBLIC_GROUPS = ["public_health", "scentprint_quiz", "product_catalogue_public", "recommendations_public"]
_INTERNAL_GROUPS = ["maison_integration_internal", "private_supplier_pilot", "review_workflow",
                    "operations_audit", "deployment_readiness", "staging_smoke", "commercial_packaging",
                    "consumer_scent_internal", "seller_demand_internal", "launch_intelligence_internal"]


def _plan(plan_type: str) -> CommercialPlanRead:
    internal = plan_type in {"internal_maison", "marketplace_operator"}
    partner = plan_type in {"api_partner", "white_label_partner"}
    features = ["public catalogue contract", "Scentprint quiz contract"]
    if partner:
        features.append("contract-reviewed exports")
    if internal:
        features += ["operator review workflow", "private workflow controls"]
    return CommercialPlanRead(
        plan_id=f"plan_{plan_type}", plan_name=plan_type.replace("_", " ").title(),
        plan_type=plan_type, target_customer=plan_type.replace("_", " "),
        included_features=features,
        excluded_features=[] if internal else ["supplier-private workflows", "cross-tenant data"],
        allowed_api_groups=_PUBLIC_GROUPS + (_INTERNAL_GROUPS if internal else
            (["commercial_packaging"] if partner else [])),
        monthly_usage_limits={"request_band": "contract_review_required"},
        data_visibility_level="internal_private" if internal else "public_safe_only",
        private_workflow_access=internal,
        export_access="operator_reviewed" if internal or partner else "public_safe_only",
        white_label_allowed=plan_type == "white_label_partner",
        requires_manual_approval=True, billing_integration_status="not_connected",
        public_safe_description="A proposed capability bundle requiring manual commercial and legal review.",
    )


COMMERCIAL_PLANS = tuple(_plan(plan_type) for plan_type in PLAN_TYPES)


def get_commercial_plans() -> list[CommercialPlanRead]:
    return list(COMMERCIAL_PLANS)


def get_commercial_plan(plan_id: str) -> CommercialPlanRead | None:
    return next((plan for plan in COMMERCIAL_PLANS if plan.plan_id == plan_id), None)
