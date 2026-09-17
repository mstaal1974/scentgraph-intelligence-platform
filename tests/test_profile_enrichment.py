import json
from pathlib import Path

import pytest

from apps.private_profile_review_console import demo_review_data, load_console_data
from aromatwin.services.profile_enrichment import (
    OUTPUT_FIELDS,
    OfflineHeuristicEnrichmentProvider,
    OpenAIEnrichmentProvider,
)
from scripts.enrich_private_profile_batch import enrich_batch


def _draft() -> dict[str, object]:
    return {
        "profile_draft_id": "draft-1",
        "brand_display_name": "Fictional Atelier",
        "fragrance_display_name": "Citrus Woods",
        "supplier_public_label": "Private source",
        "confidence_band": "medium",
        "blocking_issues": [],
        "supplier_price": "never project this",
    }


def test_offline_enrichment_builds_richer_safe_profile():
    enriched = OfflineHeuristicEnrichmentProvider().enrich(_draft())

    assert set(enriched) == set(OUTPUT_FIELDS)
    assert enriched["fragrance_family"] == "citrus"
    assert enriched["accords"] == ["citrus", "fresh"]
    assert enriched["top_notes"] == []
    assert "supplier_price" not in json.dumps(enriched)


def test_missing_evidence_requires_human_review():
    enriched = OfflineHeuristicEnrichmentProvider().enrich(
        {**_draft(), "fragrance_display_name": "Archive Number Seven"}
    )
    assert enriched["fragrance_family"] == "unclassified"
    assert "fragrance_family" in enriched["fields_requiring_human_review"]
    assert "top_notes" in enriched["fields_requiring_human_review"]


def test_private_batch_writes_only_below_private_root(tmp_path: Path):
    private = tmp_path / "data" / "private"
    profiles = private / "runs" / "run-1" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "drafts.json").write_text(json.dumps([_draft()]), encoding="utf-8")

    destination = enrich_batch("run-1", 1, private_root=private)

    assert destination == profiles / "enriched_profiles.json"
    assert destination.is_relative_to(private)
    assert not (tmp_path / "data" / "public").exists()


def test_demo_mode_works_without_private_data(tmp_path: Path):
    drafts, packets, decisions, is_demo = load_console_data(
        "missing", private_root=tmp_path / "data" / "private"
    )
    assert is_demo and drafts and not packets and not decisions
    assert drafts == demo_review_data()[0]
    assert all(row["enrichment_status"] == "enriched_pending_review" for row in drafts)


def test_openai_provider_skips_safely_without_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIEnrichmentProvider()
    assert not provider.is_available
    with pytest.raises(RuntimeError, match="skipped"):
        provider.enrich(_draft())
