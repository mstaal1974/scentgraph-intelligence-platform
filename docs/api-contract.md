# API Contract

The foundation exposes JSON and OpenAPI at `/docs` and `/openapi.json` from `aromatwin.main:app`.

- Operations: `GET /health`
- Supplier: `GET /supplier-items`, `GET /supplier-items/{id}`, `POST /supplier-items/import-preview`
- Matching: `GET /match-candidates`, `GET /match-candidates/{id}`, `POST /match-candidates/generate`
- Profile drafts: `GET /profile-drafts`, `GET /profile-drafts/{id}`, `POST /profile-drafts/generate`, `POST /profile-drafts/{id}/approve`, `POST /profile-drafts/{id}/reject`
- Enrichment sources: `GET /enrichment-sources`, `POST /enrichment-sources`
- Enrichment review: `GET /enrichment-reviews`, `GET /enrichment-reviews/{id}`, `POST /enrichment-reviews/generate`, `POST /enrichment-reviews/{id}/attach-source`, `POST /enrichment-reviews/{id}/mark-ready`, `POST /enrichment-reviews/{id}/approve`, `POST /enrichment-reviews/{id}/reject`
- Catalogue: `GET /brands`, `GET /fragrances`, `GET /fragrances/{id}`, `GET /notes`, `GET /accords`, `GET /search?q=`
- Intelligence: `GET /similar/{fragrance_id}`, `POST /recommend`, `POST /scentprint`, `GET /clone-matches/{fragrance_id}`

Profile generation persists `needs_human_review` records only and is idempotent for active supplier/candidate pairs. Approval uses server-side provenance, minimum draft confidence, and restricted-content safeguards; rejection records its reason. Neither decision promotes a catalogue record.
