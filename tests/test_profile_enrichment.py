import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from apps.private_profile_review_console import (
    demo_review_data,
    enrichment_provider,
    load_console_data,
    streamlit_anthropic_key,
    streamlit_openai_key,
)
from aromatwin.services.profile_enrichment import (
    AI_DRAFT_FIELDS,
    EVIDENCE_PROVENANCE,
    MAX_LIST_ITEMS,
    MISSING_KEY_WARNING,
    MODEL_PROVENANCE,
    OUTPUT_FIELDS,
    AnthropicEnrichmentProvider,
    AuthenticationError,
    ChainedEnrichmentProvider,
    OfflineHeuristicEnrichmentProvider,
    OpenAIEnrichmentProvider,
    ProfileEnrichmentProvider,
    RateLimitError,
    ai_fallback_allowed,
    build_provider,
    configured_provider,
    sanitise_ai_identity,
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
    enriched = provider.enrich(_draft())
    assert enriched["enrichment_sources"][-1] == {
        "source_type": "offline_fallback",
        "summary": (
            "OpenAI enrichment was unavailable or rate-limited; offline draft generated "
            "for human review."
        ),
    }


def test_missing_key_falls_back_without_crashing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert streamlit_openai_key({}) is None
    assert MISSING_KEY_WARNING == (
        "No model API key is configured. Using offline demo enrichment."
    )
    assert OfflineHeuristicEnrichmentProvider().enrich(_draft())["fragrance_family"] == "citrus"


def test_key_is_read_only_from_streamlit_secrets_or_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    assert streamlit_openai_key({}) == "environment-secret"
    assert streamlit_openai_key({"OPENAI_API_KEY": "streamlit-secret"}) == "streamlit-secret"


def test_console_reads_the_claude_key_the_same_way(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert streamlit_anthropic_key({}) is None
    monkeypatch.setenv("ANTHROPIC_API_KEY", "environment-secret")
    assert streamlit_anthropic_key({}) == "environment-secret"
    assert streamlit_anthropic_key({"ANTHROPIC_API_KEY": "streamlit-secret"}) == "streamlit-secret"


def test_console_provider_uses_claude_when_only_the_claude_key_exists(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "claude-secret")
    provider = enrichment_provider("chain", {"ANTHROPIC_API_KEY": "claude-secret"})
    assert isinstance(provider, ChainedEnrichmentProvider)


def test_console_provider_falls_back_to_offline_without_any_key(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = enrichment_provider("chain", {})
    assert isinstance(provider, OfflineHeuristicEnrichmentProvider)


class _FakeResponses:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return type("Response", (), {"output_text": json.dumps(self.payload)})()


class _FakeClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.responses = _FakeResponses(payload)


class _FailingResponses:
    def create(self, **kwargs):
        error = RateLimitError.__new__(RateLimitError)
        Exception.__init__(error, "mocked rate limit")
        raise error


class _FailingClient:
    responses = _FailingResponses()


class _AuthenticationFailingResponses:
    def create(self, **kwargs):
        error = AuthenticationError.__new__(AuthenticationError)
        Exception.__init__(error, "mocked authentication failure containing secret-key")
        raise error


class _AuthenticationFailingClient:
    responses = _AuthenticationFailingResponses()


def _ai_payload() -> dict[str, object]:
    list_fields = {
        "top_notes", "heart_notes", "base_notes", "accords", "mood_tags",
        "occasion_tags", "season_tags", "fields_requiring_human_review",
    }
    return {
        field: (["human verification"] if field in list_fields else "unknown")
        for field in AI_DRAFT_FIELDS
    }


def test_openai_call_contains_identity_only_and_returns_required_fields():
    client = _FakeClient(_ai_payload())
    draft = {
        **_draft(), "supplier_code": "SECRET-SKU", "price": "90", "AED": "330",
        "USD": "90", "stock": 12, "cost": 30, "margin": 60, "quantity": 2,
        "commercial_terms": "private", "description": "third-party copy",
        "reviews": ["third-party review"],
    }

    enriched = OpenAIEnrichmentProvider(api_key="test-key", client=client).enrich(draft)

    sent = json.dumps(client.responses.calls)
    assert "Fictional Atelier" in sent and "Citrus Woods" in sent
    for forbidden in (
        "supplier_code", "SECRET-SKU", "price", "AED", "USD", "stock", "cost",
        "margin", "quantity", "commercial_terms", "third-party copy", "third-party review",
    ):
        assert forbidden not in sent
    assert set(AI_DRAFT_FIELDS) <= enriched.keys()


def test_rate_limit_error_uses_offline_fallback():
    enriched = OpenAIEnrichmentProvider(api_key="test-key", client=_FailingClient()).enrich(
        _draft()
    )

    assert enriched["fragrance_family"] == "citrus"
    assert enriched["enrichment_sources"][-1]["source_type"] == "offline_fallback"


def test_authentication_error_uses_safe_offline_fallback():
    enriched = OpenAIEnrichmentProvider(
        api_key="test-key", client=_AuthenticationFailingClient()
    ).enrich(_draft())

    serialised = json.dumps(enriched)
    assert enriched["fragrance_family"] == "citrus"
    assert enriched["enrichment_sources"][-1]["source_type"] == "offline_fallback"
    assert "secret-key" not in serialised
    assert "authentication failure" not in serialised


def test_fallback_setting_defaults_true(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AROMATWIN_AI_ALLOW_FALLBACK", raising=False)
    assert ai_fallback_allowed()


def test_safe_existing_scent_metadata_can_be_sent_without_commercial_fields():
    payload = sanitise_ai_identity({
        **_draft(), "accords": ["fresh", "woody"], "season_tags": ["summer"],
        "price": "99", "quantity": 12, "provenance_notes": "not allow-listed",
    })

    assert payload["accords"] == ["fresh", "woody"]
    assert payload["season_tags"] == ["summer"]
    assert "price" not in payload and "quantity" not in payload
    assert "provenance_notes" not in payload


def test_api_key_is_not_logged_or_written(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    key = "test-secret-never-persist"
    client = _FakeClient(_ai_payload())
    OpenAIEnrichmentProvider(api_key=key, client=client).enrich(_draft())

    assert key not in caplog.text
    assert all(key not in path.read_text(errors="ignore") for path in tmp_path.rglob("*") if path.is_file())
    assert key not in json.dumps(client.responses.calls)


@pytest.mark.parametrize("value", ["offline", "openai", "OPENAI"])
def test_allowed_provider_values(value: str):
    assert configured_provider(value) in {"offline", "openai"}


def test_invalid_provider_is_rejected():
    with pytest.raises(ValueError, match="offline, openai"):
        configured_provider("other")


def _valid_payload(**changes: object) -> dict[str, object]:
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
        "fields_requiring_human_review": ["top_notes"],
    }
    payload.update(changes)
    return payload


def _enrich(payload: dict[str, object], draft: dict[str, object] | None = None):
    client = _FakeClient(payload)
    return OpenAIEnrichmentProvider(api_key="test-key", client=client).enrich(draft or _draft())


def test_model_output_is_validated_and_always_review_gated():
    enriched = _enrich(_valid_payload())

    assert set(enriched) == set(OUTPUT_FIELDS)
    assert enriched["review_status"] == "needs_human_review"
    assert enriched["enrichment_status"] == "enriched_pending_review"
    assert enriched["base_notes"] == ["oud", "labdanum"]
    # Nothing was supplied as evidence, so every populated field is a model assertion.
    assert set(enriched["field_provenance"].values()) == {MODEL_PROVENANCE}
    assert set(enriched["fields_requiring_human_review"]) >= set(enriched["field_provenance"])


def test_supplier_evidence_overrides_model_and_is_marked_as_evidence():
    draft = {**_draft(), "base_notes": ["driftwood", "ambergris"], "accords": ["aquatic"]}
    enriched = _enrich(_valid_payload(base_notes=["vanilla"], accords=["gourmand"]), draft)

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
    """The JSON schema fixes the shape; it does not stop a well-typed nonsense value.

    An unexpected answer becomes a flagged gap, never a coerced plausible value.
    """
    assert _enrich(_valid_payload(**{field: value}))[field] == expected


def test_model_output_cannot_carry_restricted_content():
    enriched = _enrich(
        _valid_payload(draft_scent_description="Shop now at our official website!")
    )
    assert enriched["draft_scent_description"] == ""


def test_oversized_model_lists_are_bounded():
    enriched = _enrich(_valid_payload(top_notes=[f"note {index}" for index in range(50)]))
    assert len(enriched["top_notes"]) <= MAX_LIST_ITEMS


def test_offline_fallback_still_carries_field_provenance():
    """Every path out of the provider satisfies the same output contract."""
    enriched = OpenAIEnrichmentProvider(api_key="test-key", client=_FailingClient()).enrich(
        _draft()
    )
    assert set(enriched) == set(OUTPUT_FIELDS)
    assert set(enriched["field_provenance"].values()) <= {MODEL_PROVENANCE}
    assert enriched["review_status"] == "needs_human_review"


LIST_DRAFT_FIELDS = {
    "top_notes", "heart_notes", "base_notes", "accords", "mood_tags",
    "occasion_tags", "season_tags", "fields_requiring_human_review",
}


def _claude_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        field: (["saffron"] if field in LIST_DRAFT_FIELDS else "unknown")
        for field in AI_DRAFT_FIELDS
    }
    payload.update({
        "fragrance_family": "amber woody",
        "base_notes": ["oud", "labdanum"],
        "season_tags": ["winter"],
        "occasion_tags": ["evening"],
        "draft_scent_description": "A dense resinous reading led by oud over warm labdanum.",
        "ai_confidence_band": "low",
    })
    payload.update(changes)
    return payload


class _FakeMessages:
    def __init__(self, body: str, stop_reason: str = "end_turn") -> None:
        self.body = body
        self.stop_reason = stop_reason
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=self.body)],
        )


