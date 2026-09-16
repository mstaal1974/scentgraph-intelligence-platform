# Independent Enrichment Review Workflow

## From profile draft to enrichment

A profile draft begins with supplier availability and a candidate identity. Enrichment adds independently recorded source metadata and an original, deterministic AromaTwin description. It does not publish the profile and never changes a catalogue record.

Sources are registered before use with their name, type, URL/domain, confidence, commercial-use permission, factual-reference permission, matching permission, and text/image copying permissions. Official brand sources are preferred. Reference-only, restricted, unknown, or non-commercial sources may support permitted discovery but cannot directly justify commercial approval.

The foundation does not fetch pages, scrape sites, call external AI services, or store third-party prose. Descriptions are generated from profile identifiers and source metadata only. Reviews, ratings, comments, images, article text, UGC, supplier prices, codes, and commercial terms are excluded.

## Review states

Generation creates `needs_human_review`, never approval. A reviewer may attach recorded sources and mark a review ready only when confidence is at least 0.70, licensing risk is low, every linked source permits factual reference, and no prohibited copying is detected. `ready_for_approval` still requires a separate named human approval decision.

Approval fails when provenance is insufficient, licensing risk is medium/high, copied text conflicts with a source's permissions, or state is not `ready_for_approval`. Rejection requires a reason and controlled rejection status. Generation, source attachment, readiness, approval, and rejection create immutable profile enrichment events.

`approved_for_catalogue` records remain enrichment-review outputs. A future audited promotion process will create or update public catalogue records. Maison Obsidian integration and publication are outside this stage.
