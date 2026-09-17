import json
from pathlib import Path

import pytest

from apps.private_profile_review_console import (
    batch_enrichment_limit,
    build_review_item,
    load_review_data,
    private_path,
    record_decision,
    save_enrichments,
    without_commercial_fields,
)


def _draft() -> dict[str, str]:
    return {
        "profile_draft_id": "draft-1", "brand_display_name": "Fictional Atelier",
        "fragrance_display_name": "Cloud Archive", "confidence_band": "medium",
        "evidence_status": "pending", "provenance_status": "pending",
        "enrichment_status": "ready", "review_status": "needs_human_review",
    }


def test_load_review_data_reads_private_drafts_and_optional_files(tmp_path: Path):
    root = tmp_path / "data" / "private"
    profiles = root / "runs" / "run-1" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "drafts.json").write_text(json.dumps([_draft()]), encoding="utf-8")

    drafts, packets, decisions = load_review_data("run-1", private_root=root)

    assert drafts == [_draft()]
    assert packets == []
    assert decisions == []


def test_record_decision_writes_and_updates_only_private_report(tmp_path: Path):
    root = tmp_path / "data" / "private"
    item = build_review_item(_draft())
    output = root / "reports" / "review_decisions.json"

    record_decision(item, "hold", "catalogue_reviewer", output_path=output, private_root=root)
    record_decision(item, "approve", "catalogue_reviewer", output_path=output, private_root=root)

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["decision"] == "approve"
    assert saved[0]["next_status"] == "approved_for_catalogue_review"


@pytest.mark.parametrize("path", ["../public.json", "../../samples/drafts.json"])
def test_unsupported_output_paths_are_rejected(tmp_path: Path, path: str):
    root = tmp_path / "data" / "private"
    with pytest.raises(ValueError, match="data/private"):
        private_path(path, private_root=root)


def test_commercial_supplier_fields_are_not_rendered_or_written_publicly(tmp_path: Path):
    draft = {**_draft(), "supplier_price": "99.00", "nested": {"margin_band": "high"}}
    assert "supplier_price" not in without_commercial_fields(draft)
    assert without_commercial_fields(draft)["nested"] == {}

    root = tmp_path / "data" / "private"
    record_decision(build_review_item(draft), "reject", "catalogue_reviewer",
                    output_path="reports/review_decisions.json", private_root=root)
    assert not (tmp_path / "data" / "samples").exists()
    assert not (tmp_path / "public").exists()
    saved = (root / "reports" / "review_decisions.json").read_text(encoding="utf-8")
    assert "supplier_price" not in saved and "margin_band" not in saved


def test_enrichment_is_upserted_only_at_the_private_run_path(tmp_path: Path):
    root = tmp_path / "data" / "private"
    enrichment = {**_draft(), "accords": ["fresh"], "supplier_price": "secret"}

    destination = save_enrichments("run-1", [enrichment], private_root=root)
    save_enrichments("run-1", [{**enrichment, "accords": ["woody"]}], private_root=root)

    assert destination == root / "runs" / "run-1" / "profiles" / "enriched_profiles.json"
    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert len(saved) == 1 and saved[0]["accords"] == ["woody"]
    assert "supplier_price" not in saved[0]


def test_cloud_demo_batch_enrichment_defaults_to_one_profile():
    assert batch_enrichment_limit(cloud_demo=True) == 1
