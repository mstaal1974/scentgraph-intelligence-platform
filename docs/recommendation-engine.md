# Recommendation Engine

The recommendation engine ranks approved public catalogue fragrances without reading supplier
items, profile drafts, or enrichment reviews. It accepts only catalogue projections and scent
vectors whose review status is `approved`, `review_safe`, or the existing review-safe
`needs_human_review` state. Public recommendation payloads contain an explicit allowlist and never
contain supplier prices/codes, stock, quantities, CN codes, or commercial terms.

## Ranking and explanations

Similarity is cosine similarity across the 23 bounded scent-vector dimensions. The deterministic
score is 75% vector similarity and 25% shared context, capped to `[0, 1]`; ties use the public
fragrance ID. Context signals include family, accords, mood, occasion, season, and intensity when
present. The engine labels results as similar, same-family/context, contrast, softer/stronger,
clone-or-inspired candidate, or discovery picks. Clone labels are accepted only as curated flags;
they are not inferred from third-party claims.

Reasons are short, template-generated AromaTwin sentences based on shared dimensions and context.
Difference summaries describe the largest vector deltas. Neither field copies catalogue source
descriptions, reviews, ratings, comments, images, or UGC. Confidence combines the lower input-vector
confidence with recommendation fit. Generation is idempotent by source, candidate, and type; the
source fragrance is always excluded.

## Safety and review

Every catalogue input must be approved and every vector must be approved or explicitly review-safe.
Rejected vectors, copied-content flags, restricted fields, and populated supplier-private fields
stop generation. Results generated entirely from approved vectors may be approved immediately;
all others default to `needs_human_review`. Human approval additionally requires confidence of at
least `0.70` and reruns the private/restricted-content checks. Rejection requires and stores a
reason. These gates preserve licensing boundaries: provenance supports the public facts, while the
recommendation and its prose are original AromaTwin derivations.

## API and batch generation

The API supports listing, retrieval, generation, vector-ranked similar results, contextual filters,
approval, and rejection under `/recommendations`. `scripts/build_recommendations.py` reads only
`data/catalogue_fragrances.csv` and `data/scent_vectors.csv`, writes the public-safe output, and
reports accepted and rejected counts. Input files with supplier-private headers are rejected.

This focused layer can later power Maison Obsidian catalogue discovery, Scentprint preferences,
reviewed clone alternatives, and personalised scent matching. Those consumers remain separate and
must use this public-safe boundary rather than reaching into supplier or review workflow records.
