# Fragrance Profile Draft Builder

## Supplier-first workflow

Supplier imports establish that an item is available, but they do not establish a publishable
fragrance identity. Candidate matching links an existing supplier item to a possible brand,
fragrance name, and concentration with a source type and confidence score. The builder joins those
existing records; it does not replace the import or matching layers.

For each candidate, generation produces the same original AromaTwin placeholder from the candidate
brand and name. It copies no source prose or media. Every result starts as
`needs_human_review`, so generation can never auto-approve a record.

## Drafts, review, and provenance

A profile draft is a curator work item, **not** a catalogue fragrance. Its public allowlist omits
supplier codes, prices, stock, quantities, and commercial terms. A human must independently verify
the identity and make an explicit decision. Rejection requires a stored reason.

Approval requires a complete provenance note, a permitted source type, confidence of at least
`0.75`, and an unchanged safe placeholder. Reference-only, restricted, unknown, low-confidence, or
copied content is blocked. Approval changes only the draft's review status; this layer deliberately
does not create or promote a catalogue record.

## Licensing and IP guardrails

Candidate sources may help resolve identity only within their permitted use. Third-party
descriptions, reviews, ratings, images, comments, and user-generated content cannot be copied into
drafts because availability for reference does not grant a licence to republish that material.
Descriptions for eventual publication must be independently created, reviewed, and supported by
traceable provenance.

## Future catalogue and Maison Obsidian flow

A later, separately reviewed promotion workflow will turn eligible approved drafts into canonical
catalogue records. Once that boundary exists, Maison Obsidian will consume approved catalogue
profiles through the public API—not supplier rows, candidate evidence, or profile drafts. Keeping
that integration downstream of catalogue approval preserves the review, provenance, and licensing
boundary.

## File workflow

For file workflows, run:

```console
python scripts/build_profile_drafts.py \
  --supplier-items data/supplier_items.csv \
  --match-candidates data/match_candidates.csv \
  --output data/profile_drafts.csv
```

Only the explicitly allowlisted public columns are written.
