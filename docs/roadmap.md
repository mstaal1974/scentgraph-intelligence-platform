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

## Maison product SKU catalogue

The public-safe product, variant, and bundle projection is available as a foundation for later Shopify, WooCommerce, custom storefront, and retailer-licensing adapters. Those external write integrations and storefront UI remain future work.

## Bulk profile coverage milestone

The bulk drafting, coverage, and offline enrichment-queue workflow now supplies human review at scale. Catalogue promotion, vectors, recommendations, product creation, and Maison publication remain later, separately gated actions after approved provenance-backed enrichment.

## Seller-demand intelligence
The internal demand-brief matcher and anonymised supplier-opportunity summary are the first two-sided intelligence layer. A public marketplace, portals, automated approval, and catalogue/SKU creation remain future work subject to tenancy, consent, privacy thresholds, and commercial governance.

## Consumer scent intelligence
The private Scentprint, structured feedback, thresholded community aggregation, and scent wardrobe foundation is available. Durable accounts, consent lifecycle, public reviews/community, scent-twin discovery, social proof, frontend quizzes, campaigns, and MicroPromote integration remain separately scoped future work.

## Launch intelligence readiness layer

The backend-only, explainable launch prioritisation layer now connects existing profile, sourcing, catalogue, seller-demand, and consumer-intelligence signals through safe bands and human-review gates. Storefront, dashboard, Maison Obsidian, Shopify, and MicroPromote integrations remain future, separately scoped work.

## Private pilot orchestration

This module may supply non-mutating readiness evidence to the [private pilot workflow](private-pilot-workflow.md). The pilot layer records only safe statuses, counts, bands, blockers, and human-review actions; it does not bypass this module's existing review gates or expose private source values.

## Production persistence and audit trail

The focused operational persistence boundary is now available for progressive pilot integration: durable run/review state, provenance, public-safe projections, and privacy-bounded audit events. Workflow replacement, storefront work, campaign generation, and automatic approval remain out of scope.

## Human review workflow

Human review gates now provide private, audit-oriented queues and explicit decisions. Approval is
only permission for a next internal stage; it never publishes records, creates catalogue products
or SKUs, starts launch execution, or generates campaigns. Default API projections contain only
safe identifiers, bands, statuses, role labels, summaries, and aggregate readiness counts. See
[Human review gates workflow](human-review-gates-workflow.md).

## Private supplier pilot execution pack

The focused execution layer is documented in [Private supplier pilot execution](private-supplier-pilot-execution.md). It adds path-safe intake, explicit preflight plans, private run boundaries, aggregate acceptance evidence, privacy auditing, and mandatory human review without changing the underlying intelligence workflow or permitting publication.
