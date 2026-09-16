# Fragrance Profile Draft Builder

The builder joins an existing supplier item to its match candidate and creates a review record,
not a catalogue fragrance. Every generated record starts as `needs_human_review`; approval is an
explicit human decision and does not promote the draft to the catalogue.

Descriptions are deterministic, original placeholders. The builder uses candidate identity fields
only and does not ingest or reproduce third-party descriptions, reviews, ratings, images, comments,
or user-generated content. Its public schema also omits supplier codes, prices, stock, quantities,
and commercial terms.

Approval requires documented provenance, a non-restricted source, confirmation that descriptive
content was not copied, and source confidence of at least `0.75`. Reference-only, restricted, and
unknown sources remain review material. Rejection requires and stores a reason.

For file workflows, run:

```console
python scripts/build_profile_drafts.py \
  --supplier-items data/supplier_items.csv \
  --match-candidates data/match_candidates.csv \
  --output data/profile_drafts.csv
```

Only the explicitly allowlisted public columns are written.
