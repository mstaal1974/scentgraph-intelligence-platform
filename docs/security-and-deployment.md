# Security and deployment

## Architecture and trust boundaries

AromaTwin runs as a FastAPI container backed by PostgreSQL. Put it behind a TLS-terminating reverse
proxy or managed load balancer. `/maison` is the retailer-safe public projection; `/admin` and
`/supplier-items` are internal surfaces. Set `AROMATWIN_INTERNAL_API_PREFIX=/internal` to make that
boundary explicit. Network policy should additionally prevent public access to the internal prefix
and PostgreSQL. The API-key controls are defence in depth, not a replacement for TLS or network
isolation.

Maison responses remain schema-allowlisted, approved-catalogue projections. They do not return raw
supplier rows, review records, supplier prices/codes, inventory, commercial terms, or copied
third-party content.

## Configuration

| Variable | Purpose |
| --- | --- |
| `AROMATWIN_ENVIRONMENT` | `development` by default; use `production` in production. |
| `AROMATWIN_DATABASE_URL` | SQLAlchemy PostgreSQL connection URL. |
| `AROMATWIN_API_KEY` | Optional key validation for public requests that present a key. |
| `AROMATWIN_ADMIN_API_KEY` | Required at startup in production when admin routes are enabled. |
| `AROMATWIN_PRIVATE_API_KEY` | Required at startup in production when supplier routes are enabled. |
| `AROMATWIN_ALLOWED_ORIGINS` | Comma-separated exact browser origins; `*` is rejected in production. |
| `AROMATWIN_ENABLE_ADMIN_CONSOLE` | Includes or removes the admin API and static console. |
| `AROMATWIN_ENABLE_PRIVATE_SUPPLIER_ENDPOINTS` | Includes or removes supplier workflow routes. |
| `AROMATWIN_LOG_LEVEL` | Standard Python log level, normally `INFO`. |
| `AROMATWIN_PUBLIC_API_PREFIX` | Optional prefix for Maison routes, such as `/api/v1`. |
| `AROMATWIN_INTERNAL_API_PREFIX` | Optional prefix for admin and supplier routes. |

Development permits keyless internal access and known localhost CORS origins. Production validates
configuration during application import and fails before serving if an enabled internal surface has
no key or if wildcard CORS is configured. Send keys as `X-Admin-API-Key` or
`X-Private-API-Key`; `X-API-Key` is a compatibility fallback. Rotate keys through the hosting
platform's secret manager rather than files or image layers.

## HTTP and logging controls

Every response receives a caller-supplied or generated `X-Request-ID`, plus
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: no-referrer`.
Access summaries contain method, path, status, request ID, elapsed milliseconds, and redacted query
parameters. Bodies and authentication headers are never logged. Treat logs as sensitive anyway;
restrict access and configure retention.

## Containers and deployment

For local development, copy `.env.example` to `.env` and run `docker compose up --build`. Compose
uses placeholder credentials and intentionally mounts no private supplier directory. It is not a
production manifest.

Build production images with `docker build -t aromatwin:VERSION .`. The non-root runtime image
contains application code, static console assets, and repository public CSV fixtures only. The
Docker ignore rules exclude `.env`, private/import directories, supplier spreadsheets/PDFs, caches,
tests, and repository history. Deploy an immutable tag; inject configuration at runtime; expose only
the proxy; run database migrations as a controlled release job; and verify `/health` and
`/openapi.json` after release.

For Maison Obsidian, configure only its exact storefront origin, expose the prefixed public routes,
and keep the internal prefix on a private ingress. Do not copy this repository into a storefront and
do not hardcode a production domain here.

## CI, secrets, and production-readiness

GitHub Actions lint, compile, test, data-validation, and privacy-audit checks are release gates; CI
does not deploy or store runtime datasets. Never commit `.env`, database passwords, API keys, raw
supplier files, prices, codes, inventory, commercial terms, database dumps, or production logs.
Enable secret scanning and protected environments in the repository host.

Before production:

1. Use randomly generated, distinct admin and supplier keys from a secret manager.
2. Set `production`, exact CORS origins, explicit API prefixes, and only required feature flags.
3. Terminate TLS, restrict internal ingress and database networking, and set container resource limits.
4. Run CI and a staging smoke test, then exercise key rejection and public-response privacy checks.
5. Establish encrypted automated database backups and regularly test restoration.
6. Collect availability, latency, error-rate, database, and security-event metrics with alerting.

API keys are an interim deployment control. Later, replace them with an identity provider,
short-lived tokens, tenant-scoped RBAC, auditable service identities, rate limiting, and durable
authorization logs. Add managed hosting, multi-zone PostgreSQL, backup retention, monitoring and
incident response as separate operational work; none should weaken the public/private data boundary.
