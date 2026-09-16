from pathlib import Path

from aromatwin.schemas.private_supplier_pilot import PrivateSupplierIntakeRead
from aromatwin.services.pilot_execution_plan import build_execution_plan


def item(path: Path) -> PrivateSupplierIntakeRead:
    return PrivateSupplierIntakeRead(intake_id="i", supplier_public_label="demo",
        private_source_path=str(path), detected_format="generic_supplier", file_type="csv",
        row_count_estimate=1, header_confidence="high", detected_private_fields=[],
        readiness_status="ready_for_import", blocking_issues=[], recommended_next_action="review",
        created_at="2026-01-01T00:00:00Z")


def test_plan_modes_and_review_gates(tmp_path: Path):
    plan = build_execution_plan({"run_id": "dry-1", "run_mode": "dry_run",
        "selected_stages": ["supplier_import", "review_queue"]}, [item(tmp_path / "private.csv")])
    assert plan.expected_outputs == []
    assert "supplier_match_review" in plan.required_review_gates
    review = build_execution_plan({"run_id": "review-1", "run_mode": "review_only_run",
        "selected_stages": ["supplier_import", "review_queue"]}, [])
    assert "supplier_import" not in review.stage_sequence
    private = build_execution_plan({"run_id": "private-1", "run_mode": "private_run"},
                                   [item(tmp_path / "private.csv")])
    assert private.expected_outputs == ["data/private/runs/private-1/"]
