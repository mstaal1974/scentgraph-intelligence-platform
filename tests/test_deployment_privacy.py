from pathlib import Path

from scripts.audit_deployment_privacy import audit_paths


def test_deployment_templates_are_placeholder_only() -> None:
    assert audit_paths([Path("deployment"), Path("data/samples/deployment_readiness_sample.csv"), Path("data/samples/environment_readiness_sample.csv")]) == []


def test_audit_rejects_likely_secret_and_private_field(tmp_path: Path) -> None:
    unsafe = tmp_path / "public.csv"
    unsafe.write_text("api_key=sk_abcdefghijklmnopqrstuvwxyz\nsupplier_price,12\n", encoding="utf-8")
    violations = audit_paths([unsafe])
    assert len(violations) >= 2
