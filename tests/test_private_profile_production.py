from pathlib import Path

from aromatwin.schemas.profile_production import ProfileBatchControls
from aromatwin.services.private_profile_production import run_private_profile_production
from aromatwin.services.profile_batch_planner import build_profile_batch_plan


def make_plan():
    return build_profile_batch_plan(
        [{"readiness_status": "ready_for_import", "supplier_public_label": "fictional-a"}],
        [{"candidate_id": "candidate-1", "confidence": .7}],
        ProfileBatchControls(), source_run_id="test-run",
    )


def test_dry_run_does_not_write(tmp_path):
    run, drafts, _ = run_private_profile_production(make_plan(), [{"candidate_id": "candidate-1", "confidence": .7}], private_root=tmp_path)
    assert run.mode == "dry_run"
    assert not list(tmp_path.rglob("*"))
    assert drafts[0].review_status == "needs_human_review"
    assert drafts[0].enrichment_status == "needs_enrichment"
    assert drafts[0].top_notes == [] and drafts[0].accords == []
    assert "approved" not in drafts[0].model_dump().values()


def test_private_run_writes_only_profiles_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = Path("data/private/runs")
    run, drafts, _ = run_private_profile_production(make_plan(), [{"candidate_id": "candidate-1", "confidence": .7}], mode="private_batch_run", private_root=root)
    files = list((root / run.run_id / "profiles").glob("*.json"))
    assert files
    assert all(path.is_relative_to(root / run.run_id / "profiles") for path in files)
    names = {path.name for path in files}
    assert "products.json" not in names and "maison_export.json" not in names and "campaigns.json" not in names
    assert drafts[0].review_status == "needs_human_review"
