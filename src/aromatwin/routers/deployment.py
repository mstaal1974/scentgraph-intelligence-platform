"""Deployment diagnostics with a minimal public health boundary."""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends

from aromatwin.schemas.deployment import (
    DeploymentAuditReport,
    DeploymentReadinessReport,
    EnvironmentReadinessReport,
    RuntimeHealthRead,
    RuntimeReadinessRead,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.deployment_readiness import check_deployment_readiness
from aromatwin.services.environment_readiness import check_environment_readiness
from aromatwin.services.runtime_health import runtime_health, runtime_readiness

router = APIRouter(prefix="/deployment", tags=["deployment readiness"])


@router.get("/health", response_model=RuntimeHealthRead)
def health() -> RuntimeHealthRead:
    return runtime_health()


@router.get("/readiness", response_model=RuntimeReadinessRead,
            dependencies=[Depends(require_private_api_key)])
def readiness() -> RuntimeReadinessRead:
    return runtime_readiness()


@router.get("/environment", response_model=EnvironmentReadinessReport,
            dependencies=[Depends(require_private_api_key)])
def environment() -> EnvironmentReadinessReport:
    return check_environment_readiness()


@router.post("/readiness/check", response_model=DeploymentReadinessReport,
             dependencies=[Depends(require_private_api_key)])
def readiness_check() -> DeploymentReadinessReport:
    return check_deployment_readiness()


@router.get("/audit", response_model=DeploymentAuditReport,
            dependencies=[Depends(require_private_api_key)])
def audit() -> DeploymentAuditReport:
    completed = subprocess.run([sys.executable, "scripts/audit_deployment_privacy.py"],
                               check=False, capture_output=True, text=True)
    files = list(Path("deployment").glob("*.example")) + list(Path("data/samples").glob("*readiness_sample.csv"))
    violations = [] if completed.returncode == 0 else ["Deployment privacy audit failed; run the CLI for file-level details."]
    return DeploymentAuditReport(passed=not violations, audited_file_count=len(files),
                                 violation_count=len(violations), violations=violations,
                                 summary="Public templates and readiness samples were audited.")
