from pathlib import Path

from scripts.audit_pilot_workflow_privacy import audit_paths


def test_public_samples_are_safe():
    assert audit_paths(list(Path("data/samples").glob("*pilot*.csv"))) == []


def test_audit_rejects_private_field_and_personal_record(tmp_path: Path):
    leaked = tmp_path / "pilot.csv"
    leaked.write_text("run_id,supplier_price,email\none,secret,person@example.test\n")
    violations = audit_paths([leaked])
    assert any("forbidden public field" in item for item in violations)
    assert any("personal email" in item for item in violations)


def test_demo_writes_only_safe_sample_output(tmp_path: Path):
    from aromatwin.services.pilot_workflow import PilotWorkflowService

    bundle = PilotWorkflowService(tmp_path / "data").run({
        "run_id": "fictional-demo", "run_mode": "demo_sample", "stages": ["supplier_import"]})
    outputs = [Path(item) for item in bundle["result"]["output_locations"]]
    assert outputs and all(path.is_relative_to(tmp_path / "data/samples") for path in outputs)
    assert audit_paths(outputs) == []
