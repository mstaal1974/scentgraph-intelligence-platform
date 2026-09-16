"""Private control-plane routes returning only public-safe projections."""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from aromatwin.schemas.commercial_packaging import (
    CommercialPackagingAuditReport,
    CommercialPlanPublicSummary,
    CommercialReadinessReport,
    TenantFeatureAccessPublicSummary,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.api_entitlements import build_api_entitlement_matrix, check_api_entitlement
from aromatwin.services.commercial_plans import get_commercial_plan, get_commercial_plans
from aromatwin.services.commercial_readiness import check_commercial_readiness
from aromatwin.services.tenant_feature_access import (
    build_tenant_feature_access_matrix,
    check_tenant_feature_access,
)

router = APIRouter(prefix="/commercial-packaging", tags=["internal commercial packaging"],
                   dependencies=[Depends(require_private_api_key)])


class EntitlementCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_id: str
    api_group: str


class FeatureCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_id: str
    feature_key: str


@router.get("/health")
def health(): return {"status": "ok", "visibility": "internal_private", "billing": "not_connected"}


@router.get("/plans", response_model=list[CommercialPlanPublicSummary])
def plans(): return [CommercialPlanPublicSummary.model_validate(
            p.model_dump(include=set(CommercialPlanPublicSummary.model_fields))) for p in get_commercial_plans()]


@router.get("/plans/{plan_id}", response_model=CommercialPlanPublicSummary)
def plan(plan_id: str):
    value = get_commercial_plan(plan_id)
    if not value:
        raise HTTPException(404, "Plan not found")
    return CommercialPlanPublicSummary.model_validate(
        value.model_dump(include=set(CommercialPlanPublicSummary.model_fields)))


@router.get("/entitlements")
def entitlements(): return build_api_entitlement_matrix()


@router.get("/entitlements/{plan_id}")
def plan_entitlements(plan_id: str):
    if not get_commercial_plan(plan_id):
        raise HTTPException(404, "Plan not found")
    return build_api_entitlement_matrix(plan_id)


@router.post("/entitlements/check")
def entitlement_check(request: EntitlementCheck):
    return check_api_entitlement(request.plan_id, request.api_group)


@router.get("/tenant-feature-access", response_model=list[TenantFeatureAccessPublicSummary])
def tenant_features():
    return [TenantFeatureAccessPublicSummary.model_validate(
                v.model_dump(include=set(TenantFeatureAccessPublicSummary.model_fields)))
            for v in build_tenant_feature_access_matrix()]


@router.post("/tenant-feature-access/check", response_model=TenantFeatureAccessPublicSummary)
def tenant_feature_check(request: FeatureCheck):
    return TenantFeatureAccessPublicSummary.model_validate(
        check_tenant_feature_access(request.plan_id, request.feature_key).model_dump(
            include=set(TenantFeatureAccessPublicSummary.model_fields)))


@router.get("/readiness", response_model=CommercialReadinessReport)
def readiness(): return check_commercial_readiness()


@router.post("/readiness/check", response_model=CommercialReadinessReport)
def readiness_check(): return check_commercial_readiness()


@router.get("/audit", response_model=CommercialPackagingAuditReport)
def audit():
    result = subprocess.run([sys.executable, "scripts/audit_commercial_packaging_privacy.py"],
                            check=False, capture_output=True, text=True)
    count = len(list(Path("data/samples").glob("*commercial*"))) + len(list(Path("data/samples").glob("*entitlement*")))
    return CommercialPackagingAuditReport(passed=result.returncode == 0, audited_file_count=count,
        violations=[] if result.returncode == 0 else ["Privacy audit failed; inspect operator-local output."],
        privacy_status="passed" if result.returncode == 0 else "failed")
