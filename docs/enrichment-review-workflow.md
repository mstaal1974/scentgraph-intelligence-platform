# Independent Enrichment Review Workflow

## Boundary and flow

An approved or review-ready `profile_drafts` identity can be used to generate an
`enrichment_review`. Generation copies only the draft ID, brand, fragrance name, and concentration;
it creates new AromaTwin description text and begins at `needs_human_review`. It neither approves
the review nor writes a brand, fragrance, or other catalogue record.

Sources are recorded separately with a stable reference, source type and URL where appropriate,
licence status, commercial-use permission, confidence, licensing risk, and a `reference_only` flag.
Reviewers should prefer an official maker source, then explicitly licensed factual metadata. A
supplier record can establish availability but does not prove public identity. Confidence describes
evidence quality; it never overrides licence restrictions.

## Intellectual-property guardrails

Descriptions are original AromaTwin text. Third-party descriptions, reviews, ratings, comments,
images, and user-generated content are not copied or paraphrased. Restricted sites are not scraped.
Reference-only evidence may guide investigation but cannot be promoted directly. Public enrichment
records omit supplier prices, supplier/CN codes, stock, quantities, and commercial terms.

## Human decisions

1. Generate a `needs_human_review` record from a suitable draft and attach source IDs.
2. A human verifies identity, provenance completeness, confidence, licence status, and originality.
3. `mark-ready` moves the record to `ready_for_approval` only when source provenance is present.
4. A reviewer may approve only a ready record with confidence of at least `0.75`, acceptable
   licensing risk, commercially usable non-reference evidence, and no copied restricted content.
5. Rejection requires a retained reason, such as uncertain identity, incomplete provenance,
   licensing uncertainty, low confidence, or suspected copied material.

Enrichment approval is still not catalogue approval. A later, separately controlled promotion step
may convert approved reviews into catalogue records. Maison Obsidian will later consume only those
approved catalogue profiles through the public API, never draft or enrichment-review queues.

## Bulk research queue hand-off

Bulk coverage can create an offline research queue for incomplete drafts. Tasks contain questions and permitted source-type suggestions only; they do not scrape or retain third-party copy. Completion still enters the existing human enrichment review gate.
