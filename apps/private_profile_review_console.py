"""Private, non-publishing Streamlit console for profile draft review."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aromatwin.services.profile_enrichment import (  # noqa: E402
    EVIDENCE_PROVENANCE,
    MISSING_KEY_WARNING,
    MODEL_PROVENANCE,
    OPENAI_FALLBACK_SUMMARY,
    OfflineHeuristicEnrichmentProvider,
    OpenAIError,
    build_provider,
    configured_provider,
)
from aromatwin.services.review_decisions import apply_review_decision  # noqa: E402
from aromatwin.services.review_gates import ALLOWED_DECISIONS  # noqa: E402

PROVENANCE_LABELS = {
    EVIDENCE_PROVENANCE: "✅ supplier evidence",
    MODEL_PROVENANCE: "⚠️ model proposal — unverified",
}

PRIVATE_ROOT = (REPOSITORY_ROOT / "data" / "private").resolve()
DEFAULT_RUN_ID = "first_private_supplier_profile_run_20260917"
DECISIONS_PATH = PRIVATE_ROOT / "reports" / "review_decisions.json"
SAFETY_COPY = (
    "This console records internal human review decisions only. It does not publish, "
    "approve public catalogue content, create products, or export to Maison Obsidian."
)
ENRICHMENT_WARNING = "AI enrichment is draft-only and requires human review before catalogue use."
OPENAI_FALLBACK_WARNING = (
    "OpenAI enrichment is currently unavailable or rate-limited. Offline draft enrichment "
    "was used instead."
)
COMMERCIAL_FIELD_PARTS = (
    "price", "cost", "margin", "stock", "inventory", "wholesale", "commercial_terms",
    "moq", "minimum_order", "supplier_code", "aed", "usd",
)
STATUS_BADGES = {
    "needs_enrichment": "🟠 needs_enrichment",
    "enriched_pending_review": "🔵 enriched_pending_review",
    "provenance_review_required": "🟣 provenance_review_required",
    "approved_for_catalogue_review": "🟢 approved_for_catalogue_review",
}


def private_path(path: str | Path, *, private_root: str | Path = PRIVATE_ROOT) -> Path:
    """Resolve and enforce the console's private-only filesystem boundary."""
    root = Path(private_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Profile review console paths must remain under data/private")
    return candidate


def _load_list(path: str | Path, *, private_root: str | Path = PRIVATE_ROOT) -> list[dict[str, Any]]:
    source = private_path(path, private_root=private_root)
    if not source.exists():
        return []
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError(f"Expected a JSON list of objects in {source.name}")
    return payload


def load_review_data(
    run_id: str, *, private_root: str | Path = PRIVATE_ROOT
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Load drafts and optional review inputs without leaving the private root."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", run_id):
        raise ValueError("run_id may contain only letters, numbers, dots, underscores, and hyphens")
    base = Path("runs") / run_id / "profiles"
    drafts_path = private_path(base / "drafts.json", private_root=private_root)
    if not drafts_path.is_file():
        raise FileNotFoundError(f"No private drafts found for run {run_id!r}")
    drafts = _load_list(drafts_path, private_root=private_root)
    enriched = {
        str(row.get("profile_draft_id")): row
        for row in _load_list(base / "enriched_profiles.json", private_root=private_root)
    }
    drafts = [{**draft, **enriched.get(str(draft.get("profile_draft_id")), {})} for draft in drafts]
    return (
        drafts,
        _load_list(base / "review_packets.json", private_root=private_root),
        _load_list("reports/review_decisions.json", private_root=private_root),
    )


def demo_review_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return fictional, commercially sanitised data for public demo deployments."""
    records = [
        {
            "profile_draft_id": "demo-aurora-01", "brand_display_name": "Lumen Atelier",
            "fragrance_display_name": "Citrus Aurora", "supplier_public_label": "Demo source",
            "confidence_band": "medium", "blocking_issues": [], "fragrance_family": "citrus",
            "top_notes": [], "heart_notes": [], "base_notes": [],
            "accords": ["citrus", "fresh"], "mood_tags": ["bright", "uplifting"],
            "occasion_tags": ["daytime", "casual"], "season_tags": ["spring", "summer"],
            "strength_band": "unknown", "longevity_band": "unknown", "projection_band": "unknown",
            "draft_scent_description": "A bright, fresh citrus direction shaped for an easy daytime mood.",
            "ai_confidence_band": "low",
            "enrichment_sources": [{"source_type": "demo_taxonomy", "summary": "Fictional name keyword classification."}],
            "provenance_notes": ENRICHMENT_WARNING,
            "fields_requiring_human_review": ["top_notes", "heart_notes", "base_notes", "performance"],
            "enrichment_status": "enriched_pending_review", "review_status": "needs_human_review",
        },
        {
            "profile_draft_id": "demo-ember-02", "brand_display_name": "Northstar Parfums",
            "fragrance_display_name": "Ember Woods", "supplier_public_label": "Demo source",
            "confidence_band": "low", "blocking_issues": [], "fragrance_family": "woody",
            "top_notes": [], "heart_notes": [], "base_notes": [], "accords": ["woody"],
            "mood_tags": ["grounded", "calm"], "occasion_tags": ["evening"],
            "season_tags": ["autumn", "winter"], "strength_band": "unknown",
            "longevity_band": "unknown", "projection_band": "unknown",
            "draft_scent_description": "A calm woody direction suggested only by its fictional name.",
            "ai_confidence_band": "low",
            "enrichment_sources": [{"source_type": "demo_taxonomy", "summary": "Fictional name keyword classification."}],
            "provenance_notes": ENRICHMENT_WARNING,
            "fields_requiring_human_review": ["top_notes", "heart_notes", "base_notes", "performance"],
            "enrichment_status": "enriched_pending_review", "review_status": "needs_human_review",
        },
    ]
    return records, [], []


def load_console_data(run_id: str, *, private_root: str | Path = PRIVATE_ROOT) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Load private records, falling back to safe fictional demo records."""
    try:
        drafts, packets, decisions = load_review_data(run_id, private_root=private_root)
        return drafts, packets, decisions, False
    except FileNotFoundError:
        drafts, packets, decisions = demo_review_data()
        return drafts, packets, decisions, True


def without_commercial_fields(value: Any) -> Any:
    """Remove supplier-commercial keys from objects before rendering them."""
    if isinstance(value, dict):
        return {
            key: without_commercial_fields(item)
            for key, item in value.items()
            if not any(part in key.casefold() for part in COMMERCIAL_FIELD_PARTS)
        }
    if isinstance(value, list):
        return [without_commercial_fields(item) for item in value]
    return value


def build_review_item(draft: dict[str, Any], packet: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the minimal gate contract accepted by the decision service."""
    draft_id = str(draft["profile_draft_id"])
    packet_id = str((packet or {}).get("review_packet_id", draft_id))
    return {
        "review_item_id": f"profile-review:{packet_id}",
        "gate_id": f"gate:profile_draft_review:{draft_id}",
        "gate_type": "profile_draft_review",
        "linked_entity_type": "profile_draft",
        "linked_entity_id": draft_id,
    }


def record_decision(
    review_item: dict[str, Any], decision: str, reviewer_role: str, *,
    decision_reason: str | None = None, reviewer_alias: str | None = None,
    output_path: str | Path = DECISIONS_PATH, private_root: str | Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    """Apply and upsert an internal decision in the private report only."""
    destination = private_path(output_path, private_root=private_root)
    result = apply_review_decision(
        review_item, decision, reviewer_role, decision_reason=decision_reason or None,
        reviewer_alias=reviewer_alias or None,
    )
    existing = _load_list(destination, private_root=private_root)
    existing = [row for row in existing if row.get("review_item_id") != result["review_item_id"]]
    existing.append(result)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return result


def save_enrichments(
    run_id: str, enrichments: Iterable[dict[str, Any]], *,
    private_root: str | Path = PRIVATE_ROOT,
) -> Path:
    """Upsert enrichments at the one permitted private run destination."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", run_id):
        raise ValueError("run_id may contain only letters, numbers, dots, underscores, and hyphens")
    destination = private_path(
        Path("runs") / run_id / "profiles" / "enriched_profiles.json",
        private_root=private_root,
    )
    existing = _load_list(destination, private_root=private_root)
    indexed = {str(row.get("profile_draft_id")): row for row in existing}
    for enrichment in enrichments:
        safe = without_commercial_fields(dict(enrichment))
        indexed[str(safe.get("profile_draft_id"))] = safe
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(list(indexed.values()), indent=2) + "\n", encoding="utf-8")
    return destination


