# Bulk fragrance profile generation

This workflow turns **private supplier identity inputs** into review-ready fragrance profile drafts. It is deliberately not a SKU builder, storefront publisher, catalogue publisher, or source of fragrance claims.

## Identity grouping and drafting

1. Read staged offers only from `data/private/staging/supplier_offers/`.
2. Normalise brand, fragrance name, and the optional ORI/reference.
3. Collapse duplicate rows and multiple supplier offers into a single likely fragrance identity. A profile represents a fragrance, not an offer.
4. Attach private offer and match-candidate identifiers to the operational draft. Default API summaries omit those links.
5. Reuse the profile builder's deterministic, original placeholder description and set `needs_human_review`.

Fatma-format offers do not contain ORI. They can still form candidates from normalised brand/name, but receive reduced confidence and an explicit missing-reference reason. No record is auto-approved, promoted, or used to create a catalogue record.

## Evidence limits

Supplier availability supports identity discovery, not notes or creative claims. Notes, accords, moods, seasons, occasions, projection, and longevity stay missing and require enrichment unless approved evidence supports them. The workflow never copies descriptions, reviews, ratings, images, comments, or UGC. Researchers must use first-party, licensed, authorised, or otherwise commercially permitted sources, record provenance, and write original text.

## Coverage and research queue

Coverage reports track each supplier-derived identity from `no_profile_started`, through drafting and enrichment, to separately controlled catalogue, vector, and recommendation stages. Blocking states identify low confidence, private-data risk, and missing provenance. The offline research queue prioritises identities found in multiple offers and Maison-product candidates, then provides safe questions rather than scraped content.

Human reviewers use the existing admin review process after enrichment. Only subsequent, separately authorised workflows may promote an approved identity to the catalogue, create scent vectors, build recommendations or products, and expose approved material to Maison Obsidian.

## Safe operation

```bash
python scripts/build_bulk_profile_drafts.py
python scripts/build_profile_coverage_report.py --offers data/private/staging/supplier_offers/offers.json
python scripts/prepare_enrichment_research_queue.py --coverage data/private/reports/profile_coverage.json
```

Operational outputs remain under `data/private/staging/profile_drafts/` and `data/private/reports/`. Never commit supplier files, staging/report outputs, supplier identities where sensitive, codes, CN codes, prices, currencies, stock, quantities, costs, margins, commercial terms, or copied third-party content. The files in `data/samples/` are fictional contract examples only.

## Seller-demand integration
Profile coverage can inform internal launch readiness. The [matching layer](seller-demand-supplier-match.md) only uses supported profile evidence and does not infer missing notes, accords, moods, seasons, or claims.

## Launch intelligence integration

The launch-readiness layer consumes this layer's reviewed, aggregated status or band as read-only decision support. It never changes source records, approves catalogue entries, creates SKUs, or publishes private source detail. See [Launch intelligence and commercial readiness](launch-intelligence-readiness.md).

## Private pilot orchestration

This module may supply non-mutating readiness evidence to the [private pilot workflow](private-pilot-workflow.md). The pilot layer records only safe statuses, counts, bands, blockers, and human-review actions; it does not bypass this module's existing review gates or expose private source values.
