# API Contract

The foundation exposes JSON and OpenAPI at `/docs` and `/openapi.json`.

- Operations: `GET /health`
- Supplier: `GET /supplier-items`, `GET /supplier-items/{id}`, `POST /supplier-items/import-preview`
- Matching: `GET /match-candidates`, `GET /match-candidates/{id}`, `POST /match-candidates/generate`
- Enrichment: `GET /enrichment-reviews`, `GET /enrichment-reviews/{id}`, `POST /enrichment-reviews/{id}/approve`, `POST /enrichment-reviews/{id}/reject`
- Profile drafts: `GET /profile-drafts`, `GET /profile-drafts/{id}`, `POST /profile-drafts/generate`, `POST /profile-drafts/{id}/approve`, `POST /profile-drafts/{id}/reject`
- Catalogue promotion: `GET /catalogue/brands`, `GET /catalogue/brands/{id}`, `GET /catalogue/fragrances`, `GET /catalogue/fragrances/{id}`, `POST /catalogue/promote`
- Legacy catalogue discovery: `GET /brands`, `GET /fragrances`, `GET /fragrances/{id}`, `GET /notes`, `GET /accords`, `GET /search?q=`
- Intelligence: recommendation routes below, `GET /similar/{fragrance_id}`, `POST /scentprint`, and `GET /clone-matches/{fragrance_id}`

Foundation workflow endpoints may use in-memory previews until repositories are wired, but all requests and responses remain typed. Approved catalogue routes must never expose unapproved enrichment or restricted source content.

Profile-draft responses deliberately omit supplier prices, codes, stock, quantities, and commercial
terms. Generate only creates `needs_human_review` records; approve and reject are review decisions,
not catalogue promotion operations. Approval returns `422` when provenance is incomplete, source
confidence is below `0.75`, the source is restricted/reference-only, or copied content is detected.
Rejection requires a reason, which is retained on the draft.

## Enrichment review workflow

- `POST /enrichment-reviews/generate` creates only a `needs_human_review` record.
- `POST /enrichment-reviews/{id}/mark-ready` requires sufficient recorded provenance.
- `POST /enrichment-reviews/{id}/approve` requires `ready_for_approval`, confidence at least
  `0.75`, acceptable licensing risk, non-reference commercially usable evidence, and no copied
  restricted content. It does not promote to the catalogue.
- `POST /enrichment-reviews/{id}/reject` requires and retains a rejection reason.
- `GET /enrichment-sources` and `POST /enrichment-sources` list and record provenance metadata.

Enrichment responses omit prices, supplier/CN codes, stock, quantities, commercial terms, and
third-party descriptions, reviews, ratings, images, comments, or UGC.

## Catalogue promotion

`POST /catalogue/promote` accepts only an `enrichment_review_id`. The referenced review must have
status `approved_for_catalogue`, human attribution, sufficient provenance and confidence, acceptable
licensing risk, and no restricted copied content or supplier-private values. A successful response
contains a decision and public-safe fragrance. Repeating it safely returns the existing promotion.
The `/catalogue` GET operations expose only this allowlisted projection.
# Scent vectors

`GET /scent-vectors`, `GET /scent-vectors/{id}`, and
`GET /catalogue/fragrances/{fragrance_id}/scent-vector` expose public-safe vectors. `POST
/scent-vectors/generate` generates only from an approved catalogue ID. `POST
/scent-vectors/{id}/approve` and `/reject` apply human review decisions; rejection requires a
reason. `POST /scent-vectors/similarity` compares an input vector with requested candidates (or all
candidates) and returns descending cosine similarity. Unknown IDs return 404; failed safety gates
return 422.


## Recommendations

`GET /recommendations` and `GET /recommendations/{id}` expose only allowlisted public fields.
`POST /recommendations/generate` creates duplicate-safe recommendations for an approved catalogue
source. `POST /recommendations/similar-fragrances` returns vector-ranked results, and `POST
/recommendations/contextual` filters approved candidates by mood, occasion, season, family, and
intensity where those fields exist. `POST /recommendations/{id}/approve` enforces confidence and
privacy/IP gates. `POST /recommendations/{id}/reject` requires and retains a rejection reason.
