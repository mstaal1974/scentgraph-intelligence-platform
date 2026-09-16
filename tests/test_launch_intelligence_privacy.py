from pathlib import Path

from scripts.audit_launch_intelligence_privacy import audit


def test_public_samples_pass_privacy_audit():
    root = Path(__file__).parents[1]
    tracked = [str(path.relative_to(root)) for path in (root / "data/samples").glob("launch_*.csv")]
    assert audit(root, tracked) == []


def test_audit_rejects_private_field(tmp_path):
    path = tmp_path / "data/samples/launch_bad.csv"
    path.parent.mkdir(parents=True)
    path.write_text("launch_candidate_id,supplier_price\nx,10\n", encoding="utf-8")
    assert audit(tmp_path, ["data/samples/launch_bad.csv"])
