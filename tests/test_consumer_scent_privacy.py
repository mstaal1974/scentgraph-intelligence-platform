from pathlib import Path

from scripts.audit_consumer_scent_privacy import audit

SAMPLES = ["consumer_scentprint_sample.csv", "consumer_feedback_sample.csv",
           "community_scent_intelligence_sample.csv", "scent_wardrobe_sample.csv"]


def test_public_samples_exclude_private_and_commercial_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    assert audit(root, [f"data/samples/{name}" for name in SAMPLES]) == []


def test_privacy_audit_fails_for_private_header(tmp_path: Path) -> None:
    sample = tmp_path / "data/samples/leak.csv"
    sample.parent.mkdir(parents=True)
    sample.write_text("anonymous_alias,free_text_private_note\nAnon,secret\n", encoding="utf-8")
    assert audit(tmp_path, ["data/samples/leak.csv"])


def test_openapi_exposes_consumer_scent_endpoints(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    expected = {"/consumer-scent/health", "/consumer-scent/scentprints",
                "/consumer-scent/feedback", "/consumer-scent/community-intelligence",
                "/consumer-scent/community-intelligence/build", "/consumer-scent/wardrobe/items",
                "/consumer-scent/audit"}
    assert expected <= set(paths)
