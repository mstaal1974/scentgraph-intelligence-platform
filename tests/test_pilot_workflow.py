from pathlib import Path

from aromatwin.main import create_app
from aromatwin.services.pilot_workflow import PILOT_STAGES, PilotWorkflowService


def test_dry_run_is_non_writing_and_stages_are_selectable(tmp_path: Path):
    private = tmp_path / "data/private"
    private.mkdir(parents=True)
    source = private / "approved.csv"
    source.write_text("safe_id\nfictional\n")
    bundle = PilotWorkflowService(tmp_path / "data").run({
        "run_id": "dry-one", "run_mode": "dry_run", "stages": ["supplier_import"],
        "input_locations": [str(source)],
    })
    assert [item["stage"] for item in bundle["result"]["stage_results"]] == ["supplier_import"]
    assert not (private / "runs").exists()


def test_private_run_writes_only_run_directory(tmp_path: Path):
    private = tmp_path / "data/private"
    private.mkdir(parents=True)
    source = private / "approved.csv"
    source.write_text("safe_id\nfictional\n")
    bundle = PilotWorkflowService(tmp_path / "data").run({
        "run_id": "private-one", "run_mode": "private_run", "stages": list(PILOT_STAGES),
        "input_locations": [str(source)],
    })
    assert {path.name for path in (private / "runs/private-one").iterdir()} == {
        "manifest.json", "readiness.json", "result.json"}
    assert all(Path(path).is_relative_to(private / "runs/private-one")
               for path in bundle["result"]["output_locations"])


def test_missing_inputs_skip_with_blocker(tmp_path: Path):
    bundle = PilotWorkflowService(tmp_path / "data").run({
        "run_id": "missing", "run_mode": "dry_run", "stages": ["supplier_import"]})
    stage = bundle["result"]["stage_results"][0]
    assert stage["status"] == "skipped"
    assert stage["blockers"][0]["recommended_fix"]


def test_openapi_exposes_pilot_routes():
    paths = create_app().openapi()["paths"]
    expected = {"/pilot-workflow/health", "/pilot-workflow/dry-run", "/pilot-workflow/run",
                "/pilot-workflow/runs", "/pilot-workflow/runs/{run_id}",
                "/pilot-workflow/runs/{run_id}/manifest",
                "/pilot-workflow/runs/{run_id}/readiness",
                "/pilot-workflow/runs/{run_id}/blockers", "/pilot-workflow/audit"}
    assert all(any(path.endswith(item) for path in paths) for item in expected)
