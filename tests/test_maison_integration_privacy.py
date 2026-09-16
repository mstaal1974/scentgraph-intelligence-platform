from pathlib import Path

from scripts.audit_maison_integration_privacy import FORBIDDEN_HEADERS, audit_paths


def test_samples_have_no_forbidden_headers():
    for path in Path("data/samples").glob("maison_*"):
        headers = set(path.read_text().splitlines()[0].lower().split(","))
        assert not headers & FORBIDDEN_HEADERS


def test_audit_rejects_secret_and_private_field(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("product_id,supplier_price\nx,secret\n")
    assert audit_paths([path])
