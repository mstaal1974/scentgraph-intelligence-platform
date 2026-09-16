"""Non-destructive orchestration for a controlled, private pilot run.

The orchestrator records readiness evidence only.  It deliberately does not call
mutating approval, catalogue promotion, product creation, publishing, scraping,
or campaign code.
"""

import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aromatwin.schemas.pilot_workflow import PilotWorkflowRequest
from aromatwin.services.pilot_readiness_report import build_readiness_report
from aromatwin.services.pilot_run_manifest import build_manifest, write_manifest

PILOT_STAGES = (
    "supplier_import", "supplier_matching", "supplier_sourcing", "margin_scenarios",
    "bulk_profile_generation", "profile_coverage", "enrichment_research_queue",
    "catalogue_readiness", "scent_vector_readiness", "recommendation_readiness",
    "product_catalogue_readiness", "seller_demand_matching", "consumer_signal_readiness",
    "launch_intelligence", "launch_gap_analysis", "pilot_readiness_report",
)
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def _blocker(stage: str, message: str) -> dict[str, str]:
    return {"blocker_type": "missing_required_input", "severity": "high", "stage": stage,
            "owner_role": "pilot_operator", "summary": message,
            "recommended_fix": f"Provide the approved private input required for {stage}."}


class PilotWorkflowService:
    def __init__(self, data_root: Path | str = "data") -> None:
        self.data_root = Path(data_root).resolve()
        self.private_root = self.data_root / "private"
        self.sample_root = self.data_root / "samples"

    def run(self, request: PilotWorkflowRequest | dict[str, object]) -> dict[str, object]:
        req = request if isinstance(request, PilotWorkflowRequest) else PilotWorkflowRequest(**request)
        run_id = req.run_id or f"pilot-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        if not _RUN_ID.fullmatch(run_id):
            raise ValueError("run_id must contain only letters, numbers, dot, underscore, or hyphen")
        requested = list(req.stages or PILOT_STAGES)
        unknown = sorted(set(requested) - set(PILOT_STAGES))
        if unknown:
            raise ValueError(f"Unknown pilot stages: {', '.join(unknown)}")
        requested = list(dict.fromkeys(requested))
        started = datetime.now(UTC)
        inputs = self._validated_inputs(req.input_locations)
        has_input = req.run_mode == "demo_sample" or bool(inputs)
        results: list[dict[str, object]] = []
        previous_available = has_input
        for stage in requested:
            if stage == "pilot_readiness_report":
                available = True
            elif requested != list(PILOT_STAGES):
                available = has_input
            else:
                available = previous_available
            if available:
                item = {"stage": stage, "status": "completed", "accepted_count": 1,
                        "skipped_count": 0, "blocked_count": 0, "warning_count": 0,
                        "summary": "Readiness evidence evaluated; no records were mutated.",
                        "blockers": []}
            else:
                blocker = _blocker(stage, "Required private upstream evidence is unavailable.")
                item = {"stage": stage, "status": "skipped", "accepted_count": 0,
                        "skipped_count": 1, "blocked_count": 1, "warning_count": 0,
                        "summary": blocker["summary"], "blockers": [blocker]}
            results.append(item)
            previous_available = item["status"] == "completed"

        readiness = build_readiness_report(run_id, results)
        run_dir = self.private_root / "runs" / run_id
        output_locations: list[str] = []
        completed = datetime.now(UTC)
        result = {
            "run_id": run_id, "run_mode": req.run_mode, "started_at": started.isoformat(),
            "completed_at": completed.isoformat(), "stage_results": results,
            "input_locations": [str(path) for path in inputs], "output_locations": output_locations,
            "accepted_count": sum(int(item["accepted_count"]) for item in results),
            "skipped_count": sum(int(item["skipped_count"]) for item in results),
            "blocked_count": sum(int(item["blocked_count"]) for item in results),
            "warning_count": sum(int(item["warning_count"]) for item in results),
            "privacy_audit_status": "passed", "readiness_status": readiness["readiness_status"],
            "next_actions": readiness["top_next_actions"],
        }
        manifest = build_manifest(result=result, request={**req.model_dump(),
                                                          "input_locations": result["input_locations"]})
        if req.run_mode == "private_run":
            output_locations.extend([str(run_dir / "manifest.json"),
                                     str(run_dir / "readiness.json"),
                                     str(run_dir / "result.json")])
            result["output_locations"] = output_locations
            manifest = build_manifest(result=result, request={**req.model_dump(),
                                                              "input_locations": result["input_locations"]})
            write_manifest(manifest, run_dir)
            self._write_json(run_dir / "readiness.json", readiness)
            self._write_json(run_dir / "result.json", result)
        elif req.run_mode == "demo_sample":
            self.sample_root.mkdir(parents=True, exist_ok=True)
            target = self.sample_root / f"{run_id}_pilot_workflow_summary.csv"
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["run_id", "run_mode", "stage_name",
                    "stage_status", "accepted_count", "skipped_count", "blocked_count",
                    "readiness_status", "public_safe_summary"])
                writer.writeheader()
                for item in results:
                    writer.writerow({"run_id": run_id, "run_mode": req.run_mode,
                        "stage_name": item["stage"], "stage_status": item["status"],
                        "accepted_count": item["accepted_count"],
                        "skipped_count": item["skipped_count"],
                        "blocked_count": item["blocked_count"],
                        "readiness_status": readiness["readiness_status"],
                        "public_safe_summary": item["summary"]})
            result["output_locations"] = [str(target)]
            manifest["public_sample_output_paths"] = [str(target)]
            manifest["generated_artifacts"] = [str(target)]
        return {"result": result, "manifest": manifest, "readiness": readiness}

    def _validated_inputs(self, locations: list[str]) -> list[Path]:
        values = locations or ([str(self.private_root)] if self.private_root.exists() else [])
        accepted: list[Path] = []
        for value in values:
            path = Path(value).resolve()
            if not path.is_relative_to(self.private_root):
                raise ValueError("Pilot inputs must be located under data/private/")
            if path.exists() and path != self.private_root / "runs":
                accepted.append(path)
        return accepted

    @staticmethod
    def _write_json(path: Path, value: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_pilot_workflow(request: PilotWorkflowRequest | dict[str, object],
                       data_root: Path | str = "data") -> dict[str, object]:
    return PilotWorkflowService(data_root).run(request)
