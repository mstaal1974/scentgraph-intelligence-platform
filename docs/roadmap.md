# Roadmap

1. **Foundation:** supplier-first ingestion, layered schema, matching, review workflow, licensing guardrails, typed API, and tests.
   The review-only fragrance profile draft builder and guarded catalogue promotion are available;
   Maison Obsidian can now consume approved catalogue profiles through a focused public-safe API.
2. **Data operations:** Alembic revisions, persistent repositories, curator queues, taxonomy governance, and dataset versioning.
3. **Intelligence:** calibrate the available vectors and recommendation engine, then add reviewed clone estimates, Scentprint feedback, and layering research.
4. **Commercial API:** tenant identity, scoped keys, quotas, metering, audit logs, data tiers, and SLAs.
5. **Channels:** retailer enrichment tools and optional white-label/Shopify/WooCommerce consumers.
6. **Operations:** security review, privacy controls, observability, backups, and regional production deployment.

## Deployment hardening boundary

Environment validation, internal API keys, configurable CORS and route prefixes, request IDs,
access summaries, baseline response headers, a non-root container, and deployment guidance are now
available. This is a focused deployment baseline, not complete production identity or operations.
Tenant RBAC, short-lived identity, rate limiting, durable security audit logs, managed hosting,
backup/restore automation, and monitoring remain future work.

## Test and CI reliability

The repository now has a Python 3.12 GitHub Actions gate for linting, compilation, the complete
offline test suite, public data validation, and supplier privacy auditing. Development and test
environment guidance is maintained in [development-and-testing.md](development-and-testing.md).

## Current enrichment-review boundary

The independent enrichment review queue now generates original, provenance-linked review records
and enforces human readiness, licensing, confidence, and copied-content checks. Only reviews marked
`approved_for_catalogue` cross the promotion boundary. Maison Obsidian consumption remains future.
## Scent vector and recommendation engines

The deterministic public-catalogue scent vector and explainable recommendation layers are now
available. Maison discovery, Scentprint matching, and reviewed clone-relationship projection are
now available through the retailer-safe integration; calibration and storefront wiring remain later
stages.
# Admin review console

- **Delivered:** public-safe cross-stage queue, stage/status summaries, blocker and readiness
  monitoring, guarded human decisions, CSV export, and a dependency-free internal interface.
- **Future operational work:** production authentication/authorization, a durable decision
  audit store, and deployment-specific observability. These are intentionally outside the
  lightweight console layer.
# Multi-supplier availability

The focused multi-supplier offer ingestion, private comparison, safe matching, and audit boundary
are now implemented. Future persistence/API repository wiring may replace the current typed preview
store without changing the catalogue approval workflow or public contract.

## Supplier sourcing and margin intelligence

The focused private sourcing layer now supports multi-offer ranking, audit flags, product-format costing, and safe-by-default API summaries. Future work may add persistent tenant isolation and approval history for multi-retailer licensing; it must preserve the commercial-data boundary.
