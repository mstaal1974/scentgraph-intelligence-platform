from pathlib import Path

from scripts.audit_profile_production_privacy import audit_paths


def test_public_samples_pass_profile_production_audit():
    paths = list(Path("data/samples").glob("*profile*"))
    assert audit_paths(paths) == []


def test_audit_rejects_private_and_copied_fields(tmp_path):
    sample = tmp_path / "bad.csv"
    sample.write_text("profile_draft_id,supplier_price,review_text\nfictional-1,private,copied\n")
    violations = audit_paths([sample])
    assert any("supplier_price" in item for item in violations)
    assert any("review_text" in item for item in violations)
