# Roadmap

1. **Foundation:** supplier-first ingestion, layered schema, matching, review workflow, licensing guardrails, typed API, and tests.
   The review-only fragrance profile draft builder and guarded catalogue promotion are available;
   Maison Obsidian can now consume approved catalogue profiles through a focused public-safe API.
2. **Data operations:** Alembic revisions, persistent repositories, curator queues, taxonomy governance, and dataset versioning.
3. **Intelligence:** calibrate the available vectors and recommendation engine, then add reviewed clone estimates, Scentprint feedback, and layering research.
4. **Commercial API:** tenant identity, scoped keys, quotas, metering, audit logs, data tiers, and SLAs.
5. **Channels:** retailer enrichment tools and optional white-label/Shopify/WooCommerce consumers.
6. **Operations:** security review, privacy controls, observability, backups, and regional production deployment.

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
