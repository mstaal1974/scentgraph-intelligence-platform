from pathlib import Path

from scripts.audit_commercial_packaging_privacy import SAMPLES, audit


def test_public_samples_pass():
    assert audit(SAMPLES) == []


def test_audit_rejects_secrets_private_columns_and_real_ids(tmp_path: Path):
    bad = tmp_path / "bad.csv"
    bad.write_text("tenant_id,supplier_price,api_key\ntenant_12345678,hidden,sk_live_1234567890123456\n")
    findings = audit([bad])
    assert any("forbidden column" in item for item in findings)
    assert any("likely secret" in item for item in findings)
    assert any("identifier" in item for item in findings)
