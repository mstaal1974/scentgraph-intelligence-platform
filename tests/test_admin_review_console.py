from pathlib import Path

from fastapi.testclient import TestClient

from aromatwin.routers.admin_review import _DECISIONS
from aromatwin.routers.profile_drafts import _DRAFTS
from aromatwin.services.profile_builder import (
    ProfileDraft,
    draft_description,
    draft_provenance_notes,
)


def setup_function() -> None:
    _DECISIONS.clear()
    _DRAFTS.clear()


def test_review_summary_returns_every_stage_count(client: TestClient) -> None:
    response = client.get("/admin/review/summary")
    assert response.status_code == 200
    stages = {item["stage"]: item["total"] for item in response.json()["stages"]}
    assert set(stages) == {
        "supplier_import", "match_candidate", "profile_draft", "enrichment_review",
        "catalogue_promotion", "scent_vector", "recommendation", "maison_api_ready",
    }


def test_queue_aggregates_safe_sample_stages(client: TestClient) -> None:
    queue = client.get("/admin/review/queue").json()
    stages = {item["stage"] for item in queue}
    assert {"profile_draft", "enrichment_review", "catalogue_promotion", "scent_vector",
            "recommendation"} <= stages


def test_blockers_and_readiness_explain_ready_and_not_ready(client: TestClient) -> None:
    blocked = client.get("/admin/review/blocked").json()
    assert blocked and all(item["blocking_reason"] for item in blocked)
    report = client.get("/admin/review/readiness").json()
    assert report["ready_count"] == len(report["ready"])
    assert report["not_ready_count"] == len(report["not_ready"])
    assert report["ready_count"] + report["not_ready_count"] > 0


def test_approve_delegates_to_profile_guardrails(client: TestClient) -> None:
    _DRAFTS.append(ProfileDraft(
        id=42, supplier_item_id=1, match_candidate_id=2, brand="Fictional",
        fragrance_name="Unsafe Draft", concentration=None,
        description=draft_description("Fictional", "Unsafe Draft"),
        provenance_notes=draft_provenance_notes(
            supplier_item_id=1, match_candidate_id=2, source_type="reference_only"
        ), source_type="reference_only", source_confidence=0.2,
    ))
    response = client.post(
        "/admin/review/profile_draft/42/approve", json={"reviewer": "Human reviewer"}
    )
    assert response.status_code == 422
    assert _DRAFTS[0].review_status == "needs_human_review"


def test_reject_requires_and_returns_reason(client: TestClient) -> None:
    missing = client.post(
        "/admin/review/catalogue_promotion/1/reject", json={"reviewer": "Human"}
    )
    assert missing.status_code == 422
    response = client.post(
        "/admin/review/catalogue_promotion/1/reject",
        json={"reviewer": "Human", "reason": "Provenance needs verification"},
    )
    assert response.status_code == 200
    assert response.json()["reason"] == "Provenance needs verification"


def test_request_more_sources_marks_supported_stage(client: TestClient) -> None:
    response = client.post(
        "/admin/review/profile_draft/1/request-more-sources",
        json={"reviewer": "Human", "reason": "Need another licensed source"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "requires_more_sources"
    assert client.post(
        "/admin/review/recommendation/1/request-more-sources",
        json={"reviewer": "Human"},
    ).status_code == 422


def test_outputs_have_no_private_or_restricted_content_fields(client: TestClient) -> None:
    payload = client.get("/admin/review/queue").json()
    keys = {key.lower() for item in payload for key in item}
    forbidden = {
        "supplier_price", "aed_price", "usd_price", "supplier_code", "stock", "quantity",
        "cn_code", "commercial_terms", "description", "reviews", "ratings", "images",
        "comments", "ugc",
    }
    assert keys.isdisjoint(forbidden)
    csv_text = client.get("/admin/export/review-queue").text.splitlines()[0].lower()
    assert all(field not in csv_text for field in forbidden)


def test_static_console_and_openapi_admin_routes_exist(client: TestClient) -> None:
    for name in ("index.html", "admin.js", "admin.css"):
        assert (Path("static/admin") / name).is_file()
    assert client.get("/admin-console/").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    expected = {
        "/admin/health", "/admin/review/summary", "/admin/review/queue",
        "/admin/review/queue/{stage}", "/admin/review/blocked", "/admin/review/readiness",
        "/admin/review/{stage}/{record_id}/approve",
        "/admin/review/{stage}/{record_id}/reject",
        "/admin/review/{stage}/{record_id}/request-more-sources",
        "/admin/export/review-queue",
    }
    assert expected <= paths.keys()
