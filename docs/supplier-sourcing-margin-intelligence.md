# Supplier sourcing and margin intelligence

## Purpose and boundary

Supplier sourcing intelligence converts private offers into internal buying decisions. Offers remain separate from public fragrance records because an offer is commercial evidence, not catalogue truth. Importing or ranking an offer never creates or promotes a public catalogue record.

Every sourcing route is mounted below the configured internal API prefix, protected by the private API key outside local environments, and tagged `internal private supplier sourcing`. Default API responses use an allowlist that omits supplier identity, prices, codes, CN codes, quantities, stock, currencies, costs, margins, and commercial terms. Raw offers and full decisions belong only under `data/private/`, which is ignored by Git.

## Comparison and preferred candidates

Offers group first by linked catalogue fragrance, then by linked match candidate, with normalised identity used only for unlinked review. Within a group, the service considers availability, match confidence, whether a usable private price exists, that private price, and deterministic supplier ordering. Duplicate offers, missing codes, implausible prices, and low match confidence become risk flags. The highest-ranked eligible offer is a *preferred candidate*, never an automatic purchase. Private price values influence ranking but are discarded when building the safe response.

## Margin scenarios

Margin intelligence combines fictional or privately supplied assumptions for fragrance oil, bottle, cap/sprayer, label, packaging, labour, wastage, fulfilment, marketplace, payment, referral, tax placeholder, and target margin. It estimates oil, packaging, total unit cost, target retail price, and gross margin. Supported formats are 10ml tester, 30ml bottle, 50ml bottle, car diffuser, body wash, moisturiser, and kit/bundle. Fee and target-margin percentages are treated as portions of retail price.

These are planning estimates: concentrations, tax treatment, wastage, fee bases, bundle contents, currency conversion, and operational costs require human validation. Reports therefore default to `pending_review`; confidence is not a guarantee of profitability.

## Review workflow

1. Stage a supplier file with the existing private import workflow.
2. Run the sourcing report, review duplicate, code, confidence, and price flags, and approve a preferred candidate manually.
3. Store cost assumptions privately and run margin scenarios for the intended formats.
4. Validate assumptions with purchasing and finance before using a scenario for product planning.
5. Share only a deliberately generated safe summary; never move a private report into tracked public data.

This supports Maison Obsidian purchasing, assortment planning, and pricing without coupling its public catalogue to supplier terms. Later, tenant-specific private storage, policy, and assumptions can support licensed retailers while preserving the same isolation boundary.
