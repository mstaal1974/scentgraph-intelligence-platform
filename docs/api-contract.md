# API Contract

The foundation exposes JSON and OpenAPI at `/docs` and `/openapi.json`.

- Operations: `GET /health`
- Supplier: `GET /supplier-items`, `GET /supplier-items/{id}`, `POST /supplier-items/import-preview`
- Matching: `GET /match-candidates`, `GET /match-candidates/{id}`, `POST /match-candidates/generate`
- Enrichment: `GET /enrichment-reviews`, `GET /enrichment-reviews/{id}`, `POST /enrichment-reviews/{id}/approve`, `POST /enrichment-reviews/{id}/reject`
- Catalogue: `GET /brands`, `GET /fragrances`, `GET /fragrances/{id}`, `GET /notes`, `GET /accords`, `GET /search?q=`
- Intelligence: `GET /similar/{fragrance_id}`, `POST /recommend`, `POST /scentprint`, `GET /clone-matches/{fragrance_id}`

Foundation workflow endpoints may use in-memory previews until repositories are wired, but all requests and responses remain typed. Approved catalogue routes must never expose unapproved enrichment or restricted source content.
