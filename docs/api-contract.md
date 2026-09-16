# API Contract

The foundation exposes JSON and OpenAPI at `/docs` and `/openapi.json`.

- Operations: `GET /health`
- Supplier: `GET /supplier-items`, `GET /supplier-items/{id}`, `POST /supplier-items/import-preview`
- Matching: `GET /match-candidates`, `GET /match-candidates/{id}`, `POST /match-candidates/generate`
- Profile drafts: `GET /profile-drafts`, `GET /profile-drafts/{profile_draft_id}`, `POST /profile-drafts/generate`, `POST /profile-drafts/{profile_draft_id}/approve`, `POST /profile-drafts/{profile_draft_id}/reject`
- Enrichment: `GET /enrichment-reviews`, `GET /enrichment-reviews/{id}`, `POST /enrichment-reviews/{id}/approve`, `POST /enrichment-reviews/{id}/reject`
- Catalogue: `GET /brands`, `GET /fragrances`, `GET /fragrances/{id}`, `GET /notes`, `GET /accords`, `GET /search?q=`
- Intelligence: `GET /similar/{fragrance_id}`, `POST /recommend`, `POST /scentprint`, `GET /clone-matches/{fragrance_id}`

Profile generation persists `needs_human_review` records only and is idempotent for active supplier/candidate pairs. Approval uses server-side provenance, minimum source confidence, and restricted-content safeguards; rejection records its reason. Neither decision promotes a catalogue record.
