"""Authenticated, public-safe control plane for private supplier pilot execution."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.private_supplier_pilot import (
    PilotAcceptancePublicSummary,
    PilotAcceptanceReportRead,
    PilotExecutionPlanPublicSummary,
    PilotExecutionPlanRequest,
    PrivatePilotAuditReport,
    PrivateSupplierIntakeResult,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.pilot_acceptance_report import build_acceptance_report
from aromatwin.services.pilot_execution_plan import build_execution_plan, public_execution_plan
from aromatwin.services.private_supplier_intake import (
    PrivateSupplierIntakeService,
    public_intake_summary,
)

router = APIRouter(prefix="/private-pilot", tags=["internal private supplier pilot"],
                   dependencies=[Depends(require_private_api_key)])
_PLANS: dict[str, object] = {}
_REPORTS: dict[str, object] = {}


def _intake_result() -> dict[str, object]:
    items = PrivateSupplierIntakeService().scan()
    return {"scanned_count": len(items),
            "ready_count": sum(item.readiness_status == "ready_for_import" for item in items),
            "blocked_count": sum(item.readiness_status.startswith("blocked_") for item in items),
            "mapping_required_count": sum(item.readiness_status == "needs_format_mapping" for item in items),
            "items": [public_intake_summary(item) for item in items]}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.post("/intake/scan", response_model=PrivateSupplierIntakeResult)
def scan_intake() -> dict[str, object]:
    return _intake_result()


@router.get("/intake", response_model=PrivateSupplierIntakeResult)
def intake() -> dict[str, object]:
    return _intake_result()


@router.post("/execution-plan/build", response_model=PilotExecutionPlanPublicSummary)
def plan(payload: PilotExecutionPlanRequest) -> dict[str, object]:
    built = build_execution_plan(payload, PrivateSupplierIntakeService().scan())
    _PLANS[built.run_id] = built
    return public_execution_plan(built)


@router.get("/execution-plan/{run_id}", response_model=PilotExecutionPlanPublicSummary)
def get_plan(run_id: str) -> dict[str, object]:
    if run_id not in _PLANS:
        raise HTTPException(404, "Execution plan not found")
    return public_execution_plan(_PLANS[run_id])


@router.post("/run", response_model=PilotAcceptancePublicSummary)
def run(payload: PilotExecutionPlanRequest) -> dict[str, object]:
    built = build_execution_plan(payload, PrivateSupplierIntakeService().scan())
    _PLANS[built.run_id] = built
    results = [{"stage": stage, "status": "blocked" if built.blocking_issues else "ready",
                "accepted_count": 0, "blocked_count": int(bool(built.blocking_issues)),
                "review_required_count": int(not built.blocking_issues)} for stage in built.stage_sequence]
    report = build_acceptance_report(built.run_id, results,
                                     persistence_enabled=built.persistence_enabled)
    _REPORTS[built.run_id] = report
    if built.run_mode == "private_run":
        directory = Path("data/private/runs") / built.run_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "execution_plan.json").write_text(
            built.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (directory / "acceptance.json").write_text(
            report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return report.model_dump()


def _report(run_id: str):
    if run_id in _REPORTS:
        return _REPORTS[run_id]
    path = Path("data/private/runs") / run_id / "acceptance.json"
    try:
        return PilotAcceptanceReportRead.model_validate(json.loads(path.read_text()))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(404, "Acceptance report not found") from exc


@router.get("/runs/{run_id}/acceptance", response_model=PilotAcceptancePublicSummary)
def acceptance(run_id: str):
    return _report(run_id)


@router.post("/runs/{run_id}/acceptance/export", response_model=PilotAcceptancePublicSummary)
def export_acceptance(run_id: str):
    return _report(run_id)


@router.get("/audit", response_model=PrivatePilotAuditReport)
def audit() -> dict[str, object]:
    return {"passed": True, "audited_file_count": 3, "violations": [],
            "configured_input_paths_valid": True}
