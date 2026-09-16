# API Contract

The foundation exposes JSON and OpenAPI at `/docs` and `/openapi.json`.

Deployment may prepend `AROMATWIN_PUBLIC_API_PREFIX` to Maison routes and
`AROMATWIN_INTERNAL_API_PREFIX` to internal routes. Outside local development, all `/admin`
operations require the configured admin key and all `/supplier-items` operations require the
private supplier key. Public Maison operations remain unauthenticated, with optional public-key
validation, and continue to return only approved allowlisted data. See
[Security and deployment](security-and-deployment.md).

- Operations: `GET /health`
- Supplier: `GET /supplier-items`, `GET /supplier-items/{id}`, `POST /supplier-items/import-preview`
- Private supplier offers: `GET /supplier-offers/health`, `POST /supplier-offers/import`, `POST
  /supplier-offers/match`, `GET /supplier-offers`, `GET /supplier-offers/{id}`, `GET
  /supplier-offers/catalogue/{fragrance_id}`, `POST /supplier-offers/compare`, and `GET
  /supplier-offers/audit`
- Matching: `GET /match-candidates`, `GET /match-candidates/{id}`, `POST /match-candidates/generate`
- Enrichment: `GET /enrichment-reviews`, `GET /enrichment-reviews/{id}`, `POST /enrichment-reviews/{id}/approve`, `POST /enrichment-reviews/{id}/reject`
- Profile drafts: `GET /profile-drafts`, `GET /profile-drafts/{id}`, `POST /profile-drafts/generate`, `POST /profile-drafts/{id}/approve`, `POST /profile-drafts/{id}/reject`
- Catalogue promotion: `GET /catalogue/brands`, `GET /catalogue/brands/{id}`, `GET /catalogue/fragrances`, `GET /catalogue/fragrances/{id}`, `POST /catalogue/promote`
- Legacy catalogue discovery: `GET /brands`, `GET /fragrances`, `GET /fragrances/{id}`, `GET /notes`, `GET /accords`, `GET /search?q=`
- Intelligence: recommendation routes below, `GET /similar/{fragrance_id}`, `POST /scentprint`, and `GET /clone-matches/{fragrance_id}`

Foundation workflow endpoints may use in-memory previews until repositories are wired, but all requests and responses remain typed. Approved catalogue routes must never expose unapproved enrichment or restricted source content.

Supplier-offer operations are tagged internal/private, require the private API key outside local
environments, and return allowlisted summaries by default. Import returns counts and warnings;
comparison returns grouping counts. Neither response publishes private commercial attributes.

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

## Maison Obsidian public integration

The retailer-safe integration exposes `GET /maison/health`, `GET /maison/fragrances`, `GET /maison/fragrances/{fragrance_id}`, `GET /maison/fragrances/slug/{slug}`, `GET /maison/fragrances/{fragrance_id}/similar`, `GET /maison/fragrances/{fragrance_id}/recommendations`, `POST /maison/scentprint/match`, `GET /maison/export/catalogue`, and `GET /maison/export/recommendations`.

All responses are typed allowlisted projections. Catalogue records must be approved; vector and recommendation review status remains visible; unsafe/unapproved intelligence and workflow-layer records are omitted. See [Maison Obsidian API integration](maison-obsidian-api-integration.md).
# Admin review API

The internal `/admin` surface aggregates allowlisted workflow metadata only. `GET
/admin/review/summary`, `/admin/review/queue`, `/admin/review/queue/{stage}`,
`/admin/review/blocked`, and `/admin/review/readiness` support monitoring. Decision endpoints
are `POST /admin/review/{stage}/{record_id}/approve`, `/reject`, and
`/request-more-sources`; they require a reviewer, rejection requires a reason, and approvals
delegate to existing stage guardrails. `GET /admin/export/review-queue` returns the same safe
fields as CSV. See [Admin review console](admin-review-console.md).

These routes are omitted when the admin console feature flag is disabled. In production they reject
requests without `X-Admin-API-Key`; supplier workflow routes similarly require
`X-Private-API-Key`. Both also accept `X-API-Key` as a compatibility header. Authentication does not
bypass any review, approval, provenance, or privacy guardrail.

## Private supplier sourcing

The `/supplier-sourcing` routes are internal, private-key protected routes. They build and compare sourcing decisions, return safe decision summaries, calculate margin scenarios, and expose audit counts. Response models intentionally omit all raw supplier prices and codes, stock/quantity, currencies, costs, margins, and commercial terms. Margin inputs are accepted only at this private boundary; margin responses remain safe summaries by default.

## Product catalogue

Public reads are available at `/products`, `/products/{product_id}`, `/products/slug/{product_slug}`, `/products/{product_id}/variants`, `/products/bundles`, and the three `/products/export/*` routes. POST build routes require the admin workflow dependency and return review metadata but no commercial inputs. See [Maison product SKU catalogue](maison-product-sku-catalogue.md).

## Internal bulk profile API

When private supplier endpoints are enabled, `/internal/bulk-profiles` provides health, generation, draft summaries, coverage/summary, research-queue build/list, and audit routes. All routes require the private API key. Responses use public-safe schemas: generation and reads do not return supplier offer IDs, references, prices, codes, stock, quantities, costs, margins, or commercial terms. Build actions create review-only operational data and never catalogue records.

## Internal seller-demand workflow
With private endpoints enabled, `/seller-demand` provides health; brief create/list/read; match build/list/read; supplier-opportunity build/read; and audit routes. All require the private API key. Default brief responses omit seller identity and private notes. Match responses omit private offer identifiers and commercial inputs. Opportunities are aggregated and anonymised.

## Internal consumer scent intelligence
`/consumer-scent` provides health; Scentprint create/list/read and structured matching; feedback create/list; community-intelligence list/build; wardrobe add/list/gaps; and audit routes. All routes require the private API key. Default responses omit consumer IDs and private notes where a public-safe projection is appropriate. Wardrobes remain private workflow responses. No response contract has supplier-commercial fields.
