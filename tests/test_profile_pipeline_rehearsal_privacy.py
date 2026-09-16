from pathlib import Path

from scripts.audit_profile_pipeline_rehearsal_privacy import audit_paths


def test_public_samples_pass():
    assert audit_paths(list(Path("data/samples").glob("profile_pipeline_*.csv"))) == []


def test_audit_rejects_private_and_copied_fields(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("candidate_id,supplier_price,review_text\nx,12,copied\n")
    violations = audit_paths([bad])
    assert any("supplier_price" in v for v in violations)
    assert any("review_text" in v for v in violations)