# Which secrets each provider setting needs before it can do anything but keyword inference.
# "chain" needs only one of the two, because either vendor can carry the batch alone.
PROVIDER_KEYS = {
    "offline": (),
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "chain": ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"),
}


def enrichment_provider(provider_name: str, keys: Mapping[str, str | None] | None = None):
    """Select a provider, falling back deterministically when no key exists.

    Keys are passed through the process environment rather than as arguments, because the
    chained provider builds its members itself. Nothing is written back to the environment
    unless the console actually found a value for it.
    """
    required = PROVIDER_KEYS.get(provider_name, ())
    for name in required:
        value = (keys or {}).get(name)
        if value:
            os.environ[name] = value
    if required and not any(os.environ.get(name) for name in required):
        return OfflineHeuristicEnrichmentProvider()
    return build_provider(provider_name)


def batch_enrichment_limit(*, cloud_demo: bool, requested: int = 1) -> int:
    """Return a bounded batch size, with a single-profile cloud-demo default."""
    if requested < 1:
        raise ValueError("Batch enrichment must include at least one profile")
    return 1 if cloud_demo and requested == 1 else requested


def _options(rows: Iterable[dict[str, Any]], field: str) -> list[str]:
    return sorted({str(row.get(field)) for row in rows if row.get(field) is not None})


