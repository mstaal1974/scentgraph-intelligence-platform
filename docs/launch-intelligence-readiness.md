# Launch intelligence and commercial readiness

The launch intelligence layer is a backend decision and reporting layer. It combines reviewed profile coverage and enrichment state with catalogue and product readiness, product-format and bundle readiness, supplier availability and source-confidence bands, protected margin-suitability bands, aggregated seller demand, aggregated consumer interest, scent-vector state, and recommendation readiness. It reads these signals; it does not mutate their source records.

## Explainable scoring

The deterministic score weights ten readiness dimensions and subtracts explicit privacy, provenance, and missing-data penalties. Every dimension emits a plain-language contribution. Unknown data scores as unavailable rather than being guessed. Scores are bounded from 0–100 and grouped as `low`, `moderate`, `strong`, or `priority`. Commercial inputs are represented only by bands. Seller and consumer signals must already be aggregated and must not use protected characteristics.

A score is decision support, never approval. Every candidate is created with `needs_human_review`. Statuses distinguish candidates that may be reviewed now from those awaiting profile enrichment, supplier review, catalogue approval, product setup, or a confidence/privacy/provenance hold. `bundle_candidate` and `sample_only_candidate` are planning suggestions, not product creation.

## Gaps and plans

Gap analysis maps missing requirements to severity, an explanation, a practical fix, and an accountable human role. Recommendation planning groups safe candidate IDs into top-launch, sample-first, bundle, car-diffuser, body-care, enrichment, supplier-review, catalogue, product, and recommendation setup plans. Plans neither create SKUs nor launch campaigns, and demand language is used only when supported by aggregated signals.

## Privacy boundary

Public responses are generated with an allow-list. They contain bands, statuses, reasons, and actions—not supplier commercial details, seller-private brief notes, or individual consumer records. Detailed operational files belong only under ignored `data/private/`; tracked samples are fictional. Run `python scripts/audit_launch_intelligence_privacy.py` before publishing changes.

## Safe workflow

1. Place authorised aggregate input at `data/private/launch_candidates.json`.
2. Run `python scripts/build_launch_priority_report.py`.
3. Run `python scripts/build_launch_gap_report.py`.
4. Run `python scripts/export_launch_readiness_summary.py` for an allow-listed projection.
5. Run the privacy audit and submit all recommendations for human review.

The private API is mounted below the configured internal prefix. Build endpoints require the private API key; default reads return safe summaries. This work is not a storefront, dashboard, supplier portal, or social feature. It does not integrate MicroPromote. In later, separately reviewed work, these summaries can feed dashboards, Shopify exports, Maison Obsidian, retailer portals, and MicroPromote campaign packs without coupling those systems now.

## Private pilot orchestration

This module may supply non-mutating readiness evidence to the [private pilot workflow](private-pilot-workflow.md). The pilot layer records only safe statuses, counts, bands, blockers, and human-review actions; it does not bypass this module's existing review gates or expose private source values.

## Human review workflow

Human review gates now provide private, audit-oriented queues and explicit decisions. Approval is
only permission for a next internal stage; it never publishes records, creates catalogue products
or SKUs, starts launch execution, or generates campaigns. Default API projections contain only
safe identifiers, bands, statuses, role labels, summaries, and aggregate readiness counts. See
[Human review gates workflow](human-review-gates-workflow.md).
