from aromatwin.schemas.profile_production import ProfileBatchControls
from aromatwin.services.profile_batch_planner import build_profile_batch_plan


def test_planner_blocks_without_private_intake():
    plan = build_profile_batch_plan([], [{"candidate_id": "candidate-1", "confidence": .9}])
    assert "no_private_supplier_intake" in plan.blocking_issues


def test_planner_selects_ids_and_public_label_without_commercial_values():
    intake = [{"readiness_status": "ready_for_import", "supplier_public_label": "supplier-a", "supplier_price": "private"}]
    matches = [{"candidate_id": "candidate-1", "confidence": .9, "supplier_code": "private"}]
    plan = build_profile_batch_plan(intake, matches, ProfileBatchControls())
    assert plan.selected_candidate_ids == ["candidate-1"]
    serialized = plan.model_dump_json().casefold()
    assert "supplier_price" not in serialized
    assert "supplier_code" not in serialized
