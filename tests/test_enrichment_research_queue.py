from pathlib import Path

from aromatwin.services.enrichment_research_queue import build_enrichment_research_queue


def test_queue_prioritises_multiple_offers_and_uses_safe_questions():
    coverage = [
        {"canonical_brand": "Example", "canonical_fragrance_name": "One",
         "profile_status": "needs_enrichment", "supplier_offer_count": 1,
         "missing_fields": ["notes"]},
        {"canonical_brand": "Example", "canonical_fragrance_name": "Many",
         "profile_status": "no_profile_started", "supplier_offer_count": 3,
         "missing_fields": []},
    ]
    queue = build_enrichment_research_queue(coverage)
    assert queue[0].canonical_fragrance_name == "Many"
    assert all(item.review_status == "needs_human_review" for item in queue)
    questions = " ".join(queue[0].research_questions).casefold()
    assert "permitted sources" in questions
    assert "commercial use or first-party permission" in questions


def test_operational_script_defaults_are_private_and_samples_are_public_safe():
    scripts = [Path("scripts/build_bulk_profile_drafts.py"),
               Path("scripts/build_profile_coverage_report.py"),
               Path("scripts/prepare_enrichment_research_queue.py")]
    assert all("data/private/" in path.read_text() for path in scripts)
    forbidden = ("supplier_price", "aed_price", "usd_price", "stock", "quantity", "cn_code",
                 "supplier_code", "costs", "margins", "commercial_terms")
    for sample in Path("data/samples").glob("*profile*sample.csv"):
        header = sample.read_text().splitlines()[0].casefold()
        assert not any(field in header for field in forbidden)
