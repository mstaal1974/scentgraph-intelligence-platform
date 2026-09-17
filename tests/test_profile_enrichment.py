import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from apps.private_profile_review_console import demo_review_data, load_console_data
from aromatwin.services.profile_enrichment import (
    EVIDENCE_PROVENANCE,
    MAX_LIST_ITEMS,
    MODEL_PROVENANCE,
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


class StubCompletions:
    """Stands in for the OpenAI SDK's chat.completions surface."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.seen: dict[str, object] = {}

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.seen = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


def stub_client(content: str) -> SimpleNamespace:
    completions = StubCompletions(content)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    client.completions = completions
    return client


def _model_response(**changes: object) -> str:
    payload: dict[str, object] = {
        "fragrance_family": "amber woody",
        "top_notes": ["saffron", "bergamot"],
        "heart_notes": ["rose"],
        "base_notes": ["oud", "labdanum"],
        "accords": ["amber", "woody"],
        "mood_tags": ["opulent"],
        "occasion_tags": ["evening"],
        "season_tags": ["winter"],
        "strength_band": "strong",
        "longevity_band": "very long",
        "projection_band": "strong",
        "draft_scent_description": "A dense resinous reading led by oud over warm labdanum.",
        "ai_confidence_band": "low",
    }
    payload.update(changes)
    return json.dumps(payload)


def test_model_output_is_validated_and_always_review_gated():
    provider = OpenAIEnrichmentProvider(client=stub_client(_model_response()))
    enriched = provider.enrich(_draft())

    assert set(enriched) == set(OUTPUT_FIELDS)
    assert enriched["review_status"] == "needs_human_review"
    assert enriched["enrichment_status"] == "enriched_pending_review"
    assert enriched["base_notes"] == ["oud", "labdanum"]
    # Nothing was supplied as evidence, so every populated field is a model assertion and every
    # one of them needs a human decision.
    assert set(enriched["field_provenance"].values()) == {MODEL_PROVENANCE}
    assert set(enriched["fields_requiring_human_review"]) >= set(enriched["field_provenance"])


def test_supplier_evidence_overrides_model_and_is_marked_as_evidence():
    draft = {**_draft(), "base_notes": ["driftwood", "ambergris"], "accords": ["aquatic"]}
    provider = OpenAIEnrichmentProvider(
        client=stub_client(_model_response(base_notes=["vanilla"], accords=["gourmand"]))
    )
    enriched = provider.enrich(draft)

    assert enriched["base_notes"] == ["driftwood", "ambergris"]
    assert enriched["accords"] == ["aquatic"]
    assert enriched["field_provenance"]["base_notes"] == EVIDENCE_PROVENANCE
    assert enriched["field_provenance"]["top_notes"] == MODEL_PROVENANCE
    # Evidence-backed fields do not need the reviewer's attention; inferred ones do.
    assert "base_notes" not in enriched["fields_requiring_human_review"]
    assert "top_notes" in enriched["fields_requiring_human_review"]


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("season_tags", ["spring", "narnia"], ["spring"]),
        ("occasion_tags", ["evening", "brunch"], ["evening"]),
        ("strength_band", "nuclear", "unknown"),
        ("longevity_band", "eternal", "unknown"),
        ("ai_confidence_band", "certain", "low"),
        ("top_notes", ["bergamot", "BERGAMOT", "<script>"], ["bergamot"]),
    ],
)
def test_out_of_vocabulary_model_output_is_discarded(field, value, expected):
    """An unexpected answer becomes a flagged gap, never a coerced plausible value."""
    provider = OpenAIEnrichmentProvider(client=stub_client(_model_response(**{field: value})))
    assert provider.enrich(_draft())[field] == expected


def test_model_output_cannot_carry_private_or_restricted_content():
    response = _model_response(
        draft_scent_description="Shop now at our official website!",
        supplier_price="AED 240",
        rating="4.8 out of 5 stars",
        image_url="https://example.com/x.jpg",
    )
    enriched = OpenAIEnrichmentProvider(client=stub_client(response)).enrich(_draft())
    serialised = json.dumps(enriched)

    assert enriched["draft_scent_description"] == ""
    for leaked in ("AED 240", "4.8 out of 5", "example.com", "supplier_price"):
        assert leaked not in serialised


def test_oversized_model_lists_are_bounded():
    response = _model_response(top_notes=[f"note {index}" for index in range(50)])
    enriched = OpenAIEnrichmentProvider(client=stub_client(response)).enrich(_draft())
    assert len(enriched["top_notes"]) <= MAX_LIST_ITEMS


def test_unparseable_response_degrades_to_the_deterministic_provider():
    provider = OpenAIEnrichmentProvider(client=stub_client("not json at all {{{"))
    enriched = provider.enrich(_draft())

    assert set(enriched) == set(OUTPUT_FIELDS)
    assert enriched["review_status"] == "needs_human_review"
    assert enriched["ai_confidence_band"] == "low"
    assert "could not be parsed" in enriched["provenance_notes"]


def test_enrichment_requires_identity_fields():
    provider = OpenAIEnrichmentProvider(client=stub_client(_model_response()))
    with pytest.raises(ValueError, match="Missing required profile fields"):
        provider.enrich({**_draft(), "fragrance_display_name": "  "})


def test_prompt_carries_evidence_but_never_private_columns():
    client = stub_client(_model_response())
    draft = {**_draft(), "base_notes": ["driftwood"]}
    OpenAIEnrichmentProvider(client=client).enrich(draft)
    prompt = client.completions.seen["messages"][1]["content"]

    assert "driftwood" in prompt
    assert "never project this" not in prompt
    assert client.completions.seen["response_format"] == {"type": "json_object"}
