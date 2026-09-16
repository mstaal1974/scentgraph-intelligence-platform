# API Contract

The foundation exposes JSON and OpenAPI at `/docs` and `/openapi.json`.

- Operations: `GET /health`
- Supplier: `GET /supplier-items`, `GET /supplier-items/{id}`, `POST /supplier-items/import-preview`
- Matching: `GET /match-candidates`, `GET /match-candidates/{id}`, `POST /match-candidates/generate`
- Enrichment: `GET /enrichment-reviews`, `GET /enrichment-reviews/{id}`, `POST /enrichment-reviews/{id}/approve`, `POST /enrichment-reviews/{id}/reject`
- Profile drafts: `GET /profile-drafts`, `GET /profile-drafts/{id}`, `POST /profile-drafts/generate`, `POST /profile-drafts/{id}/approve`, `POST /profile-drafts/{id}/reject`
- Catalogue: `GET /brands`, `GET /fragrances`, `GET /fragrances/{id}`, `GET /notes`, `GET /accords`, `GET /search?q=`
- Intelligence: `GET /similar/{fragrance_id}`, `POST /recommend`, `POST /scentprint`, `GET /clone-matches/{fragrance_id}`

Foundation workflow endpoints may use in-memory previews until repositories are wired, but all requests and responses remain typed. Approved catalogue routes must never expose unapproved enrichment or restricted source content.

Profile-draft responses deliberately omit supplier prices, codes, stock, quantities, and commercial
terms. Generate only creates `needs_human_review` records; approve and reject are review decisions,
not catalogue promotion operations.