class _FakeAnthropicClient:
    def __init__(self, body: str, stop_reason: str = "end_turn") -> None:
        self.messages = _FakeMessages(body, stop_reason)


class _FailingResponsesClient:
    """An OpenAI client whose every call is rate limited."""

    class _Responses:
        def create(self, **kwargs):
            error = RateLimitError.__new__(RateLimitError)
            Exception.__init__(error, "mocked rate limit")
            raise error

    responses = _Responses()


def _anthropic(body: str | dict[str, object], stop_reason: str = "end_turn"):
    text = body if isinstance(body, str) else json.dumps(body)
    client = _FakeAnthropicClient(text, stop_reason)
    return AnthropicEnrichmentProvider(api_key="test-key", client=client), client


def test_claude_call_sends_identity_only_and_validates_the_response():
    provider, client = _anthropic(_claude_payload())
    draft = {
        **_draft(), "supplier_code": "SECRET-SKU", "price": "90", "stock": 12,
        "commercial_terms": "private", "reviews": ["third-party review"],
    }

    enriched = provider.enrich(draft)

    sent = json.dumps(client.messages.calls)
    assert "Fictional Atelier" in sent and "Citrus Woods" in sent
    for forbidden in ("SECRET-SKU", "stock", "commercial_terms", "third-party review"):
        assert forbidden not in sent
    assert client.messages.calls[0]["model"] == "claude-opus-5"
    assert client.messages.calls[0]["output_config"]["format"]["type"] == "json_schema"
    assert set(enriched) == set(OUTPUT_FIELDS)
    assert enriched["review_status"] == "needs_human_review"
    assert enriched["base_notes"] == ["oud", "labdanum"]
    assert set(enriched["field_provenance"].values()) == {MODEL_PROVENANCE}


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("season_tags", ["winter", "narnia"], ["winter"]),
        ("strength_band", "nuclear", "unknown"),
        ("draft_scent_description", "Shop now at our official website!", ""),
    ],
)
def test_claude_output_is_validated_like_every_other_provider(field, value, expected):
    provider, _ = _anthropic(_claude_payload(**{field: value}))
    assert provider.enrich(_draft())[field] == expected


