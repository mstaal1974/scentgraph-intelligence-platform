# Layered Data Model

`import_batches` and `supplier_items` preserve supplier availability and raw fields. `match_candidates` stores possible identities without publishing them. `enrichment_reviews` captures permitted evidence, original/AI description state, proposed characteristics, reviewer decisions, and confidence. Only approved reviews may feed canonical `brands` and `fragrances`.

`reference_sources` describes source capabilities, while `source_provenance` records evidence attached to any entity. `review_statuses` defines controlled workflow states. Notes, accords, vectors, clone relationships, and product mappings form the proprietary intelligence layer.

`profile_drafts` links one supplier item and match candidate to an original placeholder profile,
provenance note, bounded confidence, and review decision. Drafts begin as `needs_human_review` and
contain no supplier commercial fields or third-party descriptive/media fields; approval does not
create a catalogue record. A future promotion boundary may create catalogue records only after
independent review and provenance checks.

Foreign keys, bounded scores, immutable raw values, status checks, and guarded promotion prevent reference data from becoming commercial catalogue content by accident.

## Independent enrichment review records

The review-only API representation links `profile_draft_id` to original description text,
`source_ids`, a provenance summary, bounded source confidence, licensing risk, copied-content flag,
review status, reviewer, and rejection reason. Enrichment sources record identity/reference, URL,
licence status, commercial-use permission, confidence, risk, and reference-only state. These are
workflow records, not canonical catalogue entities, and contain no supplier commercial fields.
