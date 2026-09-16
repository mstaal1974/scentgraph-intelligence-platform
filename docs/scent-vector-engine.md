# Scent Vector Engine

A scent vector is a public-safe numerical fingerprint of an approved catalogue fragrance. It
supports comparison without exposing supplier inventory or reproducing protected source material.
The engine never accepts supplier items, profile drafts, or enrichment reviews: those records must
first pass the existing human-reviewed catalogue promotion gate.

## Generation

The deterministic `public_catalogue_keyword_v1` method reads only the allowlisted public fields
family, notes, accords, season, occasion, mood, original description, and concentration. A stable
source fingerprint makes generation idempotent and causes recalculation when those inputs change.
Curated keyword matches produce values from 0 to 1 for warm, fresh, sweet, dark, woody, floral,
spicy, fruity, green, aquatic, marine, leather, powdery, resinous, smoky, gourmand, citrus,
aromatic, amber, musky, luxury, projection, and longevity. Missing evidence produces zero rather
than an invented characteristic.

Confidence increases with populated approved fields and the amount of usable descriptive evidence.
Every output retains catalogue provenance references, its generation method, confidence, review
status, and source fingerprint. Vectors default to `needs_human_review`; only a catalogue input
explicitly marked as having all source fields public-safe can be generated as approved. Human
approval requires confidence of at least 0.70 and fails if supplier-private or copied restricted
content was detected. Rejection records a reason.

## Similarity and safety

Cosine similarity compares the 23 dimensions and returns deterministic scores, highest first.
Only approved or review-safe vectors participate. API responses and the CSV are explicit
allowlists: prices, supplier/CN codes, stock, quantity, commercial terms, third-party descriptions,
reviews, ratings, comments, images, and UGC cannot enter the layer.

This layer is intentionally independent of recommendations. It provides the future numerical
foundation for recommendations, Scentprint matching, clone comparison, fragrance discovery, and
Maison Obsidian discovery tools without implementing or changing those systems now.

## Consumer signal boundary
Consumer Scentprint matching can consume an approved vector as one structured input. Consumer feedback remains a separate, thresholded signal and never rewrites the provenance-backed vector.
