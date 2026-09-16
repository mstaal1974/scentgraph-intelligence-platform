# Catalogue Promotion Workflow

Catalogue promotion is the explicit publication boundary that converts a human-approved enrichment
review into an allowlisted public brand and fragrance representation. It does not publish the
underlying workflow record.

## Why the boundary exists

Supplier items are evidence of availability and can contain confidential prices, codes, stock,
quantities, CN codes, and commercial terms. Match candidates are hypotheses. Profile drafts are
working records. None can be promoted directly. A profile draft must first become an independently
sourced enrichment review, and a human must approve that review as `approved_for_catalogue`.

## Approval gates

Promotion requires the exact `approved_for_catalogue` status, a named human reviewer, source
confidence of at least `0.75` (the configurable default), non-empty source references and provenance
summary, licensing risk below `high`, and no copied third-party content. Every other status is
rejected, including `needs_human_review`, `requires_more_sources`, `rejected_low_confidence`,
`rejected_licensing_risk`, and `rejected_duplicate`. Confidence never overrides licensing.

## Public-safe output

The promoter builds records from a fixed allowlist and retains the originating enrichment-review ID
and source-reference IDs. Supplier prices, supplier codes, stock, quantities, CN codes, commercial
terms, and third-party descriptions, reviews, ratings, comments, images, or UGC are never emitted.
Brand and fragrance slugs are deterministic. Repeating one review is idempotent, while a second
review for the same normalized brand and fragrance is rejected as a duplicate.

The CLI reads `data/enrichment_reviews.csv`, writes `data/catalogue_fragrances.csv`, and reports
accepted and rejected counts. Its `--confidence-threshold` option sets the publication threshold
for a run. Repeated review IDs remain idempotent and are reported
as rejected rather than being written twice. The catalogue API can later serve Maison Obsidian and
other retailers; this stage adds neither retailer integration nor a frontend.
