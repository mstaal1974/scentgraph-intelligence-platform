from pathlib import Path

from scripts.audit_review_workflow_privacy import audit_paths, discover

ROOT = Path(__file__).resolve().parents[1]


def test_samples_are_public_safe():
    assert not audit_paths(discover(ROOT))


def test_audit_rejects_private_fields(tmp_path):
    unsafe = tmp_path / "review.csv"
    unsafe.write_text("review_item_id,decision_reason\nx,private\n", encoding="utf-8")
    assert audit_paths([unsafe])
