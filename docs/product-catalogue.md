# Product catalogue consumer signal

The product catalogue remains authoritative for approved products and variants. Consumer scent intelligence may reference those identifiers to produce private wardrobe entries and thresholded, review-gated product aggregates. It does not create SKUs, change catalogue promotion, expose commercial supplier data, or overwrite approved product/profile facts. See [Consumer scent intelligence](consumer-scent-intelligence.md).

## Launch intelligence integration

The launch-readiness layer consumes this layer's reviewed, aggregated status or band as read-only decision support. It never changes source records, approves catalogue entries, creates SKUs, or publishes private source detail. See [Launch intelligence and commercial readiness](launch-intelligence-readiness.md).

## Maison integration readiness boundary

The Maison readiness pack consumes only approved, public-safe summaries through allow-listed contracts.
It does not change existing generation, pilot, review, persistence, or staging workflows and never
performs an external sync. See [Maison integration readiness](maison-integration-readiness.md).
