import json

from scripts.audit_persistence_privacy import audit_paths
from scripts.export_operational_audit import export_audit
from scripts.migrate_private_run_to_persistence import migrate_run


def test_privacy_audit_accepts_sample_and_rejects_private_header(tmp_path):
    assert (
        audit_paths([__import__("pathlib").Path("data/samples/persistence_summary_sample.csv")])
        == []
    )
    unsafe = tmp_path / "unsafe.csv"
    unsafe.write_text("run_id,supplier_price\nfictional,hidden\n")
    assert audit_paths([unsafe])


def test_private_manifest_migration_and_export_are_safe(tmp_path):
    run_dir = tmp_path / "runs" / "run-safe"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": "run-safe",
                "run_mode": "private_run",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:01:00+00:00",
                "stages_completed": ["normalisation"],
                "stages_skipped": [],
                "stages_failed": [],
            }
        )
    )
    (run_dir / "readiness.json").write_text(json.dumps({"readiness_status": "review_required"}))
    url = f"sqlite:///{tmp_path / 'persistence.db'}"
    assert migrate_run(run_dir, url) == "run-safe"
    output = tmp_path / "audit.csv"
    assert export_audit(output, url) >= 1
    assert audit_paths([output]) == []
    text = output.read_text().casefold()
    assert "run-safe" in text
    assert "private_run" not in text
