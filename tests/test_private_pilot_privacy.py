from pathlib import Path

from scripts.audit_private_pilot_inputs import audit_paths


def test_public_samples_pass_private_audit():
    assert audit_paths(list(Path("data/samples").glob("private_*.csv"))) == []


def test_audit_rejects_commercial_field(tmp_path: Path):
    sample = tmp_path / "unsafe.csv"
    sample.write_text("intake_id,supplier_price\nfictional,redacted\n")
    assert audit_paths([sample])
