import csv
from pathlib import Path

import pytest

from scripts.audit_private_pilot_inputs import audit_paths

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PUBLIC_SHAPE_COLUMNS = {
    "supplier_public_label",
    "brand_display_name",
    "fragrance_display_name",
    "source_format",
    "candidate_reference",
    "confidence_band",
    "review_status",
    "public_safe_summary",
}
REPLACEMENT_SAMPLES = (
    "supplier_catalogue_public_shape_sample.csv",
    "fatma_supplier_catalogue_public_shape_sample.csv",
)


def test_public_samples_pass_private_audit():
    assert audit_paths(list((ROOT / "data/samples").glob("*.csv"))) == []


def test_audit_rejects_commercial_field(tmp_path: Path):
    sample = tmp_path / "unsafe.csv"
    sample.write_text("intake_id,supplier_price\nfictional,redacted\n")
    assert audit_paths([sample])


@pytest.mark.parametrize("field", ["CODE", "QTY", "AED", "USD", "price", "cost", "margin", "stock"])
def test_audit_rejects_forbidden_public_sample_headers(tmp_path: Path, field: str):
    sample = tmp_path / "data/samples/unsafe.csv"
    sample.parent.mkdir(parents=True)
    sample.write_text(f"candidate_reference,{field}\nfictional-candidate,redacted\n")
    assert audit_paths([sample])


def test_unsafe_supplier_price_samples_are_absent():
    unsafe_names = (
        "FATMA PERFUME PRICE LIST(Table 1).csv",
        "PERFUME OIL PRICE LIST  26.04.2026 (1).csv",
    )
    assert all(not (ROOT / "data/samples" / name).exists() for name in unsafe_names)


@pytest.mark.parametrize("name", REPLACEMENT_SAMPLES)
def test_replacement_samples_use_only_safe_shape(name: str):
    path = ROOT / "data/samples" / name
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert set(reader.fieldnames or ()) == ALLOWED_PUBLIC_SHAPE_COLUMNS
    assert rows
    assert all("fictional" in " ".join(row.values()).casefold() for row in rows)


def test_private_workflow_docs_define_runtime_path_and_sample_boundary():
    docs = [
        ROOT / "docs/private-supplier-pilot-execution.md",
        ROOT / "docs/private-fragrance-profile-production.md",
        ROOT / "docs/profile-pipeline-rehearsal.md",
        ROOT / "docs/roadmap.md",
    ]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "data/private/imports/suppliers/{supplier_label}/" in text
        assert "data/samples/" in text


def test_no_private_outputs_are_tracked():
    import subprocess

    tracked = subprocess.check_output(
        ["git", "ls-files", "data/private", "data/private/**"], cwd=ROOT, text=True
    )
    assert tracked == ""