def streamlit_api_key(secrets: Any, name: str) -> str | None:
    """Read a key from Streamlit secrets, then the process environment, and nowhere else."""
    try:
        secret_key = secrets[name]
    except (KeyError, FileNotFoundError):
        secret_key = None
    if secret_key:
        return str(secret_key)
    if name in os.environ:
        return os.environ[name]
    return None


def streamlit_openai_key(secrets: Any) -> str | None:
    """Read the OpenAI key. Retained as the named entry point for the OpenAI surface."""
    return streamlit_api_key(secrets, "OPENAI_API_KEY")


def streamlit_anthropic_key(secrets: Any) -> str | None:
    """Read the Claude key, so the console can use the same backup provider as the CLI."""
    return streamlit_api_key(secrets, "ANTHROPIC_API_KEY")


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="AromaTwin Private Profile Review Console", layout="wide")
    st.title("AromaTwin Private Profile Review Console")
    st.warning(SAFETY_COPY)
    run_id = st.text_input("Run ID", value=DEFAULT_RUN_ID)
    try:
        drafts, packets, decisions, demo_mode = load_console_data(run_id)
    except (ValueError, json.JSONDecodeError) as exc:
        st.error(str(exc))
        st.stop()
    if demo_mode:
        st.info("Demo mode: showing sanitised fictional records. Decisions remain in this browser session only.")
        decisions = st.session_state.setdefault("demo_review_decisions", [])
        demo_enrichments = st.session_state.setdefault("demo_profile_enrichments", {})
        drafts = [
            {**draft, **demo_enrichments.get(str(draft.get("profile_draft_id")), {})}
            for draft in drafts
        ]
    st.warning(ENRICHMENT_WARNING)
    try:
        provider_name = configured_provider()
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    keys = {
        "OPENAI_API_KEY": streamlit_openai_key(st.secrets),
        "ANTHROPIC_API_KEY": streamlit_anthropic_key(st.secrets),
    }
    required = PROVIDER_KEYS.get(provider_name, ())
    if required and not any(keys.get(name) for name in required):
        st.info(MISSING_KEY_WARNING)
    provider = enrichment_provider(provider_name, keys)

    latest = {str(row.get("review_item_id")): row for row in decisions}
    packet_by_draft = {str(row.get("profile_draft_id")): row for row in packets}
    rows = []
    for draft in drafts:
        item = build_review_item(draft, packet_by_draft.get(str(draft.get("profile_draft_id"))))
        row = without_commercial_fields(draft)
        row["decision_status"] = latest.get(item["review_item_id"], {}).get("decision", "pending")
        rows.append(row)

    review_item_ids = {
        build_review_item(draft, packet_by_draft.get(str(draft.get("profile_draft_id"))))[
            "review_item_id"
        ]
        for draft in drafts
    }
    decision_rows = [row for item_id, row in latest.items() if item_id in review_item_ids]
    metrics = (
        ("Draft count", len(drafts)), ("Decisions recorded", len(decision_rows)),
        ("Pending review", sum(row["decision_status"] == "pending" for row in rows)),
        ("Enrichment requested", sum(row.get("decision") == "request_enrichment" for row in decision_rows)),
        ("Provenance review requested", sum(row.get("decision") == "request_provenance_review" for row in decision_rows)),
        ("Approved for catalogue review", sum(row.get("next_status") == "approved_for_catalogue_review" for row in decision_rows)),
    )
    for column, (label, value) in zip(st.columns(6), metrics):
        column.metric(label, value)

    filtered = rows
    with st.sidebar:
        st.header("Filters")
        for field in ("confidence_band", "evidence_status", "provenance_status",
                      "enrichment_status", "review_status", "decision_status"):
            choices = st.multiselect(field.replace("_", " ").title(), _options(rows, field))
            if choices:
                filtered = [row for row in filtered if str(row.get(field)) in choices]
        search = st.text_input("Search brand/fragrance").strip().casefold()
        if search:
            filtered = [row for row in filtered if search in " ".join((
                str(row.get("brand_display_name", "")),
                str(row.get("fragrance_display_name", "")),
            )).casefold()]

    table_fields = ["profile_draft_id", "brand_display_name", "fragrance_display_name",
                    "confidence_band", "evidence_status", "provenance_status",
                    "enrichment_status", "review_status", "decision_status"]
    st.subheader("Draft profiles")
    st.dataframe([{key: row.get(key) for key in table_fields} for row in filtered],
                 use_container_width=True, hide_index=True)
    if not filtered:
        st.info("No drafts match the selected filters.")
        return

    labels = {
        str(row["profile_draft_id"]):
        f"{row.get('brand_display_name', 'Unknown')} — {row.get('fragrance_display_name', 'Unknown')}"
        for row in filtered
    }
    selected_id = st.selectbox("Selected profile", labels, format_func=labels.get)
    selected = next(row for row in filtered if str(row["profile_draft_id"]) == selected_id)
    packet = packet_by_draft.get(selected_id)

    action_one, action_batch = st.columns(2)
    enrich_selected = action_one.button("Enrich selected profile", type="primary")
    batch_enrich = False
    max_profiles = 1
    if demo_mode:
        max_profiles = action_batch.number_input(
            "Max profiles", min_value=1, max_value=max(1, len(filtered)), value=1, step=1
        )
        confirm_batch = action_batch.checkbox(
            "Confirm OpenAI enrichment for visible profiles", value=False
        )
        batch_enrich = action_batch.button(
            "Batch enrich visible profiles", disabled=not confirm_batch
        )

    batch_limit = batch_enrichment_limit(cloud_demo=demo_mode, requested=int(max_profiles))
    targets = filtered[:batch_limit] if batch_enrich else ([selected] if enrich_selected else [])
    if targets:
        try:
            generated = [provider.enrich(target) for target in targets]
        except OpenAIError:
            # The provider normally handles SDK failures itself. Keep this UI-level
            # safety net free of exception details so credentials and provider
            # responses can never be exposed in the console.
            generated = [OfflineHeuristicEnrichmentProvider().enrich(target) for target in targets]
            for enrichment in generated:
                enrichment["enrichment_sources"].append({
                    "source_type": "offline_fallback",
                    "summary": OPENAI_FALLBACK_SUMMARY,
                })

        try:
            if demo_mode:
                cached = st.session_state.setdefault("demo_profile_enrichments", {})
                for enrichment in generated:
                    cached[str(enrichment["profile_draft_id"])] = enrichment
            else:
                save_enrichments(run_id, generated)
            by_id = {str(row["profile_draft_id"]): row for row in generated}
            for row in rows:
                row.update(by_id.get(str(row.get("profile_draft_id")), {}))
            selected.update(by_id.get(selected_id, {}))
            if any(
                source.get("source_type") == "offline_fallback"
                for enrichment in generated
                for source in enrichment.get("enrichment_sources", [])
            ):
                st.warning(OPENAI_FALLBACK_WARNING)
            st.success(f"Created {len(generated)} enrichment draft(s). Human review is required.")
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            st.error(f"Enrichment could not be created: {exc}")

    overview, scent_profile, evidence, review = st.tabs(
        ["Overview", "Scent Profile", "Evidence & Provenance", "Review Decision"]
    )
    with overview:
        st.subheader(f"{selected.get('brand_display_name')} — {selected.get('fragrance_display_name')}")
        for status in (selected.get("enrichment_status", "needs_enrichment"), selected.get("review_status")):
            if status:
                st.markdown(f"**Status:** `{STATUS_BADGES.get(str(status), status)}`")
        if packet:
            st.subheader("Review packet")
            st.json(without_commercial_fields(packet))
    with scent_profile:
        st.caption(f"AI provider: {provider_name}")
        scent_fields = ("fragrance_family", "top_notes", "heart_notes", "base_notes", "accords",
                        "mood_tags", "occasion_tags", "season_tags", "strength_band",
                        "longevity_band", "projection_band", "draft_scent_description")
        provenance = selected.get("field_provenance") or {}
        asserted = [field for field in scent_fields
                    if provenance.get(field) == MODEL_PROVENANCE]
        if asserted:
            st.warning(
                f"{len(asserted)} of these fields are unverified model proposals with no source "
                "evidence. Approving this profile approves each of them as fact.",
                icon="⚠️",
            )
        # A field-by-field table, not one JSON blob: the reviewer should be able to see at a
        # glance which specific claims carry evidence and which are the model's guess.
        st.dataframe(
            [
                {
                    "field": field,
                    "value": selected.get(field),
                    "basis": PROVENANCE_LABELS.get(
                        provenance.get(field, ""), "not populated"
                    ),
                }
                for field in scent_fields
            ],
            width="stretch",
            hide_index=True,
        )
    with evidence:
        st.json({field: selected.get(field) for field in (
            "ai_confidence_band", "enrichment_sources", "provenance_notes",
            "fields_requiring_human_review", "field_provenance")})
    with review:
        st.subheader("Record internal decision")
        if st.button("Mark for enrichment"):
            item = build_review_item(selected, packet)
            if demo_mode:
                result = {**item, "decision": "request_enrichment", "next_status": "needs_enrichment"}
                st.session_state["demo_review_decisions"] = [
                    row for row in decisions if row.get("review_item_id") != item["review_item_id"]
                ] + [result]
                st.success("Demo decision saved to session state only.")
            else:
                record_decision(item, "request_enrichment", "catalogue_reviewer")
                st.success("Profile marked for enrichment in the private review report.")
        with st.form("decision_form"):
            decision = st.selectbox("Decision", ALLOWED_DECISIONS)
            reviewer_role = st.text_input("Reviewer role", value="catalogue_reviewer")
            reviewer_alias = st.text_input("Reviewer alias")
            reason = st.text_area("Decision reason")
            submitted = st.form_submit_button("Save decision", type="primary")
        if submitted:
            try:
                if demo_mode:
                    result = apply_review_decision(build_review_item(selected, packet), decision,
                                                   reviewer_role, decision_reason=reason or None,
                                                   reviewer_alias=reviewer_alias or None)
                    st.session_state["demo_review_decisions"] = [
                        row for row in decisions if row.get("review_item_id") != result["review_item_id"]
                    ] + [result]
                else:
                    record_decision(build_review_item(selected, packet), decision, reviewer_role,
                                    decision_reason=reason, reviewer_alias=reviewer_alias)
            except (ValueError, OSError, json.JSONDecodeError) as exc:
                st.error(f"Decision could not be recorded: {exc}")
            else:
                st.success("The decision was recorded for internal workflow only.")


if __name__ == "__main__":
    main()
