from aromatwin.services.profile_coverage import build_profile_coverage


def item(name, **extra):
    return {"canonical_brand": "Example", "canonical_fragrance_name": name, **extra}


def test_coverage_core_lifecycle_statuses():
    offers = [item(name) for name in ("None", "Draft", "Enrich", "Approved", "Published")]
    drafts = [item("Draft", provenance_notes="ok", source_confidence=.8),
              item("Enrich", provenance_notes="ok", source_confidence=.8,
                   enrichment_needed=True, missing_profile_fields=["notes"]),
              item("Approved", provenance_notes="ok", source_confidence=.9,
                   review_status="approved")]
    catalogue = [item("Published", publication_status="published")]
    rows = build_profile_coverage(offers, profile_drafts=drafts, catalogue_records=catalogue)
    statuses = {row.canonical_fragrance_name: row.profile_status for row in rows}
    assert statuses == {"None": "no_profile_started", "Draft": "draft_created",
                        "Enrich": "needs_enrichment", "Approved": "approved_for_catalogue",
                        "Published": "catalogue_published"}
