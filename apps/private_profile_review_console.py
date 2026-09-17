"""Private, non-publishing Streamlit console for profile draft review."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aromatwin.services.review_decisions import apply_review_decision
from aromatwin.services.review_gates import ALLOWED_DECISIONS

PRIVATE_ROOT = (REPOSITORY_ROOT / "data" / "private").resolve()
DEFAULT_RUN_ID = "first_private_supplier_profile_run_20260917"
DECISIONS_PATH = PRIVATE_ROOT / "reports" / "review_decisions.json"
SAFETY_COPY = (
    "This console records internal human review decisions only. It does not publish, "
    "approve public catalogue content, create products, or export to Maison Obsidian."
)
COMMERCIAL_FIELD_PARTS = (
    "price", "cost", "margin", "stock", "inventory", "wholesale", "commercial_terms",
    "moq", "minimum_order", "supplier_code",
)


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
    return (
        _load_list(drafts_path, private_root=private_root),
        _load_list(base / "review_packets.json", private_root=private_root),
        _load_list("reports/review_decisions.json", private_root=private_root),
    )


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


def _options(rows: Iterable[dict[str, Any]], field: str) -> list[str]:
    return sorted({str(row.get(field)) for row in rows if row.get(field) is not None})


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="AromaTwin Private Profile Review Console", layout="wide")
    st.title("AromaTwin Private Profile Review Console")
    st.warning(SAFETY_COPY)
    run_id = st.text_input("Run ID", value=DEFAULT_RUN_ID)
    try:
        drafts, packets, decisions = load_review_data(run_id)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        st.error(str(exc))
        st.stop()

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
    detail, decision_panel = st.columns((3, 2))
    with detail:
        st.subheader("Profile detail")
        st.json(without_commercial_fields(selected))
        if packet:
            st.subheader("Review packet")
            st.json(without_commercial_fields(packet))
    with decision_panel:
        st.subheader("Record internal decision")
        with st.form("decision_form"):
            decision = st.selectbox("Decision", ALLOWED_DECISIONS)
            reviewer_role = st.text_input("Reviewer role", value="catalogue_reviewer")
            reviewer_alias = st.text_input("Reviewer alias")
            reason = st.text_area("Decision reason")
            submitted = st.form_submit_button("Save decision", type="primary")
        if submitted:
            try:
                record_decision(build_review_item(selected, packet), decision, reviewer_role,
                                decision_reason=reason, reviewer_alias=reviewer_alias)
            except (ValueError, OSError, json.JSONDecodeError) as exc:
                st.error(f"Decision could not be recorded: {exc}")
            else:
                st.success("The decision was recorded for internal workflow only.")


if __name__ == "__main__":
    main()
