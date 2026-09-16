# Layered Data Model

`import_batches` and `supplier_items` preserve supplier availability and raw fields in private staging. `match_candidates` stores possible identities without publishing them. `profile_drafts` transforms sanitised identifiers into original structured drafts with note, accord, context, and scent-vector JSON fields. Confidence, provenance, restricted-content detection, and reviewer decisions remain attached to every draft; generation always starts at `needs_human_review`.

`enrichment_reviews` captures later permitted evidence and proposed characteristics. Only independently verified, human-approved material may progress toward canonical `brands` and `fragrances`. Approval of a profile draft does not perform that promotion.

`reference_sources` describes source capabilities, while `source_provenance` records evidence attached to entities. Notes, accords, vectors, clone relationships, and product mappings form the proprietary intelligence layer. Foreign keys, bounded scores, controlled statuses, review checks, and guarded promotion prevent supplier or reference rows from silently becoming commercial catalogue content.
