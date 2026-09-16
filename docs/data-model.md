# Layered Data Model

`import_batches` and `supplier_items` preserve supplier availability in private staging. `match_candidates` stores identity hypotheses. `profile_drafts` transforms sanitised identifiers into original structured drafts with `top_notes_json`, `heart_notes_json`, `base_notes_json`, `accords_json`, contextual JSON fields, confidence, provenance, restricted-content detection, and human decision metadata. Every generated draft begins as `needs_human_review`.

`enrichment_sources` records source permissions and confidence without copying source content. `profile_source_links` explains how a source supports a profile. `enrichment_reviews` stores original review-ready content, structured attributes, confidence, licensing risk, copied-text detection, and human decisions. `profile_enrichment_events` provides an append-only audit trail.

Profile approval requires clean content, sufficient confidence, permitted server-side provenance, and an explicit reviewer, but remains separate from catalogue promotion. Canonical `brands` and `fragrances` remain behind a future audited promotion step. Foreign keys, bounded scores, permission flags, controlled states, database checks, and event history prevent supplier or reference records from silently becoming public content.
