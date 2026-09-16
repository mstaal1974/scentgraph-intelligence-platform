"""Authenticated Maison integration readiness control plane (no outbound I/O)."""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.maison_integration import (
    MaisonIntegrationAuditReport,
    MaisonIntegrationReadinessReport,
    MaisonSyncManifestPublicSummary,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.maison_export_contracts import contract_fields
from aromatwin.services.maison_integration_readiness import check_maison_integration_readiness
from aromatwin.services.maison_sync_manifest import build_sync_manifest

router = APIRouter(prefix="/maison-integration", tags=["internal maison integration"],
                   dependencies=[Depends(require_private_api_key)])
_MANIFESTS: dict[str, MaisonSyncManifestPublicSummary] = {}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "operation": "local_only"}


@router.get("/readiness", response_model=MaisonIntegrationReadinessReport)
def readiness():
    return check_maison_integration_readiness()


@router.post("/readiness/check", response_model=MaisonIntegrationReadinessReport)
def check_readiness():
    return check_maison_integration_readiness()


def _contract(name: str) -> dict[str, object]:
    return {"contract": name, "fields": contract_fields()[name], "visibility": "public_safe"}


@router.get("/contracts/products")
def products_contract(): return _contract("products")


@router.get("/contracts/recommendations")
def recommendations_contract(): return _contract("recommendations")


@router.get("/contracts/scentprint-matches")
def scentprint_contract(): return _contract("scentprint_matches")


@router.get("/contracts/bundles")
def bundles_contract(): return _contract("bundles")


@router.post("/sync-manifest/build", response_model=MaisonSyncManifestPublicSummary)
def build_manifest():
    full = build_sync_manifest()
    summary = MaisonSyncManifestPublicSummary.model_validate(full.model_dump())
    _MANIFESTS[summary.sync_manifest_id] = summary
    return summary


@router.get("/sync-manifest/{sync_manifest_id}", response_model=MaisonSyncManifestPublicSummary)
def manifest(sync_manifest_id: str):
    if sync_manifest_id not in _MANIFESTS:
        raise HTTPException(404, "Sync manifest not found")
    return _MANIFESTS[sync_manifest_id]


@router.get("/audit", response_model=MaisonIntegrationAuditReport)
def audit():
    completed = subprocess.run([sys.executable, "scripts/audit_maison_integration_privacy.py"],
                               check=False, capture_output=True, text=True)
    files = list(Path("data/samples").glob("maison_*"))
    return MaisonIntegrationAuditReport(passed=completed.returncode == 0,
        audited_file_count=len(files), violations=[] if completed.returncode == 0 else
        ["Maison integration privacy audit failed; inspect the local operator output."])
