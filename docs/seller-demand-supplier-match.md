# Seller demand to supplier matching

This internal intelligence layer is the first two-sided commercial workflow in AromaTwin. It connects a structured retail launch requirement to existing supplier, sourcing, profile, catalogue, scent-vector, and product-format evidence. It does **not** publish listings, create catalogue records or SKUs, approve a supplier, or constitute a public marketplace.

## Two directions

### Seller → supplier

A private demand brief captures the seller segment, target customer, desired families, notes, accords, moods, occasions, seasons, performance preferences, inspired-by hints, formats, bands, positioning, urgency, exclusions, and private notes. Inspired-by values are discovery hints only: they are neither verified equivalence nor legal or marketing claims. Every brief begins in `needs_human_review`; its text is never auto-published.

The matcher scores scent profile, note/accord, mood/occasion/season, format, availability, profile completeness, catalogue readiness, commercial suitability **band**, source confidence, and launch readiness. Explanations, missing requirements, and risk flags accompany the score. Missing reference/ORI evidence reduces confidence. A match is a review candidate—not a product.

### Supplier → seller

The reverse report groups matches by a stable anonymised supplier label. It reports counts, strong themes, readiness and profile gaps, and a safe recommended action. It never reveals seller identity, private notes, or exact brief detail. Small cohorts should remain internal until a future minimum aggregation policy is defined.

## Privacy boundaries

Seller identity and private notes remain seller-private. Supplier identity, offer identifiers, codes, references, prices, costs, currency values, inventory and commercial terms remain supplier-private. Default API projections use allowlists: suppliers receive anonymised aggregate demand, while seller match responses receive only an anonymised supplier label and suitability band. Detailed operational JSON belongs under ignored `data/private/reports/`; tracked samples are fictional and contain only safe summary fields.

Protecting both sides is commercially necessary: prices and terms can expose negotiation positions, while raw briefs can disclose a retailer's launch strategy. Access is key-protected, human-reviewed, and no output is automatically promoted or published.

## Launch readiness

Launch readiness combines profile completeness, catalogue readiness, source confidence, and format evidence. It is an evidence score, not an approval. Gaps produce an enrichment action; even a high score retains `needs_human_review`.

## Wider workflow and future

Maison Obsidian can use these internal rankings to prioritise sourcing research without changing its website or public API. Later, after permissions, tenancy, consent, aggregation thresholds, and commercial governance exist, this layer could support a supplier portal, retailer portal, curated marketplace, or licensed intelligence product. Those surfaces are explicitly out of scope here.

```bash
python scripts/build_seller_demand_matches.py --briefs data/private/briefs.json --offers data/private/offers.json
python scripts/build_supplier_opportunity_report.py --matches data/private/reports/seller-demand-matches.json
python scripts/audit_seller_supplier_matching.py
```

## Launch intelligence integration

The launch-readiness layer consumes this layer's reviewed, aggregated status or band as read-only decision support. It never changes source records, approves catalogue entries, creates SKUs, or publishes private source detail. See [Launch intelligence and commercial readiness](launch-intelligence-readiness.md).