@pytest.mark.parametrize(
    ("body", "stop_reason"),
    [("not json at all {{{", "end_turn"), ('{"fragrance_family": "x"}', "refusal")],
)
def test_claude_degrades_safely_on_bad_or_refused_responses(body, stop_reason):
    """An unparseable answer and a safety decline both fall back rather than crash."""
    provider, _ = _anthropic(body, stop_reason)
    enriched = provider.enrich(_draft())

    assert set(enriched) == set(OUTPUT_FIELDS)
    assert enriched["review_status"] == "needs_human_review"
    assert any(
        source["source_type"] == "offline_fallback" for source in enriched["enrichment_sources"]
    )


def test_claude_without_a_key_falls_back_instead_of_raising(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicEnrichmentProvider()
    assert not provider.is_available
    assert provider.enrich(_draft())["review_status"] == "needs_human_review"


def test_chain_uses_claude_when_the_primary_provider_is_rate_limited():
    """The point of the chain: one vendor failing must not drop a batch to keyword inference."""
    chain = ChainedEnrichmentProvider(
        OpenAIEnrichmentProvider(
            api_key="test-key", client=_FailingResponsesClient(), allow_fallback=True
        ),
        AnthropicEnrichmentProvider(
            api_key="test-key",
            client=_FakeAnthropicClient(json.dumps(_claude_payload())),
            allow_fallback=True,
        ),
    )

    enriched = chain.enrich(_draft())

    assert [s["source_type"] for s in enriched["enrichment_sources"]] == [
        "anthropic_original_draft"
    ]
    assert enriched["fragrance_family"] == "amber woody"


def test_chain_returns_the_offline_draft_only_when_every_provider_degrades():
    chain = ChainedEnrichmentProvider(
        OpenAIEnrichmentProvider(
            api_key="test-key", client=_FailingResponsesClient(), allow_fallback=True
        ),
        AnthropicEnrichmentProvider(
            api_key="test-key", client=_FakeAnthropicClient("not json"), allow_fallback=True
        ),
    )

    enriched = chain.enrich(_draft())

    assert set(enriched) == set(OUTPUT_FIELDS)
    assert enriched["review_status"] == "needs_human_review"
    assert any(
        source["source_type"] == "offline_fallback" for source in enriched["enrichment_sources"]
    )


def test_chain_requires_at_least_one_provider():
    with pytest.raises(ValueError, match="at least one provider"):
        ChainedEnrichmentProvider()


@pytest.mark.parametrize("value", ["offline", "openai", "anthropic", "chain"])
def test_every_allowed_provider_can_be_built(value: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(build_provider(value), ProfileEnrichmentProvider)


def test_unknown_provider_names_every_allowed_value():
    with pytest.raises(ValueError, match="offline, openai, anthropic, chain"):
        build_provider("gemini")
