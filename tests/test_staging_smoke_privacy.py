import csv
from pathlib import Path

from scripts.audit_staging_smoke_privacy import audit_paths


def test_audit_rejects_likely_secret(tmp_path):
    unsafe = tmp_path / "public.csv"
    unsafe.write_text("name,api_key\nexample,sk_thisisnotallowed123456\n", encoding="utf-8")
    report = audit_paths([unsafe])
    assert not report.passed
    assert report.violation_count


def test_public_samples_have_only_allowlisted_fields():
    allowed_smoke = {
        "smoke_run_id", "check_name", "status", "blocker_type", "warning_count",
        "recommended_next_action", "public_safe_summary",
    }
    allowed_handoff = {"checklist_id", "step", "status", "recommended_next_action", "public_safe_summary"}
    paths = [
        (Path("data/samples/staging_smoke_report_sample.csv"), allowed_smoke),
        (Path("data/samples/staging_operator_handoff_sample.csv"), allowed_handoff),
    ]
    for path, allowed in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            fields = set(csv.DictReader(handle).fieldnames or [])
        assert fields <= allowed
    assert audit_paths([path for path, _ in paths]).passed
