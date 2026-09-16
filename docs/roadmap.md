# Roadmap

1. **Foundation:** supplier-first ingestion, layered schema, matching, review workflow, licensing guardrails, typed API, and tests.
   The review-only fragrance profile draft builder and guarded catalogue promotion are available;
   Maison Obsidian consumption of approved catalogue profiles remains future work.
2. **Data operations:** Alembic revisions, persistent repositories, curator queues, taxonomy governance, and dataset versioning.
3. **Intelligence:** calibrated vectors, reviewed clone estimates, contextual recommendations, Scentprint feedback, and layering research.
4. **Commercial API:** tenant identity, scoped keys, quotas, metering, audit logs, data tiers, and SLAs.
5. **Channels:** retailer enrichment tools and optional white-label/Shopify/WooCommerce consumers.
6. **Operations:** security review, privacy controls, observability, backups, and regional production deployment.

## Current enrichment-review boundary

The independent enrichment review queue now generates original, provenance-linked review records
and enforces human readiness, licensing, confidence, and copied-content checks. Only reviews marked
`approved_for_catalogue` cross the promotion boundary. Maison Obsidian consumption remains future.
