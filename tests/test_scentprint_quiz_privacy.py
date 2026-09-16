import csv
from pathlib import Path

from scripts.audit_scentprint_quiz_privacy import audit_paths


def test_public_quiz_samples_pass_privacy_audit():
    paths = list(Path("data/samples").glob("scentprint_quiz*"))
    assert paths
    assert audit_paths(paths) == []
    for path in paths:
        if path.suffix == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                headers = set(next(csv.reader(handle)))
            assert not headers & {"email", "phone", "supplier_price", "supplier_code", "stock",
                                  "quantity", "cost", "margin", "raw_feedback"}


def test_audit_fails_private_field_sensitive_question_and_free_text(tmp_path):
    leaked = tmp_path / "leaked.csv"
    leaked.write_text("email,answer_type\ndemo@example.test,free_text\n", encoding="utf-8")
    contract = {"questions": [{"question_id": "bad", "question_text": "What is your age?",
                 "answer_type": "free_text_disabled", "options": [], "scoring_dimensions": []}]}
    errors = audit_paths([leaked], contract)
    assert errors
    assert any("sensitive question" in error for error in errors)
    assert any("forbidden public fields" in error for error in errors)
