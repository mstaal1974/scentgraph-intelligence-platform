# Layered Data Model

`import_batches` and `supplier_items` preserve supplier availability and raw fields. `match_candidates` stores possible identities without publishing them. `enrichment_reviews` captures permitted evidence, original/AI description state, proposed characteristics, reviewer decisions, and confidence. Only approved reviews may feed canonical `brands` and `fragrances`.

`reference_sources` describes source capabilities, while `source_provenance` records evidence attached to any entity. `review_statuses` defines controlled workflow states. Notes, accords, vectors, clone relationships, and product mappings form the proprietary intelligence layer.

`profile_drafts` links one supplier item and match candidate to an original placeholder profile,
provenance note, bounded confidence, and review decision. Drafts begin as `needs_human_review` and
contain no supplier commercial fields or third-party descriptive/media fields; draft approval does
not create a catalogue record. The separate promoter creates an allowlisted public record only from
an `approved_for_catalogue` enrichment review with sufficient provenance.

Foreign keys, bounded scores, immutable raw values, status checks, and guarded promotion prevent reference data from becoming commercial catalogue content by accident.

## Scent vectors

Each scent vector belongs to one approved public catalogue fragrance and stores 23 bounded
dimensions, confidence, generation method, review status, provenance references, and a fingerprint
of its allowlisted source fields. The fingerprint provides idempotency and change detection. This
derived public-safe layer cannot point directly to supplier items, profile drafts, or enrichment
reviews. See [Scent Vector Engine](scent-vector-engine.md).

## Recommendations

Recommendations link one approved public catalogue fragrance to another and store a controlled
type, bounded deterministic score, original reason, shared-dimension JSON, difference summary,
bounded confidence, generation method, review state, timestamps, and optional rejection reason.
The source/candidate/type identity is duplicate-safe. Recommendations derive only from catalogue
records and approved or review-safe vectors; they never link directly to supplier or review layers.
See [Recommendation Engine](recommendation-engine.md).

## Independent enrichment review records

The review-only API representation links `profile_draft_id` to original description text,
`source_ids`, a provenance summary, bounded source confidence, licensing risk, copied-content flag,
review status, reviewer, and rejection reason. Enrichment sources record identity/reference, URL,
licence status, commercial-use permission, confidence, risk, and reference-only state. These are
workflow records, not canonical catalogue entities, and contain no supplier commercial fields.

## Promoted catalogue records

The public catalogue projection contains public IDs, brand/name and deterministic slugs,
concentration, original description, confidence, provenance summary/reference IDs, and its source
enrichment-review ID. It deliberately contains no supplier-commercial values.

## Maison consumer projection

Maison card, detail, recommendation, similarity, Scentprint, and export schemas are derived views, not new canonical entities. Their IDs link only to approved catalogue fragrances. Safe vectors, recommendations, and reviewed clone relationships may enrich the view, while supplier, candidate, draft, and review entities cannot be represented directly. The projection is an explicit allowlist and stores no storefront or supplier-commercial state.
# Admin review projection

`AdminReviewQueueItem` is a read projection, not a new foundation entity. It identifies a
source record by stage and ID, then exposes only title, review state, confidence, licensing and
restricted-content flags, provenance summary, blocker, reviewer, update time, and next action.
It cannot contain supplier commercial fields or copied third-party content. Summary, blocked,
readiness, decision, and export schemas derive from that allowlisted projection; the existing
stage records remain authoritative.
# Supplier offers

`supplier_offers` stores private, provenance-bearing commercial availability independently from
`supplier_items` and public fragrances. Optional foreign keys link an offer to an existing match
candidate or catalogue fragrance. The record retains raw and normalised identity, file provenance,
private commercial attributes, confidence, and review state. It never owns or creates a public
fragrance profile. See [Multi-supplier offer import](multi-supplier-offer-import.md).

## Private sourcing projections

Supplier sourcing decisions and product-format margin scenarios are computed projections rather than public catalogue entities. Decisions link to an existing catalogue fragrance or match candidate, retain risk and review state, and keep supplier/commercial fields in private reports. They intentionally require no public catalogue schema or foundation migration.

## Maison product projection

`ProductCatalogue` references one approved catalogue fragrance. `ProductVariant` references a product and carries a deterministic SKU, format, size, and optional public retail price. `ProductBundle` references product and variant IDs. These public projections are deliberately separate from supplier offers and internal margin scenarios; see [Maison product SKU catalogue](maison-product-sku-catalogue.md).

## Operational bulk profile records

Bulk profile drafts, coverage rows, and research queue items are file-backed operational projections in this phase, not new catalogue entities. Private drafts retain source offer/match identifiers; public-safe summaries omit those links and all commercial supplier attributes. Coverage records describe workflow state, while research tasks contain missing-field questions and no copied source content.

## Seller demand intelligence (service-layer records)
`SellerDemandBrief` is private launch intent. `SellerSupplierMatch` links a brief to an existing offer/candidate without creating a catalogue record or SKU. `SupplierOpportunity` is a derived anonymised aggregation. These are transient/service and private-report records, so no foundation migration is required.

## Consumer scent intelligence (service-layer records)
`ConsumerScentprint` stores only structured scent preferences under a pseudonymous alias. `ConsumerFeedback` retains private notes internally and exposes an explicit safe projection. `CommunityScentIntelligence` is thresholded aggregate evidence that supplements rather than overwrites approved profiles. `ScentWardrobeItem` is private by default. These transient records do not add a customer identity model or require a foundation migration.

## Launch intelligence records

`LaunchIntelligenceRead` is a derived, non-persistent decision record keyed by a deterministic launch candidate ID. It references optional fragrance and product IDs, readiness/status bands, an explainable score, blockers, requirements, formats, and human review state. `LaunchGapRead` assigns each derived gap to an owner role. `LaunchRecommendationPlanRead` groups candidate IDs into non-executing planning themes. Raw commercial and personal source fields are outside these contracts.

## Private pilot orchestration

This module may supply non-mutating readiness evidence to the [private pilot workflow](private-pilot-workflow.md). The pilot layer records only safe statuses, counts, bands, blockers, and human-review actions; it does not bypass this module's existing review gates or expose private source values.

## Operational persistence

Ten `persistent_*` tables hold workflow runs, stages, safe artifact metadata, draft/review/launch summaries, redacted demand and scentprint summaries, provenance, and audit events. They intentionally exclude raw private and commercial data. See [Production persistence and audit trail](production-persistence-audit.md).

## Human review workflow

Human review gates now provide private, audit-oriented queues and explicit decisions. Approval is
only permission for a next internal stage; it never publishes records, creates catalogue products
or SKUs, starts launch execution, or generates campaigns. Default API projections contain only
safe identifiers, bands, statuses, role labels, summaries, and aggregate readiness counts. See
[Human review gates workflow](human-review-gates-workflow.md).
