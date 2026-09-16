# Maison product SKU catalogue

The product SKU catalogue is an allowlisted projection between AromaTwin's approved public fragrance intelligence and a future Maison Obsidian storefront. It does not replace the fragrance catalogue: a fragrance describes scent identity and evidence, while a product represents a sellable Maison concept and a variant represents its format.

## Promotion and original copy

Only approved public catalogue records are eligible. The builder may use review-safe vectors and public-safe recommendations to produce tags and summaries. It creates original copy from allowlisted scent attributes; it never copies source descriptions, reviews, ratings, images, comments, or user-generated content. Duplicate fragrance identifiers collapse to one product.

## Variants and SKUs

Deterministic SKUs use `MAISON-{BRANDSLUG}-{FRAGRANCESLUG}-{FORMAT}`. Supported formats are 10ml tester, 30ml bottle, 50ml bottle, car diffuser, body wash, moisturiser, and kit/bundle. A public retail price is an optional storefront value. Private supplier prices, landed costs, calculations, margins, stock, quantities, supplier identifiers, tariff codes, currencies and terms are neither product fields nor export fields. An internal margin scenario may inform a public selling-price suggestion upstream, but only that final approved selling price crosses this boundary.

## Bundles

Discovery, mood, season, occasion, note-family, car-diffuser, body-care layering, and approved inspired-by collection kits reference product and variant IDs. Their descriptions are original. Inspired-by collections may be assembled only from separately approved public relationship data; no third-party copy is carried into them.

## Storefront boundary

Public-safe fields include product identity, original descriptions, scent families, notes, accords, moods, occasions, seasons, tags, formats, sizes, SKUs, approved selling prices and publication status. Supplier identity and codes, CN codes, costs, margins, stock, quantities, AED/USD values, private notes, terms, copied content and UGC must never be exposed.

The read-only `/products` API and CSV exports can later feed Shopify, WooCommerce, custom storefronts, or retailer-licensing integrations. Storefront writes and website UI remain outside this repository and layer.

## Commands

```bash
python scripts/build_product_catalogue.py --bundles
python scripts/export_maison_products.py
```
