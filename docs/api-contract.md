# API Contract

The initial contract is JSON over HTTP and is documented through OpenAPI at `/docs` and `/openapi.json`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service status |
| GET | `/brands` | List brands |
| GET | `/brands/{brand_id}` | Fetch a brand |
| GET | `/fragrances` | List fragrances |
| GET | `/fragrances/{fragrance_id}` | Fetch a fragrance |
| GET | `/notes` | List note taxonomy |
| GET | `/accords` | List accord taxonomy |
| GET | `/search?q=` | Search canonical entities |
| GET | `/similar/{fragrance_id}` | Similarity candidates |
| POST | `/recommend` | Contextual recommendation request |
| POST | `/scentprint` | Build and match a preference vector |
| GET | `/clone-matches/{fragrance_id}` | Directional clone alternatives |

Foundation responses may be empty or illustrative but remain typed. Future commercial access adds versioning, API keys, tenant scopes, quotas, metering, and licensed response fields without leaking database access.
