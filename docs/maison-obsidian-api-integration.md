# Maison Obsidian API integration

Maison Obsidian consumes AromaTwin through the read-only `/maison` API or deterministic CSV exports. AromaTwin remains a separate intelligence platform: curation, provenance, vectors, review decisions, and recommendation generation stay upstream, while a retailer receives only approved projections. This supports later licensing to multiple retailers without coupling intelligence to one storefront.

## Public-safe boundary

The integration starts with approved catalogue fragrances. It never projects supplier items, match candidates, profile drafts, or enrichment reviews. Vectors must have an `approved`, `public_safe`, or `review_safe` status (and retain that status in the response); recommendations and inspired-by relationships must be `approved` or `public_safe`. Every linked fragrance must also exist in the approved catalogue.

Supplier prices and codes, AED/USD prices, stock, quantities, CN codes, and commercial terms must never cross this boundary. Neither may third-party descriptions, reviews, ratings, images, comments, or user-generated content. Explicit response schemas prevent source rows from passing through to clients.

## Payloads

* Catalogue cards contain public ID and slug, title, brand, family, accords, mood, occasion, season, confidence, review status, and provenance status.
* Fragrance details add concentration, original approved description, notes, a safe vector summary, recommendation IDs, and reviewed inspired-by relationships.
* Similar-fragrance and recommendation results embed a public card with score, confidence, reason, type, and review status. Results are deterministically ranked by score and ID.
* `POST /maison/scentprint/match` accepts a `dimensions` object of known 0–1 scent dimensions, optional family/mood/occasion/season filters, and a result limit. It returns ranked catalogue cards with vector confidence and review status.

See [API contract](api-contract.md) for the complete route list and OpenAPI for generated schemas.

## Export workflow

Run `python scripts/export_maison_catalogue.py`. The command reads `catalogue_fragrances.csv`, `scent_vectors.csv`, and `recommendations.csv`, applies the API gates, writes `maison_catalogue_export.csv` and `maison_recommendation_export.csv`, and reports accepted/rejected catalogue counts. Rows and JSON cells are stable and CSV-ready.

## Website and licensing path

A future Maison website change can call these contracts through a small server-side client and cache catalogue exports; no storefront code is part of this change. A future multi-retailer layer can add tenant-scoped keys, field tiers, quotas, and audit logs around the same projection without sharing supplier data or moving intelligence into retailer repositories.

## Product SKU integration

The separate `/products` surface exposes approved product, variant, bundle, and storefront-export projections without exposing supplier or margin inputs. See [Maison product SKU catalogue](maison-product-sku-catalogue.md). Existing `/maison` fragrance-intelligence endpoints remain unchanged.
